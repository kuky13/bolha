# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Captura Qt e leitura Windows limitada à duração do gesto manual."""
import math
import time
from collections import deque
from PySide6.QtCore import QPointF
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget
from .platform import drag_pointer


class MouseGrab:
    def __init__(self,widget):self.widget=widget;self.pointer=None;self.samples=deque(maxlen=64)

    def begin(self,point):
        self.samples.clear();self.track(point)
        self.pointer=drag_pointer()
        if self.widget.isVisible() and QGuiApplication.platformName() not in ('offscreen','minimal'):
            self.widget.grabMouse()

    def sample(self):
        if self.pointer is None:return None
        point,down=self.pointer.sample();point=QPointF(point)
        if not math.isfinite(point.x()) or not math.isfinite(point.y()):raise OSError('Ponteiro indisponível')
        return point,down

    def track(self,point):
        now=time.monotonic()
        if self.samples and now<self.samples[-1][0]:self.samples.clear()
        sample=(now,point.x(),point.y())
        if self.samples and now==self.samples[-1][0]:self.samples[-1]=sample
        else:self.samples.append(sample)
        while self.samples and now-self.samples[0][0]>.12:self.samples.popleft()

    def velocity(self,point):
        self.track(point)
        if len(self.samples)<2:return 0.,0.
        first,last=self.samples[0],self.samples[-1]
        if math.hypot(last[1]-first[1],last[2]-first[2])<4:return 0.,0.
        dt=max(last[0]-first[0],.001)
        return (last[1]-first[1])/dt,(last[2]-first[2])/dt

    def stop(self):
        self.pointer=None;self.samples.clear()
        if QWidget.mouseGrabber() is self.widget:self.widget.releaseMouse()
