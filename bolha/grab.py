# SPDX-License-Identifier: GPL-3.0-only
"""Captura Qt e leitura Windows limitada à duração do gesto manual."""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget
from .platform import drag_pointer


class MouseGrab:
    def __init__(self,widget):self.widget=widget;self.pointer=None

    def begin(self):
        self.pointer=drag_pointer()
        if self.widget.isVisible() and QGuiApplication.platformName() not in ('offscreen','minimal'):
            self.widget.grabMouse()

    def sample(self):
        if self.pointer is None:return None
        point,down=self.pointer.sample();point=QPointF(point)
        if not math.isfinite(point.x()) or not math.isfinite(point.y()):raise OSError('Ponteiro indisponível')
        return point,down

    def stop(self):
        self.pointer=None
        if QWidget.mouseGrabber() is self.widget:self.widget.releaseMouse()
