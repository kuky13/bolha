# SPDX-License-Identifier: GPL-3.0-only
"""Gestos Qt exercitam o controlador real e seus limites de objetos."""
from pathlib import Path
from types import SimpleNamespace
import time
import pytest
from PySide6.QtCore import QPoint,QPointF,Qt
from game import Game
from pestinha import config
from bolha.scene import NativeScene,ObjectWindow

CONTENT=Path(__file__).resolve().parents[2]/'assets/bolha/content'

class SelectedMenu:
    """Seleciona a ação apresentada sem abrir um menu modal no teste."""
    def __init__(self,parent):self.action=object()
    def addAction(self,text):
        assert text=='Guardar objeto';return self.action
    def exec(self,point):return self.action


def mouse(x,y):
    return SimpleNamespace(button=lambda:Qt.LeftButton,globalPosition=lambda:QPointF(x,y))

@pytest.mark.parametrize('kind',['meme','bilhete'])
def test_guardar_travessura_libera_limite_e_notifica_controlador(qt_application,tmp_path,monkeypatch,kind):
    import bolha.scene as scene_module
    monkeypatch.setattr(scene_module,'QMenu',SelectedMenu)
    game=Game(tmp_path,CONTENT);game.configure(dict(maxObjects=1))
    item=game.mischief._make(kind,'feliz',False);item.place(400,300);game.mischief._add(item)
    game.mischief.last_act=-1e9
    perms=dict(config.DEFAULT_PERMISSIONS,travessuras=True)
    assert not game.mischief.allowed(perms,game.prof,False)
    window=ObjectWindow(NativeScene(game),item)
    window.contextMenuEvent(SimpleNamespace(globalPos=lambda:QPoint(400,300)))
    assert item.closed and item not in game.mischief.things and item.id not in game.objects
    assert game.mischief.allowed(perms,game.prof,False)
    assert game.mischief_ctl.dismiss_times  # descarte real alimenta o aprendizado
    window.close()

@pytest.mark.parametrize('kind',['ball','notebook'])
def test_guardar_objeto_persistente_preserva_instancia_para_reabrir(qt_application,tmp_path,monkeypatch,kind):
    import bolha.scene as scene_module
    monkeypatch.setattr(scene_module,'QMenu',SelectedMenu)
    game=Game(tmp_path,CONTENT)
    item=game.ball if kind=='ball' else game.mesa.caderno
    item.show();window=ObjectWindow(NativeScene(game),item)
    window.contextMenuEvent(SimpleNamespace(globalPos=lambda:QPoint(0,0)))
    assert not item.closed and item.id in game.objects
    assert game.ball_stored if kind=='ball' else game.mesa.escondido
    game.interact(dict(type=kind))
    assert not game.ball_stored if kind=='ball' else not game.mesa.escondido
    window.close()


def test_arrasto_com_parada_final_nao_vira_clique(qt_application,tmp_path,monkeypatch):
    clock=[100.];monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT)
    item=game.mischief._make('bilhete','feliz',False);item.place(400,300);game.mischief._add(item)
    window=ObjectWindow(NativeScene(game),item)
    window.mousePressEvent(mouse(400,300))
    clock[0]+=.08;window.mouseMoveEvent(mouse(500,300))
    clock[0]+=.15;window.mouseMoveEvent(mouse(501,300))
    clock[0]+=.02;window.mouseReleaseEvent(mouse(501,300))
    assert item in game.mischief.things and not item.closed
    assert item._cx==501 and not game.scene_dragging
    assert not game.mischief_ctl.dismiss_times
    window.close()


def test_clique_sem_arrasto_ainda_descarta(qt_application,tmp_path):
    game=Game(tmp_path,CONTENT)
    item=game.mischief._make('bilhete','feliz',False);item.place(400,300);game.mischief._add(item)
    window=ObjectWindow(NativeScene(game),item)
    window.mousePressEvent(mouse(400,300));window.mouseReleaseEvent(mouse(401,301))
    assert item.closed and item not in game.mischief.things
    window.close()


def test_falha_inicial_so_ativa_no_modo_teste(monkeypatch):
    from bolha.__main__ import main
    from bolha import VERSION
    monkeypatch.setenv('BOLHA_TEST','1');monkeypatch.setenv('BOLHA_TEST_FAIL_START',VERSION)
    assert main()==2
    monkeypatch.delenv('BOLHA_TEST')
    import PySide6.QtWidgets
    class ReachedApplication(Exception):pass
    def reached(*_):raise ReachedApplication()
    monkeypatch.setattr(PySide6.QtWidgets,'QApplication',reached)
    with pytest.raises(ReachedApplication):main()
    monkeypatch.setenv('BOLHA_TEST','1');monkeypatch.setenv('BOLHA_TEST_FAIL_START','999.0.0')
    with pytest.raises(ReachedApplication):main()
