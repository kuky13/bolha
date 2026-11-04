# SPDX-License-Identifier: GPL-3.0-only
"""Geometria Qt/Windows, regiões nativas e único atalho de pânico."""
import ctypes
import sys
from PySide6.QtCore import QAbstractNativeEventFilter


def desktop_layout(app, exclude=()):
    native = {}
    if sys.platform == 'win32':
        import win32api
        for handle, _, _ in win32api.EnumDisplayMonitors():
            info = win32api.GetMonitorInfo(handle)
            native[info['Device'].lower()] = info['Monitor']
    areas = []
    for index, screen in enumerate(app.screens()):
        rect, monitor, scale = screen.availableGeometry(), screen.geometry(), screen.devicePixelRatio()
        physical = native.get(screen.name().lower())
        areas.append(dict(id=index,x=rect.x(),y=rect.y(),width=rect.width(),height=rect.height(),scaleFactor=scale,
                          nativeX=physical[0] if physical else monitor.x(),nativeY=physical[1] if physical else monitor.y(),
                          nativeWidth=physical[2]-physical[0] if physical else monitor.width()*scale,nativeHeight=physical[3]-physical[1] if physical else monitor.height()*scale,
                          monitorX=monitor.x(),monitorY=monitor.y(),monitorWidth=monitor.width(),monitorHeight=monitor.height()))
    return dict(areas=areas or [dict(id=0,x=0,y=0,width=1280,height=760,scaleFactor=1)],exclude=list(exclude))


class PanicHotkey(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.registered = False
        if sys.platform == 'win32':
            # CTRL + ALT + SHIFT + B, sem leitura ou registro de teclas.
            self.registered = bool(ctypes.windll.user32.RegisterHotKey(None, 0xB01, 0x4007, ord('B')))

    def nativeEventFilter(self, kind, message):
        if sys.platform == 'win32':
            from ctypes.wintypes import MSG
            msg = MSG.from_address(int(message))
            if msg.message == 0x312 and msg.wParam == 0xB01:
                self.callback()
                return True, 0
        return False, 0

    def stop(self):
        if self.registered:
            ctypes.windll.user32.UnregisterHotKey(None,0xB01)
            self.registered=False
