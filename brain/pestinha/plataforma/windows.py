# SPDX-License-Identifier: GPL-3.0-or-later
"""Leituras Windows preservadas do Pestinha; sem captura de conteúdo."""


import ctypes
from ctypes import wintypes
import psutil
import pywintypes
import win32api
import win32con
import win32gui
import win32process


SHELL_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"}

class LASTINPUTINFO(ctypes.Structure):
    """Estrutura da API do Windows que guarda o instante da última entrada (teclado ou mouse)."""
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

def ocioso_segundos():
    """Tempo ocioso lido da API do Windows (GetLastInputInfo)."""
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0
    now = ctypes.windll.kernel32.GetTickCount() & 0xFFFFFFFF
    return ((now - info.dwTime) & 0xFFFFFFFF) / 1000.0

def processo_ativo():
    """Nome do programa da janela ativa, pelo pid da janela e o psutil."""
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return "unknown.exe"
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name().lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, ValueError,
            pywintypes.error):
        return "unknown.exe"

def tela_cheia():
    """Janela em primeiro plano cobrindo o monitor inteiro (jogo, vídeo, apresentação)."""
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return False
    try:
        if win32gui.GetClassName(hwnd) in SHELL_CLASSES:
            return False
        # maximizada também passa das bordas do monitor quando não há barra de tarefas nele (ou ela se
        # esconde sozinha); o que separa as duas é a moldura, que a tela cheia de verdade não tem
        estilo = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        if ctypes.windll.user32.IsZoomed(hwnd) and estilo & (win32con.WS_CAPTION | win32con.WS_THICKFRAME):
            return False
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        m_left, m_top, m_right, m_bottom = win32api.GetMonitorInfo(monitor)["Monitor"]
    except Exception:
        return False
    return left <= m_left and top <= m_top and right >= m_right and bottom >= m_bottom

def _is_cloaked(hwnd):
    """Diz se o Windows está mostrando a janela como escondida (ex.: ela está em outro desktop virtual)."""
    cloaked = ctypes.c_int(0)
    try:
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(hwnd), 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked)
        )
    except Exception:
        return False
    return cloaked.value != 0

def _frame_rect(hwnd):
    """Retângulo visível (sem as bordas invisíveis de redimensionar do Windows 10/11)."""
    rect = wintypes.RECT()
    try:
        if ctypes.windll.dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(hwnd), 9, ctypes.byref(rect), ctypes.sizeof(rect)
        ) == 0:
            return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        pass
    return win32gui.GetWindowRect(hwnd)

def janelas_visiveis(excluir, escala=1.0):
    """Janelas visíveis em ordem de z (de cima para baixo): [(hwnd, (l, t, r, b), maximizada)]."""
    found = []
    user32 = ctypes.windll.user32

    def callback(hwnd, _):
        """Chamado pelo Windows para cada janela: guarda só as que estão visíveis e são janelas de verdade."""
        try:
            if hwnd in excluir or not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
                return True
            if win32gui.GetClassName(hwnd) in SHELL_CLASSES:
                return True
            # só janelas "de verdade" (as do Alt+Tab): sem dono, sem overlay transparente
            ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            if ex & (win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE):
                return True
            if win32gui.GetWindow(hwnd, win32con.GW_OWNER) or _is_cloaked(hwnd):
                return True
            rect = _frame_rect(hwnd)
            if rect[2] - rect[0] < 120 or rect[3] - rect[1] < 60:
                return True
            found.append((hwnd, rect, bool(user32.IsZoomed(hwnd))))
        except Exception:
            pass        # janela sumiu no meio da leitura
        return True

    try:
        win32gui.EnumWindows(callback, None)
    except Exception as error:
        log(f"[senses] não deu para listar janelas: {error}")
    return found

def retangulo_ativo(escala=1.0):
    """Retângulo da janela ativa (pixels físicos), para ele olhar para ela."""
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None
    try:
        if win32gui.GetClassName(hwnd) in SHELL_CLASSES:
            return None
        return _frame_rect(hwnd)
    except Exception:
        return None
