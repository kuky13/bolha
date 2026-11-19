# SPDX-License-Identifier: GPL-3.0-or-later
import math
import random
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from pestinha.core.episodic import EpisodicMemory, MAX_ACTIONS, MAX_CONTEXTS
from pestinha.core.nervous_system import LIFBrain
from intelligence import Intelligence


def test_lif_pool_centers_do_not_pile_up():
    brain = LIFBrain()
    sensory_y = [p['center'][1] for p in brain.pools if p['group'] == 'sensory']
    motor_y = [p['center'][1] for p in brain.pools if p['group'] == 'motor']
    assert all(0.05 <= y <= 0.95 for y in sensory_y)
    assert all(0.05 <= y <= 0.95 for y in motor_y)
    assert len(set(round(y, 4) for y in sensory_y)) == len(sensory_y)
    assert len(set(round(y, 4) for y in motor_y)) == len(motor_y)


def test_apply_learning_updates_in_place_without_reallocating():
    brain = LIFBrain()
    w_id = id(brain.W)
    wl_id = id(brain.W_lif)
    brain.stimulate({'CARESS': 1.0})
    brain.step(20)
    brain.learn(1.0, 0.1, 0.25)
    assert id(brain.W) == w_id
    assert id(brain.W_lif) == wl_id
    assert np.allclose(brain.W[:, brain.Ns:], brain.W_lif)
    # Verify exact equivalence against W_base + learned * plastic_masks
    expected = brain.W_base.copy()
    for i, c in enumerate(brain.sensory_names):
        a = brain.pool(c)
        for j, post in enumerate(brain.plastic_posts):
            if brain.learned[i, j] != 0.0:
                b = brain.pool(post)
                expected[a['start']:a['start'] + a['n'], b['start']:b['start'] + b['n']] += (
                    brain.learned[i, j] * brain.plastic_masks[(c, post)]
                )
    assert np.allclose(brain.W, expected)


def test_episodic_consolidate_bounds_and_goal_isolation(tmp_path):
    mem = EpisodicMemory(tmp_path / 'ep.jsonl', tmp_path / 'prefs.json', rng=random.Random(1))
    for i in range(MAX_CONTEXTS + 20):
        ep = mem.start(f'ACT_{i}|observando', f'act_{i % (MAX_ACTIONS + 5)}')
        mem.resolve(ep, 'ok', 0.2)
    mem.consolidate()
    assert len(mem.table) <= MAX_CONTEXTS
    assert len(mem.totals) <= MAX_ACTIONS

    goal_ep = mem.start('rotina:1|PROGRAMMING|observando', 'goal:work', goal=True)
    mem.on_interaction()
    assert goal_ep['carinho'] is False
    mem.tick(goal_ep['inicio'] + 20.0, keep_ok=5.0, window=10.0)
    assert any(ep is goal_ep for ep in mem.open)


def test_intelligence_budget_hysteresis_and_deslocar(tmp_path):
    mem = EpisodicMemory(tmp_path / 'ep.jsonl', tmp_path / 'prefs.json', rng=random.Random(2))
    intel = Intelligence(mem, tmp_path / 'habits.json', rng=random.Random(2))
    for _ in range(3):
        intel.budget(150.0, limit=100.0)
    assert intel.compatibility
    for _ in range(3):
        intel.budget(80.0, limit=100.0)
    assert intel.compatibility == ''

    intel.until = 10.0
    intel.next_choice = 5.0
    intel.next_sample = 30.0
    intel.deslocar(12.0)
    assert math.isclose(intel.until, 22.0)
    assert math.isclose(intel.next_choice, 17.0)
    assert math.isclose(intel.next_sample, 42.0)
