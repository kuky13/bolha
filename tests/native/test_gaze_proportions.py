# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Regressão: olhar lateral nunca aumenta só um dos olhos."""
import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter
from bolha.character import draw_character, EMOTIONS, GOLD


class EyePainter(QPainter):
    def __init__(self, image):
        super().__init__(image)
        self.eyes = []

    def drawPath(self, path):
        if self.brush().style() != Qt.NoBrush and self.brush().color() == QColor(GOLD):
            self.eyes.append(path.boundingRect())
        super().drawPath(path)


@pytest.mark.parametrize('emotion', [e for e in EMOTIONS if e not in ('dormindo', 'tonto')])
@pytest.mark.parametrize('gaze', [(-1,-1), (-1,0), (-1,1), (0,-1), (0,0), (0,1), (1,-1), (1,0), (1,1)])
def test_eyes_have_equal_size_and_level_for_every_gaze(qt_application, emotion, gaze):
    image=QImage(320,320,QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter=EyePainter(image)
    draw_character(painter,160,160,emotion=emotion,gaze=gaze,blink_left=0.,blink_right=0.)
    painter.end()
    assert len(painter.eyes)==2
    a,b=painter.eyes
    assert a.width()==pytest.approx(b.width(),abs=1e-8)
    assert a.height()==pytest.approx(b.height(),abs=1e-8)
    assert a.center().y()==pytest.approx(b.center().y(),abs=1e-8)


def test_intentional_wink_still_closes_one_eye(qt_application):
    image=QImage(320,320,QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter=EyePainter(image)
    draw_character(painter,160,160,gaze=(1.,.5),blink_left=1.,blink_right=0.)
    painter.end()
    assert len(painter.eyes)==1
