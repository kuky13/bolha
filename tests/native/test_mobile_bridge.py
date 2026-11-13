# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Phone bridge contracts which cannot be exercised by the desktop entry point."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def mobile(tmp_path):
    spec = importlib.util.spec_from_file_location('test_mobile_bridge', ROOT/'android/app/src/main/python/mobile.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.start(str(tmp_path), str(ROOT/'assets/bolha/content'))
    module.resize(411., 700., 2.625)
    yield module
    module.fetcher.stop()


def test_size_preferences_survive_rotation_and_restart(mobile, tmp_path):
    mobile.configure(dict(avatarSize=96, senseCursor=False, shakeEnabled=True,
                          objectScales=dict(toy=.65, notebook=1.4)))
    mobile.resize(700., 411., 2.625)
    frame = json.loads(mobile.tick(.016))
    assert frame['radius'] == 48
    assert frame['preferences']['objectScales']['toy'] == .65
    assert not frame['preferences']['senseCursor']
    mobile.save()
    mobile.game = None
    mobile.fetcher.stop()
    mobile.start(str(tmp_path), str(ROOT/'assets/bolha/content'))
    assert mobile.preferences['avatarSize'] == 96
    assert not mobile.preferences['senseCursor']
    assert mobile.preferences['shakeEnabled']


def test_shake_is_optional_and_never_releases_a_held_object(mobile):
    pet, toy = mobile.game.body, mobile.game.ball.body
    pet.vx = toy.vx = 0.
    mobile.motion(22., 5., True)
    assert pet.vx == toy.vx == 0.
    mobile.configure(dict(shakeEnabled=True))
    pet.held = True
    mobile.motion(22., 5., True)
    assert pet.held and pet.vx == 0.
    assert toy.vx < 0 and not toy.grounded
    assert mobile.game.intelligence.history[-1]['source'] == 'phone_motion_neural_policy'


def test_neural_panel_exposes_real_connections_only_on_demand(mobile):
    assert 'neural' not in json.loads(mobile.tick(.016))


def test_native_media_failure_removes_object_without_punishing_learning(mobile):
    mobile.configure(dict(onlineReactions=True))
    item = mobile.game.mischief.create_online_reaction('feliz')
    assert item is not None
    mobile.media_cache[item.id] = object()
    mobile.media_requested.add(item.id)
    dismissed = len(mobile.game.mischief_ctl.dismiss_times)
    mobile.control(dict(type='reaction-failed', id=item.id))
    assert item.closed
    assert item.id not in mobile.media_cache
    assert item.id not in mobile.media_requested
    assert len(mobile.game.mischief_ctl.dismiss_times) == dismissed
    assert 'exibir' in mobile.last_error


def test_screen_off_cancels_held_pet_and_toy_without_throwing(mobile):
    mobile.action('hold-start')
    mobile.action('drag-start', 'toy', 180., 140.)
    assert mobile.game.body.held and mobile.game.ball.body.held
    mobile.control(dict(type='suspend'))
    assert not mobile.game.body.held and not mobile.game.ball.body.held
    assert mobile.game.held_since is None and not mobile.game.scene_dragging
    assert mobile.game.body.vx == mobile.game.ball.body.vx == 0.
    mobile.control(dict(type='monitor', value=True))
    mobile.control(dict(type='inspect-neuron', index=3))
    frame = json.loads(mobile.tick(.016))
    assert len(frame['neural']['positions']) == frame['neurons'] == 470
    for edge in frame['neural']['connections']:
        assert mobile.game.brain.W[edge['source'], edge['target']] == edge['weight']
    mobile.control(dict(type='monitor', value=False))
    assert 'neural' not in json.loads(mobile.tick(.016))


def test_drag_release_keeps_logical_touch_velocity(mobile):
    mobile.action('drag-start', 'pet', 180., 150.)
    mobile.action('drag', 'pet', 220., 180.)
    mobile.action('drag-end', 'pet', 220., 180., 600., -350.)
    assert not mobile.game.body.held
    assert mobile.game.body.vx == 600. and mobile.game.body.vy == -350.
    mobile.resize(411., 700., 3.5)
    assert mobile.game.body.half_w == mobile.preferences['avatarSize']/2


def test_all_expression_previews_are_serializable_and_do_not_change_emotion(mobile):
    initial = mobile.game.state.emotion
    mobile.control(dict(type='panel', value=True))
    for name in mobile.EXPRESSION_NAMES:
        mobile.control(dict(type='expression', name=name))
        frame = json.loads(mobile.tick(.016))
        assert frame['poseMode'] == name
        assert frame['emotion'] == initial
        assert 'mouth_enabled' in frame['pose']
