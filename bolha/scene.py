# SPDX-License-Identifier: GPL-3.0-only
"""Janelas Qt dos objetos; posições e física pertencem somente ao Game."""
import math
import time
from PySide6.QtCore import Qt,QRect,QRectF,QPointF,QEvent
from PySide6.QtGui import QPainter,QColor,QPen,QFont,QRegion,QPainterPath
from PySide6.QtWidgets import QWidget,QMenu
from .pet import FLAGS
from .character import draw_character
from .objects import paint_notebook,paint_ball,paint_peanut,peanut_shape,notebook_shape
from .grab import MouseGrab

class ObjectWindow(QWidget):
    def __init__(self, scene, item):
        super().__init__(None, FLAGS|(Qt.WindowTransparentForInput if item.kind=='fireworks' else Qt.WindowType(0)))
        self.scene,self.item=scene,item
        self.setWindowTitle('Bolha · '+item.kind)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.offset=None;self.press_position=None;self.dragged=False
        self.mouse_grab=MouseGrab(self);self.drag_position=None
        self.resize(round(item.width()),round(item.height()))
        self._sync_mask()
    def _sync_mask(self):
        item=self.item
        if item.kind=='fireworks':return
        peanut=item.kind=='ball' and getattr(item,'appearance','ball')=='peanut'
        key=(self.width(),self.height(),self.devicePixelRatioF(),item.kind,item.working,
             getattr(item,'appearance',None),item.roll_angle if peanut else None)
        if key==getattr(self,'_mask_key',None):return
        if peanut:
            path=peanut_shape(self.width()/2,self.height()/2,item.body.half_w,item.roll_angle)
            mask=QRegion(path.toFillPolygon().toPolygon())
        elif item.kind in ('ball','paper'):
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
        if not visible:self.cancel_interaction()
        self.setVisible(visible)
        key=tuple(data[field] for field in ('kind','text','image','angle','working','x','y'))+(
            getattr(item,'appearance',None),
            getattr(item,'emotion',None),getattr(item,'title',None),getattr(item,'subtitle',None),
            self.width(),self.height(),self.devicePixelRatioF(),visible)
        if key!=getattr(self,'_paint_key',None) or (visible and item.kind=='fireworks'):
            self._paint_key=key;self.update()
    def enterEvent(self,event):
        # Apresentar o brinquedo ao ponteiro não congela a vontade neural de brincar.
        if self.item.kind!='ball':self.scene.game.hover=True
    def leaveEvent(self,event):
        if self.offset is None:self.scene.game.hover=False
    def mousePressEvent(self,event):
        if event.button()!=Qt.LeftButton or self.offset is not None or not self.scene.game.visible() or not self.item.isVisible():return
        p=event.globalPosition();self.offset=(p.x()-self.item._cx,p.y()-self.item._cy)
        self.press_position=(p.x(),p.y());self.dragged=False;self.drag_position=QPointF(p)
        self.scene.game.interact(dict(type='drag-start',id=self.item.id,x=self.item._cx,y=self.item._cy))
        try:self.mouse_grab.begin(p)
        except (OSError,AttributeError,RuntimeError):self.cancel_interaction()
    def mouseMoveEvent(self,event):
        if self.offset is None:return
        if self._drag_to(event.globalPosition()):self.sync()
    def _drag_to(self,p):
        self.mouse_grab.track(p)
        if p==self.drag_position:return False
        self.drag_position=QPointF(p)
        if math.dist(self.press_position,(p.x(),p.y()))>=4:self.dragged=True
        self.scene.game.interact(dict(type='drag',id=self.item.id,x=p.x()-self.offset[0],y=p.y()-self.offset[1]))
        return True
    def mouseReleaseEvent(self,event):
        if event.button()!=Qt.LeftButton or self.offset is None:return
        try:sample=self.mouse_grab.sample()
        except (OSError,AttributeError,RuntimeError,TypeError,ValueError):self.cancel_interaction();return
        p,down=sample if sample is not None else (event.globalPosition(),False)
        if down:
            if self._drag_to(p):self.sync()
            return
        self._release_at(p)
    def _release_at(self,p):
        click=not self.dragged and math.dist(self.press_position,(p.x(),p.y()))<4
        x,y=p.x()-self.offset[0],p.y()-self.offset[1]
        vx,vy=self.mouse_grab.velocity(p) if self.item.kind=='ball' else (0.,0.)
        self.offset=None;self.press_position=None;self.drag_position=None;self.dragged=False
        self.mouse_grab.stop()
        self.scene.game.interact(dict(type='drag-end',id=self.item.id,x=x,y=y,vx=vx,vy=vy))
        if click:
            self.scene.game.interact(dict(type='dismiss',id=self.item.id))
        self.scene.game.hover=self.item.kind!='ball' and self.mask().contains(self.mapFromGlobal(p.toPoint()))
    def poll_interaction(self):
        if self.offset is None:return
        if not self.scene.game.visible() or self.scene.game.panel or not self.item.isVisible() or not self.isVisible():self.cancel_interaction();return
        try:sample=self.mouse_grab.sample()
        except (OSError,AttributeError,RuntimeError,TypeError,ValueError):self.cancel_interaction();return
        if sample is None:return
        p,down=sample
        if down:self._drag_to(p)
        else:self._release_at(p)
    def cancel_interaction(self):
        if self.offset is None:return
        self.offset=None;self.press_position=None;self.dragged=False;self.drag_position=None
        self.mouse_grab.stop()
        self.scene.game.interact(dict(type='drag-end',id=self.item.id,x=self.item._cx,y=self.item._cy,cancelled=True))
        self.scene.game.hover=False
    def event(self,event):
        if event.type()==QEvent.UngrabMouse and getattr(self,'offset',None) is not None:
            if self.mouse_grab.pointer is None:self.cancel_interaction()
            else:self.poll_interaction()
        return super().event(event)
    def hideEvent(self,event):
        self.cancel_interaction();super().hideEvent(event)
    def closeEvent(self,event):
        self.cancel_interaction();super().closeEvent(event)
    def contextMenuEvent(self,event):
        self.cancel_interaction()
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
            if kind=='ball' and self.item.appearance=='peanut':
                paint_peanut(p,w/2,h/2,self.item.body.half_w,self.item.roll_angle)
            else:
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
    def poll_interactions(self):
        for window in list(self.windows.values()):window.poll_interaction()
    def cancel_interactions(self):
        for window in list(self.windows.values()):window.cancel_interaction()
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
