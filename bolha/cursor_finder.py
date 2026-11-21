# SPDX-License-Identifier: GPL-3.0-or-later
"""Sinal temporário de cursor, inspirado no Multi-Monitor-Mouse-Finder (NOTICE.md)."""
import math
import time

from PySide6.QtCore import QPointF, QRect, Qt
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from .character import draw_character


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
        self.until = 0
        self.target = None
        self.screen = None

    def start(self, seconds):
        self.started = time.monotonic()
        self.until = self.started + seconds
        self.screen = None

    def dismiss(self):
        self.until = 0
        self.hide()

    def tick(self, game, now):
        if not self.until:
            return
        if now >= self.until or game.panicked or not game.prefs['senseWindows']:
            self.dismiss()
            return
        pos = QCursor.pos()
        screens = QGuiApplication.screens()
        index_by_screen = {screen.name(): i for i, screen in enumerate(screens)}
        screen_at = QGuiApplication.screenAt(pos)
        # Em bordas com DPI diferentes, a direção vem da geometria do próprio Qt.
        target = locate((pos.x(), pos.y()), game.areas, game.monitors, game.blocked)
        if screen_at is not None:
            cursor_index = index_by_screen[screen_at.name()]
            if cursor_index < len(game.areas) and cursor_index not in game.blocked:
                target = cursor_index, (pos.x(), pos.y()), None
        if target is None or target[0] >= len(screens) or len(screens) != len(game.areas):
            self.dismiss()
            return
        index, anchor, direction = target
        area = game.areas[index]
        age = now - self.started
        x, y = anchor
        # Começa no ponto seguro mais próximo e converge em dois pulinhos.
        offset = 33 + 49 * max(0., 1. - age * 1.65)
        toward = 1 if x >= (area[0]+area[2])/2 else -1
        px, py = _nearest((x-toward*offset, y-20-15*abs(math.sin(age*11))), area, 33)
        bounds = screens[index].geometry()
        rect = QRect(round(min(x, px)-42), round(min(y, py)-42),
                     round(abs(x-px)+85), round(abs(y-py)+85)).intersected(bounds)
        screen = screens[index]
        if screen is not self.screen:
            self.winId()
            self.windowHandle().setScreen(screen)
            self.screen = screen
        if rect != self.geometry():
            self.setGeometry(rect)
        gaze = 1 if x > px else -1 if x < px else 0
        self.target = (x-rect.x(), y-rect.y(), px-rect.x(), py-rect.y(), direction, age, gaze)
        if not self.isVisible():
            self.show()
        self.update()

    def paintEvent(self, event):
        if self.target is None:
            return
        x, y, px, py, direction, age, toward = self.target
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        draw_character(painter, px, py, scale=.49, angle=5*toward*math.sin(age*11),
                       emotion='feliz', gaze=(toward, .12))
        painter.setPen(QPen(QColor('#282133'), 5))
        ring = 13 + 7 * (.5 + .5 * math.sin(age*10))
        if direction is None:
            painter.drawEllipse(QPointF(x,y), ring, ring)
            painter.setPen(QPen(QColor('#ffdd83'), 2))
            painter.drawEllipse(QPointF(x,y), ring, ring)
            painter.drawEllipse(QPointF(x,y), 3, 3)
        else:
            painter.translate(x,y)
            painter.rotate(math.degrees(direction))
            painter.setBrush(QColor('#ffdd83'))
            painter.drawPolygon(QPolygonF([QPointF(16,0), QPointF(-12,-10), QPointF(-6,0), QPointF(-12,10)]))
        painter.end()
