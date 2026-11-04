# SPDX-License-Identifier: GPL-3.0-only
"""Janelas e gestos derivados de PetWindow do Pestinha (GPL-3.0-or-later).

Uma camada visual sem entrada preserva o halo. A janela de entrada tem
máscara circular nativa: a região fora do corpo recebe cliques no desktop.
"""
import math
import time
from collections import deque
from PySide6.QtCore import Qt,QRect,QPointF,QEvent,Signal
from PySide6.QtGui import QPainter,QColor,QRegion
from PySide6.QtWidgets import QWidget
from .character import draw_character,draw_sleep_marks,draw_reaction_marks
from .motion import ExpressionMotion

FLAGS = Qt.FramelessWindowHint|Qt.Tool|Qt.WindowStaysOnTopHint|Qt.WindowDoesNotAcceptFocus


class PetVisual(QWidget):
    painted=Signal()
    def __init__(self, pet):
        super().__init__(None,FLAGS|Qt.WindowTransparentForInput)
        self.pet=pet
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        # A geleia e o halo cabem no tamanho máximo sem ampliar a janela de entrada.
        self.setFixedSize(320,320)
        self.paint_times=deque(maxlen=600)

    def paintEvent(self,event):
        game=self.pet.game;now=time.monotonic()
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        if game.state.desk_top is not None:
            p.setClipRect(QRect(0,0,self.width(),max(0,int(game.state.desk_top-self.y()))))
        blink=1.0 if now < self.pet.blink_until else 0.0
        pose=self.pet.motion.pose
        # A transformação comum gira corpo, olhos e orelhas em torno do mesmo centro.
        draw_character(p,self.width()/2,self.height()/2,scale=game.body.half_w/49,
                       angle=game.body.angle+pose['angle_offset'],emotion=pose['emotion'],
                       blink=max(blink,pose['blink']),gaze=pose['gaze'] or game.state.gaze,
                       blink_left=pose['blink_left'],blink_right=pose['blink_right'],
                       ear_tilt=pose['ear_tilt'],ear_raise=pose['ear_raise'],
                       eye_open=pose['eye_open'],squash=pose['squash'],
                       body_opacity=game.prefs.get('opacity',1))
        if pose['zzz_strength']>0:
            draw_sleep_marks(p,self.width()/2,self.height()/2,game.body.half_w/49,
                             pose['zzz_phase'],pose['zzz_strength'])
        if pose['effect'] and pose['effect_strength']>0:
            draw_reaction_marks(p,self.width()/2,self.height()/2,game.body.half_w/49,
                                pose['effect_phase'],pose['effect'],pose['effect_strength'])
        p.end();self.paint_times.append(now);self.painted.emit()


class PetWindow(QWidget):
    menu_requested=Signal(object)
    def __init__(self, game):
        super().__init__(None,FLAGS)
        self.game=game;self.body=game.body
        self.setAccessibleName('Bolha')
        self.setWindowTitle('Bolha')
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True);self.setFixedSize(256,256)
        self.visual=PetVisual(self)
        self.press=None;self.offset=(0.,0.);self.dragging=False
        self.rubs=deque();self.next_blink=time.monotonic()+3.4;self.blink_until=0.
        self.motion=ExpressionMotion(time.monotonic())
        self.sync()

    def sync(self):
        now=time.monotonic()
        self.motion.update(self.game,now,self.press[1] if self.press else None)
        if self.motion.mode=='wink':self.blink_until=0.
        elif now>=self.next_blink:
            self.blink_until=now+.13;self.next_blink=now+3.2+(math.sin(now)*.5+.5)*2
        x,y=round(self.body.x-self.width()/2),round(self.body.y-self.height()/2)
        self.move(x,y)
        self.visual.move(round(self.body.x-self.visual.width()/2),round(self.body.y-self.visual.height()/2))
        r=round(self.body.half_w)
        clip=max(0,min(256,int(self.game.state.desk_top-y))) if self.game.state.desk_top is not None else 256
        key=(r,clip,self.devicePixelRatioF())
        if key!=getattr(self,'_mask_key',None):
            mask=QRegion(QRect(128-r,128-r,r*2,r*2),QRegion.Ellipse)
            if clip<256:mask=mask.intersected(QRegion(0,0,256,clip))
            self.setMask(mask);self._mask_key=key
        show=self.game.visible()
        if show and not self.isVisible(): self.visual.show();self.show()
        if not show:
            self.cancel_interaction();self.hide();self.visual.hide()
        self.visual.update()

    def paintEvent(self,event):
        # Alpha1 é invisível ao usuário, mas fornece entrada na região nativa.
        p=QPainter(self);p.fillRect(self.rect(),QColor(0,0,0,1));p.end()

    def enterEvent(self,event): self.game.hover=True
    def leaveEvent(self,event):
        if not self.press:self.game.hover=False

    def mousePressEvent(self,event):
        if event.button()!=Qt.LeftButton:return
        pos=event.globalPosition();now=time.monotonic()
        self.press=(pos,now);self.offset=(pos.x()-self.body.x,pos.y()-self.body.y)
        self.game.state.pressing=True
        self.game.interact({'type':'hold-start'})

    def mouseMoveEvent(self,event):
        pos=event.globalPosition();now=time.monotonic()
        if self.press is None:
            self.rubs.append((now,pos.x()))
            while self.rubs and now-self.rubs[0][0]>.9:self.rubs.popleft()
            directions=[math.copysign(1,b[1]-a[1]) for a,b in zip(self.rubs, list(self.rubs)[1:]) if abs(b[1]-a[1])>2]
            if sum(a!=b for a,b in zip(directions,directions[1:]))>=3:
                self.game.interact({'type':'caress'});self.rubs.clear()
            return
        if not self.dragging and math.hypot(pos.x()-self.press[0].x(),pos.y()-self.press[0].y())<4:return
        if not self.dragging:
            self.dragging=True
            self.game.interact(dict(type='drag-start',x=self.body.x,y=self.body.y))
            self.body.grounded=False;self.body.platform=None
        self.body.x,self.body.y=pos.x()-self.offset[0],pos.y()-self.offset[1]
        self.game.fit(self.body)
        self.sync()

    def mouseReleaseEvent(self,event):
        if event.button()!=Qt.LeftButton or self.press is None:return
        if self.dragging:
            self.game.interact(dict(type='drag-end',x=self.body.x,y=self.body.y))
        self.game.interact({'type':'hold-end'})
        self.press=None;self.dragging=False;self.game.state.pressing=False
        self.game.hover=self.mask().contains(self.mapFromGlobal(event.globalPosition().toPoint()))

    def contextMenuEvent(self,event):self.menu_requested.emit(event.globalPos())
    def wheelEvent(self,event):self.game.interact(dict(type='spin',value=event.angleDelta().y()/120*100))
    def cancel_interaction(self):
        if self.press is not None:self.game.interact({'type':'hold-end','cancelled':True})
        if self.dragging:
            self.body.held=False;self.body.vx=self.body.vy=0;self.body.grounded=False
        self.press=None;self.dragging=False;self.game.state.pressing=False;self.game.senses.set_dragging(False)
    def event(self,event):
        if event.type()==QEvent.UngrabMouse and (getattr(self,'press',None) is not None or getattr(self,'dragging',False)):self.cancel_interaction()
        return super().event(event)
    def closeEvent(self,event):self.visual.close();super().closeEvent(event)
