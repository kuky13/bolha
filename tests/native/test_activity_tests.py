# SPDX-License-Identifier: GPL-3.0-or-later
"""O ensaio usa Game real, sem gravar na memória e sem reativar sensores."""
from pathlib import Path

import pytest

from bolha.activity_tests import ActivityTestSession, ACTIVITY_TESTS
from bolha.preferences import defaults, sanitize, ACTIVITY_SWITCHES, PreferencesStore
from game import Game
from pestinha import scene, store


CONTENT = Path(__file__).resolve().parents[2]/'assets/bolha/content'


def files(directory):
    return {str(path.relative_to(directory)): path.read_bytes()
            for path in directory.rglob('*') if path.is_file()}


def live_game(tmp_path):
    game = Game(tmp_path/'brain', CONTENT)
    game.configure(defaults())
    game.save()
    return game


def test_flags_persist_without_enabling_sensors(tmp_path):
    preferences = PreferencesStore(tmp_path)
    patch = {key: False for _, key, _ in ACTIVITY_SWITCHES}
    patch.update(senseApp=False, senseIdle=False, senseCursor=False, senseWindows=False)
    saved = preferences.save(patch)
    restored = PreferencesStore(tmp_path).preferences
    assert all(restored[key] is False for key in patch)
    assert restored == saved
    assert sanitize({'signsEnabled': 'false'}, saved)['signsEnabled'] is False


def test_real_game_steps_do_not_change_original_memory_even_on_save(tmp_path):
    live = live_game(tmp_path)
    before = files(live.data_dir)
    learned = live.brain.learned.copy()
    session = ActivityTestSession(live)
    temporary = session.root
    try:
        assert scene._current is session.game
        assert session.game.brain is not live.brain
        session.run('sleep', now=100.)
        assert session.game.sleep.asleep and not live.sleep.asleep
        session.game.save()
        session.next_step(now=101.)
        assert not session.game.sleep.asleep
        session.game.interact(dict(type='caress'), now=102.)
        session.game.save()
        assert files(live.data_dir) == before
        assert (live.brain.learned == learned).all()
    finally:
        session.stop()
    assert not temporary.exists()
    assert scene._current is live
    assert files(live.data_dir) == before
    assert store._dispatcher is None
    session.stop()


def test_disabled_function_and_sensor_are_reported_not_enabled(tmp_path):
    live = live_game(tmp_path)
    live.configure(dict(juggleEnabled=False, senseCursor=False, onlineReactions=False))
    before = files(live.data_dir)
    session = ActivityTestSession(live)
    try:
        assert 'desligada' in session.run('juggle')
        assert session.current is None
        assert 'ponteiro' in session.run('toy')
        assert session.current is None
        assert 'desligada' in session.run('gif')
        assert not session.game.prefs['senseCursor']
        assert not session.game.prefs['onlineReactions']
        assert files(live.data_dir) == before
    finally:
        session.stop()


def test_cleanup_restores_scene_dispatcher_after_an_action_error(tmp_path, monkeypatch):
    live = live_game(tmp_path)
    before = files(live.data_dir)
    queued = []
    previous = store._dispatcher
    dispatcher = lambda *args: queued.append(args)
    store.set_dispatcher(dispatcher)
    try:
        session = ActivityTestSession(live)
        with pytest.raises(OSError, match='fora do perfil'):
            store.write_text(live.data_dir/'dont-write.txt', 'forbidden')
        monkeypatch.setattr(session.game, '_cancel_holds', lambda *_: (_ for _ in ()).throw(RuntimeError('cleanup error')))
        with pytest.raises(RuntimeError, match='cleanup error'):
            session.stop()
        assert store._dispatcher is dispatcher
        assert scene._current is live
        assert not session.root.exists()
        assert not queued
        assert files(live.data_dir) == before
    finally:
        store.set_dispatcher(previous)


def test_constructor_failure_does_not_leave_scene_or_dispatcher_changed(tmp_path, monkeypatch):
    live = live_game(tmp_path)
    original = store._dispatcher
    import game
    def fail(*_):
        scene.set_scene(object())
        raise OSError('copy failed')
    monkeypatch.setattr(game, 'Game', fail)
    with pytest.raises(OSError, match='copy failed'):
        ActivityTestSession(live)
    assert scene._current is live
    assert store._dispatcher is original


def test_catalogue_and_steps_use_actual_controllers(tmp_path):
    live = live_game(tmp_path)
    keys = {item.key for item in ACTIVITY_TESTS}
    assert {'sleep', 'hold', 'throw', 'revolution', 'sign', 'gif', 'pop', 'cursor'} <= keys
    session = ActivityTestSession(live)
    try:
        session.run('revolution', now=100.)
        assert session.game.protest.stage == 4
        assert session.game.protest.grievance > 0
        assert session.game.state.protest_stage == 4
        assert session.has_next
        appearance = session.game.prefs['toyAppearance']
        session.next_step(now=101.)
        assert session.game.prefs['toyAppearance'] != appearance
        assert live.prefs['toyAppearance'] == appearance
        session.next_step(now=102.)
        assert session.game.protest.stage == 0
        assert not session.has_next
        assert not live.protest.stage
    finally:
        session.stop()
