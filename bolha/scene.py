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
from pestinha.scene import minimum_object_dimensions, object_scale


def object_dimensions(item, avatar_size=136, object_scales=None, bounds=None):
    """Dimensões proporcionais comuns à física, colisão e janela nativa."""
    factor=object_scale(item,avatar_size,object_scales,bounds)
    minimum_w,minimum_h=minimum_object_dimensions(getattr(item,'kind',''))
    return max(minimum_w,item._base_w*factor),max(minimum_h,item._base_h*factor)

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
        self.reaction_remaining=0.;self._reaction_tick=time.monotonic();self._context_open=False
        self.resize(round(item.width()),round(item.height()))
        self._sync_mask()
    def _sync_mask(self):
        item=self.item
        if item.kind=='fireworks':return
        image=self.reaction_media.current_image() if item.kind=='meme' and self.reaction_media is not None else None
        peanut=item.kind=='ball' and getattr(item,'appearance','ball')=='peanut'
        key=(self.width(),self.height(),self.devicePixelRatioF(),item.kind,item.working,
             getattr(item,'appearance',None),item.roll_angle if peanut else None,
             image.width() if image is not None else None,image.height() if image is not None else None)
        if key==getattr(self,'_mask_key',None):return
        if peanut:
            path=peanut_shape(self.width()/2,self.height()/2,item.body.half_w,item.roll_angle)
            mask=QRegion(path.toFillPolygon().toPolygon())
        elif item.kind=='meme':
            rect=self._media_rect(image) if image is not None and not image.isNull() else QRectF()
            mask=QRegion(QRect(round(rect.x()),round(rect.y()),max(0,round(rect.width())),max(0,round(rect.height()))))
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
            self.reaction_remaining=15.
            self._reaction_tick=time.monotonic()
    def release_reaction_media(self):
        if getattr(self,'reaction_media',None) is not None:
            self.reaction_media.release()
            self.reaction_media=None
    def sync(self):
        item=self.item;data=item.snapshot()
        wanted=(max(20,round(item.width())),max(20,round(item.height())))
        if wanted!=(self.width(),self.height()):
            self.resize(*wanted)
            if self.reaction_media is not None:self.reaction_media.set_target_size(max(wanted))
        self._sync_mask()
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
        scale_kind=self.scene.scale_kind(self.item)
        smaller=larger=reset=None
        if self.scene.on_scale_change:
            scale_menu=menu.addMenu('Tamanho')
            smaller=scale_menu.addAction('Menor')
            larger=scale_menu.addAction('Maior')
            reset=scale_menu.addAction('Padrão')
        open_source=None
        if self.item.kind=='meme' and getattr(self.item,'source_url',None):
            open_source=menu.addAction('Abrir origem')
        info=None
        if self.item.kind=='meme' and self.reaction_media is not None:
            candidate=self.reaction_media.candidate
            provider={'reactiongifs':'ReactionGIFs','nekos.best':'Nekos.best'}.get(candidate.provider,candidate.provider)
            label=' · '.join(part for part in (provider,candidate.title) if part)
            if label:
                info=menu.addAction(label)
                if hasattr(info,'setEnabled'):info.setEnabled(False)
        self._context_open=True
        try:chosen=menu.exec(event.globalPos())
        finally:self._context_open=False
        if chosen==action:
            if self.item.kind=='ball':self.scene.game.interact(dict(type='ball'))
            elif self.item.kind=='notebook':self.scene.game.interact(dict(type='notebook'))
            elif self.item.kind in ('meme','note','sign'):
                self.scene.game.interact(dict(type='dismiss',id=self.item.id))
            else:self.item.hide()
        elif open_source is not None and chosen==open_source:
            self._open_reaction_source()
        elif chosen is not None and chosen in (smaller,larger,reset):
            current=float(self.scene.game.prefs.get('objectScales',{}).get(scale_kind,1.))
            factor=1. if chosen==reset else max(.6,min(1.8,current+(-.1 if chosen==smaller else .1)))
            if self.scene.on_scale_change:self.scene.on_scale_change(scale_kind,factor)
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
            scale=min(w/max(1,self.item._base_w),h/max(1,self.item._base_h))
            for burst in range(4):
                phase=(age+burst*.51)%1.6;r=phase*55*scale;alpha=round(220*(1-phase/1.6))
                cx=w*(.2+.2*burst);cy=h*(.3+.12*(burst%2))
                p.setPen(QPen(QColor(255,205,100,alpha),max(1.,2*scale)))
                for ray in range(12):
                    a=ray*math.tau/12+burst;p.drawLine(QPointF(cx+math.cos(a)*r*.6,cy+math.sin(a)*r*.6),QPointF(cx+math.cos(a)*r,cy+math.sin(a)*r))
        elif kind=='meme':
            img=self.reaction_media.current_image() if self.reaction_media is not None else None
            if img is not None and not img.isNull():
                p.drawImage(self._media_rect(img),img)
        else:
            scale=min(w/max(1,self.item._base_w),h/max(1,self.item._base_h))
            corner=kind=='corner';p.setPen(QPen(QColor('#846c49'),max(1.,2*scale)));p.setBrush(QColor('#e4cfa1' if corner else '#fff0be'));p.drawRoundedRect(QRectF(1,1,w-2,h-2),7*scale,7*scale)
            p.setPen(QColor('#493b30'));p.setFont(QFont('Segoe UI',max(9,round(10*scale)),QFont.Weight.DemiBold));pad=max(6,round(10*scale));p.drawText(QRectF(pad,pad,w-pad*2,h-pad*2),Qt.AlignCenter|Qt.TextWordWrap,self.item.text)
        p.end()

    def _media_rect(self,image):
        scale=min(self.width()/max(1,image.width()),self.height()/max(1,image.height()))
        width,height=image.width()*scale,image.height()*scale
        return QRectF((self.width()-width)/2,(self.height()-height)/2,width,height)

class NativeScene:
    def __init__(self,game,reaction_fetcher=None,on_scale_change=None):
        self.game=game;self.windows={}
        self.fetcher=reaction_fetcher or OnlineReactionFetcher()
        self.on_scale_change=on_scale_change
        self.reaction_status={}
        self._reaction_deadlines={}
    @staticmethod
    def scale_kind(item):
        kind=getattr(item,'kind','')
        return ('toy' if kind in ('ball','paper') else 'notebook' if kind=='notebook' else
                'reaction' if kind=='meme' else 'note' if kind=='note' else 'sign' if kind=='sign' else
                'corner' if kind=='corner' else 'effects' if kind=='fireworks' else 'sign')
    def get_reaction_status(self, ident):
        return self.reaction_status.get(str(ident), {'state':'idle','reason':''})
    def _status(self, ident, state, reason=''):
        ident=str(ident);self.reaction_status.pop(ident,None)
        self.reaction_status[ident]={'state':state,'reason':str(reason)[:180]}
        if len(self.reaction_status)>32:
            self.reaction_status.pop(next(iter(self.reaction_status)))
    def request_reaction(self, ident):
        """Dispara uma tentativa imediatamente em objeto meme já criado e visível."""
        ident=str(ident);item=self.game.objects.get(ident);window=self.windows.get(ident)
        if item is None or item.kind!='meme' or not item.isVisible() or not self.game.visible():
            self._status(ident,'canceled','objeto indisponível ou cena pausada');return False
        if not self.game.prefs.get('mischiefEnabled',True) or not self.game.prefs.get('onlineReactions',True):
            self._status(ident,'canceled','reações online desativadas');return False
        if window is None:
            window=ObjectWindow(self,item);self.windows[ident]=window
        window.reaction_requested=False
        return self._start_reaction(ident,item,window)
    def _start_reaction(self, ident, item, window):
        if not self.fetcher.submit(ident,getattr(item,'emotion','observando'),getattr(item,'reaction_kind','meme')):
            self._status(ident,'canceled','fila indisponível ou cheia')
            self._abort_meme(ident,item)
            return False
        window.reaction_requested=True;self._reaction_deadlines[str(ident)]=time.monotonic()+20
        self._status(ident,'loading','buscando GIF em memória');return True
    def poll_interactions(self):
        for window in list(self.windows.values()):window.poll_interaction()
    def cancel_interactions(self):
        for window in list(self.windows.values()):window.cancel_interaction()
    def _total_media_bytes(self):
        return sum(w.reaction_media.byte_size for w in self.windows.values() if w.reaction_media is not None)
    def _abort_meme(self,ident,item=None):
        self.fetcher.cancel(ident)
        self._reaction_deadlines.pop(str(ident),None)
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
                self._status(ident,'canceled','pedido cancelado: objeto oculto ou cena pausada')
                continue
            if payload is None or error is not None:
                message=str(error or 'sem resultados')
                reason='no-results' if 'candidato' in message.lower() or 'resultados' in message.lower() else 'network'
                self._status(ident,reason,message);self._reaction_deadlines.pop(str(ident),None)
                self._abort_meme(ident,item)
                continue
            if self._total_media_bytes()+len(payload.data)>MAX_TOTAL_MEDIA_BYTES:
                self._status(ident,'memory','limite de RAM para mídia atingido');self._reaction_deadlines.pop(str(ident),None)
                self._abort_meme(ident,item)
                continue
            try:
                media=InMemoryMedia(payload,target_size=max(window.width(),window.height()))
            except Exception as error:
                self._status(ident,'decode',str(error));self._reaction_deadlines.pop(str(ident),None)
                self._abort_meme(ident,item)
                continue
            window.set_reaction_media(media)
            self._status(ident,'ready','');self._reaction_deadlines.pop(str(ident),None)
    def sync(self):
        self._poll_reactions()
        now=time.monotonic()
        for ident,deadline in list(self._reaction_deadlines.items()):
            if now>=deadline:
                self.fetcher.cancel(ident);self._reaction_deadlines.pop(ident,None)
                self._status(ident,'network','tempo máximo da busca excedido')
                item=self.game.objects.get(ident)
                if item is not None:self._abort_meme(ident,item)
        online=self.game.prefs.get('onlineReactions',True) and self.game.prefs.get('mischiefEnabled',True)
        for ident,item in list(self.game.objects.items()):
            area=self.game.bounds((item._cx,item._cy))
            item.apply_scale(object_scale(item,self.game.prefs.get('avatarSize',136),self.game.prefs.get('objectScales'),area))
            body=getattr(item,'body',None)
            held=bool(item.carried or getattr(item,'dragging',False) or getattr(body,'held',False))
            if not held and body is not None:
                self.game.fit(body);item.place(body.x,body.y)
            elif not held:
                left,top,right,bottom=area;half_w,half_h=math.ceil(item.width()/2),math.ceil(item.height()/2)
                x=max(left+half_w,min(right-half_w,item._cx))
                y=max(top+half_h,min(bottom-half_h,item._cy))
                if (x,y)!=(item._cx,item._cy):item.place(x,y)
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
            if window.reaction_media is not None:
                tick=time.monotonic()
                paused=(not window.isVisible() or window.underMouse() or window._context_open
                        or item.carried or window.offset is not None)
                if not paused:window.reaction_remaining-=max(0.,tick-window._reaction_tick)
                window._reaction_tick=tick
                if window.reaction_remaining<=0:
                    self._status(ident,'expired','reação exibida por 15 segundos')
                    self._abort_meme(ident,item)
                    continue
            if item.kind=='meme' and window.reaction_media is None and not window.reaction_requested:
                if self.game.visible() and item.isVisible() and online:
                    if not self._start_reaction(ident,item,window):continue
                    self._poll_reactions()
                    if ident not in self.windows:
                        continue
            window.sync()
        for ident in set(self.windows)-set(self.game.objects):
            self.fetcher.cancel(ident)
            self.windows.pop(ident).close()
    def close(self):
        self.fetcher.stop()
        self._reaction_deadlines.clear()
        for window in self.windows.values():window.close()
        self.windows.clear()
    def ids(self):return [int(w.winId()) for w in self.windows.values()]
