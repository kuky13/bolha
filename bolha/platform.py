# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Geometria Qt/Windows, regiões nativas e único atalho de pânico."""
import ctypes
import sys
from PySide6.QtCore import QAbstractNativeEventFilter
from PySide6.QtGui import QCursor,QGuiApplication


class WindowsDragPointer:
    """Só existe durante uma pega; posição em coordenadas lógicas do Qt."""
    def __init__(self):
        user32=ctypes.windll.user32
        metrics=user32.GetSystemMetrics;metrics.argtypes=[ctypes.c_int];metrics.restype=ctypes.c_int
        self.key=2 if metrics(23) else 1  # SM_SWAPBUTTON fixa o primário físico neste gesto.
        self.state=user32.GetAsyncKeyState
        self.state.argtypes=[ctypes.c_int];self.state.restype=ctypes.c_short

    def sample(self):
        return QCursor.pos(),bool(self.state(self.key)&0x8000)


def drag_pointer():
    if sys.platform=='win32' and QGuiApplication.platformName()=='windows':return WindowsDragPointer()
    return None


def set_app_id():
    """Fixa a identidade de instalação; falha vira somente um aviso local."""
    if sys.platform!='win32':return None
    from .installation import APP_ID
    try:
        function=ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        function.argtypes=[ctypes.c_wchar_p];function.restype=ctypes.c_long
        result=function(APP_ID)
        if result<0:return f'Não foi possível definir o identificador da Bolha: HRESULT0x{result&0xffffffff:08X}.'
    except (OSError,AttributeError) as error:return 'Não foi possível definir o identificador da Bolha: '+str(error)
    return None


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
