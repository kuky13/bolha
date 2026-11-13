# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Apoio acompanha pequenos arrastos de janela e solta superfícies indisponíveis."""
import pytest
from pestinha.core.physics import Body

BOUNDS = (0., 0., 1280., 760.)


def perched():
    body = Body(500., 332., 68., 68., circular=True)
    body.grounded, body.platform, body.surface = True, 42, 400.
    return body


@pytest.mark.parametrize('offset', [-45., -8., 8., 45.])
def test_same_window_vertical_drag_preserves_support(offset):
    body = perched()
    body.vx = 20.
    body.step(.016, BOUNDS, [(42, 200., 900., 400.+offset)])
    assert body.grounded and body.platform == 42
    assert body.surface == 400.+offset
    assert body.y == 332.+offset
    assert body.vy == 0.
    assert body.x > 500.  # Pode caminhar enquanto a janela se move.


@pytest.mark.parametrize('platforms', [[], [(43, 700., 1100., 400.)],
                                      [(42, 200., 900., 500.)],
                                      [(42, 800., 1100., 400.)]])
def test_missing_minimized_relocated_or_out_of_reach_platform_detaches(platforms):
    body = perched()
    before = body.y
    body.step(.016, BOUNDS, platforms)
    assert not body.grounded and body.platform is None
    body.step(.016, BOUNDS, platforms)
    assert body.y > before and body.vy > 0.


def test_walking_off_window_edge_falls_without_snapping_to_top():
    body = perched()
    body.x, body.vx = 899., 300.
    body.step(.016, BOUNDS, [(42, 200., 960., 400.)])
    assert not body.grounded and body.platform is None
    before = body.y
    body.step(.016, BOUNDS, [(42, 200., 960., 400.)])
    assert body.y > before


def test_falling_body_still_lands_on_visible_window_top():
    body = Body(500., 300., 68., 68., circular=True)
    body.vy = 200.
    for _ in range(20):
        body.step(.016, BOUNDS, [(42, 200., 900., 400.)])
        if body.grounded: break
    assert body.grounded and body.platform == 42
    assert body.y == 332.


def test_new_visible_window_underneath_can_take_over_support():
    body = perched()
    body.step(.016, BOUNDS, [(43, 200., 900., 400.)])
    assert not body.grounded and body.platform is None
    body.step(.016, BOUNDS, [(43, 200., 900., 400.)])
    assert body.grounded and body.platform == 43
    assert body.y == 332.
