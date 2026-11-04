# SPDX-License-Identifier: GPL-3.0-only
"""Janelas Qt dos objetos; posições e física pertencem somente ao Game."""
import math
import time
from PySide6.QtCore import Qt,QRect,QRectF,QPointF
from PySide6.QtGui import QPainter,QColor,QPen,QFont,QRegion,QPainterPath,QPolygonF
from PySide6.QtWidgets import QWidget,QMenu
from .pet import FLAGS
from .character import draw_character

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
        if item.kind in ('ball','paper'):self.setMask(QRegion(self.rect(),QRegion.Ellipse))
        elif item.kind!='fireworks':
            path=QPainterPath()
            if item.kind=='notebook':
                w,h=self.width(),self.height();path.addRoundedRect(QRectF(10,1,w-20,h-16),8,8)
                path.addPolygon(QPolygonF([QPointF(12,h-20),QPointF(w-12,h-20),QPointF(w,h-2),QPointF(0,h-2)]))
            else:path.addRoundedRect(QRectF(self.rect()),8,8)
            self.setMask(QRegion(path.toFillPolygon().toPolygon()))
    def sync(self):
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
            p.setPen(QPen(QColor('#b89aff'),2));p.setBrush(QColor('#6958a8' if kind=='ball' else '#eee4d6'));p.drawEllipse(QRectF(2,2,w-4,h-4))
            p.setPen(QPen(QColor('#c9b9ff'),2));p.drawArc(QRectF(8,2,w-12,h-4),90*16,180*16)
        elif kind=='notebook':
            p.setPen(QPen(QColor('#6b657e'),4));p.setBrush(QColor('#26232f'));p.drawRoundedRect(QRectF(12,3,w-24,h-20),7,7)
            p.setPen(QColor('#ffcf60'));p.setFont(QFont('Segoe UI',18));p.drawText(QRectF(15,20,w-30,35),Qt.AlignCenter,'♡')
            p.setFont(QFont('Segoe UI',8));p.setPen(QColor('#b9acd9'));p.drawText(QRectF(15,63,w-30,20),Qt.AlignCenter,'meu cantinho' if not self.item.working else 'bolha trabalhando')
            p.setPen(Qt.NoPen);p.setBrush(QColor('#777184'));p.drawPolygon(QPolygonF([QPointF(12,h-18),QPointF(w-12,h-18),QPointF(w,h-4),QPointF(0,h-4)]))
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
