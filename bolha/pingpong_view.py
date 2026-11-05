# SPDX-License-Identifier: GPL-3.0-only
"""Lightweight, input-transparent desktop ping-pong overlay."""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .pet import FLAGS


class PingPongView(QWidget):
    """Paint only the court and player paddle over the existing desktop scene."""

    def __init__(self):
        super().__init__(None, FLAGS | Qt.WindowTransparentForInput)
        self.setWindowTitle('Bolha · Pingue-pongue')
        self.setAccessibleName('Mesa de pingue-pongue da Bolha')
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
        left, top, right, bottom = match.area
        l, t, r, b = match.court
        x0, y0 = round(max(left,l-12)), round(max(top,t-66))
        x1, y1 = round(min(right,r+12)), round(min(bottom,b+40))
        geometry = x0, y0, max(1,x1-x0), max(1,y1-y0)
        frame_key = (match.court, match.player_x, round(match.player_y), match.player_half,
                     match.player_score, match.pet_score, match.rally, match.best,
                     match.serve_delay > 0., match.winner, self._paused)
        if self.geometry().getRect() != geometry:
            self.setGeometry(*geometry)
        if not self.isVisible():
            self.show()
        if self._frame_key != frame_key:
            self._frame_key = frame_key
            self.update()

    def _line(self, p, x1, y1, x2, y2):
        p.setPen(QPen(QColor(8,16,28,175),4.,Qt.DashLine,Qt.RoundCap))
        p.drawLine(round(x1), round(y1), round(x2), round(y2))
        p.setPen(QPen(QColor(227,210,250,205),2.,Qt.DashLine,Qt.RoundCap))
        p.drawLine(round(x1), round(y1), round(x2), round(y2))

    def _font(self, size, bold):
        return QFont(self.font().family(),size,QFont.Bold if bold else QFont.Medium)

    def _label(self, p, rect, text, *, size=13, bold=False, color=QColor(255,255,255), align=Qt.AlignCenter):
        font = self._font(size,bold)
        text_width = QFontMetricsF(font).horizontalAdvance(text)
        if text_width > rect.width():
            font.setPointSizeF(max(7.,size*(rect.width()-3)/text_width))
        p.setPen(QColor(0, 0, 0, 190))
        p.setFont(font)
        p.drawText(rect.translated(0, 1), align, text)
        p.setPen(color)
        p.drawText(rect, align, text)

    def paintEvent(self, event):
        match = self._match
        if match is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        ox, oy = self.x(), self.y()
        left, top, right, bottom = match.court
        x1, y1, x2, y2 = left-ox, top-oy, right-ox, bottom-oy
        court = QRectF(x1, y1, x2-x1, y2-y1)

        # A paired outline creates contrast without filling or obscuring the play area.
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(7, 16, 27, 175), 5.0))
        p.drawRoundedRect(court, 12, 12)
        p.setPen(QPen(QColor(255, 255, 255, 195), 2.0))
        p.drawRoundedRect(court, 12, 12)
        mid_x = (x1+x2)/2
        self._line(p, mid_x, y1+3, mid_x, y2-3)

        # Paddle position comes from the simulation. Do not paint the pet or toy here;
        # their real windows stay visible through this nearly transparent layer.
        px, py = match.player_x-ox, match.player_y-oy
        half = max(8, float(match.player_half))
        paddle_w = 10.0
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(5, 13, 23, 150))
        p.drawRoundedRect(QRectF(px-paddle_w/2-2, py-half-2, paddle_w+4, half*2+4), 6, 6)
        p.setBrush(QColor(255, 255, 255, 235))
        p.drawRoundedRect(QRectF(px-paddle_w/2, py-half, paddle_w, half*2), 5, 5)

        # HUD occupies the reserved top margin, with compact translucent capsules.
        hud_y = max(5, top-oy-58)
        score = f'VOCÊ {match.player_score}    ·    {match.pet_score} BOLHA'
        panel_w = min(self.width()-16,max(232,QFontMetricsF(self._font(12,True)).horizontalAdvance(score)+34))
        panel = QRectF((self.width()-panel_w)/2, hud_y, panel_w, 46)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(9, 17, 29, 162))
        p.drawRoundedRect(panel, 15, 15)
        self._label(p, QRectF(panel.left()+12, panel.top()+5, panel.width()-24, 18),
                    score,size=12,bold=True)
        small = f"TROCAS {match.rally}   ·   RECORDE {match.best}"
        self._label(p, QRectF(panel.left()+10, panel.top()+23, panel.width()-20, 17), small, size=10,
                    color=QColor(224, 235, 247))

        if self._paused:
            instruction = 'Pausa · volte à quadra'
        elif match.finished:
            instruction = ('Você venceu! · feche pelo menu' if match.winner == 'player'
                           else 'A Bolha venceu · feche pelo menu')
        elif match.serve_delay > 0:
            instruction = 'Saque · mova a raquete com o mouse'
        else:
            instruction = 'Mova o mouse para defender'
        hint = QRectF(0, min(self.height()-35, bottom-oy+11), self.width(), 26)
        p.setPen(Qt.NoPen)
        hint_w = min(self.width()-16,max(250,QFontMetricsF(self._font(10,True)).horizontalAdvance(instruction)+24))
        hint_box = QRectF((self.width()-hint_w)/2, hint.top(), hint_w, 25)
        p.setBrush(QColor(9, 17, 29, 145))
        p.drawRoundedRect(hint_box, 12, 12)
        self._label(p, hint_box.adjusted(8, 0, -8, 0), instruction, size=10, bold=True)
        p.end()
