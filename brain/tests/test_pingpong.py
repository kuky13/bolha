# SPDX-License-Identifier: GPL-3.0-only
import pytest
from pathlib import Path
import time

from game import Game
from pingpong import PingPong

CONTENT = Path(__file__).resolve().parents[2]/'assets/bolha/content'


def game():
    return PingPong((-1920, -100, -640, 620), 80, 18)


def test_negative_desktop_coordinates_and_small_monitor():
    g = game()
    assert g.court == pytest.approx((-1820, -22.5, -740, 577.5))
    assert g.pet_x-g.pet_radius > g.area[0]
    small = PingPong((0, 0, 500, 360), 55, 14)
    assert small.court[2] - small.court[0] >= 220
    with pytest.raises(ValueError):
        PingPong((0, 0, 300, 200), 50, 20)


def test_serve_delay_and_wall_rebound():
    g = game()
    for _ in range(5):
        assert g.step(.12, g.player_y, .5) is None
    assert g.vx == 0
    g.step(.06, g.player_y, .5)
    assert g.vx > 0
    g.ball_y = g.court[1] + g.toy_radius + 1
    g.vy = -500
    g.step(.02, g.player_y, .5)
    assert g.vy > 0


def test_player_hit_then_miss_scores_pet():
    g = game()
    g.serve_delay = 0
    g.ball_x = g.player_x - 30
    g.ball_y = g.player_y
    g.vx, g.vy = 500, 0
    assert g.step(.04, g.player_y, .5) == 'player_hit'
    assert g.vx < 0
    g.ball_x = g.court[2] - 1
    g.ball_y = g.court[1] + g.toy_radius + 2
    g.vx = 500
    assert g.step(.05, g.player_y, .5) == 'pet_point'
    assert g.pet_score == 1 and g.serve_delay > 0


def test_first_to_five_finishes():
    g = game()
    g.player_score = 4
    g.ball_x = g.court[0] + 5
    g.ball_y = g.court[3] - g.toy_radius - 2
    g.vx = -1500
    g.serve_delay = 0
    assert g.step(.02, g.player_y, .5) == 'player_point'
    assert g.finished and g.winner == 'player'
    assert g.step(1, g.player_y, 1) is None


@pytest.mark.parametrize('appearance',['ball','peanut'])
def test_partida_real_usa_brinquedo_e_restaura_passeio(tmp_path, monkeypatch, appearance):
    clock = [100.]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game = Game(tmp_path, CONTENT)
    game.configure(dict(toyAppearance=appearance,senseApp=False,senseIdle=False,senseWindows=False))
    game.interact({'type':'ball'})
    origin = game.body.x,game.body.y,game.ball.body.x,game.ball.body.y
    toy = game.ball
    assert game.interact({'type':'pingpong'}) is None
    match = game.pingpong
    assert game.ball is toy and toy.isVisible() and toy.appearance==appearance
    game.interact(dict(type='cursor',x=-200,y=-200))
    game.tick(.016,clock[0])
    assert game.pingpong_paused() and match.serve_delay==.65
    for _ in range(420):
        clock[0] += .016
        game.interact(dict(type='cursor',x=match.player_x,y=match.ball_y))
        game.tick(.016,clock[0])
        if match.rally>=2:
            break
    assert match.rally>=2
    assert (toy.body.x,toy.body.y)==(match.ball_x,match.ball_y)
    assert (game.body.x,game.body.y)==(match.pet_x,match.pet_y)
    game.interact({'type':'panel','value':True})
    ball_x = match.ball_x
    game.tick(.016,clock[0]+.016)
    assert match.ball_x==ball_x
    game.save()
    import json
    assert json.loads((tmp_path/'position.json').read_text())==dict(x=origin[0],y=origin[1])
    game.interact({'type':'pingpong'})
    assert game.pingpong is None and not toy.isVisible()
    assert (game.body.x,game.body.y,toy.body.x,toy.body.y)==origin


def test_desligar_cursor_e_bloquear_tela_encerram_partida(tmp_path):
    game = Game(tmp_path, CONTENT)
    game.configure({'senseCursor':False})
    assert 'cursor' in game.interact({'type':'pingpong'})
    assert game.pingpong is None
    game.configure({'senseCursor':True})
    game.interact({'type':'pingpong'})
    assert game.pingpong is not None
    game.configure({'senseCursor':False})
    assert game.pingpong is None
    game.configure({'senseCursor':True})
    game.interact({'type':'pingpong'})
    game.blocked={0}
    game.tick(.016)
    assert game.pingpong is None
