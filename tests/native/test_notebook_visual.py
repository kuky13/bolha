# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""A arte detalhada preserva escala, silhueta e anima somente quando em uso."""
from pathlib import Path

import pytest
from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import QImage, QPainter, QPainterPathStroker
from bolha.objects import paint_notebook, notebook_shape


def render(width, height, working=False, phase=0.):
    image=QImage(width,height,QImage.Format_ARGB32_Premultiplied);image.fill(0)
    painter=QPainter(image);painter.setRenderHint(QPainter.Antialiasing)
    paint_notebook(painter,QRectF(0,0,width,height),working,phase)
    painter.end()
    return image


@pytest.mark.parametrize('size',[(66,42),(110,70),(198,126),(170,70),(110,115)])
@pytest.mark.parametrize('working',[False,True])
def test_art_stays_within_hit_silhouette_at_all_scales(qt_application,size,working):
    width,height=size
    image=render(width,height,working)
    path=notebook_shape(QRectF(0,0,width,height),working)
    # Inclui somente a cobertura parcial de antialias ao redor do contorno.
    stroker=QPainterPathStroker();stroker.setWidth(2.)
    covered=path.united(stroker.createStroke(path))
    visible=0
    for y in range(height):
        for x in range(width):
            if image.pixelColor(x,y).alpha()>20:
                visible+=1
                assert covered.contains(QPointF(x+.5,y+.5)),(size,working,x,y)
    assert visible>width*height*.2
    assert image.pixelColor(0,0).alpha()==0


def test_working_notebook_animates_only_screen_and_keys(qt_application):
    idle=render(110,70,False,0.)
    assert idle==render(110,70,False,.7)
    a,b=render(110,70,True,.05),render(110,70,True,.15)
    changes={(x,y) for y in range(70) for x in range(110) if a.pixel(x,y)!=b.pixel(x,y)}
    screen={(x,y) for x,y in changes if 10<=x<=100 and 9<=y<=44}
    keys={(x,y) for x,y in changes if 16<=x<=94 and 49<=y<=56}
    assert screen and keys and changes==screen|keys
    # O texto fica na tela quando a Bolha tira o dedo da tecla.
    assert a.pixelColor(44,39)!=idle.pixelColor(44,39)
    assert b.pixelColor(44,39)!=idle.pixelColor(44,39)


def test_desk_pose_tracks_notebook_and_clears_after_putting_it_away(tmp_path):
    from game import Game
    from bolha.motion import ExpressionMotion

    game=Game(tmp_path, Path(__file__).resolve().parents[2] / 'assets/bolha/content')
    game.configure(dict(avatarSize=180,objectScales=dict(notebook=.65)))
    game.mesa.caderno.place(400,500)
    game.mesa.tick(.01,{},20.,True,game.play)
    game.last_think=10.
    game.tick(.016,.05)
    motion=ExpressionMotion(0.)
    tap=motion.update(game,.05).copy()
    pause=motion.update(game,2.8).copy()
    assert game.state.at_desk and game.mesa.caderno.working
    assert game.body.x==400
    assert game.state.desk_top==game.mesa.caderno.screen_top()
    # O sorriso cabe acima da tampa, mesmo com a personagem grande.
    assert game.state.desk_top-game.body.y > .39*game.body.half_h
    assert tap['gaze'][1]>pause['gaze'][1]
    assert tap['mouth_open']==pause['mouth_open']==0.
    game.mesa.caderno.place(415,510)
    game.tick(.016,2.82)
    assert game.body.x==415 and game.state.desk_top==game.mesa.caderno.screen_top()
    game.interact(dict(type='notebook'),now=2.85)
    assert not game.mesa.caderno.working and game.state.desk_top is None
    assert not game.state.at_desk
