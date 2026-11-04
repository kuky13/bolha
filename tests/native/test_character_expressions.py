# SPDX-License-Identifier: GPL-3.0-only
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


def test_every_expression_stays_inside_deformed_rotating_body(qt_application):
    for radius, squash in ((40, -.25), (68, .25), (100, -.25)):
        scale = radius / 49
        for angle in (0, 45, 135, 270):
            cosine, sine = math.cos(math.radians(angle)), math.sin(math.radians(angle))
            for emotion in EMOTIONS:
                pixels = render(draw_character, scale=scale, squash=squash, angle=angle,
                                emotion=emotion, gaze=(1, -1), ear_tilt=10)
                ys, xs = np.nonzero(gold(pixels))
                assert len(xs), emotion
                dx, dy = (xs + .5 - 160) / scale, (ys + .5 - 160) / scale
                local_x = (dx*cosine + dy*sine) / (1+squash)
                local_y = (-dx*sine + dy*cosine) / (1-squash)
                assert np.all(np.hypot(local_x, local_y) < FACE_RADIUS + 2), emotion
                assert np.all(local_y < 12), 'Nenhuma expressão acrescenta boca.'


def test_angry_and_sad_eyes_have_opposite_readable_lids(qt_application):
    slopes = {}
    for emotion in ('bravo', 'triste'):
        pixels = gold(render(draw_character, emotion=emotion))
        ys, xs = np.nonzero(pixels[150:171, 135:151])
        slopes[emotion] = np.polyfit(xs, ys, 1)[0]
    assert slopes['bravo'] > .03
    assert slopes['triste'] < -.03


@pytest.mark.parametrize('kind', ['carinho', 'tonto', 'bravo'])
def test_reaction_marks_move_fade_and_fit_visual_window(qt_application, kind):
    assert not render(draw_reaction_marks, kind=kind, strength=0).any()
    first = render(draw_reaction_marks, kind=kind, phase=.2, scale=100/49)
    second = render(draw_reaction_marks, kind=kind, phase=.8, scale=100/49)
    assert not np.array_equal(first, second)
    ys, xs = np.nonzero(first[:, :, 3])
    assert len(xs) and xs.min() > 0 and xs.max() < 319
    assert ys.min() > 0 and ys.max() < 319


def test_sleep_marks_float_and_restore_painter_state(qt_application):
    assert not render(draw_sleep_marks, strength=0).any()
    first = render(draw_sleep_marks, phase=.2, scale=100/49)
    second = render(draw_sleep_marks, phase=1.3, scale=100/49)
    assert not np.array_equal(first, second)
    ys, xs = np.nonzero(first[:, :, 3])
    assert len(xs) and xs.min() > 160 and xs.max() < 319
    assert ys.min() > 0 and ys.max() < 160
    image = QImage(320, 320, QImage.Format_RGBA8888)
    painter = QPainter(image)
    painter.translate(4, 9)
    painter.setOpacity(.45)
    before = painter.worldTransform(), painter.opacity(), painter.pen(), painter.brush()
    draw_sleep_marks(painter, 160, 160, scale=2, phase=.6)
    draw_reaction_marks(painter, 160, 160, scale=2, phase=.6)
    assert before == (painter.worldTransform(), painter.opacity(), painter.pen(), painter.brush())
    painter.end()
