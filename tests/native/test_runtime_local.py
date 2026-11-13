# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
import ctypes
from pathlib import Path
from types import SimpleNamespace
from bolha.app import local_log_excerpt
from bolha.platform import set_app_id
import bolha.platform as platform


def test_app_id_windows_tem_assinatura_e_hresult_local(monkeypatch):
    class Function:
        argtypes=None;restype=None;result=0
        def __call__(self,value):self.value=value;return self.result
    function=Function()
    monkeypatch.setattr(platform.sys,'platform','win32')
    monkeypatch.setattr(ctypes,'windll',SimpleNamespace(shell32=SimpleNamespace(SetCurrentProcessExplicitAppUserModelID=function)),raising=False)
    assert set_app_id() is None
    assert function.value=='solutions.kuky.bolha'
    assert function.argtypes==[ctypes.c_wchar_p] and function.restype==ctypes.c_long
    function.result=-2147467259
    assert 'HRESULT0x80004005' in set_app_id()


def test_app_id_nao_chama_windows_fora_do_windows(monkeypatch):
    monkeypatch.setattr(platform.sys,'platform','linux')
    monkeypatch.delattr(ctypes,'windll',raising=False)
    assert set_app_id() is None


def test_log_somente_ultimas_linhas_e_limite_de_bytes(tmp_path):
    directory=tmp_path/'logs';directory.mkdir()
    lines=[f'linha-{index:04}: '+('♡'*400) for index in range(200)]
    (directory/'main.log').write_text('\n'.join(lines),encoding='utf-8')
    result=local_log_excerpt(tmp_path)
    assert 'linha-0199:' in result and 'linha-0000:' not in result
    assert len(result.splitlines())<=60
    assert len(result.encode('utf-8'))<=65536


def test_log_erro_de_leitura_vira_aviso(tmp_path,monkeypatch):
    def unavailable(*_args,**_kwargs):raise PermissionError('acesso negado')
    monkeypatch.setattr(Path,'open',unavailable)
    assert local_log_excerpt(tmp_path)=='[aviso] Log local indisponível: acesso negado'


def test_aviso_automatico_de_update_preserva_foco_e_adia(qt_application):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QPushButton
    from bolha.app import NativeApp
    deferred=[]
    installed=[]
    controller=SimpleNamespace(update_dialog=None,updater=SimpleNamespace(
        state={'version':'0.4.10'}, defer=lambda:deferred.append('deferred'),
        install=lambda:installed.append(True)))
    NativeApp.show_update_countdown(controller,30)
    dialog=controller.update_dialog
    assert dialog.windowFlags()&Qt.WindowType_Mask==Qt.Tool
    assert not dialog.windowFlags()&Qt.WindowStaysOnTopHint
    assert dialog.testAttribute(Qt.WA_ShowWithoutActivating)
    assert '0.4.10' in controller.update_label.text() and '30 s.' in controller.update_label.text()
    NativeApp.show_update_countdown(controller,17)
    assert controller.update_dialog is dialog and '17 s.' in controller.update_label.text()
    buttons={button.text():button for button in dialog.findChildren(QPushButton)}
    buttons['Instalar agora'].click()
    assert installed==[True]
    buttons['Adiar por uma hora'].click()
    assert deferred==['deferred']
    dialog.close()
    assert deferred==['deferred','deferred']  # fechar o aviso também adia


def test_falha_apos_primeiro_ciclo_nao_confirma_atualizacao(qt_application,tmp_path):
    from collections import deque
    import queue
    import time
    from PySide6.QtCore import QTimer
    from bolha.app import NativeApp
    confirmed=[]
    frame=QTimer();frame.start(1000)
    controller=SimpleNamespace(quitting=False,updating=False,suspended=False,last_tick=time.monotonic(),
        frame_times=deque(),frame=frame,first_paint=True,first_think=False,healthy=False,
        initial_errors=[],data_dir=tmp_path,update_dialog=None,updater=None,
        store=SimpleNamespace(preferences={'senseCursor':False},error=''),
        writer=SimpleNamespace(errors=queue.SimpleQueue(),failure=None),warn=lambda *_:None,
        _health=confirmed.append)
    controller.game=SimpleNamespace(body=SimpleNamespace(x=0,y=0),
        tick=lambda *_:setattr(controller,'first_think',True))
    def broken_sync():raise RuntimeError('falha de desenho')
    controller.pet=SimpleNamespace(sync=broken_sync,poll_interaction=lambda:None)
    controller.scene=SimpleNamespace(poll_interactions=lambda:None)
    controller.cancel_interactions=lambda:None
    NativeApp.tick(controller)
    assert controller.first_think and controller.first_paint and not frame.isActive()
    NativeApp.poll(controller)
    assert not controller.healthy and not confirmed
