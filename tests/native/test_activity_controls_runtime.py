# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import math
import pytest
from game import Game

CONTENT = Path(__file__).resolve().parents[2]/'assets/bolha/content'


@pytest.fixture
def game(tmp_path):
    return Game(tmp_path, CONTENT)


def test_disabling_live_activities_stops_effects_without_erasing_grievance(game):
    game.protest.stage = 4
    game.protest.grievance = 1.2
    game.protest.respawn_at = 100.
    game.protest_ctl.carry(100., False)
    note = game.mischief._make('bilhete', 'contente', False)
    game.mischief._add(note)
    game.festa.fogos.launch(game.body.x, game.body.y)
    game.play.chase_until = 200.
    game.play.juggle_count = 4
    game.configure(dict(protestsEnabled=False, signsEnabled=False, revolutionEnabled=False,
                        fireworksEnabled=False, notesEnabled=False, chaseEnabled=False,
                        juggleEnabled=False, notebookEnabled=False))
    assert game.protest.grievance == 1.2 and game.protest.stage == 4
    assert game.protest.sign is None and not game.revolucao.papeis
    assert not game.play.juggling() and game.play.chase_until == 0.
    assert note.closed and not game.festa.fogos.isVisible()
    assert not game.mesa.caderno.isVisible()
    assert game.state.protest_stage == 0
    game.tick(.016, 100.1)
    assert game.protest.sign is None and not game.revolucao.papeis
    assert not game.mesa.caderno.isVisible()


@pytest.mark.parametrize('setting,event', [
    ('notebookEnabled', {'type': 'work'}), ('notebookEnabled', {'type': 'notebook'}),
    ('fireworksEnabled', {'type': 'celebrate'}), ('pingpongEnabled', {'type': 'pingpong'}),
    ('juggleEnabled', {'type': 'play', 'trick': 'juggle'}),
])
def test_disabled_commands_report_reason(game, setting, event):
    game.configure({setting: False})
    assert 'desligada' in game.interact(event, now=100.)
    assert game.intelligence.current_decision['refusal_reason'] == 'activity_disabled'


def test_turning_sign_back_on_restores_current_protest_without_new_stage(game, monkeypatch):
    monkeypatch.setattr('game.time.monotonic', lambda: 100.)
    game.protest.stage = 4
    game.protest.respawn_at = 99.
    game.protest_ctl.carry(100., False)
    assert game.protest.sign is not None and game.protest.respawn_at is None
    game.configure({'signsEnabled': False})
    assert game.protest.sign is None
    game.configure({'signsEnabled': True})
    game.protest_ctl.carry(101., False)
    assert game.protest.sign is not None and game.protest.stage == 4


def test_release_anger_follows_brain_and_caress_instead_of_fixed_duration(game):
    game.release_reaction = dict(kind='birra', started=100., until=100.4, intensity=.9)
    game.state.tone.r.update(ANGRY=.9, SAD=.2, SETTLE=0.)
    for i in range(200):
        game._update_release_reaction(.1, 100.+i*.1, False)
    assert game.release_reaction['until'] > 120.
    assert .7 < game.release_reaction['intensity'] < .9
    game.state.tone.r.update(ANGRY=0., SAD=0., SETTLE=1.)
    game._update_release_reaction(.1, 120., True)
    assert .1 < game.release_reaction['intensity'] < .7
    for i in range(30):
        game._update_release_reaction(.1, 120.+i*.1, True)
    assert not game.release_reaction


@pytest.mark.parametrize('block', ['panel', 'held', 'sleep', 'disabled'])
def test_revolution_runtime_guard(game, block, monkeypatch):
    game.protest.stage = 4
    game.protest.grievance = 1.3
    game.last_think = 200.
    game.revolucao.policy.event = lambda *args, **kwargs: True
    if block == 'panel': game.panel = True
    elif block == 'held': game.body.held = True
    elif block == 'sleep': game.sleep.fall_asleep()
    else: game.configure({'revolutionEnabled': False})
    game.tick(.016, 100.)
    assert not game.revolucao.papeis


def test_revolution_uses_opposite_selected_toy_and_not_main_toy(game):
    game.last_think = 200.
    game.configure({'toyAppearance': 'peanut', 'senseCursor': False})
    game.protest.stage = 4
    game.protest.grievance = 1.3
    game.revolucao.policy.event = lambda *args, **kwargs: True
    game.tick(.016, 100.)
    assert len(game.revolucao.papeis) == 1
    shot = game.revolucao.papeis[0]['bola']
    assert shot.kind == 'projectile' and shot.appearance == 'ball'
    assert shot is not game.ball and math.isfinite(shot.body.vx)
