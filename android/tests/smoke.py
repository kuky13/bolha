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


def visible_overlay():
    dump = windows()
    return all(name in dump for name in ('BolhaMascote', 'BolhaBrinquedo'))


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
        wait_for('ativação ao retornar das configurações', visible_overlay)
        adb('shell', 'am', 'start', '-W', '-a', 'android.settings.SETTINGS')
        wait_for('mascote e brinquedo sobre outro aplicativo', lambda:
                 visible_overlay() and foreground_app('com.android.settings'))
        services = adb('shell', 'dumpsys', 'activity', 'services', PACKAGE).decode()
        assert 'FloatingBolha' in services and 'isForeground=true' in services, services
        (output / 'flutuante.png').write_bytes(adb('exec-out', 'screencap', '-p'))
        passed.append('Permissão Android; mascote e brinquedo sobre outro app; serviço em primeiro plano')

        activity()
        tap(control('Parar de flutuar'))
        wait_for('remoção das duas janelas', lambda: all(
            name not in windows() for name in ('BolhaMascote', 'BolhaBrinquedo')))
        control('470 neurônios')
        adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
        wait_for('memória gravada', lambda: b'"x"' in adb(
            'shell', 'run-as', PACKAGE, 'cat', 'files/memory/position.json', check=False))
        activity()
        control('470 neurônios')
        assert control('Vibração').get('checked') == 'false'
        passed.append('Sobreposição encerrada; sessão, memória e preferência recuperadas')
        print('\n'.join(passed))
    finally:
        (output / 'logcat.txt').write_bytes(adb('logcat', '-d', check=False))
        (output / 'janelas.txt').write_text(windows(), encoding='utf-8')
        (output / 'atividades.txt').write_bytes(adb('shell', 'dumpsys', 'activity', 'activities'))
        adb('shell', 'uiautomator', 'dump', WINDOW_XML, check=False)
        (output / 'interface.xml').write_bytes(adb('exec-out', 'cat', WINDOW_XML, check=False))
        if not (output / 'flutuante.png').exists():
            (output / 'diagnostico.png').write_bytes(adb('exec-out', 'screencap', '-p'))
        (output / 'relatorio.json').write_text(json.dumps({'validado': passed},
            indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    smoke(args.apk, args.output)
