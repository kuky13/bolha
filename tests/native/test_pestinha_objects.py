# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Desenhos GPL preservam aparência, rolagem e a autoridade da física existente."""
import math
from pathlib import Path
import pytest
from PySide6.QtCore import QRectF,QPoint,Qt
from PySide6.QtGui import QImage,QPainter
from game import Game
from bolha.objects import paint_notebook,paint_ball
from bolha.scene import NativeScene,ObjectWindow

CONTENT=Path(__file__).resolve().parents[2]/'assets/bolha/content'

def notebook(working=False,width=110,height=70):
    image=QImage(width,height,QImage.Format_ARGB32_Premultiplied);image.fill(0)
    painter=QPainter(image);painter.setRenderHint(QPainter.Antialiasing)
    paint_notebook(painter,QRectF(0,0,width,height),working);painter.end()
    return image


def ball(angle=0,paper=False):
    image=QImage(44,44,QImage.Format_ARGB32_Premultiplied);image.fill(0)
    painter=QPainter(image);painter.setRenderHint(QPainter.Antialiasing)
    paint_ball(painter,22,22,18,angle,paper);painter.end()
    return image


def test_notebook_detalhado_com_tela_teclas_base_e_estado_de_trabalho(qt_application):
    idle=notebook();working=notebook(True)
    # A tela tem painel, linhas de atividade e contraste com a moldura.
    assert len({idle.pixelColor(x,30).name() for x in range(12,98)})>4
    assert idle.pixelColor(55,20).lightness()<idle.pixelColor(55,61).lightness()
    assert working.pixelColor(98,61)!=idle.pixelColor(98,61)
    assert working.pixelColor(4,30).name()=='#c6a8ee'
    assert idle.pixelColor(4,30)!=working.pixelColor(4,30)

@pytest.mark.parametrize('paper',[False,True])
def test_bola_completa_mesmo_periodo_e_desenho_muda_quando_gira(qt_application,paper):
    initial=ball(0,paper);turned=ball(math.pi/2,paper);full=ball(math.tau,paper)
    assert bytes(initial.bits())==bytes(full.bits())
    assert bytes(initial.bits())!=bytes(turned.bits())
    assert initial.pixelColor(0,0).alpha()==0
    if not paper:
        assert initial.pixelColor(22,22).name()=='#14401f'
        highlight=initial.pixelColor(17,16);assert highlight.green()>240
        low=initial.pixelColor(22,34);assert low.green()>low.red() and low.green()>low.blue()


def test_rolagem_usa_corpo_existente_uma_vez_e_cache_para_quando_bola_para(qt_application,tmp_path,monkeypatch):
    game=Game(tmp_path,CONTENT);item=game.ball;body=item.body;calls=[]
    original=body.step
    def step(*args):calls.append(args);return original(*args)
    monkeypatch.setattr(body,'step',step)
    body.vx=100
    item.step(.016,game.bounds())
    assert item.body is body and len(calls)==1
    assert item.roll_angle==pytest.approx(100*.016*.8)
    snapshot=item.snapshot();assert snapshot['angle']==pytest.approx(math.degrees(item.roll_angle))
    body.vx=0;item.step(.016,game.bounds());assert item.snapshot()['angle']==snapshot['angle']
    item.dragging=True;item.step(.016,game.bounds());assert len(calls)==2
    assert item.snapshot()['angle']==snapshot['angle']


def test_mascaras_correspondem_aos_novos_desenhos_e_nao_mudam_raio_fisico(qt_application,tmp_path):
    game=Game(tmp_path,CONTENT);scene=NativeScene(game)
    window=ObjectWindow(scene,game.mesa.caderno);window.sync()
    assert window.mask().contains(QPoint(window.width()//2,window.height()//2))
    assert not window.mask().contains(QPoint(1,window.height()//2))
    assert not window.mask().contains(QPoint(0,0))
    assert window.windowFlags()&Qt.WindowDoesNotAcceptFocus
    game.mesa.caderno.set_working(True);window.sync()
    assert window.mask().contains(QPoint(window.width()//2,window.height()-9))
    toy=ObjectWindow(scene,game.ball)
    assert game.ball.body.half_w==game.ball.body.half_h==17
    assert toy.mask().contains(QPoint(toy.width()//2,toy.height()//2))
    assert not toy.mask().contains(QPoint(1,toy.height()//2))
    assert not toy.mask().contains(QPoint(0,0))
    window.close();toy.close()


def test_assets_fotograficos_excluidos_nao_entram_no_projeto():
    assets=Path(__file__).resolve().parents[2]/'assets'
    assert not any(path.name in ('notebook.png','bolinha_tenis.png') for path in assets.rglob('*.png'))
