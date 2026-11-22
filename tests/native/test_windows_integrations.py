import asyncio
import ctypes
from ctypes import wintypes
import json
from types import SimpleNamespace as NS

import pytest
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel, QMenu, QProgressBar, QSystemTrayIcon, QVBoxLayout, QWidget

from bolha.battery_panel import BatteryPanel, panel_position
from bolha.cursor_finder import locate
from bolha.preferences import PreferencesStore, defaults, sanitize
from bolha.windows_battery import BatteryAlerts, BatteryMonitor, parse_devices
from bolha.windows_hotkeys import DoubleTap, Hotkeys, RawHeader, binding
from bolha.windows_media import SpotifyReaction, session_operation
from bolha.windows_settings import WindowsSettings


def test_double_tap_counts_releases_and_rejects_holds_combinations_and_repeat():
    tap = DoubleTap()
    assert not tap.event(True, True, 0)
    assert not tap.event(True, True, .025)
    assert not tap.event(True, False, .05)
    assert not tap.event(True, True, .18)
    assert tap.event(True, False, .24)
    assert not tap.event(True, True, 1)
    assert not tap.event(False, True, 1.025)
    assert not tap.event(True, False, 1.05)
    assert not tap.event(True, True, 1.18)
    assert not tap.event(True, False, 1.22)
    assert not tap.event(True, True, 2)
    assert not tap.event(True, False, 2.4)
    assert not tap.event(True, True, 2.5, modified=True)
    assert not tap.event(True, False, 2.6)


def test_shortcuts_reserve_panic_and_use_layout_to_locate_punctuation():
    def scan(character):
        return {ord('='): 0xBB, ord('b'): ord('B'), ord('+'): 0x1BB}.get(character, -1)
    assert binding('Ctrl+=', scan) == (2, 0xBB)
    assert binding('Ctrl++', scan) == (6, 0xBB)
    assert binding('Alt esquerdo', scan, double=True) == (0, 0xA4)
    for value in ('Ctrl+Alt+Shift+B', 'Esc', 'F12', 'Q'):
        with pytest.raises(ValueError):
            binding(value, scan)
    assert binding('Ctrl+=', lambda _: 0xA5) == (2, 0xA5)
    with pytest.raises(ValueError):
        binding('Ctrl++', scan, double=True)


def test_cursor_detects_negative_screen_taskbar_gap_and_fullscreen():
    areas = [(-1920, 60, -640, 740), (0, 0, 1920, 1040), (1920, -500, 2880, 200)]
    monitors = [(-1920, 60, -640, 780), (0, 0, 1920, 1080), (1920, -500, 2880, 220)]
    assert locate((-1890, 766), areas, monitors, set()) == (0, (-1890, 766), None)
    index, _, arrow = locate((-1200, 210), areas, monitors, {0})
    assert index == 1 and abs(arrow) > 2.9
    index, _, arrow = locate((-400, 380), areas, monitors, set())
    assert index == 0 and abs(arrow) < .1
    assert locate((10, 400), areas, monitors, {0, 1, 2}) is None
    assert locate((-1200, 210), areas[1:], monitors[1:], set())[0] == 0


class Status:
    PLAYING, PAUSED, STOPPED, OPENED = range(4)


class Session:
    def __init__(self, source, status):
        self.source_app_user_model_id = source
        self.status = status
        self.commands = []

    def get_playback_info(self):
        return NS(playback_status=self.status, controls=NS(is_pause_enabled=True, is_play_enabled=True))

    async def try_get_media_properties_async(self):
        return NS(title='  Lua\n Cheia ', artist='Banda Coração')

    async def try_pause_async(self):
        self.commands.append('pause')
        return True

    async def try_play_async(self):
        self.commands.append('play')
        return True


def test_media_uses_current_session_and_spotify_requires_desktop_playing():
    browser = Session('browser.spotify.exe', Status.PAUSED)
    store = Session('SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify', Status.PLAYING)
    client = Session('Spotify.exe', Status.PAUSED)

    class Manager:
        @classmethod
        async def request_async(cls):
            return NS(get_current_session=lambda: browser, get_sessions=lambda: [browser, client, store])
    assert asyncio.run(session_operation(Manager, Status, 'toggle'))
    assert browser.commands == ['play'] and not client.commands and not store.commands
    assert asyncio.run(session_operation(Manager, Status, 'spotify')) == ('Lua Cheia', 'Banda Coração')
    store.status = Status.PAUSED
    browser.status = Status.PLAYING
    assert asyncio.run(session_operation(Manager, Status, 'spotify')) is None
    assert asyncio.run(session_operation(Manager, Status, 'toggle'))
    assert browser.commands == ['play', 'pause']


def test_spotify_reactions_have_cooldown_and_dont_repeat_on_pause_resume():
    policy = SpotifyReaction()
    assert 'Lua' in policy.observe(('Lua', 'Banda'), 2, True)
    assert policy.observe(None, 320, True) is None
    assert policy.observe(('Lua', 'BANDA'), 350, True) is None
    assert policy.observe(('Outra', 'Banda'), 360, False) is None
    assert policy.observe(('Outra', 'Banda'), 380, True) is None
    assert 'Orelha' in policy.observe(('Orelha', ''), 381, True)
    assert policy.observe(('Breve', ''), 385, True) is None


def test_battery_parses_utf8_suppresses_initial_alert_and_requires_recovery():
    def readings(percent, **fields):
        data = [dict(key='a', name='Fone Pêssego', percent=percent, **fields)]
        return parse_devices(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    alerts = BatteryAlerts()
    assert 'Indisponível' in readings(-1)[0].display
    assert 'Média' in readings(-1, level='Média')[0].display
    assert 'repouso' in readings(-1, asleep=True, connected=False)[0].display
    assert not readings(12, connected=False)
    assert not alerts.observe(readings(7), 15, True)
    assert not alerts.observe(readings(28), 15, True)
    assert not alerts.observe(readings(7, asleep=True), 15, True)
    assert alerts.observe(readings(15), 15, True)[0].display == 'Fone Pêssego · 15%'
    assert not alerts.observe([], 15, True)
    assert not alerts.observe(readings(14), 15, True)
    assert not alerts.observe(readings(28), 15, True)
    assert not alerts.observe(readings(11), 15, False)
    with pytest.raises(ValueError):
        parse_devices(b'"corrupt"')


def test_settings_capture_and_individual_values(qt_application, tmp_path):
    shell = QWidget()
    battery = BatteryMonitor(lambda _: None, tmp_path)
    features = NS(battery=battery, battery_panel=NS(toggle=lambda: None),
                  shortcut_status='', media=NS(status=''), capture_shortcut=lambda _: None)
    settings = WindowsSettings(QVBoxLayout(shell), features, lambda: None)
    settings.load(defaults())
    assert settings.values()['finderKey'] == 'Alt esquerdo'
    settings.finder_key.begin()
    QTest.keyClick(settings.finder_key, Qt.Key_F8)
    settings.media_key.begin()
    QTest.keyClick(settings.media_key, Qt.Key_Equal, Qt.ControlModifier)
    assert settings.values()['finderKey'] == 'F8'
    assert settings.values()['mediaKey'] == 'Ctrl+='
    prefs = sanitize(dict(settings.values(), batteryThreshold=-9))
    assert prefs['batteryThreshold'] == 1
    assert prefs['batteryEnabled'] and prefs['spotifyEnabled']
    shell.close()


def test_battery_popup_pins_awake_devices_and_stays_inside_taskbar_screen(qt_application, tmp_path, monkeypatch):
    monkeypatch.setattr('bolha.battery_panel.getpass.getuser', lambda: 'Conta <local>')
    monitor = BatteryMonitor(lambda _: None, tmp_path)
    monitor.enabled = True
    monitor.devices = parse_devices(json.dumps([
        dict(key='a', name='A sleeping', percent=20, asleep=True, kind=['unknown']),
        dict(key='z', name='Z <connected>', percent=80, kind='mouse'),
    ]).encode())
    tray = QSystemTrayIcon()
    tray.show()
    panel = BatteryPanel(monitor, tray)
    labels = [label.text() for label in panel.scroll.widget().findChildren(QLabel)]
    assert labels.index('Z <connected>') < labels.index('A sleeping')
    assert [device.kind for device in monitor.devices] == ['other', 'mouse']
    icons = panel.scroll.widget().findChildren(QLabel, 'batteryDeviceIcon')
    assert len(icons) == 2 and all(not icon.pixmap().isNull() for icon in icons)
    assert icons[0].pixmap().toImage() != icons[1].pixmap().toImage()
    assert 'Z &lt;connected&gt;' in icons[0].toolTip()
    assert 'Conta &lt;local&gt;' in icons[0].toolTip()
    panel.toggle()
    assert panel.isVisible()
    monitor.configure(False, 15, True)
    assert panel.isVisible() and tray.isVisible()
    assert not panel.scroll.isVisible()
    panel.close()
    tray.hide()
    screen = QRect(-960, 0, 960, 680)
    work = QRect(-960, 24, 960, 656)
    pos = panel_position(work, screen, QRect(-42, 0, 20, 20), QSize(300,200))
    assert work.contains(QRect(pos, QSize(300,200)))
    assert pos.y() >= 24


def test_raw_mouse_button_down_releases_without_consuming_click():
    events = []
    header_length = ctypes.sizeof(RawHeader)
    message = wintypes.MSG(message=0xFF)

    def native_packet(flags):
        def receive(_handle, _command, buffer, _size, _header):
            ctypes.memset(buffer, 0, len(buffer))
            ctypes.c_uint16.from_buffer(buffer, header_length + 4).value = flags
            return header_length + 24
        return receive

    hotkeys = NS(active={}, raw=True, mouse_callback=lambda: events.append('release'),
                 editing=lambda: False, input_buffer=ctypes.create_string_buffer(header_length + 24))
    for flags in (0, 0x2, 0x400, 0x4):
        hotkeys.user = NS(GetRawInputData=native_packet(flags))
        assert Hotkeys.nativeEventFilter(hotkeys, 'windows_generic_MSG', ctypes.addressof(message)) == (False,0)
    assert events == ['release']


def test_battery_popup_renders_worker_snapshot_after_hidden_and_unknown_charge(qt_application, tmp_path):
    monitor = BatteryMonitor(lambda _: None, tmp_path)
    monitor.enabled = True
    tray = QSystemTrayIcon()
    panel = BatteryPanel(monitor, tray)
    monitor._status('Nenhum periférico compatível encontrado.')
    assert not panel.scroll.widget().findChildren(QLabel, 'batteryDeviceIcon')

    rows = [
        dict(key='usb', name='Fone USB', kind='headset', percent=80, via='HeadsetControl'),
        dict(key='bt', name='Teclado Bluetooth', kind='keyboard', percent=-1, via='Bluetooth'),
        dict(key='rf', name='Mouse sem fio', kind='mouse', percent=34, via='Dongle'),
        dict(key='gone', name='Já desconectado', connected=False, percent=53),
        'entrada inválida',
    ]
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(monitor, 'refresh', lambda: None)
        monitor.devices = parse_devices(json.dumps(rows[:1]).encode())
        monitor._status('Leitura atualizada.')
        panel.toggle()
        qt_application.processEvents()
        assert panel.scroll.viewport().height() >= 40
        assert len(panel.scroll.widget().findChildren(QLabel, 'batteryDeviceIcon')) == 1

    monitor.devices = parse_devices(json.dumps(rows).encode())
    monitor._status('Leitura atualizada.')
    qt_application.processEvents()
    viewport = panel.scroll.widget()
    assert len(viewport.findChildren(QLabel, 'batteryDeviceIcon')) == 3
    assert sorted(bar.value() for bar in viewport.findChildren(QProgressBar)) == [34, 80]
    assert 'Carga indisponível' in [item.text() for item in viewport.findChildren(QLabel)]
    assert tray.toolTip() == 'Fone USB\n80%'
    monitor._status('Falha na leitura de bateria. Exibindo a última leitura.')
    assert panel.scroll.widget() is viewport
    panel.close()


def test_tray_uses_distinct_device_icons_and_respects_connection_and_preferences(qt_application, tmp_path):
    monitor = BatteryMonitor(lambda _: None, tmp_path)
    tray, menu = QSystemTrayIcon(), QMenu()
    tray.setContextMenu(menu)
    panel = BatteryPanel(monitor, tray)
    fallback_icon = tray.icon().cacheKey()
    assert tray.toolTip() == 'Bolha · Baterias'
    if qt_application.platformName() == 'windows':
        assert QSystemTrayIcon.isSystemTrayAvailable()
    tray.show()
    monitor.enabled = True
    rows = [
        dict(key='mouse', name='Mouse Claro', kind='mouse', percent=80),
        dict(key='phone', name='Celular', kind='phone', percent=-1),
        dict(key='headset', name='Headset Bluetooth', kind='headset', percent=40),
        dict(key='buds', name='Galaxy Buds', kind='headset', percent=55),
        dict(key='normal', name='AirPods Max', kind='headset', percent=50),
        dict(key='duplicate', name='Mouse Claro', kind='mouse', percent=50),
        dict(key='old', name='Teclado', kind='keyboard', asleep=True, connected=False),
    ]
    devices = parse_devices(json.dumps(rows).encode())
    assert [device.kind for device in devices] == [
        'mouse', 'phone', 'headset', 'earbuds', 'headphones', 'mouse', 'keyboard']
    monitor.devices = devices[:1]
    monitor.changed.emit()
    assert tray.icon().cacheKey() != fallback_icon
    assert tray.toolTip() == 'Mouse Claro\n80%'
    assert not panel._device_trays

    monitor.devices = devices[::-1]
    monitor.changed.emit()
    assert panel._primary_key == 'mouse'
    assert set(panel._device_trays) == {'phone', 'headset', 'buds', 'normal', 'duplicate'}
    phone = panel._device_trays['phone']
    assert phone.toolTip() == 'Celular\nCarga indisponível'
    assert phone.contextMenu() is menu
    assert len({entry.icon().cacheKey() for entry in panel._device_trays.values()}) == 5
    monitor.changed.emit()
    assert panel._device_trays['phone'] is phone
    monitor.devices = [device for device in devices if device.key != 'phone']
    monitor.changed.emit()
    assert 'phone' not in panel._device_trays and not phone.isVisible()
    monitor.devices = devices
    monitor.changed.emit()
    phone = panel._device_trays['phone']
    monitor.success = True
    monitor._failed()
    assert tray.toolTip().endswith('80% · Última leitura')
    phone.activated.emit(QSystemTrayIcon.Trigger)
    qt_application.processEvents()
    assert panel.isVisible() and panel._anchor is phone

    panel.set_hidden_devices(['mouse', 'phone', 'headset', 'buds', 'normal', 'duplicate'])
    assert not panel._device_trays and panel._anchor is tray
    assert not phone.isVisible()
    assert tray.icon().cacheKey() == fallback_icon
    panel.set_hidden_devices(['phone'])
    assert 'phone' not in panel._device_trays and panel._primary_key != 'phone'
    monitor.configure(False, 15, True)
    assert not panel._device_trays and tray.toolTip() == 'Bolha · Baterias'
    panel.close()
    tray.hide()


def test_windows_settings_retains_hidden_device_keys_when_device_reconnects(qt_application, tmp_path):
    store = PreferencesStore(tmp_path)
    assert store.preferences['batteryHiddenTrayDevices'] == []
    shell = QWidget()
    battery = BatteryMonitor(lambda _: None, tmp_path)
    features = NS(battery=battery, battery_panel=NS(toggle=lambda: None),
                  shortcut_status='', media=NS(status=''), capture_shortcut=lambda _: None)
    changes = []
    settings = WindowsSettings(QVBoxLayout(shell), features, lambda *args: changes.append(args))
    settings.load(store.preferences)
    device = parse_devices(b'[{"key":"phone:1","name":"Celular","kind":"phone","percent":40}]')[0]
    battery.devices = [device]
    battery.changed.emit()
    item = settings.devices.item(0)
    assert item.text() == 'Celular · 40%' and item.checkState() == Qt.Checked
    changes.clear()
    item.setCheckState(Qt.Unchecked)
    assert len(changes) == 1
    store.save(settings.values())
    battery.devices = []
    battery.changed.emit()
    assert settings.devices.count() == 0
    settings.load(PreferencesStore(tmp_path).preferences)
    battery.devices = [device]
    battery.changed.emit()
    assert settings.devices.item(0).checkState() == Qt.Unchecked
    assert settings.values()['batteryHiddenTrayDevices'] == ['phone:1']
    shell.close()


def test_tray_tooltip_keeps_charge_visible_with_a_long_unicode_name():
    raw = json.dumps([dict(key='test', name='🎧' * 170, percent=0)]).encode()
    tooltip = parse_devices(raw)[0].tray_tooltip(stale=True)
    assert len(tooltip.encode('utf-16-le')) <= 254
    assert tooltip.endswith('…\n0% · Última leitura')


def test_mascot_tray_requires_opt_in_and_can_be_toggled_without_duplicates(qt_application):
    from bolha.app import NativeApp
    assert defaults()['mascotTrayIcon'] is False
    assert sanitize({'mascotTrayIcon': True})['mascotTrayIcon'] is True
    controller = NativeApp.__new__(NativeApp)
    controller.qapp = qt_application
    controller.menu = QMenu()
    controller.tray = QSystemTrayIcon(controller.qapp)
    controller.tray.show()
    controller.mascot_tray = None
    controller.sync_mascot_tray(False)
    assert controller.mascot_tray is None and controller.tray.isVisible()
    controller.sync_mascot_tray(True)
    first = controller.mascot_tray
    controller.sync_mascot_tray(True)
    assert controller.mascot_tray is first and first.isVisible()
    assert first.contextMenu() is controller.menu
    controller.sync_mascot_tray(False)
    assert not first.isVisible() and controller.tray.isVisible()
    controller.tray.hide()
    controller.tray.deleteLater()
