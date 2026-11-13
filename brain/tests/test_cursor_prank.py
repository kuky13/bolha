# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
from pathlib import Path

import pytest

from game import Game


CONTENT = Path(__file__).resolve().parents[2] / 'assets/bolha/content'


def test_prank_never_starts_with_default_preferences(tmp_path):
    game = Game(tmp_path, CONTENT)
    game.body.grounded = True
    game.idle = 10000.
    game.state.emotion = 'bravo'
    game.state.tone.r['ANGRY'] = 1.
    game.cursor_prank.update(game, .016, 100.)
    game.cursor_prank.update(game, .016, 102.)
    assert not game.cursor_prank.active
    assert not game.cursor_prank.hidden_cursor


def prepared_game(tmp_path, monkeypatch, choice='approach'):
    game = Game(tmp_path, CONTENT)
    game.configure(dict(cursorPrankEnabled=True, adaptiveBehavior=True,
                        senseCursor=True, senseIdle=True))
    game.body.x, game.body.y = 600., 600.
    game.body.grounded = True
    game.body.angle = 0.
    game.cursor = (840., 350.)
    game.idle = 130.
    def choose(context, candidates, epsilon, bias=None):
        name = context.split('|')[0].removeprefix('cursor_prank_')
        preferred = {'intent': choice, 'capture': 'swallow', 'bote': 'pounce',
                     'swallow': 'chew'}.get(name, 'queasy')
        return preferred if preferred in candidates else candidates[0]
    monkeypatch.setattr(game.memory, 'choose', choose)
    return game


def test_idle_only_offers_a_brain_choice_and_can_be_refused(tmp_path, monkeypatch):
    game = prepared_game(tmp_path, monkeypatch, 'watch')
    assert not game.cursor_prank.update(game, .016, 100.)
    assert not game.cursor_prank.active
    decision = game.intelligence.current_decision
    assert decision['target'] == 'watch'
    assert decision['source'] == 'cursor_prank_policy'
    assert decision['factors']['idleSeconds'] == 130.
    assert not game.cursor_prank.hidden_cursor


def test_approach_uses_velocity_without_teleporting_and_has_cooldown(tmp_path, monkeypatch):
    game = prepared_game(tmp_path, monkeypatch)
    before = game.body.x, game.body.y
    game.cursor_prank.update(game, .016, 100.)
    assert game.cursor_prank.phase == 'approach'
    assert (game.body.x, game.body.y) == before
    assert 0. < game.body.vx <= 405.
    assert game.cursor_prank.next_attempt == 400.
    game.cursor_prank.cancel(game, 101.)
    game.cursor_prank.update(game, .016, 399.)
    assert not game.cursor_prank.active


def test_physical_approach_reaches_an_idle_pointer_and_unreachable_attempt_is_bounded(tmp_path, monkeypatch):
    game = prepared_game(tmp_path, monkeypatch)
    area = (0., 0., 1280., 720.)
    game.body.x, game.body.y = 300., area[3] - game.body.half_h
    game.body.surface = area[3]
    game.cursor = (600., 400.)
    for frame in range(500):
        held = game.cursor_prank.update(game, .016, 100. + frame * .016)
        if held:
            break
        game.body.step(.016, area, [])
    assert game.cursor_prank.hidden_cursor
    assert game.cursor_prank.phase == 'swallow'
    assert frame > 1
    assert 0. < game.body.x < area[2]

    game.cursor_prank.cancel(game, 110.)
    game.cursor_prank.next_attempt = game.cursor_prank.next_offer = 0.
    game.body.grounded = True
    game.cursor = (600., -9000.)
    game.cursor_prank.update(game, .016, 111.)
    game.cursor_prank.update(game, .016, 119.1)
    assert not game.cursor_prank.active
    assert not game.cursor_prank.hidden_cursor


@pytest.mark.parametrize('angle,offset', [(0., (0., 1.)), (90., (-1., 0.)),
                                         (180., (0., -1.)), (-90., (1., 0.))])
def test_capture_uses_rotated_mouth_contact(tmp_path, monkeypatch, angle, offset):
    game = prepared_game(tmp_path, monkeypatch)
    game.body.angle = angle
    distance = game.body.half_w * 18. / 49.
    expected = game.body.x + offset[0] * distance, game.body.y + offset[1] * distance
    assert game.cursor_prank.mouth_position(game.body) == pytest.approx(expected)
    game.cursor = expected
    game.cursor_prank.update(game, .016, 100.)
    assert game.cursor_prank.hidden_cursor


def test_keyboard_activity_also_cancels_an_idle_approach(tmp_path, monkeypatch):
    game = prepared_game(tmp_path, monkeypatch)
    game.cursor_prank.update(game, .016, 100.)
    game.idle = 0.
    game.cursor_prank.update(game, .016, 100.1)
    assert not game.cursor_prank.active


def test_capture_chews_until_mouse_moves_then_learns_neutral_escape(tmp_path, monkeypatch):
    game = prepared_game(tmp_path, monkeypatch)
    game.cursor = (game.body.x, game.body.y + game.body.half_w * 18. / 49.)
    assert game.cursor_prank.update(game, .016, 100.)
    assert game.cursor_prank.phase == 'swallow' and game.cursor_prank.hidden_cursor
    assert game.cursor_prank.update(game, .016, 100.4)
    assert game.cursor_prank.phase == 'chew'
    assert game.cursor_prank.update(game, .016, 10000.)
    game.interact(dict(type='cursor', x=game.cursor[0] + 20., y=game.cursor[1]), now=10000.1)
    assert not game.cursor_prank.hidden_cursor
    assert game.cursor_prank.phase == 'spit'
    assert game.memory.recent[-1]['valencia'] == 0.
    game.interact(dict(type='caress'), now=10001.)
    assert game.memory.recent[-1]['valencia'] == .8
    assert game.intelligence.history[-1]['source'] == 'cursor_prank_policy'


def test_strong_anger_allows_active_mouse_and_idle_attempt_stops_when_it_moves(tmp_path, monkeypatch):
    game = prepared_game(tmp_path, monkeypatch)
    game.idle = 0.
    game.state.emotion = 'bravo'
    game.state.tone.r['ANGRY'] = 1.
    game.cursor_prank.update(game, .016, 100.)
    assert not game.cursor_prank.active
    game.cursor_prank.update(game, .016, 101.7)
    assert game.cursor_prank.active and game.cursor_prank.angry_attempt
    game.interact(dict(type='cursor', x=900., y=350.), now=101.8)
    assert game.cursor_prank.active
    game.cursor_prank.cancel(game, 102.)
    game.cursor_prank.next_attempt = 0.
    game.cursor_prank.next_offer = 0.
    game.state.emotion = 'contente'
    game.idle = 130.
    game.cursor_prank.update(game, .016, 200.)
    assert not game.cursor_prank.angry_attempt
    game.interact(dict(type='cursor', x=910., y=350.), now=200.1)
    assert not game.cursor_prank.active


@pytest.mark.parametrize('setting', ['cursorPrankEnabled', 'adaptiveBehavior', 'senseCursor', 'senseIdle'])
def test_disabled_control_cancels_swallowed_cursor(tmp_path, monkeypatch, setting):
    game = prepared_game(tmp_path, monkeypatch)
    game.cursor = (game.body.x, game.body.y + game.body.half_w * 18. / 49.)
    game.cursor_prank.update(game, .016, 100.)
    game.configure({setting: False})
    assert not game.cursor_prank.hidden_cursor and not game.cursor_prank.active


def test_panel_and_user_hold_cancel_and_persistence_preserves_seed(tmp_path, monkeypatch):
    game = prepared_game(tmp_path, monkeypatch)
    game.cursor = (game.body.x, game.body.y + game.body.half_w * 18. / 49.)
    game.cursor_prank.update(game, .016, 100.)
    game.interact(dict(type='panel', value=True), now=100.1)
    assert not game.cursor_prank.active
    game.save()
    loaded = Game(tmp_path, CONTENT)
    assert loaded.brain.seed == 1313 and loaded.brain.N == 470
    assert not loaded.cursor_prank.hidden_cursor
