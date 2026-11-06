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


def test_objeto_parado_nao_repinta_sem_mudanca_mas_invalida_estado_tamanho_dpi(qt_application,tmp_path,monkeypatch):
    game=Game(tmp_path,CONTENT);item=game.mesa.caderno;item.show()
    window=ObjectWindow(NativeScene(game),item);calls=[]
    monkeypatch.setattr(window,'update',lambda:calls.append('update'))
    window.sync();assert len(calls)==1
    window.sync();window.sync();assert len(calls)==1
    item.place(item._cx+50,item._cy);window.sync();assert len(calls)==2
    item.set_working(True);window.sync();assert len(calls)==3
    item.apply_scale(.8);window.sync();assert len(calls)==4
    monkeypatch.setattr(window,'devicePixelRatioF',lambda:1.5);window.sync();assert len(calls)==5
    item.hide();window.sync();assert len(calls)==6
    item.show();window.sync();assert len(calls)==7
    window.close()


def test_fogos_visiveis_continuam_animados(qt_application,tmp_path,monkeypatch):
    game=Game(tmp_path,CONTENT);item=game.festa.fogos;item.launch(400,300)
    window=ObjectWindow(NativeScene(game),item);calls=[]
    monkeypatch.setattr(window,'update',lambda:calls.append('update'))
    window.sync();window.sync();window.sync();assert len(calls)==3
    window.close()


def test_brinquedo_repousa_no_chao_com_sincronizacao_qt(qt_application,tmp_path):
    game=Game(tmp_path,CONTENT)
    game.configure(dict(senseCursor=False,roaming=False,mischiefEnabled=False))
    scene=NativeScene(game)
    ball=game.ball
    body=ball.body
    floor=game.bounds()[3]
    body.x,body.y=420.,floor-body.half_h-28.
    ball.kick(120.,20.)
    ball.place()
    try:
        for _ in range(180):
            ball.step(.016,game.bounds())
            scene.sync()
        assert body.grounded and body.y == floor-body.half_h
        assert body.vx == body.vy == 0.
        resting=(body.x,body.y,ball.roll_angle)
        for _ in range(60):
            ball.step(.016,game.bounds())
            scene.sync()
        assert (body.x,body.y,ball.roll_angle)==resting
    finally:scene.close()


def test_mascara_pet_cacheada_invalida_tamanho_e_recorte_ao_mover(qt_application,tmp_path,monkeypatch):
    from bolha.pet import PetWindow
    from PySide6.QtGui import QRegion
    game=Game(tmp_path,CONTENT);pet=PetWindow(game);calls=[]
    original=pet.setMask
    def changed(mask):calls.append(QRegion(mask));original(mask)
    monkeypatch.setattr(pet,'setMask',changed)
    pet.sync();pet.sync();assert not calls
    game.configure(dict(avatarSize=180));pet.sync();assert len(calls)==1
    assert pet.mask().boundingRect().width()==180
    game.state.desk_top=game.body.y;pet.sync();assert len(calls)==2
    assert pet.mask().boundingRect().bottom()<128
    game.body.y-=20;pet.sync();assert len(calls)==3
    game.state.desk_top=None;pet.sync();assert len(calls)==4
    assert pet.mask().boundingRect().height()==180
    monkeypatch.setattr(pet,'devicePixelRatioF',lambda:1.5);pet.sync();assert len(calls)==5
    pet.close()
