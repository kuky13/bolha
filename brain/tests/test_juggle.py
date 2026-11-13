# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import time

import pytest

from game import Game
from bolha.motion import ExpressionMotion

CONTENT = Path(__file__).resolve().parents[2]/'assets/bolha/content'


def ready(tmp_path):
    game = Game(tmp_path,CONTENT)
    game.configure(dict(roaming=False, mischiefEnabled=False))
    game.body.x,game.ball.body.x = 180.,255.
    for body in (game.body,game.ball.body):
        body.surface = game.bounds()[3]
        body.y = body.surface-body.half_h
        body.grounded = True
    game.state.emotion = game.behavior.emotion = 'feliz'
    return game


@pytest.mark.parametrize('target', [1,100])
def test_juggle_counts_only_physical_touches_and_fades(tmp_path,monkeypatch,target):
    game = ready(tmp_path)
    now = time.monotonic()
    game.last_think = now+120.
    def pick(lo,hi):
        assert (lo,hi)==(1,100)
        return target
    monkeypatch.setattr('pestinha.body.brincadeira.random.randint',pick)
    game.interact(dict(type='play',trick='juggle'),now=now)
    counts = []
    for frame in range(3200):
        tick = now+frame/60
        game.tick(1/60,tick)
        count = game.play.juggle_count
        if count and (not counts or count!=counts[-1]):
            assert game.ball.body.vy<0.
            assert game.play.count_text(tick)[0]==str(count)
            counts.append(count)
        if count==target:
            break
    assert counts==list(range(1,target+1))
    assert game.play.count_text(tick+1.18)[1]<.3
    assert game.play.count_text(tick+1.3) is None


def test_pickup_interrupts_count_and_leaves_toy_in_hand(tmp_path,monkeypatch):
    game = ready(tmp_path)
    now = time.monotonic()
    monkeypatch.setattr('pestinha.body.brincadeira.random.randint',lambda *_:10)
    game.interact(dict(type='play',trick='juggle'),now=now)
    game.tick(.016,now)
    assert game.play.juggling()
    game.interact(dict(type='drag-start',id=game.ball.id,x=252.,y=280.),now=now+.08)
    game.tick(.016,now+.08)
    assert game.ball.body.held and not game.play.juggling()
    assert game.play.count_text(now+.08) is None


def test_brain_can_choose_juggling_without_a_manual_request(tmp_path,monkeypatch):
    game = ready(tmp_path)
    game.ball.body.x = game.body.x+70.
    choices_seen = []
    def choose(action,choices,**_):
        choices_seen.append((action,choices))
        return 'juggle'
    monkeypatch.setattr(game.play.policy,'choose',choose)
    action = game.play.tick(time.monotonic(),game.body,game.ball,game.cursor,'feliz',1.,game.bounds())
    assert action=='juggle' and game.play.juggle_count==1
    assert ('toy_play',['kick','juggle','wait']) in choices_seen


def test_slow_frames_do_not_hide_or_reset_the_running_count(tmp_path,monkeypatch):
    game = ready(tmp_path)
    now = time.monotonic()
    game.last_think = now+60.
    monkeypatch.setattr('pestinha.body.brincadeira.random.randint',lambda *_:6)
    game.interact(dict(type='play',trick='juggle'),now=now)
    numbers = []
    for frame in range(170):
        tick = now+frame*.22
        game.tick(.22,tick)  # Game caps physics steps at 50 ms.
        text, alpha = game.play.count_text(tick)
        assert alpha==1.
        if not numbers or text!=numbers[-1]:
            numbers.append(text)
        if text=='6':
            break
    assert numbers==[str(n) for n in range(1,7)]


def test_missed_ball_keeps_the_last_number_until_it_fades(tmp_path,monkeypatch):
    game = ready(tmp_path)
    now = time.monotonic()
    game.last_think = now+20.
    monkeypatch.setattr('pestinha.body.brincadeira.random.randint',lambda *_:6)
    game.interact(dict(type='play',trick='juggle'),now=now)
    game.tick(.016,now)
    assert game.play.juggling()
    toy = game.ball.body
    toy.x = game.body.x+300.
    toy.vx = 0.
    for frame in range(1,100):
        tick = now+frame*.016
        game.tick(.016,tick)
        if not game.play.juggling():
            break
    assert toy.grounded and not game.play.juggling()
    assert game.play.count_text(tick)==('1',1.)
    assert 0.<game.play.count_text(tick+1.17)[1]<.5
    assert game.play.count_text(tick+1.26) is None


def test_juggle_pose_stays_coherent_between_taps(tmp_path,monkeypatch):
    game = ready(tmp_path)
    now = time.monotonic()
    game.last_think = now+20.
    monkeypatch.setattr('pestinha.body.brincadeira.random.randint',lambda *_:6)
    game.interact(dict(type='play',trick='juggle'),now=now)
    game.tick(.016,now)
    motion = ExpressionMotion(now)
    contact = motion.update(game,now+.055)
    between_taps = motion.update(game,now+.45)
    assert motion.mode=='embaixadinha'
    assert contact['emotion']==between_taps['emotion']=='contente'
    assert contact['mouth_open']>.4 and between_taps['mouth_open']==0.
