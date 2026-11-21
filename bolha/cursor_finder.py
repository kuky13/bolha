# SPDX-License-Identifier: GPL-3.0-or-later
"""Sinal temporário de cursor, inspirado no Multi-Monitor-Mouse-Finder (NOTICE.md)."""
import math

from PySide6.QtCore import QPointF, QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget


def _clamp(value, low, high):
    return max(low, min(value, high))


def _nearest(point, area, margin=0):
    x, y = point
    left, top, right, bottom = area
    mx, my = min(margin, (right-left-1)/2), min(margin, (bottom-top-1)/2)
    return (_clamp(x, left+mx, right-1-mx), _clamp(y, top+my, bottom-1-my))


def locate(cursor, areas, monitors, blocked):
    index = next((i for i, (l,t,r,b) in enumerate(monitors)
                  if l <= cursor[0] < r and t <= cursor[1] < b), None)
    if index is not None and index not in blocked:
        return index, cursor, None
    free = [i for i in range(len(areas)) if i not in blocked]
    if not free:
        return None
    def distance(i):
        x, y = _nearest(cursor, areas[i])
        return (x-cursor[0])**2 + (y-cursor[1])**2
    nearest = min(free, key=distance)
    anchor = _nearest(cursor, areas[nearest], 28)
    return nearest, anchor, math.atan2(cursor[1]-anchor[1], cursor[0]-anchor[0])


class CursorFinder(QWidget):
    def __init__(self):
        flags = (Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
                 Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus)
        super().__init__(None, flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.direction = 0.

    def indicate(self, point, direction):
        if direction is None:
            self.hide()
            return
        x, y = point
        self.direction = direction
        self.setGeometry(QRect(round(x)-22, round(y)-22, 44, 44))
        if not self.isVisible():
            self.show()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(22,22)
        painter.rotate(math.degrees(self.direction))
        painter.setPen(QPen(QColor('#282133'), 3))
        painter.setBrush(QColor('#ffdd83'))
        painter.drawPolygon(QPolygonF([QPointF(16,0), QPointF(-12,-10), QPointF(-6,0), QPointF(-12,10)]))
        painter.end()
