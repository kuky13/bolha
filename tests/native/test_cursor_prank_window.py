# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
from pathlib import Path
import time

from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest

from game import Game
from bolha.pet import PetWindow
from bolha.motion import animation_pose, ExpressionMotion


CONTENT = Path(__file__).resolve().parents[2] / 'assets/bolha/content'


def chewing_window(tmp_path):
    game = Game(tmp_path, CONTENT)
    game.configure(dict(cursorPrankEnabled=True, senseCursor=True, senseIdle=True))
    game.body.x, game.body.y = 600., 350.
    game.cursor = (600., 375.)
    game.cursor_prank._enter('chew', time.monotonic())
    game.cursor_prank.anchor = game.cursor
    window = PetWindow(game)
    return game, window


def test_scoped_blank_cursor_restores_on_real_movement_or_close(qt_application, tmp_path):
    game, window = chewing_window(tmp_path)
    try:
        assert window.cursor().shape() == Qt.BlankCursor
        assert not window._release_prank_cursor(QPointF(*game.cursor))
        assert window.cursor().shape() == Qt.BlankCursor
        assert window._release_prank_cursor(QPointF(610., 375.))
        assert window.cursor().shape() != Qt.BlankCursor
        assert game.cursor_prank.phase == 'spit'
        game.cursor_prank._enter('chew', time.monotonic())
        window.sync()
        assert window.cursor().shape() == Qt.BlankCursor
        window.close()
        assert window.cursor().shape() != Qt.BlankCursor
        assert not game.cursor_prank.hidden_cursor
    finally:
        window.close()


def test_disabling_cursor_reading_restores_the_widget_cursor(qt_application, tmp_path):
    game, window = chewing_window(tmp_path)
    try:
        assert window.cursor().shape() == Qt.BlankCursor
        game.configure(dict(senseCursor=False))
        window.sync()
        assert window.cursor().shape() != Qt.BlankCursor
        assert not game.cursor_prank.active
    finally:
        window.close()


def test_click_immediately_restores_cursor_without_starting_a_drag(qt_application, tmp_path):
    game, window = chewing_window(tmp_path)
    try:
        QTest.mouseClick(window, Qt.LeftButton)
        assert window.cursor().shape() != Qt.BlankCursor
        assert game.cursor_prank.phase == 'spit'
        assert not game.body.held and window.press is None
    finally:
        window.close()


def test_angry_prank_keeps_the_actual_brain_anger_visible(tmp_path):
    game = Game(tmp_path, CONTENT)
    game.cursor_prank._enter('approach', 100.)
    game.cursor_prank.angry_attempt = True
    game.state.tone.r['ANGRY'] = .91
    pose = ExpressionMotion(100.).update(game, 100.1)
    assert pose['emotion'] == 'bravo'
    assert pose['anger'] == .91
    assert pose['mouth_curve'] < 0.


def test_gag_frames_have_shared_mouth_state_and_neutral_frames_keep_small_mouth():
    for phase in ('cursor_approach', 'cursor_pounce', 'cursor_swallow', 'cursor_chew',
                  'cursor_spit', 'cursor_recover'):
        pose = animation_pose(phase, .16)
        assert 0. <= pose['mouth_open'] <= 1.
        assert -1. <= pose['mouth_curve'] <= 1.
        assert 0. <= pose['tongue'] <= 1.
    assert animation_pose('cursor_swallow', .05)['mouth_open'] > .6
    assert animation_pose('cursor_chew', .2)['mouth_chew'] > 0.
    assert animation_pose('cursor_spit', .4)['tongue'] > 0.
    assert animation_pose('observando', 0.)['mouth_open'] == 0.
