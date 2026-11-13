# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Falas locais escolhidas pela política neural, sem ler conteúdo do desktop."""
import math
import time

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen, QTransform
from PySide6.QtWidgets import QWidget
from .pet import FLAGS

from .dialogue import Dialogue, LINES, THOUGHTS, SPEECH_INTERVAL, AMBIENT_MIN_INTERVAL, speech_duration

COMPACT_TEXT_PADDING = (11, 8, 12)
BUBBLE_TEXT_FLAGS = Qt.AlignCenter | Qt.TextWordWrap


def bubble_path(rect, thought=False, anchor=None, tail_top=False, *, compact=False):
    """Silhueta comum a falas e bilhetes; a ponta permanece dentro da janela."""
    tail_space = 12 if compact else 16
    r = QRectF(rect).adjusted(2, 2, -2, -tail_space)
    path = QPainterPath()
    radius = 10 if compact else 15
    path.addRoundedRect(r, radius, radius)
    anchor_margin = 14 if compact else 20
    x = max(r.left()+anchor_margin, min(r.right()-anchor_margin, anchor if anchor is not None else r.center().x()))
    scale = .7 if compact else 1.
    if thought:
        path.addEllipse(QPointF(x, r.bottom()+5*scale), 4*scale, 3*scale)
        path.addEllipse(QPointF(x-3*scale, r.bottom()+11*scale), 2*scale, 2*scale)
    else:
        tail = QPainterPath(QPointF(x-9*scale, r.bottom()-1))
        tail.quadTo(x-5*scale, r.bottom()+7*scale, x-2*scale, r.bottom()+13*scale)
        tail.quadTo(x+3*scale, r.bottom()+5*scale, x+10*scale, r.bottom()-1)
        tail.closeSubpath()
        path = path.united(tail)
    if tail_top:
        path = QTransform().translate(0, rect.top()+rect.bottom()).scale(1, -1).map(path)
    return path


def paint_bubble(painter, rect, text, thought=False, anchor=None, opacity=1., tail_top=False, *, compact=False):
    painter.save()
    painter.setOpacity(painter.opacity()*max(0., min(1., opacity)))
    painter.setPen(QPen(QColor('#9383af' if compact else '#b4a0d8'), 1. if compact else 1.3))
    painter.setBrush(QColor(37, 33, 47, 224 if compact else 255))
    painter.drawPath(bubble_path(rect, thought, anchor, tail_top, compact=compact))
    painter.setPen(QColor('#fff1c7'))
    font = QFont('Segoe UI', 10)
    painter.setFont(font)
    pad_x, pad_y, tail = COMPACT_TEXT_PADDING if compact else (14, 10, 14)
    text_rect = QRectF(rect).adjusted(pad_x, pad_y + (tail if tail_top else 0),
                                    -pad_x, -pad_y - (0 if tail_top else tail))
    painter.drawText(text_rect, BUBBLE_TEXT_FLAGS, text)
    painter.restore()


class SpeechWindow(QWidget):
    def __init__(self, game):
        super().__init__(None, FLAGS | Qt.WindowTransparentForInput)
        self.game = game
        self.dialogue = Dialogue()
        self.text = ''
        self.thought = False
        self.started = self.until = 0.
        self.counting = False
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setWindowTitle('Bolha · pensamento')
        self.setAccessibleName('Fala da Bolha')

    def present(self, text, thought=False, now=None):
        self.text, self.thought = str(text), bool(thought)
        self.started = time.monotonic() if now is None else now
        self.until = self.started + speech_duration(self.text)
        self.setAccessibleDescription(self.text)

    def sync(self, now=None):
        now = time.monotonic() if now is None else now
        game = self.game
        if not game.pet_visible(now) or game.panel or now < game.quiet_until or game.mischief.has_note():
            self.until = 0.
            self.hide()
            self.dialogue.previous = None
            self.dialogue.next_ambient = None
            return
        count = game.play.count_text(now)
        if count:
            self.counting = True
            if self.text != count[0]:
                self.text, self.thought = count[0], False
                self.setAccessibleDescription(self.text)
        else:
            if self.counting:
                self.counting = False
                self.until = 0.
            result = self.dialogue.update(game, now)
            if result:
                self.present(*result, now=now)
        if not self.text or (not count and now >= self.until):
            self.hide()
            return
        left, top, right, bottom = game.bounds((game.body.x, game.body.y))
        metrics = QFontMetricsF(QFont('Segoe UI', 10), self)
        pad_x, pad_y, tail = COMPACT_TEXT_PADDING
        width = min(212, int(right-left-16), max(46, math.ceil(metrics.horizontalAdvance(self.text))+2*pad_x+2))
        if width < 46:
            self.hide()
            return
        text_bounds = metrics.boundingRect(QRectF(0., 0., width-2*pad_x, 0.), BUBBLE_TEXT_FLAGS, self.text)
        height = math.ceil(text_bounds.height()) + 2*pad_y + tail + 3
        if height > bottom-top-16:
            self.hide()
            return
        self.resize(width, height)
        center_x = game.body.x
        if count:
            side = 1 if right-center_x >= center_x-left else -1
            center_x += side*(game.body.half_w+width/2+10.)
        x = max(left+8, min(right-width-8, center_x-width/2))
        self.anchor = game.body.x-x
        target_y = game.body.y-game.body.half_h-height-8
        toy = game.ball.body
        covers_toy = game.ball.isVisible() and (
            x-toy.half_w < toy.x < x+width+toy.half_w
            and target_y-toy.half_h < toy.y < target_y+height+toy.half_h)
        below_y = game.body.y+game.body.half_h+8
        self.tail_top = target_y < top+8 or (covers_toy and below_y+height <= bottom-8)
        if self.tail_top:
            target_y = below_y
        self.alpha = count[1] if count else min(1., max(0., (now-self.started)/.22), max(0., (self.until-now)/.30))
        eased = 1.-(1.-self.alpha)**3
        y = max(top+8, min(bottom-height-8, target_y+(1.-eased)*6))
        self.move(round(x), round(y))
        self.show()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        paint_bubble(p, QRectF(self.rect()), self.text, self.thought, self.anchor, self.alpha, self.tail_top, compact=True)
        p.end()
