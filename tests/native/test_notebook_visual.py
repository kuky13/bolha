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


@pytest.mark.parametrize('size',[(66,42),(132,96),(216,157),(170,70),(110,115)])
@pytest.mark.parametrize('working',[False,True])
def test_art_stays_within_hit_silhouette_at_all_scales(qt_application,size,working):
    width,height=size
    image=render(width,height,working)
    path=notebook_shape(QRectF(0,0,width,height))
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
    idle=render(132,96,False,0.)
    assert idle==render(132,96,False,.7)
    active,pause=render(132,96,True,.05),render(132,96,True,.15)
    changes={(x,y) for y in range(96) for x in range(132) if active.pixel(x,y)!=pause.pixel(x,y)}
    keys={(x,y) for x,y in changes if 22<=x<=112 and 74<=y<=82}
    assert keys and changes==keys
    # A escrita permanece na tela depois que a Bolha solta a tecla.
    assert active.pixelColor(37,49)==pause.pixelColor(37,49)
    assert pause.pixelColor(37,49)!=idle.pixelColor(37,49)
    blink=render(132,96,True,2.55)
    assert blink.pixelColor(72,49)!=render(132,96,True,3.1).pixelColor(72,49)


@pytest.mark.parametrize('phase',[.05,.25,.45,.65,1.15,1.35,1.55,1.75,2.55,3.1])
def test_typing_preserves_chassis_and_silhouette(qt_application,phase):
    idle,working=render(132,96),render(132,96,True,phase)
    for y in range(96):
        for x in range(132):
            assert idle.pixelColor(x,y).alpha()==working.pixelColor(x,y).alpha()
            if idle.pixel(x,y)!=working.pixel(x,y):
                assert (31<=x<=101 and 18<=y<=58 or
                        22<=x<=112 and 74<=y<=82 or
                        111<=x<=116 and 83<=y<=87),(phase,x,y)


@pytest.mark.parametrize('phase',[float('nan'),float('inf'),float('-inf')])
def test_invalid_clock_does_not_break_drawing(qt_application,phase):
    assert render(132,96,True,phase)==render(132,96,True,0.)


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
