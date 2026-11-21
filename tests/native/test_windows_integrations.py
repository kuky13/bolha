import asyncio
import ctypes
from ctypes import wintypes
import json
from types import SimpleNamespace as NS

import pytest
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel, QSystemTrayIcon, QVBoxLayout, QWidget

from bolha.battery_panel import BatteryPanel, panel_position
from bolha.cursor_finder import locate
from bolha.preferences import defaults, sanitize
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
    panel = BatteryPanel(monitor, QSystemTrayIcon())
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
    assert not panel.isVisible() and not panel.tray.isVisible()
    panel.close()
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
