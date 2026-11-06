# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""O pedido estático do driver jamais controla aplicativos fora do teste."""
from pathlib import Path
from types import SimpleNamespace
import queue
import pytest
from bolha.app import NativeApp


def controller(path):
    result=SimpleNamespace(data_dir=path,writer=SimpleNamespace(errors=queue.SimpleQueue()),
                           first_paint=False,first_think=False,healthy=False,updater=None,update_dialog=None,
                           stopped=False,errors=[])
    result.quit=lambda:setattr(result,'stopped',True)
    result.warn=result.errors.append
    return result

@pytest.mark.parametrize('missing',['BOLHA_TEST','BOLHA_TEST_ALLOW_STOP','BOLHA_TEST_USER_DATA'])
def test_pedido_ignorado_sem_cada_guard(tmp_path,monkeypatch,missing):
    for key,value in (('BOLHA_TEST','1'),('BOLHA_TEST_ALLOW_STOP','1'),('BOLHA_TEST_USER_DATA',str(tmp_path))):
        monkeypatch.setenv(key,value)
    monkeypatch.delenv(missing)
    request=tmp_path/'test-stop.request';request.write_text('não executar')
    app=controller(tmp_path);NativeApp.poll(app)
    assert not app.stopped and request.exists()


def test_parada_so_do_perfil_de_teste_sem_ler_conteudo(tmp_path,monkeypatch):
    test_profile=tmp_path/'test';test_profile.mkdir();other_profile=tmp_path/'other';other_profile.mkdir()
    for key,value in (('BOLHA_TEST','1'),('BOLHA_TEST_ALLOW_STOP','1'),('BOLHA_TEST_USER_DATA',str(test_profile))):
        monkeypatch.setenv(key,value)
    request=test_profile/'test-stop.request';request.write_text('nunca executar este conteúdo')
    other_request=other_profile/'test-stop.request';other_request.write_text('preservar')
    preserved=test_profile/'keep.txt';preserved.write_text('preservar')
    monkeypatch.setattr(Path,'read_text',lambda *_args,**_kwargs:(_ for _ in ()).throw(AssertionError('conteúdo não pode ser lido')))
    app=controller(test_profile);other=controller(other_profile)
    NativeApp.poll(other);assert not other.stopped and other_request.exists()
    NativeApp.poll(app)
    assert app.stopped and not request.exists()
    assert not other.stopped and other_request.exists() and preserved.exists()
