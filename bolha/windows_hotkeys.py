# SPDX-License-Identifier: GPL-3.0-or-later
"""Atalhos locais. A entrada bruta nunca é consumida, registrada ou armazenada."""
import ctypes
from ctypes import wintypes
import time

from PySide6.QtCore import QAbstractNativeEventFilter
from PySide6.QtGui import QKeySequence

PANIC = (7, ord('B'))
MODIFIERS = {
    'Alt': 0xA4, 'Alt esquerdo': 0xA4, 'Alt direito': 0xA5,
    'Ctrl': 0xA2, 'Shift': 0xA0, 'Meta': 0x5B,
}
NAMED_KEYS = {
    'Esc': 0x1B, 'Tab': 0x09, 'Backspace': 0x08, 'Return': 0x0D, 'Enter': 0x0D,
    'Ins': 0x2D, 'Del': 0x2E, 'Home': 0x24, 'End': 0x23, 'Space': 0x20,
    'Left': 0x25, 'Up': 0x26, 'Right': 0x27, 'Down': 0x28,
    'PgUp': 0x21, 'PgDown': 0x22, 'Pause': 0x13, 'Print': 0x2C,
    'CapsLock': 0x14, 'NumLock': 0x90, 'ScrollLock': 0x91, 'Menu': 0x5D,
}
NAMED_KEYS.update({f'F{i}': 0x6F + i for i in range(1, 25)})
KEY_MODS = {'Alt': 1, 'Ctrl': 2, 'Shift': 4, 'Meta': 8}


def binding(text, scan, *, double=False):
    if double and text in MODIFIERS:
        return 0, MODIFIERS[text]
    sequence = QKeySequence.fromString(text, QKeySequence.PortableText)
    if sequence.count() != 1:
        raise ValueError('Escolha uma única tecla ou combinação')
    portable = sequence.toString(QKeySequence.PortableText)
    if not portable:
        raise ValueError('Tecla inválida')
    mods = 0
    while (name := portable.partition('+')[0]) in KEY_MODS and '+' in portable:
        mods |= KEY_MODS[name]
        portable = portable[len(name)+1:]
    if portable in NAMED_KEYS:
        key = NAMED_KEYS[portable]
    elif len(portable) == 1:
        character = portable.lower() if portable.isalpha() else portable
        result = scan(ord(character))
        if result == -1 or result >> 8 & ~7:
            raise ValueError('Tecla indisponível neste layout')
        key = result & 255
        shift = (result >> 8) & 7
        mods |= (4 if shift & 1 else 0) | (2 if shift & 2 else 0) | (1 if shift & 4 else 0)
    else:
        raise ValueError('Tecla não suportada neste layout')
    if key in (0x1B, 0x7B) or (mods, key) == PANIC:
        raise ValueError('Atalho reservado pelo Windows ou pela Bolha')
    if double and mods:
        raise ValueError('Para toque duplo, escolha uma tecla sem modificadores')
    return mods, key


class DoubleTap:
    def __init__(self):
        self.reset()

    def reset(self):
        self.started = None
        self.last = None
        self.held = False

    def event(self, match, pressed, now, modified=False):
        if not match:
            if pressed:
                self.started = self.last = None
            return False
        if modified:
            self.started = self.last = None
            self.held = pressed
            return False
        if pressed:
            if not self.held:
                self.held = True
                self.started = now
            return False
        self.held = False
        started, self.started = self.started, None
        if started is None or now - started > .35:
            self.last = None
            return False
        emit = self.last is not None and now - self.last <= .35
        self.last = None if emit else started
        return emit


class RawDevice(ctypes.Structure):
    _fields_ = [('page', wintypes.USHORT), ('usage', wintypes.USHORT),
                ('flags', wintypes.DWORD), ('target', wintypes.HWND)]


class RawHeader(ctypes.Structure):
    _fields_ = [('type', wintypes.DWORD), ('size', wintypes.DWORD),
                ('device', wintypes.HANDLE), ('parameter', wintypes.WPARAM)]


class RawKeyboard(ctypes.Structure):
    _fields_ = [('scan', wintypes.USHORT), ('flags', wintypes.USHORT),
                ('reserved', wintypes.USHORT), ('key', wintypes.USHORT),
                ('message', wintypes.UINT), ('extra', wintypes.ULONG)]


class Hotkeys(QAbstractNativeEventFilter):
    def __init__(self, app, hwnd, callbacks, dismiss, editing):
        super().__init__()
        self.app = app
        self.hwnd = hwnd
        self.callbacks = callbacks
        self.dismiss = dismiss
        self.editing = editing
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.user.GetForegroundWindow.restype = wintypes.HWND
        self.user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.c_void_p]
        self.user.GetKeyboardLayout.argtypes = [wintypes.DWORD]
        self.user.GetKeyboardLayout.restype = wintypes.HANDLE
        self.user.VkKeyScanExW.argtypes = [wintypes.WCHAR, wintypes.HANDLE]
        self.user.VkKeyScanExW.restype = ctypes.c_short
        self.user.GetRawInputData.argtypes = [wintypes.HANDLE, wintypes.UINT, ctypes.c_void_p,
                                              ctypes.POINTER(wintypes.UINT), wintypes.UINT]
        self.user.GetRawInputData.restype = wintypes.UINT
        self.user.GetAsyncKeyState.restype = ctypes.c_short
        self.active = {}
        self.layout = None
        self.double = None
        self.tap = DoubleTap()
        self.raw = False
        self.next_id = 0xB10
        self.app.installNativeEventFilter(self)

    def keyboard_layout(self):
        thread = self.user.GetWindowThreadProcessId(self.user.GetForegroundWindow(), None)
        return self.user.GetKeyboardLayout(thread)

    def _raw_subscription(self, enabled):
        device = RawDevice(1, 6, 0x100 if enabled else 1, self.hwnd if enabled else None)
        if not self.user.RegisterRawInputDevices(ctypes.byref(device), 1, ctypes.sizeof(device)):
            raise OSError('O Windows recusou a leitura do atalho do localizador')
        self.raw = enabled

    def configure(self, prefs):
        layout = self.keyboard_layout()
        scan = lambda char: self.user.VkKeyScanExW(chr(char), layout)
        finder = prefs['finderEnabled'] and prefs['senseWindows']
        double = (binding(prefs['finderKey'], scan, double=True)[1]
                  if finder and prefs['finderDouble'] else None)
        wanted = {}
        if finder and not prefs['finderDouble']:
            wanted['finder'] = binding(prefs['finderKey'], scan)
        if prefs['mediaEnabled']:
            wanted['media'] = binding(prefs['mediaKey'], scan)
        binds = list(wanted.values())
        if len(binds) != len(set(binds)) or (0, double) in binds:
            raise ValueError('O localizador e a mídia precisam de atalhos diferentes')
        old_by_binding = {combo: ident for ident, (_, combo) in self.active.items()}
        fresh = {}
        registered = []
        try:
            for action, combo in wanted.items():
                ident = old_by_binding.get(combo)
                if ident is None:
                    ident = self.next_id
                    self.next_id = 0xB10 + (self.next_id - 0xB10 + 1) % 0x100
                    if not self.user.RegisterHotKey(None, ident, combo[0] | 0x4000, combo[1]):
                        raise OSError(f'Atalho de {"mídia" if action == "media" else "localização"} ocupado ou reservado')
                    registered.append(ident)
                fresh[ident] = (action, combo)
            if finder != self.raw:
                self._raw_subscription(finder)
        except OSError:
            for ident in registered:
                self.user.UnregisterHotKey(None, ident)
            raise
        for ident in self.active.keys() - fresh.keys():
            self.user.UnregisterHotKey(None, ident)
        if double != self.double or layout != self.layout:
            self.tap.reset()
        self.active, self.double, self.layout = fresh, double, layout

    def nativeEventFilter(self, kind, message):
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == 0x312 and msg.wParam in self.active:
            if not self.editing():
                self.callbacks[self.active[msg.wParam][0]]()
            return True, 0
        if msg.message != 0xFF or not self.raw:
            return False, 0
        if self.editing():
            self.tap.reset()
            return False, 0
        header = ctypes.sizeof(RawHeader)
        buffer = ctypes.create_string_buffer(header + ctypes.sizeof(RawKeyboard))
        size = wintypes.UINT(len(buffer))
        read = self.user.GetRawInputData(msg.lParam, 0x10000003, buffer, ctypes.byref(size), header)
        if read == len(buffer) and RawHeader.from_buffer(buffer).type == 1:
            data = RawKeyboard.from_buffer(buffer, header)
            key, pressed = data.key, not data.flags & 1
            if key in (0x11, 0x12):
                key = {0x11: 0xA2, 0x12: 0xA4}[key] + bool(data.flags & 2)
            elif key == 0x10:
                key = 0xA1 if data.scan == 0x36 else 0xA0
            if key == 0x1B and pressed:
                self.dismiss()
            if self.double is not None and key != 0xFF:
                match = key == self.double
                other_modifiers = (0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x5B, 0x5C)
                modified = match and any(self.user.GetAsyncKeyState(vk) < 0
                                         for vk in other_modifiers if vk != key)
                if self.tap.event(match, pressed, time.monotonic(), modified):
                    self.callbacks['finder']()
        return False, 0

    def stop(self):
        self.app.removeNativeEventFilter(self)
        if self.raw:
            try:
                self._raw_subscription(False)
            except OSError:
                pass
        for ident in self.active:
            self.user.UnregisterHotKey(None, ident)
        self.active.clear()
