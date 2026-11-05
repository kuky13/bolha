# SPDX-License-Identifier: GPL-3.0-only
"""Compact, click-through score and instruction capsule for desktop ping-pong."""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter
from PySide6.QtWidgets import QWidget

from .pet import FLAGS


class PingPongView(QWidget):
    """Show status without covering the toy, pet, or pointer interaction."""

    def __init__(self):
        super().__init__(None, FLAGS | Qt.WindowTransparentForInput)
        self.setWindowTitle('Bolha · Pingue-pongue')
        self.setAccessibleName('Placar do pingue-pongue da Bolha')
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setMouseTracking(False)
        self._match = None
        self._paused = False
        self._frame_key = None

    def sync(self, match, paused=False):
        self._match = match
        self._paused = bool(paused)
        if match is None:
            if self.isVisible():
                self.hide()
            self._frame_key = None
            return
        left, top, right, _ = match.area
        width = round(min(360.,right-left-24.))
        geometry = round((left+right-width)/2),round(top+12),width,64
        key = (match.player_score, match.pet_score, match.rally, match.best,
               match.serve_delay > 0, match.finished, match.winner, self._paused, geometry)
        if self.geometry().getRect() != geometry:
            self.setGeometry(*geometry)
        if not self.isVisible():
            self.show()
        if key != self._frame_key:
            self._frame_key = key
            self.update()

    def _font(self, size, bold):
        return QFont(self.font().family(), size, QFont.Bold if bold else QFont.Medium)

    def _label(self, painter, rect, text, *, size, bold=False, color=QColor(255,255,255)):
        font = self._font(size, bold)
        width = QFontMetricsF(font).horizontalAdvance(text)
        if width > rect.width():
            font.setPointSizeF(max(7., size * (rect.width()-4) / width))
        painter.setFont(font)
        painter.setPen(QColor(0,0,0,190))
        painter.drawText(rect.translated(0,1), Qt.AlignCenter, text)
        painter.setPen(color)
        painter.drawText(rect, Qt.AlignCenter, text)

    def paintEvent(self, event):
        match = self._match
        if match is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._paused:
            instruction = 'Pausado · volte à tela ou feche o menu'
        elif match.finished:
            instruction = ('Você venceu! · feche pelo menu da Bolha' if match.winner == 'player'
                           else 'A Bolha venceu · feche pelo menu da Bolha')
        elif match.serve_delay > 0:
            instruction = 'Saque · prepare o ponteiro'
        else:
            instruction = 'Toque no brinquedo com o ponteiro'

        score = f'VOCÊ  {match.player_score}   ·   {match.pet_score}  BOLHA'
        stats = f'TROCAS {match.rally}   ·   RECORDE {match.best}'
        panel = QRectF(self.rect())
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(9,17,29,178))
        painter.drawRoundedRect(panel, 17, 17)
        self._label(painter, QRectF(panel.left()+10,panel.top()+4,panel.width()-20,20), score,
                    size=12,bold=True)
        self._label(painter, QRectF(panel.left()+10,panel.top()+24,panel.width()-20,17), stats,
                    size=9,color=QColor(218,230,243))
        self._label(painter, QRectF(panel.left()+8,panel.top()+42,panel.width()-16,18), instruction,
                    size=9,bold=True,color=QColor(255,255,255))
        painter.end()
