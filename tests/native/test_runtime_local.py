# SPDX-License-Identifier: GPL-3.0-only
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
