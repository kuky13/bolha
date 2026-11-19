# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter, QColor, QFont, QFontMetricsF
import pytest
from bolha.speech import measure_text_box, paint_box_text, _text_lines, bubble_font, SpeechWindow
from game import Game


@pytest.mark.parametrize('family', ['Segoe UI', 'Liberation Sans', 'DejaVu Sans'])
def test_multiline_text_reserves_font_leading(qt_application, family):
    font = QFont(family, 10)
    layout, lines, height = _text_lines('Trabalhando muito ou só encarando a tela comigo?', 190., font)
    assert len(lines) >= 2
    assert all(line.leadingIncluded() for line in lines)
    assert all(line.height() >= line.ascent()+line.descent()+max(0.,line.leading()) for line in lines)
    assert height >= QFontMetricsF(font).height()*len(lines)


@pytest.mark.parametrize('scale', [1., 1.25, 1.5, 2.])
@pytest.mark.parametrize('width', [96., 124., 190., 260.])
def test_reference_text_measured_and_painted_with_identical_wrap(qt_application, scale, width):
    image = QImage(round(400*scale), round(250*scale), QImage.Format_ARGB32_Premultiplied)
    image.setDevicePixelRatio(scale)
    image.fill(QColor('transparent'))
    text = 'OLHA A BOLINHA QUE ACHEI'
    height, font = measure_text_box(text, width, device=image)
    layout, lines, glyph_height = _text_lines(text, width-28., font, image)
    assert height-34 >= glyph_height+2.
    assert all(line.height() <= glyph_height for line in lines)
    painter = QPainter(image)
    try:
        painter.setPen(QColor('#fff1c7'))
        paint_box_text(painter, QRectF(14., 10., width-28., height-34.), text, now=0.)
    finally:
        painter.end()
    assert any(image.pixelColor(x, y).alpha() for x in range(image.width()) for y in range(image.height()))


def test_long_unbroken_text_wraps_and_long_speech_remains_visible(qt_application, tmp_path):
    text = 'Brinquedo'*200
    layout, lines, height = _text_lines(text, 100., bubble_font())
    assert len(lines) > 10
    assert all(line.naturalTextWidth() <= 100.1 for line in lines)
    game = Game(tmp_path, Path(__file__).resolve().parents[2]/'assets/bolha/content')
    game.areas = [(0., 0., 320., 300.)]
    game.body.x, game.body.y = 270., 260.
    window = SpeechWindow(game)
    try:
        window.dialogue.next_ambient = 1000.
        window.present(text, now=100.)
        window.sync(101.)
        assert window.isVisible()
        assert window.geometry().right() < 320 and window.geometry().bottom() < 300
        game.configure({'speechEnabled': False})
        window.sync(101.1)
        assert not window.isVisible()
    finally:
        window.close()
