# SPDX-License-Identifier: GPL-3.0-only
"""Janelas Qt dos objetos; posições e física pertencem somente ao Game."""
import math
import time
from PySide6.QtCore import Qt,QRect,QRectF,QPointF
from PySide6.QtGui import QPainter,QColor,QPen,QFont,QRegion,QPainterPath
from PySide6.QtWidgets import QWidget,QMenu
from .pet import FLAGS
from .character import draw_character
from .objects import paint_notebook,paint_ball,notebook_shape

class ObjectWindow(QWidget):
    def __init__(self, scene, item):
        super().__init__(None, FLAGS|(Qt.WindowTransparentForInput if item.kind=='fireworks' else Qt.WindowType(0)))
        self.scene,self.item=scene,item
        self.setWindowTitle('Bolha · '+item.kind)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.offset=None;self.samples=[];self.press_position=None;self.dragged=False
        self.resize(round(item.width()),round(item.height()))
        self._sync_mask()
    def _sync_mask(self):
        item=self.item
        if item.kind=='fireworks':return
        key=(self.width(),self.height(),self.devicePixelRatioF(),item.kind,item.working)
        if key==getattr(self,'_mask_key',None):return
        if item.kind in ('ball','paper'):
            radius=item.body.half_w+1
            mask=QRegion(QRect(round(self.width()/2-radius),round(self.height()/2-radius),round(radius*2),round(radius*2)),QRegion.Ellipse)
        else:
            if item.kind=='notebook':path=notebook_shape(QRectF(self.rect()),item.working)
            else:
                path=QPainterPath();path.addRoundedRect(QRectF(self.rect()),8,8)
            mask=QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask);self._mask_key=key
    def sync(self):
        self._sync_mask()
        item=self.item;data=item.snapshot()
        self.move(round(data['x']-self.width()/2),round(data['y']-self.height()/2))
        visible=item.isVisible() and self.scene.game.visible()
        self.setVisible(visible)
        key=tuple(data[field] for field in ('kind','text','image','angle','working','x','y'))+(
            getattr(item,'emotion',None),getattr(item,'title',None),getattr(item,'subtitle',None),
            self.width(),self.height(),self.devicePixelRatioF(),visible)
        if key!=getattr(self,'_paint_key',None) or (visible and item.kind=='fireworks'):
            self._paint_key=key;self.update()
    def enterEvent(self,event):self.scene.game.hover=True
    def leaveEvent(self,event):
        if self.offset is None:self.scene.game.hover=False
    def mousePressEvent(self,event):
        if event.button()!=Qt.LeftButton:return
        p=event.globalPosition();self.offset=(p.x()-self.item._cx,p.y()-self.item._cy)
        self.press_position=(p.x(),p.y());self.dragged=False
        self.samples=[(time.monotonic(),p.x(),p.y())]
        self.scene.game.interact(dict(type='drag-start',id=self.item.id,x=self.item._cx,y=self.item._cy))
    def mouseMoveEvent(self,event):
        if self.offset is None:return
        p=event.globalPosition();now=time.monotonic()
        if math.dist(self.press_position,(p.x(),p.y()))>=4:self.dragged=True
        self.samples.append((now,p.x(),p.y()));self.samples=[s for s in self.samples if now-s[0]<.12]
        self.scene.game.interact(dict(type='drag',id=self.item.id,x=p.x()-self.offset[0],y=p.y()-self.offset[1]));self.sync()
    def mouseReleaseEvent(self,event):
        if self.offset is None:return
        p=event.globalPosition();a,b=self.samples[0],self.samples[-1];dt=max(.001,b[0]-a[0])
        vx,vy=((b[1]-a[1])/dt,(b[2]-a[2])/dt) if time.monotonic()-b[0]<.1 else (0,0)
        self.scene.game.interact(dict(type='drag-end',id=self.item.id,x=p.x()-self.offset[0],y=p.y()-self.offset[1],vx=vx,vy=vy))
        if not self.dragged and math.dist(self.press_position,(p.x(),p.y()))<4:
            self.scene.game.interact(dict(type='dismiss',id=self.item.id))
        self.offset=None;self.press_position=None
    def contextMenuEvent(self,event):
        menu=QMenu(self);action=menu.addAction('Guardar objeto')
        if menu.exec(event.globalPos())==action:
            if self.item.kind=='ball':self.scene.game.interact(dict(type='ball'))
            elif self.item.kind=='notebook':self.scene.game.interact(dict(type='notebook'))
            elif self.item.kind in ('meme','note','sign'):
                self.scene.game.interact(dict(type='dismiss',id=self.item.id))
            else:self.item.hide()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height();kind=self.item.kind
        if kind in ('ball','paper'):
            paint_ball(p,w/2,h/2,radius=self.item.body.half_w,
                       angle=self.item.roll_angle,paper=kind=='paper')
        elif kind=='notebook':
            paint_notebook(p,QRectF(self.rect()),self.item.working)
        elif kind=='fireworks':
            age=max(0,3.2-(self.item.until-time.monotonic()))
            for burst in range(4):
                phase=(age+burst*.51)%1.6;r=phase*55;alpha=round(220*(1-phase/1.6))
                cx=w*(.2+.2*burst);cy=h*(.3+.12*(burst%2))
                p.setPen(QPen(QColor(255,205,100,alpha),2))
                for ray in range(12):
                    a=ray*math.tau/12+burst;p.drawLine(QPointF(cx+math.cos(a)*r*.6,cy+math.sin(a)*r*.6),QPointF(cx+math.cos(a)*r,cy+math.sin(a)*r))
        elif kind=='meme':
            p.setPen(QPen(QColor('#75658e'),2));p.setBrush(QColor('#201d2d'));p.drawRoundedRect(QRectF(1,1,w-2,h-2),9,9)
            draw_character(p,w/2,h*.48,scale=min(w,h)/180,emotion=getattr(self.item,'emotion','observando'))
            p.setPen(QColor('#f0eaf6'));p.setFont(QFont('Segoe UI',9,QFont.Weight.DemiBold));p.drawText(QRectF(10,8,w-20,h*.18),Qt.AlignCenter|Qt.TextWordWrap,getattr(self.item,'title','Bolha'))
            p.setPen(QColor('#ffda76'));p.setFont(QFont('Segoe UI',9));p.drawText(QRectF(10,h*.78,w-20,h*.18),Qt.AlignCenter|Qt.TextWordWrap,getattr(self.item,'subtitle','um pouquinho de atenção'))
        else:
            corner=kind=='corner';p.setPen(QPen(QColor('#846c49'),2));p.setBrush(QColor('#e4cfa1' if corner else '#fff0be'));p.drawRoundedRect(QRectF(1,1,w-2,h-2),7,7)
            p.setPen(QColor('#493b30'));p.setFont(QFont('Segoe UI',10,QFont.Weight.DemiBold));p.drawText(QRectF(10,10,w-20,h-20),Qt.AlignCenter|Qt.TextWordWrap,self.item.text)
        p.end()

class NativeScene:
    def __init__(self,game):self.game=game;self.windows={}
    def sync(self):
        for ident,item in list(self.game.objects.items()):
            if item.closed:
                if ident in self.windows:self.windows.pop(ident).close()
                continue
            if ident not in self.windows:self.windows[ident]=ObjectWindow(self,item)
            self.windows[ident].sync()
        for ident in set(self.windows)-set(self.game.objects):self.windows.pop(ident).close()
    def close(self):
        for window in self.windows.values():window.close()
        self.windows.clear()
    def ids(self):return [int(w.winId()) for w in self.windows.values()]
