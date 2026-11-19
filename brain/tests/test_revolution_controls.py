# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
from types import SimpleNamespace

import pytest
from game import Game
from pestinha.mind.revolucao import MAXIMO_PAPEIS, VIDA_PAPEL

CONTENT=Path(__file__).resolve().parents[2]/'assets/bolha/content'


def tick(game,now,**kw):
    game.revolucao.tick(now,.016,game.bounds(),(400,300),(300,-150),game.body,
                       True,True,[],100,**kw)


def test_opposite_projectile_each_shot_and_brain_controls_firing(tmp_path):
    game=Game(tmp_path,CONTENT)
    game.revolucao.policy=SimpleNamespace(event=lambda *args,**kw:False)
    tick(game,100)
    assert not game.revolucao.papeis
    game.revolucao.policy=SimpleNamespace(event=lambda *args,**kw:True)
    tick(game,101,toy_appearance='peanut')
    tick(game,101.2,toy_appearance='ball')
    assert len(game.revolucao.papeis)==1
    tick(game,101.7,toy_appearance='ball')
    first,second=[entry['bola'] for entry in game.revolucao.papeis]
    assert (first.kind,first.appearance)==('projectile','ball')
    assert (second.kind,second.appearance)==('projectile','peanut')
    assert first is not game.ball and second is not game.ball


def test_revolution_limit_lifetime_clear_and_disabled_sensor(tmp_path,monkeypatch):
    game=Game(tmp_path,CONTENT)
    game.revolucao.policy=SimpleNamespace(event=lambda *args,**kw:True)
    for index in range(10):tick(game,100+index*.61)
    assert len(game.revolucao.papeis)<=MAXIMO_PAPEIS==6
    born=100+9*.61
    game.revolucao.policy=SimpleNamespace(event=lambda *args,**kw:False)
    tick(game,born+VIDA_PAPEL)
    assert not game.revolucao.papeis
    def forbidden(*args,**kw):raise AssertionError('sensor desligado foi usado')
    import pestinha.mind.revolucao as module
    monkeypatch.setattr(module,'push_from_cursor',forbidden)
    choices=[]
    def choose(action, candidates, **kwargs):
        choices.append(action)
        return 'up'
    game.revolucao.policy=SimpleNamespace(event=lambda *args,**kw:True, choose=choose)
    tick(game,120,sense_cursor=False)
    tick(game,120.1,sense_cursor=False)
    assert game.revolucao.papeis
    assert choices == ['revolution_target']
    tick(game,121,enabled=False)
    assert not game.revolucao.papeis
    assert not any(item.kind=='projectile' for item in game.objects.values())
    tick(game,122,areas=[])
    assert not game.revolucao.papeis


def test_safe_target_avoids_monitor_gaps_and_blocked_display(tmp_path):
    game=Game(tmp_path,CONTENT)
    areas=[(-800,-100,-160,600),(100,0,700,500)]
    for cursor in ((0,0),(9999,9999),(-300,100)):
        target=game.revolucao._target(game.body,cursor,True,areas)
        assert any(left<=target[0]<right and top<=target[1]<bottom for left,top,right,bottom in areas)
