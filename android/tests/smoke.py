# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the installed APK with adb on a disposable emulator."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

PACKAGE = 'solutions.kuky.bolha.mobile'
WINDOW_XML = '/sdcard/bolha-window.xml'


def adb(*args, check=True):
    return subprocess.run(['adb', *args], check=check, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=30).stdout


def wait_for(label, predicate, seconds=25):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        result = predicate()
        if result is not None and result is not False:
            return result
        time.sleep(.4)
    raise AssertionError(f'Tempo esgotado: {label}')


def hierarchy():
    adb('shell', 'rm', '-f', WINDOW_XML)
    adb('shell', 'uiautomator', 'dump', WINDOW_XML, check=False)
    try:
        return ET.fromstring(adb('exec-out', 'cat', WINDOW_XML, check=False)).iter('node')
    except ET.ParseError:
        return ()


def control(text):
    return wait_for(text, lambda: next((node for node in hierarchy()
        if text in node.get('text', '') and node.get('package') == PACKAGE), None),
        seconds=35)


def tap(node):
    x1, y1, x2, y2 = map(int, re.findall(r'\d+', node.get('bounds', '')))
    adb('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))


def activity():
    result = adb('shell', 'am', 'start', '-W', '-n', f'{PACKAGE}/.MainActivity').decode()
    assert 'Status: ok' in result, result


def windows():
    return adb('shell', 'dumpsys', 'window', 'windows').decode()


def overlay_frames():
    frames = {}
    for block in re.split(r'(?=  Window #\d+ Window\{)', windows()):
        header = block.splitlines()[0] if block else ''
        for name in ('BolhaMascote', 'BolhaBrinquedo'):
            if not re.search(r'\b' + name + r'\}:$', header):
                continue
            visible = all(value in block for value in (
                'mHasSurface=true', 'isOnScreen=true', 'isVisible=true',
                'Surface: shown=true', 'mDrawState=HAS_DRAWN'))
            frame = re.search(r'\bframe=\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]', block)
            if visible and frame:
                frames[name] = tuple(map(int, frame.groups()))
    return frames


def visible_overlay():
    return len(overlay_frames()) == 2


def drag_overlay(name, output):
    bounds = overlay_frames()[name]
    x, y = (bounds[0]+bounds[2])//2, (bounds[1]+bounds[3])//2
    target_x = 300 if x > 500 else 700
    target_y = max(300, y-330)
    gesture = subprocess.Popen(['adb', 'shell', 'input', 'swipe', str(x), str(y),
                                str(target_x), str(target_y), '1800'])
    try:
        def moved():
            frame = overlay_frames().get(name)
            return frame is not None and abs((frame[0]+frame[2])/2-x) > 35
        wait_for('arrasto de ' + name, moved, seconds=8)
        (output / ('arrasto-' + name + '.png')).write_bytes(adb('exec-out', 'screencap', '-p'))
        assert gesture.wait(timeout=8) == 0
        wait_for('soltura de ' + name, visible_overlay)
    finally:
        if gesture.poll() is None:
            gesture.terminate()
            gesture.wait(timeout=3)


def foreground_app(package):
    dump = adb('shell', 'dumpsys', 'activity', 'activities').decode()
    return any(package in line for line in dump.splitlines() if 'topResumedActivity=' in line)


def smoke(apk, output):
    passed = []
    try:
        adb('logcat', '-c')
        adb('shell', 'settings', 'put', 'secure', 'anr_show_background', '0')
        page_size = adb('shell', 'getconf', 'PAGE_SIZE').decode().strip()
        print(f'Android page size: {page_size}', flush=True)
        adb('install', '-r', str(apk))
        activity()
        wait_for('atividade da Bolha em primeiro plano', lambda: foreground_app(PACKAGE))
        control('470 neurônios')
        for action in ('Carinho', 'Dormir / acordar', 'Dormir / acordar', 'Bola / amendoim'):
            tap(control(action))
        (output / 'aplicativo.png').write_bytes(adb('exec-out', 'screencap', '-p'))
        passed.append('APK instalado; sessão e 470 neurônios ativos; comandos da interface exercitados')

        haptics = control('Vibração')
        assert haptics.get('checked') == 'true'
        tap(haptics)
        assert control('Vibração').get('checked') == 'false'
        wait_for('preferência de vibração salva', lambda: b'name="haptics" value="false"' in
                 adb('shell', 'run-as', PACKAGE, 'cat', 'shared_prefs/options.xml', check=False))
        passed.append('Preferência de vibração salva com o controle desligado')

        tap(control('Flutuar'))
        wait_for('configuração de sobreposição do Android', lambda:
                 foreground_app('com.android.settings'))
        adb('shell', 'appops', 'set', PACKAGE, 'SYSTEM_ALERT_WINDOW', 'allow')
        adb('shell', 'pm', 'grant', PACKAGE, 'android.permission.POST_NOTIFICATIONS')
        adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
        wait_for('criação das janelas após autorizar a sobreposição', lambda:
                 all(name in windows() for name in ('BolhaMascote', 'BolhaBrinquedo')))
        adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
        wait_for('mascote e brinquedo visíveis sobre o launcher', lambda:
                 visible_overlay() and foreground_app('com.android.launcher3'))
        services = adb('shell', 'dumpsys', 'activity', 'services', PACKAGE).decode()
        assert 'FloatingBolha' in services and 'isForeground=true' in services, services
        (output / 'janelas-flutuantes.txt').write_text(windows(), encoding='utf-8')
        (output / 'flutuante.png').write_bytes(adb('exec-out', 'screencap', '-p'))
        passed.append('Permissão Android; mascote e brinquedo desenhados e visíveis sobre o launcher; serviço em primeiro plano')
        for name in ('BolhaMascote', 'BolhaBrinquedo'):
            drag_overlay(name, output)
        passed.append('Arrasto e soltura da mascote e do brinquedo sobre outro aplicativo')

        activity()
        tap(control('Parar de flutuar'))
        wait_for('remoção das duas janelas', lambda: all(
            name not in windows() for name in ('BolhaMascote', 'BolhaBrinquedo')))
        control('470 neurônios')
        memory_path = 'files/memory/bolha/nervous.json'
        previous_save = wait_for('memória inicial disponível', lambda: saved_memory(memory_path, 0))
        adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
        wait_for('memória gravada', lambda: b'"x"' in adb(
            'shell', 'run-as', PACKAGE, 'cat', 'files/memory/position.json', check=False))
        before = wait_for('gravação concluída antes de encerrar o processo', lambda:
                          saved_memory(memory_path, previous_save['saved_at']))
        assert before['seed'] == 1313
        adb('shell', 'am', 'force-stop', PACKAGE)
        assert not adb('shell', 'pidof', PACKAGE, check=False).strip()
        activity()
        control('470 neurônios')
        assert control('Vibração').get('checked') == 'false'
        adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
        after = wait_for('aprendizado preservado após reiniciar o processo', lambda:
            preserved_memory(memory_path, before))
        (output / 'memoria-reaberta.json').write_text(json.dumps(after, ensure_ascii=False,
            indent=2) + '\n', encoding='utf-8')
        passed.append('Sobreposição encerrada; processo reiniciado; semente, aprendizado e preferência recuperados')
        print('\n'.join(passed))
    finally:
        (output / 'logcat.txt').write_bytes(adb('logcat', '-d', check=False))
        (output / 'janelas.txt').write_text(windows(), encoding='utf-8')
        (output / 'atividades.txt').write_bytes(adb('shell', 'dumpsys', 'activity', 'activities'))
        (output / 'memoria-final.json').write_bytes(adb('shell', 'run-as', PACKAGE,
            'cat', 'files/memory/bolha/nervous.json', check=False))
        adb('shell', 'uiautomator', 'dump', WINDOW_XML, check=False)
        (output / 'interface.xml').write_bytes(adb('exec-out', 'cat', WINDOW_XML, check=False))
        if not (output / 'flutuante.png').exists():
            (output / 'diagnostico.png').write_bytes(adb('exec-out', 'screencap', '-p'))
        (output / 'relatorio.json').write_text(json.dumps({'validado': passed},
            indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def saved_memory(path, since):
    try:
        saved = json.loads(adb('shell', 'run-as', PACKAGE, 'cat', path, check=False))
    except json.JSONDecodeError:
        return None
    return saved if saved.get('saved_at', 0) > since else None


def preserved_memory(path, before):
    after = saved_memory(path, before['saved_at'])
    if (after is not None and after.get('seed') == before['seed']
            and after.get('learned') == before['learned']):
        return after
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    smoke(args.apk, args.output)
