# SPDX-License-Identifier: GPL-3.0-or-later
import math
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from game import Game
from bolha.scene import NativeScene,ObjectWindow,placard_path
from bolha.speech import measure_text_box
from pestinha.scene import Ball

CONTENT=Path(__file__).resolve().parents[2]/'assets/bolha/content'


@pytest.mark.parametrize('angle',[0,45,90,180,-45])
def test_placard_fits_narrow_display_rotates_and_text_is_measured(qt_application,tmp_path,angle):
    game=Game(tmp_path,CONTENT)
    game.areas=[(-320.,0.,0.,720.)]
    game.body.x,game.body.y=-50,600
    game.configure({'avatarSize':200,'objectScales':{'sign':1.8},'onlineReactions':False})
    game.body.angle=angle
    game.protest.stage=4;game.protest.respawn_at=1
    game.protest_ctl.carry(10,False)
    sign=game.protest.sign;sign.text='OLHA A BOLINHA QUE ACHEI'
    scene=NativeScene(game)
    try:
        scene.sync()
        assert sign.attached and sign.carried
        assert sign.snapshot()['angle']==angle
        assert -320<=sign._cx-sign.width()/2<=sign._cx+sign.width()/2<=0
        assert 0<=sign._cy-sign.height()/2<=sign._cy+sign.height()/2<=720
        path=placard_path(sign).boundingRect()
        assert path.left()>=0 and path.top()>=0
        assert path.right()<=sign.width() and path.bottom()<=sign.height()
        stable=(sign.board_width,sign.board_height)
        scene.sync();assert (sign.board_width,sign.board_height)==stable
        if angle==0:
            needed,_=measure_text_box(sign.text,sign.board_width,padding=(12,9,0))
            assert sign.board_height>=needed
    finally:scene.close()


def test_projectile_is_drawn_without_capturing_mouse_or_sharing_toy(qt_application,tmp_path):
    game=Game(tmp_path,CONTENT)
    projectile=Ball(400,200,kind='projectile');projectile.appearance='peanut';projectile.show()
    scene=NativeScene(game);window=ObjectWindow(scene,projectile)
    try:
        window.sync()
        assert window.windowFlags()&Qt.WindowTransparentForInput
        assert not window.grab().toImage().isNull()
        assert projectile.snapshot()['radius']==17
        projectile.deleteLater()
        assert game.ball.id in game.objects
    finally:window.close();scene.close()
