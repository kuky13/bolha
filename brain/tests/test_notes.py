# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import time

from game import Game
from pestinha import config


CONTENT = Path(__file__).resolve().parents[2] / 'assets/bolha/content'


def test_note_near_pet_uses_one_slot_and_expires_without_negative_learning(tmp_path):
    game = Game(tmp_path, CONTENT)
    game.desktop(dict(areas=[dict(x=-420, y=0, width=420, height=720)]))
    game.body.x, game.body.y = -78, 634
    game.cursor = (-400, 360)
    now = time.monotonic()
    bounds = game.bounds()
    plan, note = game.mischief.plan('bilhete', 'feliz')
    assert plan == 'note'
    assert game.mischief.show_note(note, game.body, bounds, game.cursor, now)
    assert bounds[0] <= note.x-note.width()/2 < note.x+note.width()/2 <= bounds[2]
    assert 0 < game.body.y-note.y < 150
    assert not game.behavior.mission
    game.memory.start('IDLE|feliz', 'bilhete', note)
    perms = dict(config.DEFAULT_PERMISSIONS)
    assert not any(a.startswith('bilhete') for a in game.mischief.available('feliz', perms))
    duplicate = game.mischief._make('bilhete', 'feliz', False)
    assert not game.mischief.show_note(duplicate, game.body, bounds, game.cursor, now)
    game.mischief_ctl.expire_notes(now+.2)
    assert note.opacity == 1.
    game.mischief_ctl.expire_notes(note.expires_at-.175)
    assert .49 < note.snapshot()['opacity'] < .51
    game.interact(dict(type='drag-start', id=note.id, x=note.x, y=note.y))
    game.tick(0., note.expires_at)
    assert note.closed and note.id not in game.objects and not game.scene_dragging
    assert all(ep['thing'] is not note for ep in game.memory.open)
    assert not game.mischief_ctl.dismiss_times
    assert 'bilhete' in game.mischief.available('feliz', perms)
