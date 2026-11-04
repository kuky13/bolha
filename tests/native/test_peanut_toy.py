# SPDX-License-Identifier: GPL-3.0-only
import math
import time
from pathlib import Path
from types import SimpleNamespace
import pytest
from PySide6.QtCore import QPoint,QPointF,QEvent,Qt
from PySide6.QtGui import QImage,QPainter
from game import Game
from bolha.objects import paint_peanut
from bolha.preferences import PreferencesStore
from bolha.scene import NativeScene,ObjectWindow

CONTENT=Path(__file__).resolve().parents[2]/'assets/bolha/content'


def peanut(angle):
    image=QImage(44,44,QImage.Format_ARGB32_Premultiplied);image.fill(0)
    p=QPainter(image);p.setRenderHint(QPainter.Antialiasing)
    paint_peanut(p,22,22,17,angle);p.end();return image


def test_amendoim_gira_sem_recorte_e_sem_sprites(qt_application):
    first=peanut(0)
    assert bytes(first.bits())==bytes(peanut(math.tau).bits())
    assert bytes(first.bits())!=bytes(peanut(math.pi/2).bits())
    for angle in (0,.3,math.pi/2,math.pi):
        image=peanut(angle)
        assert image.pixelColor(22,22).alpha()>0
        assert not any(image.pixelColor(x,0).alpha() or image.pixelColor(x,43).alpha() for x in range(44))
        assert not any(image.pixelColor(0,y).alpha() or image.pixelColor(43,y).alpha() for y in range(44))


def test_seletor_persiste_sem_reativar_sensores(tmp_path):
    store=PreferencesStore(tmp_path)
    assert store.preferences['toyAppearance']=='peanut'
    store.save({'toyAppearance':'ball','senseCursor':False})
    reopened=PreferencesStore(tmp_path)
    assert reopened.preferences['toyAppearance']=='ball' and reopened.preferences['senseCursor'] is False
    reopened.save({'toyAppearance':'unknown'})
    assert reopened.preferences['toyAppearance']=='ball'
    reopened.reset_appearance()
    assert reopened.preferences['toyAppearance']=='ball' and reopened.preferences['senseCursor'] is False


def test_trocar_aparencia_atualiza_mascara_sem_mudar_fisica(qt_application,tmp_path):
    game=Game(tmp_path,CONTENT);scene=NativeScene(game);window=ObjectWindow(scene,game.ball)
    body=game.ball.body
    window.sync();before=window.mask()
    game.ball.roll_angle=math.pi/2;window.sync()
    assert window.mask()!=before
    game.configure({'toyAppearance':'ball'});window.sync()
    assert window.mask()!=before and game.ball.body is body
    assert body.half_w==body.half_h==17
    assert window.mask().contains(QPoint(21,21))
    assert window.windowFlags()&Qt.WindowDoesNotAcceptFocus
    window.close()


def mouse(x,y):
    return SimpleNamespace(button=lambda:Qt.LeftButton,globalPosition=lambda:QPointF(x,y))


@pytest.mark.parametrize('dragged',[False,True])
def test_toy_pega_imovel_ou_arrastado_rapido_cai_sem_impulso(qt_application,tmp_path,monkeypatch,dragged):
    clock=[100.];monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT);game.ball.body.x,game.ball.body.y=500,300;game.ball.place()
    window=ObjectWindow(NativeScene(game),game.ball);window.sync()
    try:
        body=game.ball.body;body.vx,body.vy,body.omega=900,-800,200
        window.enterEvent(None)
        assert not game.hover
        window.mousePressEvent(mouse(500,300))
        assert body.held and game.ball.dragging and body.vx==body.vy==body.omega==0
        if dragged:
            clock[0]+=.001;window.mouseMoveEvent(mouse(700,200))
        before=body.x,body.y
        window.mouseReleaseEvent(mouse(*before))
        assert not body.held and not game.ball.dragging and window.offset is None
        assert not game.hover and body.vx==body.vy==body.omega==0
        clock[0]+=.016;game.tick(.016,clock[0])
        assert body.x==before[0] and body.y>before[1] and body.vy>0
    finally:window.close()


@pytest.mark.parametrize('reason',['ungrab','hidden','panic','close'])
def test_cancelamento_do_toy_nao_deixa_pega_presa(qt_application,tmp_path,reason):
    game=Game(tmp_path,CONTENT);window=ObjectWindow(NativeScene(game),game.ball);window.sync()
    try:
        window.mousePressEvent(mouse(game.ball._cx,game.ball._cy))
        assert game.ball.body.held
        if reason=='ungrab':window.event(QEvent(QEvent.UngrabMouse))
        elif reason=='close':window.close()
        else:
            game.interact({'type':'panic'} if reason=='panic' else {'type':'hide','value':True})
            window.sync()
        assert window.offset is None and not game.ball.dragging and not game.ball.body.held
        assert not game.hover and not game.scene_dragging
        assert game.ball.body.vx==game.ball.body.vy==game.ball.body.omega==0
    finally:window.close()


def test_soltar_notebook_fora_desmarca_hover_que_pausava_pet(qt_application,tmp_path):
    game=Game(tmp_path,CONTENT);item=game.mesa.caderno;item.show()
    window=ObjectWindow(NativeScene(game),item);window.sync()
    try:
        window.enterEvent(None);assert game.hover
        window.mousePressEvent(mouse(item._cx,item._cy))
        window.leaveEvent(None);assert game.hover
        window.mouseReleaseEvent(mouse(item._cx+500,item._cy-200))
        assert not game.hover and not game.scene_dragging
    finally:window.close()
