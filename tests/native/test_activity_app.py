# SPDX-License-Identifier: GPL-3.0-or-later
from bolha.app import NativeApp
from pestinha import scene, store
import pytest


def test_actual_windows_switch_to_test_game_and_restore_after_stop(qt_application, tmp_path, monkeypatch):
    from bolha.updates import Updater
    monkeypatch.setattr(Updater, 'start', lambda self: None)
    monkeypatch.setenv('BOLHA_TEST', '1')
    controller = NativeApp(qt_application, tmp_path)
    original, original_scene = controller.game, controller.scene
    try:
        controller.frame.stop()
        controller.profile_timer.stop()
        controller.status_timer.stop()
        original.save()
        assert controller.writer.flush()
        before = {str(p):p.read_bytes() for p in original.data_dir.rglob('*') if p.is_file()}
        controller.show_settings()
        settings = controller.dialogs[0]
        assert not controller.start_activity_test('sleep')
        assert controller.game is not original and controller.game.sleep.asleep
        assert controller.pet.game is controller.game and controller.scene.game is controller.game
        assert not settings.isVisible() and controller.activity_test_dialog.isVisible()
        assert not controller.game.panel
        controller.game.save()
        controller.activity_test_dialog.advance()
        assert not controller.game.sleep.asleep
        controller.stop_activity_test()
        assert controller.game is original and controller.scene is original_scene
        assert scene._current is original and store._dispatcher == controller.writer.submit
        assert settings.isVisible() and original.panel
        assert controller.writer.flush()
        assert {str(p):p.read_bytes() for p in original.data_dir.rglob('*') if p.is_file()} == before
    finally:
        controller.quit()
