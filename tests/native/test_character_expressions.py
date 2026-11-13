# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""As expressões continuam legíveis e contidas quando a esfera vira geleia."""
import math

import numpy as np
import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter

from bolha.character import (EMOTIONS, FACE_RADIUS, draw_character,
                             draw_reaction_marks, draw_sleep_marks)


def render(draw, **kwargs):
    image = QImage(320, 320, QImage.Format_RGBA8888)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    draw(painter, 160, 160, **kwargs)
    painter.end()
    return np.frombuffer(image.constBits(), dtype=np.uint8).reshape(320, 320, 4).copy()


def gold(pixels):
    return ((pixels[:, :, 0] > 180) & (pixels[:, :, 1] > 110)
            & (pixels[:, :, 2] < 150) & (pixels[:, :, 3] > 32))


@pytest.mark.parametrize('mouth_enabled', [False, True])
def test_every_expression_stays_inside_deformed_rotating_body(qt_application, mouth_enabled):
    for radius, squash in ((24, -.25), (40, -.25), (68, .25), (100, -.25)):
        scale = radius / 49
        for angle in (0, 45, 135, 270):
            cosine, sine = math.cos(math.radians(angle)), math.sin(math.radians(angle))
            for emotion in EMOTIONS:
                pixels = render(draw_character, scale=scale, squash=squash, angle=angle,
                                emotion=emotion, gaze=(1, -1), ear_tilt=10,
                                mouth_enabled=mouth_enabled)
                ys, xs = np.nonzero(gold(pixels))
                assert len(xs), emotion
                dx, dy = (xs + .5 - 160) / scale, (ys + .5 - 160) / scale
                local_x = (dx*cosine + dy*sine) / (1+squash)
                local_y = (-dx*sine + dy*cosine) / (1-squash)
                assert np.all(np.hypot(local_x, local_y) < FACE_RADIUS + 2), emotion
                if not mouth_enabled:
                    assert np.all(local_y < 12), 'A opção sem boca preserva olhos e orelhas.'


def test_angry_and_sad_eyes_have_opposite_readable_lids(qt_application):
    slopes = {}
    for emotion in ('bravo', 'triste'):
        pixels = gold(render(draw_character, emotion=emotion))
        ys, xs = np.nonzero(pixels[150:171, 135:151])
        slopes[emotion] = np.polyfit(xs, ys, 1)[0]
    assert slopes['bravo'] > .03
    assert slopes['triste'] < -.03


def test_olhos_e_orelhas_apontam_para_o_lado_do_olhar(qt_application):
    left = gold(render(draw_character,emotion='atento',gaze=(-1.,0.)))
    right = gold(render(draw_character,emotion='atento',gaze=(1.,0.)))
    for region, displacement in ((slice(125,145),6.),(slice(147,174),12.)):
        left_x = np.nonzero(left[region])[1].mean()
        right_x = np.nonzero(right[region])[1].mean()
        assert right_x-left_x>displacement


@pytest.mark.parametrize('heading,angle,squash', [(-42.,28.,.20),(38.,-24.,-.20),(95.,64.,.12)])
def test_arco_da_rebatida_mantem_direcao_apos_deformar(qt_application,heading,angle,squash):
    effect=render(draw_reaction_marks,kind='rebatida',phase=.12,angle=angle,squash=squash,
                  effect_angle=heading-angle)
    ys,xs=np.nonzero(effect[:,:,3])
    weights=effect[ys,xs,3].astype(float)
    x=np.average(xs+.5-160,weights=weights)
    y=np.average(ys+.5-160,weights=weights)
    assert math.degrees(math.atan2(y,x))==pytest.approx(heading,abs=1.)


@pytest.mark.parametrize('angle', [0., -90., 137.])
def test_arco_de_contato_nasce_na_coordenada_informada(qt_application, angle):
    pixels = render(draw_reaction_marks, kind='rebatida', angle=angle, at_contact=True)
    ys, xs = np.nonzero(pixels[:,:,3])
    assert len(xs)
    assert np.min(np.hypot(xs+.5-160., ys+.5-160.)) < 2.
    assert np.max(np.hypot(xs+.5-160., ys+.5-160.)) < 15.


@pytest.mark.parametrize('kind', ['carinho', 'tonto', 'bravo', 'perseguindo', 'comemorando', 'rebatida'])
def test_reaction_marks_move_fade_and_fit_visual_window(qt_application, kind):
    assert not render(draw_reaction_marks, kind=kind, strength=0).any()
    first = render(draw_reaction_marks, kind=kind, phase=.2, scale=100/49)
    second = render(draw_reaction_marks, kind=kind, phase=.8, scale=100/49)
    assert not np.array_equal(first, second)
    for radius, squash in ((40, -.25), (100, 0.), (100, .25)):
        scale = radius / 49
        base = render(draw_reaction_marks, kind=kind, phase=.35, scale=scale, squash=squash, angle=0)
        by, bx = np.nonzero(base[:, :, 3])
        bw = base[by, bx, 3].astype(float)
        base_mx = np.average(bx + .5 - 160, weights=bw)
        base_my = np.average(by + .5 - 160, weights=bw)
        for angle in (0, 45, 90, 180, 270):
            rotated = render(draw_reaction_marks, kind=kind, phase=.35,
                             scale=scale, squash=squash, angle=angle)
            ys, xs = np.nonzero(rotated[:, :, 3])
            assert len(xs) and xs.min() > 0 and xs.max() < 319
            assert ys.min() > 0 and ys.max() < 319
            weights = rotated[ys, xs, 3].astype(float)
            rad = math.radians(angle)
            dx, dy = xs + .5 - 160, ys + .5 - 160
            ux = dx * math.cos(rad) + dy * math.sin(rad)
            uy = -dx * math.sin(rad) + dy * math.cos(rad)
            assert np.average(ux, weights=weights) == pytest.approx(base_mx, abs=1.5)
            assert np.average(uy, weights=weights) == pytest.approx(base_my, abs=1.5)


def test_sleep_marks_float_rotate_and_restore_painter_state(qt_application):
    assert not render(draw_sleep_marks, strength=0).any()
    first = render(draw_sleep_marks, phase=.2, scale=100/49)
    second = render(draw_sleep_marks, phase=1.3, scale=100/49)
    assert not np.array_equal(first, second)
    ys, xs = np.nonzero(first[:, :, 3])
    assert len(xs) and xs.min() > 160 and xs.max() < 319
    assert ys.min() > 0 and ys.max() < 160
    turned = render(draw_sleep_marks, phase=.2, scale=100/49, angle=180, squash=-.2)
    ty, tx = np.nonzero(turned[:, :, 3])
    assert len(tx) and tx.min() > 0 and tx.max() < 160
    assert ty.min() > 160 and ty.max() < 319
    image = QImage(320, 320, QImage.Format_RGBA8888)
    painter = QPainter(image)
    painter.translate(4, 9)
    painter.setOpacity(.45)
    before = painter.worldTransform(), painter.opacity(), painter.pen(), painter.brush()
    draw_sleep_marks(painter, 160, 160, scale=2, phase=.6, angle=90, squash=.15)
    draw_reaction_marks(painter, 160, 160, scale=2, phase=.6, angle=90, squash=.15)
    assert before == (painter.worldTransform(), painter.opacity(), painter.pen(), painter.brush())
    painter.end()


def test_rage_red_palette_and_attached_marks_in_pet_visual(qt_application, tmp_path):
    from pathlib import Path
    from game import Game
    from bolha.pet import PetWindow
    from bolha.motion import animation_pose
    calm = render(draw_character, emotion='observando', anger=0.)
    irritated = render(draw_character, emotion='bravo', anger=.45)
    furious = render(draw_character, emotion='bravo', anger=1.)
    # O interior da esfera escurecida fica visivelmente rubro conforme a raiva cresce.
    sample = slice(125, 195), slice(125, 195)
    calm_red = calm[*sample, 0].astype(float) - calm[*sample, 2].astype(float)
    mid_red = irritated[*sample, 0].astype(float) - irritated[*sample, 2].astype(float)
    high_red = furious[*sample, 0].astype(float) - furious[*sample, 2].astype(float)
    assert calm_red.mean() < mid_red.mean() < high_red.mean()
    assert high_red.mean() > 45 and furious[*sample, 0].mean() > calm[*sample, 0].mean() + 40
    content = Path(__file__).resolve().parents[2] / 'assets/bolha/content'
    game = Game(tmp_path, content)
    pet = PetWindow(game)
    try:
        pose = animation_pose('held', 4., 1.)
        pose['angle_offset'] = 0.
        pet.motion.pose = pose
        game.body.angle = 0.
        upright = pet.visual.grab().toImage()
        game.body.angle = 90.
        lying = pet.visual.grab().toImage()
        assert upright.pixelColor(160, 185).red() > upright.pixelColor(160, 185).blue() + 35
        assert lying.pixelColor(135, 160).red() > lying.pixelColor(135, 160).blue() + 35
        assert upright.bits() != lying.bits()
    finally:
        pet.close()
