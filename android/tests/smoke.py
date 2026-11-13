# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the installed APK with adb on a disposable emulator.

UI checks use real Android controls and persisted Python preferences. Emulator
sensor injection is recorded separately from validation on a physical phone.
"""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import time
import xml.etree.ElementTree as ET

PACKAGE = 'solutions.kuky.bolha.mobile'
WINDOW_XML = '/sdcard/bolha-window.xml'
CONFIG_PATH = 'files/memory/config.json'
MEMORY_PATH = 'files/memory/bolha/nervous.json'
PET_WINDOWS = {'BolhaVisual', 'BolhaMascote', 'BolhaBrinquedo'}


def adb(*args, check=True):
    return subprocess.run(['adb', *args], check=check, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=30).stdout


def wait_for(label, predicate, seconds=25):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        result = predicate()
        # ElementTree leaf nodes are falsey even when they match a selector.
        if result is not None and result is not False:
            return result
        time.sleep(.4)
    raise AssertionError(f'Tempo esgotado: {label}')


def hierarchy():
    adb('shell', 'rm', '-f', WINDOW_XML)
    adb('shell', 'uiautomator', 'dump', WINDOW_XML, check=False)
    try:
        return list(ET.fromstring(adb('exec-out', 'cat', WINDOW_XML, check=False)).iter('node'))
    except ET.ParseError:
        return []


def bounds(node):
    values = re.findall(r'-?\d+', node.get('bounds', ''))
    return tuple(map(int, values)) if len(values) == 4 else (0, 0, 0, 0)


def find_control(nodes, text, *, exact=False, kind=None, description=False):
    for node in nodes:
        if node.get('package') != PACKAGE:
            continue
        if kind and not node.get('class', '').endswith(kind):
            continue
        value = node.get('content-desc' if description else 'text', '')
        if (value == text if exact else text in value):
            x1, y1, x2, y2 = bounds(node)
            if x2 > x1 and y2 > y1:
                return node
    return None


def scroll_container(nodes, *, backwards=False, horizontal=False):
    containers = [node for node in nodes if node.get('package') == PACKAGE
                  and node.get('scrollable') == 'true'
                  and ('HorizontalScrollView' in node.get('class', '')) == horizontal]
    if not containers:
        return False
    # The content ScrollView/ListView, rather than a fixed screen coordinate,
    # also works in landscape, on tablets, and inside a Spinner dropdown.
    node = max(containers, key=lambda item: (bounds(item)[2]-bounds(item)[0]) *
               (bounds(item)[3]-bounds(item)[1]))
    x1, y1, x2, y2 = bounds(node)
    if x2-x1 < 24 or y2-y1 < 24:
        return False
    if horizontal:
        start, end = (x1+int((x2-x1)*.8), (y1+y2)//2), (x1+int((x2-x1)*.2), (y1+y2)//2)
    else:
        start, end = ((x1+x2)//2, y1+int((y2-y1)*.8)), ((x1+x2)//2, y1+int((y2-y1)*.2))
    if backwards:
        start, end = end, start
    adb('shell', 'input', 'swipe', *(str(value) for value in (*start, *end)), '320')
    return True


def ui_signature(nodes):
    # A changing energy/trace label is not a scroll. Keep text for stable native
    # controls/dropdown rows, and geometry for other views.
    return tuple((node.get('class'), node.get('text') if node.get('class', '').endswith(
        ('Button', 'Switch', 'Spinner', 'CheckedTextView')) else '',
        node.get('content-desc'), node.get('bounds')) for node in nodes)


def control(text, *, exact=False, kind=None, description=False, scroll=True, seconds=35):
    deadline = time.monotonic() + seconds
    backwards, changes, previous = False, 0, None
    while time.monotonic() < deadline:
        nodes = hierarchy()
        found = find_control(nodes, text, exact=exact, kind=kind, description=description)
        if found is not None:
            return found
        signature = ui_signature(nodes)
        if scroll and nodes and changes < 2:
            if signature == previous:
                backwards = not backwards
                changes += 1
            if changes < 2:
                scroll_container(nodes, backwards=backwards)
            previous = signature
        else:
            time.sleep(.4)
    raise AssertionError(f'Controle não encontrado: {text}')


def tap(node):
    x1, y1, x2, y2 = bounds(node)
    assert x2 > x1 and y2 > y1, node.attrib
    adb('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))


def section(label):
    backwards, previous = False, None
    for _ in range(12):
        nodes = hierarchy()
        found = find_control(nodes, label, exact=True, kind='Button')
        if found is not None:
            tap(found)
            break
        signature = ui_signature(nodes)
        if signature == previous:
            backwards = not backwards
        assert scroll_container(nodes, backwards=backwards, horizontal=True), label
        previous = signature
    else:
        raise AssertionError(f'Seção não encontrada: {label}')
    # The content scroll offset can survive switching sections.
    previous = None
    for _ in range(8):
        nodes = hierarchy()
        signature = ui_signature(nodes)
        if signature == previous or not scroll_container(nodes, backwards=True):
            break
        previous = signature
    return label


def set_switch(label, enabled):
    node = control(label, exact=True, kind='Switch')
    assert node.get('enabled') == 'true', f'{label}: controle desabilitado'
    if node.get('checked') != str(enabled).lower():
        tap(node)
    wait_for(label, lambda: control(label, exact=True, kind='Switch', scroll=False,
             seconds=4).get('checked') == str(enabled).lower())


def set_slider(label, fraction):
    node = control(label, exact=True, kind='SeekBar', description=True)
    x1, y1, x2, y2 = bounds(node)
    # Stay inside the native SeekBar track, away from the touch target's edge.
    x = x1 + round((x2-x1) * fraction)
    adb('shell', 'input', 'swipe', str(x), str((y1+y2)//2), str(x), str((y1+y2)//2), '180')


def select_spinner(value):
    tap(control('', kind='Spinner'))
    # Native dropdown entries can have an Android resource ID while retaining
    # the owning application's package, so selectors do not depend on IDs.
    tap(control(value, exact=True, kind='TextView'))


def activity():
    result = adb('shell', 'am', 'start', '-W', '-n', f'{PACKAGE}/.MainActivity').decode()
    assert 'Status: ok' in result, result


def windows():
    return adb('shell', 'dumpsys', 'window', 'windows').decode()


def overlay_frames():
    frames = {}
    for block in re.split(r'(?=  Window #\d+ Window\{)', windows()):
        header = block.splitlines()[0] if block else ''
        name = next((value for value in PET_WINDOWS if re.search(r'\b' + value + r'\}:$', header)), None)
        if name is None:
            continue
        visible = all(value in block for value in (
            'mHasSurface=true', 'isOnScreen=true', 'isVisible=true',
            'Surface: shown=true', 'mDrawState=HAS_DRAWN'))
        frame = re.search(r'\bframe=\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]', block)
        if visible and frame:
            frames[name] = tuple(map(int, frame.groups()))
    return frames


def visible_overlay():
    return PET_WINDOWS <= overlay_frames().keys()


def screenshot(output, name):
    png = adb('exec-out', 'screencap', '-p')
    assert png[:8] == b'\x89PNG\r\n\x1a\n', 'Captura Android inválida'
    (output / name).write_bytes(png)
    return struct.unpack('>II', png[16:24])


def display_size():
    png = adb('exec-out', 'screencap', '-p')
    return struct.unpack('>II', png[16:24])


def center(frame):
    return ((frame[0]+frame[2])/2, (frame[1]+frame[3])/2)


def drag_overlay(name, output):
    start = overlay_frames()[name]
    x, y = map(round, center(start))
    width, height = display_size()
    target_x = round(width*(.25 if x > width/2 else .75))
    target_y = round(max(height*.3, y-height*.25))
    gesture = subprocess.Popen(['adb', 'shell', 'input', 'swipe', str(x), str(y),
                                str(target_x), str(target_y), '1800'])
    try:
        def moved():
            frame = overlay_frames().get(name)
            return frame is not None and abs(center(frame)[0]-x) > 35
        wait_for('arrasto de ' + name, moved, seconds=8)
        screenshot(output, 'arrasto-' + name + '.png')
        assert gesture.wait(timeout=8) == 0
        wait_for('soltura de ' + name, visible_overlay)
    finally:
        if gesture.poll() is None:
            gesture.terminate()
            gesture.wait(timeout=3)


def foreground_app(package):
    dump = adb('shell', 'dumpsys', 'activity', 'activities').decode()
    return any(package in line for line in dump.splitlines() if 'topResumedActivity=' in line)


def private_json(path):
    try:
        return json.loads(adb('shell', 'run-as', PACKAGE, 'cat', path, check=False))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def preference(key, expected):
    data = private_json(CONFIG_PATH)
    return data is not None and data.get('preferences', {}).get(key) == expected


def saved_preference(key):
    data = private_json(CONFIG_PATH)
    return None if data is None else data.get('preferences', {}).get(key)


def saved_memory(path, since):
    saved = private_json(path)
    return saved if saved is not None and saved.get('saved_at', 0) > since else None


def preserved_memory(path, before):
    after = saved_memory(path, before['saved_at'])
    if (after is not None and after.get('seed') == before['seed']
            and after.get('learned') == before['learned']):
        return after
    return None


def try_emulator_shake(output, supported):
    result = {'sensorDisponivelNaInterface': supported, 'validado': False}
    if not supported:
        result['limite'] = 'Emulador sem sensor de movimento disponível.'
        return result
    status = adb('emu', 'sensor', 'status', check=False).decode(errors='replace')
    (output / 'sensores-emulador.txt').write_text(status, encoding='utf-8')
    sensor = 'linear-acceleration' if 'linear-acceleration' in status else 'acceleration'
    result['sensorInjetado'] = sensor
    if 'acceleration' not in status or 'KO:' in status:
        result['limite'] = 'O console deste emulador não oferece injeção de aceleração.'
        return result
    # With roaming off, reject natural movement as evidence of a shake.
    baseline = []
    deadline = time.monotonic()+12
    while time.monotonic() < deadline:
        frame = overlay_frames().get('BolhaBrinquedo')
        if frame:
            baseline.append(center(frame))
            baseline = baseline[-5:]
        if len(baseline) == 5 and max(abs(point[0]-baseline[0][0])+abs(point[1]-baseline[0][1])
                                      for point in baseline) < 5:
            break
        time.sleep(.3)
    if len(baseline) < 5 or max(abs(point[0]-baseline[0][0])+abs(point[1]-baseline[0][1])
                              for point in baseline) >= 5:
        result['limite'] = 'Brinquedo em movimento; a geometria não distingue o gesto do movimento natural.'
        return result
    origin = baseline[-1]
    z = 0 if sensor == 'linear-acceleration' else 9.81
    responses = []
    try:
        responses.append(adb('emu', 'sensor', 'set', sensor, f'0:0:{z}', check=False).decode(errors='replace'))
        time.sleep(.3)
        responses.append(adb('emu', 'sensor', 'set', sensor, f'24:0:{z}', check=False).decode(errors='replace'))
        time.sleep(.15)
        responses.append(adb('emu', 'sensor', 'set', sensor, f'-24:0:{z}', check=False).decode(errors='replace'))
        if any('KO:' in response for response in responses):
            result['respostasConsole'] = responses
            result['limite'] = 'O console recusou a injeção deste sensor; validação física segue pendente.'
            return result
        trace = []
        deadline = time.monotonic()+3
        while time.monotonic() < deadline:
            frames = overlay_frames()
            trace.append({key: list(center(value)) for key, value in frames.items()})
            if 'BolhaBrinquedo' in frames:
                x, y = center(frames['BolhaBrinquedo'])
                if abs(x-origin[0])+abs(y-origin[1]) > 20:
                    result['validado'] = True
            time.sleep(.1)
        result['origemBrinquedo'] = list(origin)
        result['janelasDepoisDosPicos'] = trace
        result['respostasConsole'] = responses
        if not result['validado']:
            result['limite'] = 'Injeção não confirmou deslocamento; validação física segue pendente. Testes Java e Python cobrem detecção e impulso.'
        screenshot(output, 'chacoalhar-emulador.png')
    finally:
        adb('emu', 'sensor', 'set', sensor, f'0:0:{z}', check=False)
    return result


def migrate_previous(apk, output):
    """Exercise an actual APK upgrade, without clearing its private data."""
    adb('install', '-r', str(apk))
    activity()
    control('470 neurônios', scroll=False)
    tap(control('Carinho', exact=True, kind='Button', scroll=False))
    legacy_haptics = control('Vibração', exact=True)
    if legacy_haptics.get('checked') == 'true':
        tap(legacy_haptics)
    assert control('Vibração', exact=True).get('checked') == 'false'
    wait_for('preferência antiga de vibração salva', lambda: b'name="haptics" value="false"' in
             adb('shell', 'run-as', PACKAGE, 'cat', 'shared_prefs/options.xml', check=False))
    adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
    before = wait_for('memória gravada pelo APK anterior', lambda: saved_memory(MEMORY_PATH, 0))
    assert before['seed'] == 1313 and before.get('learned'), before
    (output / 'memoria-versao-anterior.json').write_text(json.dumps(before, ensure_ascii=False,
        indent=2)+'\n', encoding='utf-8')
    adb('shell', 'am', 'force-stop', PACKAGE)
    assert not adb('shell', 'pidof', PACKAGE, check=False).strip()
    return before


def smoke(apk, output, previous_apk=None):
    passed, pending, artifacts_errors = [], ['Chacoalhar e vibração em um celular físico.'], []
    rotation_settings = None
    shake_result = {}
    completed = False
    try:
        adb('logcat', '-c')
        adb('shell', 'settings', 'put', 'secure', 'anr_show_background', '0')
        page_size = adb('shell', 'getconf', 'PAGE_SIZE').decode().strip()
        print(f'Android page size: {page_size}', flush=True)
        previous_memory = migrate_previous(previous_apk, output) if previous_apk else None
        adb('install', '-r', str(apk))
        activity()
        wait_for('atividade da Bolha em primeiro plano', lambda: foreground_app(PACKAGE))
        control('470 neurônios', scroll=False)
        if previous_memory is not None:
            wait_for('vibração antiga migrada para as preferências do cérebro',
                     lambda: preference('hapticsEnabled', False))
            adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
            upgraded_memory = wait_for('memória antiga carregada e regravada pela nova versão',
                lambda: preserved_memory(MEMORY_PATH, previous_memory))
            (output / 'memoria-migrada.json').write_text(json.dumps(upgraded_memory,
                ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
            passed.append('Atualização real do APK anterior com install -r: assinatura aceita, semente, aprendizado e vibração desligada preservados')
            activity()
            control('470 neurônios', scroll=False)
        for action in ('Carinho', 'Dormir / acordar', 'Dormir / acordar'):
            tap(control(action, exact=True, kind='Button', scroll=False))
        # Toggle twice so the initially visible toy is still available for drags.
        tap(control('Brinquedo', exact=True, kind='Button', scroll=False))
        tap(control('Brinquedo', exact=True, kind='Button', scroll=False))
        screenshot(output, 'aplicativo.png')
        passed.append('APK instalado; sessão e 470 neurônios ativos; carinho, sono e brinquedo exercitados')

        tap(control('Central da Bolha', exact=True, kind='Button', scroll=False))
        section('Aparência')
        screenshot(output, 'central.png')
        set_slider('Tamanho da Bolha', .72)
        size = wait_for('tamanho salvo', lambda: value if isinstance(
            value := saved_preference('avatarSize'), (int, float)) and 140 <= value <= 180 else False)
        set_switch('Boca nas expressões', False)
        wait_for('boca desligada salva', lambda: preference('mouthEnabled', False))
        select_spinner('Bolinha')
        wait_for('formato bolinha salvo', lambda: preference('toyAppearance', 'ball'))
        select_spinner('Amendoim')
        wait_for('formato amendoim salvo', lambda: preference('toyAppearance', 'peanut'))
        passed.append('Central: tamanho persistido, boca desligada e troca entre bolinha e amendoim')

        section('Comportamento')
        set_switch('Passear e explorar', False)
        wait_for('passeio pausado salvo', lambda: preference('roaming', False))
        motion = control('Reagir ao chacoalhar', exact=True, kind='Switch')
        supported = motion.get('enabled') == 'true'
        if supported:
            control('Sensor de movimento disponível.')
            set_switch('Reagir ao chacoalhar', True)
            wait_for('movimento ativado salvo', lambda: preference('shakeEnabled', True))
        else:
            assert motion.get('checked') == 'false'
            control('não oferece um sensor de movimento compatível.')
        set_switch('Vibração', False)
        wait_for('preferência de vibração salva', lambda: preference('hapticsEnabled', False)
                 and b'name="haptics" value="false"' in adb('shell', 'run-as', PACKAGE,
                     'cat', 'shared_prefs/options.xml', check=False))
        passed.append('Comportamento: passeio pausado, disponibilidade do sensor e vibração desligada persistida')

        section('Cérebro')
        control('rede de 470 neurônios')
        graph = control('Atividade dos neurônios da Bolha.', description=True, scroll=False)
        tap(graph)
        control('Neurônio ', scroll=False)
        screenshot(output, 'cerebro.png')
        passed.append('Cérebro: rede real informada pelo motor, neurônio selecionável e atividade inspecionada')

        section('Atividades')
        # Notebook begins visible, so both presses exercise hide and show.
        tap(control('Notebook', exact=True, kind='Button'))
        tap(control('Notebook', exact=True, kind='Button'))
        tap(control('Mostrar / guardar brinquedo', exact=True, kind='Button'))
        tap(control('Mostrar / guardar brinquedo', exact=True, kind='Button'))
        control('Testar expressões')
        select_spinner('bravo')
        tap(control('Ver expressão', exact=True, kind='Button'))
        screenshot(output, 'expressao-brava.png')
        tap(control('Encerrar teste', exact=True, kind='Button'))
        passed.append('Atividades: notebook, brinquedo e prévia de expressão brava sem aprendizado')

        section('Privacidade')
        app_context = control('Reconhecer aplicativo ativo', exact=True, kind='Switch')
        assert app_context.get('checked') == 'false'
        assert preference('senseApp', False)
        control('Acesso de uso ainda desligado no Android.')
        passed.append('Privacidade: leitura de aplicativo ativo continua desligada sem conceder acesso de uso')
        tap(control('Voltar', exact=True, kind='Button', scroll=False))
        control('470 neurônios', scroll=False)
        screenshot(output, 'aplicativo-configurado.png')

        tap(control('Flutuar', exact=True, kind='Button', scroll=False))
        wait_for('configuração de sobreposição do Android', lambda: foreground_app('com.android.settings'))
        adb('shell', 'appops', 'set', PACKAGE, 'SYSTEM_ALERT_WINDOW', 'allow')
        adb('shell', 'pm', 'grant', PACKAGE, 'android.permission.POST_NOTIFICATIONS')
        adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
        wait_for('criação das janelas após autorizar a sobreposição', lambda: all(name in windows() for name in PET_WINDOWS))
        adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
        wait_for('mascote e brinquedo visíveis sobre o launcher', lambda: visible_overlay() and foreground_app('com.android.launcher3'))
        services = adb('shell', 'dumpsys', 'activity', 'services', PACKAGE).decode()
        assert 'FloatingBolha' in services and 'isForeground=true' in services, services
        (output / 'janelas-flutuantes.txt').write_text(windows(), encoding='utf-8')
        screenshot(output, 'flutuante.png')
        passed.append('Permissão Android; desenho e áreas de interação da mascote e brinquedo visíveis sobre o launcher; serviço em primeiro plano')
        for name in ('BolhaMascote', 'BolhaBrinquedo'):
            drag_overlay(name, output)
        passed.append('Arrasto e soltura da mascote e do brinquedo sobre outro aplicativo')

        try:
            shake_result = try_emulator_shake(output, supported)
        except subprocess.SubprocessError as error:
            shake_result = {'validado': False, 'limite': f'Console do sensor indisponível: {error}'}
        (output / 'chacoalhar.json').write_text(json.dumps(shake_result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        if shake_result['validado']:
            passed.append('Emulador: dois picos de aceleração e deslocamento observado do brinquedo solto')
        else:
            pending.append(shake_result['limite'])
        wait_for('sessão flutuante mantida após teste do sensor', visible_overlay)

        rotation_settings = {key: adb('shell', 'settings', 'get', 'system', key).decode().strip()
                             for key in ('accelerometer_rotation', 'user_rotation')}
        adb('shell', 'settings', 'put', 'system', 'accelerometer_rotation', '0')
        adb('shell', 'settings', 'put', 'system', 'user_rotation', '1')
        try:
            wait_for('orientação horizontal', lambda: display_size()[0] > display_size()[1], seconds=12)
        except AssertionError:
            pending.append('Rotação horizontal indisponível nesta imagem de emulador.')
        else:
            wait_for('janelas reposicionadas em paisagem', visible_overlay)
            screenshot(output, 'paisagem.png')
            passed.append('Orientação horizontal: mascote e brinquedo continuam desenhados após redimensionar')
        adb('shell', 'settings', 'put', 'system', 'user_rotation', '0')
        wait_for('retorno à orientação vertical', lambda: display_size()[1] > display_size()[0], seconds=15)
        wait_for('janelas restauradas em retrato', visible_overlay)

        activity()
        tap(control('Parar de flutuar', exact=True, kind='Button', scroll=False))
        wait_for('remoção das janelas', lambda: all(name not in windows() for name in PET_WINDOWS))
        control('470 neurônios', scroll=False)
        tap(control('Central da Bolha', exact=True, kind='Button', scroll=False))
        section('Comportamento')
        if supported:
            set_switch('Reagir ao chacoalhar', False)
            wait_for('movimento desligado salvo', lambda: preference('shakeEnabled', False))
        tap(control('Voltar', exact=True, kind='Button', scroll=False))
        previous_save = wait_for('memória inicial disponível', lambda: saved_memory(MEMORY_PATH, 0))
        adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
        wait_for('posição gravada', lambda: b'"x"' in adb('shell', 'run-as', PACKAGE,
                 'cat', 'files/memory/position.json', check=False))
        before = wait_for('gravação concluída antes de encerrar o processo', lambda: saved_memory(MEMORY_PATH, previous_save['saved_at']))
        assert before['seed'] == 1313
        assert before.get('learned'), 'Aprendizado ausente do arquivo neural'
        adb('shell', 'am', 'force-stop', PACKAGE)
        assert not adb('shell', 'pidof', PACKAGE, check=False).strip()
        activity()
        control('470 neurônios', scroll=False)
        tap(control('Central da Bolha', exact=True, kind='Button', scroll=False))
        section('Aparência')
        assert preference('avatarSize', size) and preference('mouthEnabled', False)
        assert control('Boca nas expressões', exact=True, kind='Switch').get('checked') == 'false'
        section('Comportamento')
        assert control('Vibração', exact=True, kind='Switch').get('checked') == 'false'
        assert preference('hapticsEnabled', False) and preference('shakeEnabled', False)
        assert preference('senseApp', False) and preference('toyAppearance', 'peanut')
        adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
        after = wait_for('aprendizado preservado após reiniciar o processo', lambda: preserved_memory(MEMORY_PATH, before))
        (output / 'memoria-reaberta.json').write_text(json.dumps(after, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        passed.append('Sobreposição encerrada; processo reiniciado; semente, aprendizado, tamanho, boca e privacidade recuperados')
        completed = True
        print('\n'.join(passed), flush=True)
    finally:
        if rotation_settings:
            for key, value in rotation_settings.items():
                try:
                    adb('shell', 'settings', 'delete' if value == 'null' else 'put', 'system', key,
                        *(() if value == 'null' else (value,)), check=False)
                except (subprocess.SubprocessError, OSError) as error:
                    artifacts_errors.append(f'restaurar {key}: {error}')
        captures = {
            'logcat.txt': lambda: adb('logcat', '-d', check=False),
            'janelas.txt': lambda: windows().encode('utf-8'),
            'atividades.txt': lambda: adb('shell', 'dumpsys', 'activity', 'activities'),
            'sensores-android.txt': lambda: adb('shell', 'dumpsys', 'sensorservice', check=False),
            'memoria-final.json': lambda: adb('shell', 'run-as', PACKAGE, 'cat', MEMORY_PATH, check=False),
            'preferencias-final.json': lambda: adb('shell', 'run-as', PACKAGE, 'cat', CONFIG_PATH, check=False),
            'interface.xml': lambda: (hierarchy(), adb('exec-out', 'cat', WINDOW_XML, check=False))[1],
            'diagnostico.png': lambda: adb('exec-out', 'screencap', '-p'),
        }
        for name, capture in captures.items():
            try:
                (output / name).write_bytes(capture())
            except (subprocess.SubprocessError, OSError) as error:
                artifacts_errors.append(f'{name}: {error}')
        (output / 'relatorio.json').write_text(json.dumps({'concluido': completed, 'validado': passed,
            'pendente': pending, 'chacoalhar': shake_result, 'errosDeCaptura': artifacts_errors},
            indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--previous-apk', type=Path, default=os.environ.get('BOLHA_TEST_PREVIOUS_APK'),
                        help='Instala e migra um APK anterior antes do restante do teste; preserva os dados.')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    smoke(args.apk, args.output, args.previous_apk)
