# SPDX-License-Identifier: GPL-3.0-only
"""Janelas Qt dos objetos; posições e física pertencem somente ao Game."""
import math
import time
from PySide6.QtCore import Qt,QRect,QRectF,QPointF,QEvent,QUrl
from PySide6.QtGui import QPainter,QColor,QPen,QFont,QRegion,QPainterPath,QDesktopServices
from PySide6.QtWidgets import QWidget,QMenu
from .pet import FLAGS
from .objects import paint_notebook,paint_ball,paint_peanut,peanut_shape,notebook_shape
from .grab import MouseGrab
from .reactions import (
    InMemoryMedia, MAX_TOTAL_MEDIA_BYTES, NEKOS_HOSTS,
    OnlineReactionFetcher, REACTIONGIFS_HOSTS, validate_reaction_url,
)

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
        self.reaction_media=None;self.reaction_requested=False
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
    def set_reaction_media(self, media):
        self.release_reaction_media()
        self.reaction_media=media
        if media is not None:
            cand=media.candidate
            self.item.source_url=cand.source_url
            self.item.attribution=cand.attribution
            self.item.provider=cand.provider
            self.item.title=cand.title
            self.item.born=time.monotonic()
    def release_reaction_media(self):
        if getattr(self,'reaction_media',None) is not None:
            self.reaction_media.release()
            self.reaction_media=None
    def sync(self):
        self._sync_mask()
        item=self.item;data=item.snapshot()
        self.move(round(data['x']-self.width()/2),round(data['y']-self.height()/2))
        ready=(self.reaction_media is not None) if item.kind=='meme' else True
        visible=item.isVisible() and self.scene.game.visible() and ready
        if self.reaction_media is not None:
            self.reaction_media.set_paused(not visible)
        if not visible:self.cancel_interaction()
        self.setVisible(visible)
        frame_no=self.reaction_media.frame_number() if self.reaction_media is not None else -1
        key=tuple(data[field] for field in ('kind','text','image','angle','working','x','y'))+(
            getattr(item,'appearance',None),
            getattr(item,'emotion',None),getattr(item,'title',None),getattr(item,'attribution',None),
            frame_no,self.width(),self.height(),self.devicePixelRatioF(),visible)
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
        self.cancel_interaction()
        if self.reaction_media is not None:self.reaction_media.set_paused(True)
        super().hideEvent(event)
    def closeEvent(self,event):
        self.cancel_interaction()
        self.release_reaction_media()
        super().closeEvent(event)
    def _open_reaction_source(self):
        url=getattr(self.item,'source_url',None)
        if not url:return False
        try:
            safe=validate_reaction_url(url,REACTIONGIFS_HOSTS|NEKOS_HOSTS,upgrade_http=False)
        except ValueError:
            return False
        return bool(QDesktopServices.openUrl(QUrl(safe)))
    def contextMenuEvent(self,event):
        self.cancel_interaction()
        menu=QMenu(self);action=menu.addAction('Guardar objeto')
        open_source=None
        if self.item.kind=='meme' and getattr(self.item,'source_url',None):
            open_source=menu.addAction('Abrir origem')
        chosen=menu.exec(event.globalPos())
        if chosen==action:
            if self.item.kind=='ball':self.scene.game.interact(dict(type='ball'))
            elif self.item.kind=='notebook':self.scene.game.interact(dict(type='notebook'))
            elif self.item.kind in ('meme','note','sign'):
                self.scene.game.interact(dict(type='dismiss',id=self.item.id))
            else:self.item.hide()
        elif open_source is not None and chosen==open_source:
            self._open_reaction_source()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.setRenderHint(QPainter.SmoothPixmapTransform)
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
            img=self.reaction_media.current_image() if self.reaction_media is not None else None
            if img is not None and not img.isNull():
                p.setPen(QPen(QColor('#75658e'),2));p.setBrush(QColor('#181522'))
                p.drawRoundedRect(QRectF(1,1,w-2,h-2),9,9)
                footer_h=22
                pad=6
                avail_w=max(16,w-pad*2)
                avail_h=max(16,h-footer_h-pad*2)
                iw,ih=max(1,img.width()),max(1,img.height())
                scale=min(avail_w/iw,avail_h/ih)
                dw,dh=iw*scale,ih*scale
                dx=(w-dw)/2
                dy=pad+(avail_h-dh)/2
                clip=QPainterPath();clip.addRoundedRect(QRectF(pad,pad,avail_w,avail_h),6,6)
                p.save();p.setClipPath(clip)
                p.drawImage(QRectF(dx,dy,dw,dh),img)
                p.restore()
                label=getattr(self.item,'attribution','') or getattr(self.item,'provider','') or 'Reação online'
                p.setPen(QColor('#cfc6e6'))
                p.setFont(QFont('Segoe UI',8))
                p.drawText(QRectF(8,h-footer_h,w-16,footer_h-3),Qt.AlignCenter|Qt.TextSingleLine,label[:38])
        else:
            corner=kind=='corner';p.setPen(QPen(QColor('#846c49'),2));p.setBrush(QColor('#e4cfa1' if corner else '#fff0be'));p.drawRoundedRect(QRectF(1,1,w-2,h-2),7,7)
            p.setPen(QColor('#493b30'));p.setFont(QFont('Segoe UI',10,QFont.Weight.DemiBold));p.drawText(QRectF(10,10,w-20,h-20),Qt.AlignCenter|Qt.TextWordWrap,self.item.text)
        p.end()

class NativeScene:
    def __init__(self,game,reaction_fetcher=None):
        self.game=game;self.windows={}
        self.fetcher=reaction_fetcher or OnlineReactionFetcher()
    def poll_interactions(self):
        for window in list(self.windows.values()):window.poll_interaction()
    def cancel_interactions(self):
        for window in list(self.windows.values()):window.cancel_interaction()
    def _total_media_bytes(self):
        return sum(w.reaction_media.byte_size for w in self.windows.values() if w.reaction_media is not None)
    def _abort_meme(self,ident,item=None):
        self.fetcher.cancel(ident)
        window=self.windows.pop(ident,None)
        if window is not None:window.close()
        target=item or self.game.objects.get(ident)
        if target is not None:
            if hasattr(self.game,'mischief_ctl'):self.game.mischief_ctl.abort_thing(target)
            else:target.deleteLater()
    def _poll_reactions(self):
        online=self.game.prefs.get('onlineReactions',True) and self.game.prefs.get('mischiefEnabled',True)
        if not online:
            self.fetcher.clear()
            for ident,window in list(self.windows.items()):
                if window.item.kind=='meme':
                    self._abort_meme(ident,window.item)
            return
        for ident,payload,error in self.fetcher.poll():
            item=self.game.objects.get(ident)
            window=self.windows.get(ident)
            if item is None or item.closed or not item.isVisible() or window is None or not self.game.visible():
                continue
            if payload is None or error is not None:
                self._abort_meme(ident,item)
                continue
            if self._total_media_bytes()+len(payload.data)>MAX_TOTAL_MEDIA_BYTES:
                self._abort_meme(ident,item)
                continue
            try:
                media=InMemoryMedia(payload,target_size=max(window.width(),window.height()))
            except Exception:
                self._abort_meme(ident,item)
                continue
            window.set_reaction_media(media)
    def sync(self):
        self._poll_reactions()
        online=self.game.prefs.get('onlineReactions',True) and self.game.prefs.get('mischiefEnabled',True)
        for ident,item in list(self.game.objects.items()):
            if item.closed:
                self.fetcher.cancel(ident)
                if ident in self.windows:self.windows.pop(ident).close()
                continue
            if item.kind=='meme' and (not online or not item.isVisible() or not self.game.visible()):
                if not online:
                    self._abort_meme(ident,item)
                    continue
                self.fetcher.cancel(ident)
                if ident in self.windows and self.windows[ident].reaction_media is None:
                    self._abort_meme(ident,item)
                    continue
            if ident not in self.windows:self.windows[ident]=ObjectWindow(self,item)
            window=self.windows[ident]
            if item.kind=='meme' and window.reaction_media is None and not window.reaction_requested:
                if self.game.visible() and item.isVisible() and online:
                    window.reaction_requested=True
                    if not self.fetcher.submit(ident,getattr(item,'emotion','observando'),getattr(item,'reaction_kind','meme')):
                        self._abort_meme(ident,item)
                        continue
                    self._poll_reactions()
                    if ident not in self.windows:
                        continue
            window.sync()
        for ident in set(self.windows)-set(self.game.objects):
            self.fetcher.cancel(ident)
            self.windows.pop(ident).close()
    def close(self):
        self.fetcher.stop()
        for window in self.windows.values():window.close()
        self.windows.clear()
    def ids(self):return [int(w.winId()) for w in self.windows.values()]
