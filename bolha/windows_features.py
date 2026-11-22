# SPDX-License-Identifier: GPL-3.0-or-later
"""Integrações optativas do desktop Windows."""
import time

from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QSystemTrayIcon, QWidget

from .battery_panel import BatteryPanel
from .cursor_finder import CursorFinder, locate
from .windows_battery import BatteryMonitor
from .windows_hotkeys import Hotkeys
from .windows_media import Media, SpotifyReaction


class WindowsFeatures:
    def __init__(self, controller):
        self.controller = controller
        self.finder = CursorFinder()
        self.media = Media()
        self.reaction = SpotifyReaction()
        self.battery = BatteryMonitor(self.low_battery)
        self.battery_panel = BatteryPanel(self.battery, controller.tray, self._save_panel_visibility)
        self.capture = False
        self.shortcut_status = ''
        self.last_layout = None
        self.raw_receiver = QWidget()
        self.hotkeys = Hotkeys(controller.qapp, int(self.raw_receiver.winId()),
                               {'finder': self.show_cursor, 'media': self.toggle_media},
                               self.cancel_finder, lambda: self.capture)
        self.prefs = {}
        self.configure(controller.store.preferences, strict=False)

    def configure(self, prefs, *, strict=True):
        shortcut_keys = ('finderEnabled', 'finderDouble', 'finderKey', 'senseWindows', 'mediaEnabled', 'mediaKey')
        if not self.capture and any(self.prefs.get(key) != prefs[key] for key in shortcut_keys):
            self._bind(prefs, strict=strict)
        if not prefs['finderEnabled'] or not prefs['senseWindows']:
            self.cancel_finder()
        if not prefs['spotifyEnabled']:
            self.reaction.last_track = None
            self.controller.pet.dance_started = None
            self.controller.scene.speech.clear_external()
        if not prefs['mediaEnabled']:
            self.media.toggle_pending = False
        self.battery_panel.set_hidden_devices(prefs['batteryHiddenTrayDevices'])
        self.battery_panel.set_hidden_panel_devices(prefs['batteryHiddenPanelDevices'])
        self.battery.configure(prefs['batteryEnabled'], prefs['batteryThreshold'], prefs['batteryAlerts'])
        self.prefs = dict(prefs)

    def _save_panel_visibility(self, keys):
        self.controller.store.save({'batteryHiddenPanelDevices': keys})

    def _bind(self, prefs, *, strict):
        self.last_layout = self.hotkeys.keyboard_layout()
        try:
            self.hotkeys.configure(prefs)
        except (OSError, ValueError) as error:
            if strict:
                raise
            self.shortcut_status = str(error) + '.'
            if not self.prefs:
                # Um atalho ocupado na primeira execução não tira o outro do ar.
                for fallback in (dict(prefs, mediaEnabled=False), dict(prefs, finderEnabled=False)):
                    try:
                        self.hotkeys.configure(fallback)
                    except (OSError, ValueError):
                        continue
                    break
        else:
            self.shortcut_status = ''

    def capture_shortcut(self, active):
        self.capture = active
        if active:
            self.cancel_finder()
            self.hotkeys.configure(dict(self.prefs, finderEnabled=False, mediaEnabled=False))
        else:
            self._bind(self.prefs, strict=False)

    def _available(self):
        app = self.controller
        return not (app.quitting or app.updating or app.suspended or app.game.panicked
                    or app.activity_test is not None or self.capture)

    def show_cursor(self):
        if self._available() and self.prefs['finderEnabled'] and self.prefs['senseWindows']:
            game = self.controller.game
            if game.native_error:
                return
            if game.cursor_prank.start_finder(game, time.monotonic()):
                try:
                    self.hotkeys.listen_click(self.release_finder)
                except OSError as error:
                    self.cancel_finder()
                    self.shortcut_status = str(error) + '.'

    def release_finder(self):
        game = self.controller.game
        game.cursor_prank.release_finder(game, time.monotonic())
        self.finder.hide()

    def cancel_finder(self):
        game = self.controller.game
        if game.cursor_prank.guided:
            game.cursor_prank.cancel(game, time.monotonic())
            self.controller.pet._restore_prank_cursor()
        self.finder.hide()
        self._stop_listening_for_click()

    def _stop_listening_for_click(self):
        if self.hotkeys.mouse_callback:
            try:
                self.hotkeys.listen_click(None)
            except OSError:
                # Descarta a entrada mesmo se o Windows não remover a inscrição.
                self.hotkeys.mouse_callback = None

    def guide_cursor(self):
        game = self.controller.game
        prank = game.cursor_prank
        if not prank.guided or prank.phase == 'spit':
            self.finder.hide()
            self._stop_listening_for_click()
            return
        if not self._available() or game.native_error or not self.prefs['senseWindows']:
            self.cancel_finder()
            return
        point = QCursor.pos()
        target = locate((point.x(), point.y()), game.areas, game.monitors, game.blocked)
        if target is None:
            self.cancel_finder()
            return
        index, (x, y), direction = target
        prank.target = x, y, game.areas[index], direction is None
        self.finder.indicate((x, y), direction)

    def toggle_media(self):
        if self._available() and self.prefs['mediaEnabled']:
            self.media.request('toggle')

    def can_dance(self, now):
        game = self.controller.game
        return (self._available() and self.prefs['spotifyEnabled'] and self.prefs['senseWindows']
                and not game.blocked and not game.native_error and game.pet_interactive()
                and not game.panel and not game.body.held and game.body.grounded
                and not game.sleep.asleep and not game.mesa.sentado and not game.castigo.dentro
                and not game.state.protest_stage and now >= game.quiet_until
                and not game.cursor_prank.active and not game.pingpong and not game.play.juggling()
                and not game.play.finishing_juggle(now) and not game.behavior.toy_action)

    def tick(self, now):
        pet = self.controller.pet
        if pet.dance_started is not None:
            if now - pet.dance_started >= 2.2 or not self.can_dance(now):
                pet.dance_started = None
                self.controller.scene.speech.clear_external()

    def poll(self):
        if not self.capture and self.hotkeys.keyboard_layout() != self.last_layout:
            self._bind(self.prefs, strict=False)
        now = time.monotonic()
        active = self._available() and self.prefs['spotifyEnabled'] and self.prefs['senseWindows']
        track = self.media.poll(now, active)
        message = self.reaction.observe(track, now, self.can_dance(now)) if track else None
        if message:
            self.controller.pet.dance_started = now
            self.controller.scene.speech.offer(message, now)

    def low_battery(self, devices):
        if not self._available() or not self.prefs.get('batteryAlerts'):
            return
        names = ', '.join(f'{device.name} ({device.percent}%)' for device in devices[:2])
        if len(devices) > 2:
            names += f' e mais {len(devices)-2}'
        self.controller.tray.showMessage('Bolha · Bateria fraca', names, QSystemTrayIcon.Warning, 6000)

    def cancel(self):
        self.cancel_finder()
        self.controller.pet.dance_started = None
        self.controller.scene.speech.clear_external()

    def stop(self):
        self.cancel()
        self.hotkeys.stop()
        self.battery.stop()
        self.battery_panel.close()
        self.finder.close()
        self.raw_receiver.close()
