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
    assert a.pixelColor(42,39)!=idle.pixelColor(42,39)
    assert b.pixelColor(42,39)!=idle.pixelColor(42,39)


@pytest.mark.parametrize('x, side', [(-608, -1), (-230, 1)])
def test_desk_pose_chooses_the_free_side_and_tracks_notebook(tmp_path,x,side):
    from game import Game
    from bolha.motion import ExpressionMotion

    game=Game(tmp_path, Path(__file__).resolve().parents[2] / 'assets/bolha/content')
    game.configure(dict(avatarSize=180,objectScales=dict(notebook=.65)))
    game.desktop(dict(areas=[dict(x=-660,y=0,width=480,height=660)]))
    notebook=game.mesa.caderno
    notebook.place(x,500)
    assert notebook.width()<2*game.body.half_w
    game.mesa.tick(.01,{},20.,True,game.play)
    game.last_think=10.
    game.tick(.016,.05)
    motion=ExpressionMotion(0.)
    tap=motion.update(game,.05).copy()
    pause=motion.update(game,2.8).copy()
    assert game.state.at_desk and game.mesa.caderno.working
    assert game.state.desk_top is None
    assert (x-game.body.x)*side > game.body.half_w
    assert -660+game.body.half_w<=game.body.x<=-180-game.body.half_w
    assert tap['gaze'][0]*side > .5
    assert tap['gaze'][1]>pause['gaze'][1]
    assert tap['mouth_open']==pause['mouth_open']==0.
    old_x=game.body.x
    notebook.place(x+10*side,510)
    game.tick(.016,2.82)
    assert game.body.x==pytest.approx(old_x+10*side)
    assert game.body.y+game.body.half_h==pytest.approx(notebook.base_y())
    game.interact(dict(type='notebook'),now=2.85)
    assert not game.mesa.caderno.working and game.state.desk_top is None
    assert not game.state.at_desk
