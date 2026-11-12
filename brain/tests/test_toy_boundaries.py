# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""O brinquedo contorna a personagem em paredes e atravessa costuras de telas."""
import math
from pathlib import Path

import pytest
from game import Game

CONTENT = Path(__file__).resolve().parents[2] / 'assets/bolha/content'


@pytest.mark.parametrize('appearance', ['peanut', 'ball'])
@pytest.mark.parametrize('pet_xy,toy_xy', [
    ((1190, 500), (1263, 500)), ((90, 500), (17, 500)),
    ((500, 90), (500, 17)), ((500, 670), (500, 743)),
    ((1212, 692), (1263, 743)), ((68, 692), (17, 743)),
])
def test_contact_separates_circles_without_leaving_screen(tmp_path, appearance, pet_xy, toy_xy):
    game = Game(tmp_path, CONTENT)
    pet, toy = game.body, game.ball.body
    game.ball.appearance = appearance
    pet.x, pet.y = pet_xy
    toy.x, toy.y = toy_xy
    pet.vx, pet.vy = toy.x-pet.x, toy.y-pet.y
    toy.grounded = True
    game.ball.place()
    game._toy_contact(pet_xy, toy_xy, 100.)
    radius = pet.half_w + toy.half_w
    assert math.dist((pet.x, pet.y), (toy.x, toy.y)) >= radius
    assert toy.half_w <= toy.x <= 1280-toy.half_w
    assert toy.half_h <= toy.y <= 760-toy.half_h
    assert (game.ball._cx, game.ball._cy) == (toy.x, toy.y)


@pytest.mark.parametrize('side', [-1, 1])
def test_sustained_horizontal_push_does_not_pin_toy(tmp_path, side):
    game = Game(tmp_path, CONTENT)
    pet, toy = game.body, game.ball.body
    pet.x, pet.y = (1190 if side > 0 else 90), 692
    toy.x, toy.y = (1263 if side > 0 else 17), 692
    pet.grounded, pet.surface = True, 760
    positions = []
    for frame in range(90):
        before_pet, before_toy = (pet.x, pet.y), (toy.x, toy.y)
        pet.vx = side*240
        pet.step(.016, game.bounds(), [])
        game.ball.step(.016, game.bounds((toy.x, toy.y)))
        game._toy_contact(before_pet, before_toy, 100+frame*.016)
        positions.append((toy.x, toy.y))
        assert math.dist((pet.x, pet.y), (toy.x, toy.y)) >= pet.half_w+toy.half_w-.01
    assert max(y for _, y in positions)-min(y for _, y in positions) > 30
    assert len({(round(x), round(y)) for x, y in positions}) > 40


@pytest.mark.parametrize('seam', [0., 1280.])
def test_contact_does_not_turn_shared_edge_into_wall(tmp_path, seam):
    game = Game(tmp_path, CONTENT)
    game.areas = [(seam-1280, 0., seam, 760.), (seam, 0., seam+1280, 760.)]
    game.monitors = list(game.areas)
    pet, toy = game.body, game.ball.body
    pet.x, pet.y = seam-80., 500.
    toy.x, toy.y = seam-10., 500.
    pet.vx = 240.
    game._toy_contact((pet.x, pet.y), (toy.x, toy.y), 100.)
    assert toy.x > seam  # O fit por monitor prendia o brinquedo antes da costura.
    assert toy.y == 500.
    assert math.dist((pet.x, pet.y), (toy.x, toy.y)) == pytest.approx(85.5)


@pytest.mark.parametrize('held', ['pet', 'toy', 'dragging'])
def test_contact_never_repositions_held_body(tmp_path, held):
    game = Game(tmp_path, CONTENT)
    pet, toy = game.body, game.ball.body
    pet.x, pet.y, toy.x, toy.y = 1190., 500., 1263., 500.
    if held == 'pet': pet.held = True
    elif held == 'toy': toy.held = True
    else: game.ball.dragging = True
    before = vars(toy).copy()
    game._toy_contact((pet.x, pet.y), (toy.x, toy.y), 100.)
    assert vars(toy) == before


def test_contact_crosses_physical_seam_with_different_dpi_and_artificial_gap(tmp_path):
    game = Game(tmp_path, CONTENT)
    game.desktop({'areas': [
        dict(x=0., y=0., width=1536., height=864., monitorX=0., monitorY=0.,
             monitorWidth=1536., monitorHeight=864., nativeX=0., nativeY=0.,
             nativeWidth=1920., nativeHeight=1080., scaleFactor=1.25),
        dict(x=1920., y=0., width=1280., height=720., monitorX=1920., monitorY=0.,
             monitorWidth=1280., monitorHeight=720., nativeX=1920., nativeY=0.,
             nativeWidth=1920., nativeHeight=1080., scaleFactor=1.5),
    ]})
    pet, toy = game.body, game.ball.body
    pet.x, pet.y = 1456., 300.
    toy.x, toy.y = 1526., 300.
    pet.vx = 240.
    game._toy_contact((pet.x, pet.y), (toy.x, toy.y), 100.)
    assert toy.x > 1536.
    assert toy.y == 300.
    game.ball.step(.016, game.bounds((toy.x, toy.y)), game.areas, game.monitors, game.displays)
    assert 1920. < toy.x < 1940.
    assert toy.y == pytest.approx(250., abs=2.)
    assert toy.vx > 0.


def test_contact_after_monitor_disconnection_uses_remaining_edges(tmp_path):
    game = Game(tmp_path, CONTENT)
    game.areas = [(-1280., 0., 0., 760.), (0., 0., 1280., 760.)]
    game.monitors = list(game.areas)
    pet, toy = game.body, game.ball.body
    pet.x, pet.y, toy.x, toy.y = 1190., 500., 1263., 500.
    # A remoção da tela esquerda não deixa uma abertura fantasma na direita.
    game.areas = [(0., 0., 1280., 760.)]
    game.monitors = list(game.areas)
    game._toy_contact((pet.x, pet.y), (toy.x, toy.y), 100.)
    assert toy.x <= 1263.
    assert math.dist((pet.x, pet.y), (toy.x, toy.y)) >= 85.
    assert toy.y < pet.y
