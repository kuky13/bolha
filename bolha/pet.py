# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Janelas e gestos derivados de PetWindow do Pestinha (GPL-3.0-or-later).

Uma camada visual sem entrada preserva o halo. A janela de entrada tem
máscara circular nativa: a região fora do corpo recebe cliques no desktop.
"""
import math
import time
from collections import deque
from PySide6.QtCore import Qt,QRect,QRectF,QPointF,QEvent,Signal
from PySide6.QtGui import QPainter,QColor,QRegion
from PySide6.QtWidgets import QWidget
from .character import draw_character,draw_sleep_marks,draw_reaction_marks
from .motion import ExpressionMotion,FLOOR_POSES
from .grab import MouseGrab

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
        pose=self.pet.motion.pose
        radius=game.body.half_w
        scale=radius/49*pose.get('visual_scale',1.)
        angle=game.body.angle+pose['angle_offset']
        squash=pose['squash']
        cx,cy=self.width()/2,self.height()/2
        if 'corner_peek' in pose:
            inward,depth,emerge=pose['corner_peek']
            left,_,right,_=game.bounds()
            edge=left if inward>0 else right
            cx+=(edge+inward*radius*depth-game.body.x)*(1.-emerge)
            # O recorte também esconde a Bolha quando há um monitor vizinho.
            p.setClipRect(QRectF(left-self.x(),0.,right-left,self.height()),Qt.IntersectClip)
        floor_squash,shift=self.pet.floor_pose()
        p.save()
        p.translate(cx,cy+shift)
        p.scale(1.+floor_squash,1.-floor_squash)
        if self.pet.motion.mode in FLOOR_POSES:
            squash=0.
        # A transformação comum gira corpo, olhos, orelhas e marcas no mesmo centro.
        if pose['body_opacity']>0.:
            p.save()
            p.setOpacity(p.opacity()*pose['body_opacity'])
            draw_character(p,0.,0.,scale=scale,
                           angle=angle,emotion=pose['emotion'],
                           blink=pose['blink'],gaze=self.pet.visual_gaze,
                           ear_gaze=self.pet.visual_ear_gaze,
                           blink_left=pose['blink_left'],blink_right=pose['blink_right'],
                           ear_tilt=pose['ear_tilt'],ear_raise=pose['ear_raise'],
                           eye_open=pose['eye_open'],squash=squash,
                           body_opacity=game.prefs.get('opacity',1),
                           anger=pose.get('anger',0.),
                           mouth_enabled=pose.get('mouth_enabled',True),
                           mouth_open=pose.get('mouth_open'), mouth_curve=pose.get('mouth_curve'),
                           mouth_chew=pose.get('mouth_chew',0.), tongue=pose.get('tongue',0.),
                           mouth_width=pose.get('mouth_width',1.), mouth_skew=pose.get('mouth_skew',0.),
                           cursor_inside=pose.get('cursor_inside',False),
                           cursor_spit=pose.get('cursor_spit',0.))
            p.restore()
        if pose['zzz_strength']>0:
            draw_sleep_marks(p,0.,0.,scale,
                             pose['zzz_phase'],pose['zzz_strength'],angle=angle,squash=squash)
        if pose['effect'] and pose['effect_strength']>0 and not (
                pose['effect']=='rebatida' and 'impact_point' in pose):
            if pose['effect']=='pop':
                scale=radius/49
                squash=0.
            draw_reaction_marks(p,0.,0.,scale,
                                pose['effect_phase'],pose['effect'],pose['effect_strength'],
                                angle=angle,squash=squash,effect_angle=pose.get('effect_angle',0.))
        p.restore()
        if 'impact_point' in pose:
            x, y = pose['impact_point']
            draw_reaction_marks(p, x-self.x(), y-self.y(), radius/49,
                                pose['impact_phase'], 'rebatida', pose['impact_strength'],
                                angle=pose['impact_angle'], at_contact=True)
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
        self.visual_gaze=game.state.gaze
        self.visual_ear_gaze=game.state.gaze
        self.gaze_tick=time.monotonic()
        self.press=None;self.offset=(0.,0.);self.dragging=False
        self.mouse_grab=MouseGrab(self);self.drag_position=None
        self.rubs=deque()
        self.motion=ExpressionMotion(time.monotonic())
        self._saved_prank_cursor=None
        self.sync()

    def floor_pose(self):
        """Mantém a base do desenho e a máscara no chão durante a deformação."""
        pose=self.motion.pose
        radius=self.body.half_w
        if self.motion.mode in FLOOR_POSES:
            squash=pose['squash']
            clearance=max(0.,self.body.surface-self.body.y-radius)
            contact=max(0.,1.-clearance/24.)
            return squash,radius*squash*contact
        return 0.,0.

    def sync(self):
        now=time.monotonic()
        self.motion.update(self.game,now,self.press[1] if self.press else None)
        target=self.motion.pose['gaze'] or self.game.state.gaze
        elapsed=max(0.,now-self.gaze_tick)
        running=self.motion.pose['effect']=='perseguindo'
        eye_ease=1. if running else 1-math.exp(-22*elapsed)
        ear_ease=1. if running else 1-math.exp(-12*elapsed)
        self.visual_gaze=tuple(current+(goal-current)*eye_ease for current,goal in zip(self.visual_gaze,target))
        self.visual_ear_gaze=tuple(current+(goal-current)*ear_ease for current,goal in zip(self.visual_ear_gaze,target))
        self.gaze_tick=now
        x,y=round(self.body.x-self.width()/2),round(self.body.y-self.height()/2)
        self.move(x,y)
        self.visual.move(round(self.body.x-self.visual.width()/2),round(self.body.y-self.visual.height()/2))
        radius=self.body.half_w*self.motion.pose['visual_scale']
        squash,shift=self.floor_pose()
        rx,ry=round(radius*(1.+squash)),round(radius*(1.-squash))
        rise=round(shift)
        clip=max(0,min(256,int(self.game.state.desk_top-y))) if self.game.state.desk_top is not None else 256
        key=(rx,ry,rise,clip,self.devicePixelRatioF())
        if key!=getattr(self,'_mask_key',None):
            mask=QRegion(QRect(128-rx,128-ry+rise,rx*2,ry*2),QRegion.Ellipse)
            if clip<256:mask=mask.intersected(QRegion(0,0,256,clip))
            self.setMask(mask);self._mask_key=key
        visual_show=self.game.pet_visible(now)
        input_show=self.game.pet_interactive() and 'corner_peek' not in self.motion.pose
        if visual_show and not self.visual.isVisible():self.visual.show()
        if not visual_show:self.visual.hide()
        if input_show and not self.isVisible():self.show()
        if not input_show:
            if self.isVisible():self.cancel_interaction();self.hide()
        self._sync_prank_cursor(input_show)
        self.visual.update()

    def _restore_prank_cursor(self):
        if self._saved_prank_cursor is not None:
            self.setCursor(self._saved_prank_cursor)
            self._saved_prank_cursor=None

    def _sync_prank_cursor(self,input_show):
        prank=getattr(self.game,'cursor_prank',None)
        inside=self.mask().contains(self.mapFromGlobal(QPointF(*self.game.cursor).toPoint()))
        hidden=bool(prank and prank.hidden_cursor and input_show and inside)
        if hidden and self._saved_prank_cursor is None:
            self._saved_prank_cursor=self.cursor()
            self.setCursor(Qt.BlankCursor)
        elif not hidden:
            self._restore_prank_cursor()
            if prank and prank.hidden_cursor:
                prank.pointer_moved(self.game,time.monotonic())

    def _release_prank_cursor(self,moved_to=None):
        prank=getattr(self.game,'cursor_prank',None)
        if prank is None or not prank.hidden_cursor:return False
        if moved_to is not None and prank.anchor is not None:
            if math.dist((moved_to.x(),moved_to.y()),prank.anchor)<=1.:return False
        prank.pointer_moved(self.game,time.monotonic())
        self._restore_prank_cursor()
        self.sync()
        return True

    def paintEvent(self,event):
        # Alpha1 é invisível ao usuário, mas fornece entrada na região nativa.
        p=QPainter(self);p.fillRect(self.rect(),QColor(0,0,0,1));p.end()

    def enterEvent(self,event): self.game.hover=True
    def leaveEvent(self,event):
        if not self.press:self.game.hover=False

    def mousePressEvent(self,event):
        if self._release_prank_cursor():
            event.accept();return
        if event.button()!=Qt.LeftButton or self.press is not None or not self.game.visible():return
        if self.game.pingpong is not None:return
        pos=event.globalPosition();now=time.monotonic()
        self.press=(pos,now);self.offset=(pos.x()-self.body.x,pos.y()-self.body.y)
        self.drag_position=QPointF(pos)
        self.game.state.pressing=True
        self.game.interact({'type':'hold-start'})
        try:self.mouse_grab.begin(pos)
        except (OSError,AttributeError,RuntimeError):self.cancel_interaction()

    def mouseMoveEvent(self,event):
        if self._release_prank_cursor(event.globalPosition()):return
        if self.game.pingpong is not None:return
        pos=event.globalPosition();now=time.monotonic()
        if self.press is None:
            self.rubs.append((now,pos.x()))
            while self.rubs and now-self.rubs[0][0]>.9:self.rubs.popleft()
            directions=[math.copysign(1,b[1]-a[1]) for a,b in zip(self.rubs, list(self.rubs)[1:]) if abs(b[1]-a[1])>2]
            if sum(a!=b for a,b in zip(directions,directions[1:]))>=3:
                self.game.interact({'type':'caress'});self.rubs.clear()
            return
        if self._drag_to(pos):self.sync()

    def _drag_to(self,pos):
        self.mouse_grab.track(pos)
        if pos==self.drag_position:return False
        kind='drag' if self.dragging else 'drag-start'
        self.dragging=True;self.drag_position=QPointF(pos)
        self.game.interact(dict(type=kind,x=pos.x()-self.offset[0],y=pos.y()-self.offset[1]))
        return True

    def mouseReleaseEvent(self,event):
        if event.button()!=Qt.LeftButton or self.press is None:return
        try:sample=self.mouse_grab.sample()
        except (OSError,AttributeError,RuntimeError,TypeError,ValueError):self.cancel_interaction();return
        pos,down=sample if sample is not None else (event.globalPosition(),False)
        if down:
            if self._drag_to(pos):self.sync()
            return
        self._release_at(pos)

    def _release_at(self,pos):
        moved=self.dragging or pos!=self.drag_position
        vx,vy=self.mouse_grab.velocity(pos)
        self.press=None;self.dragging=False;self.drag_position=None
        self.mouse_grab.stop()
        if moved:self.game.interact(dict(type='drag-end',x=pos.x()-self.offset[0],y=pos.y()-self.offset[1],vx=vx,vy=vy))
        self.game.interact({'type':'hold-end'})
        self.game.state.pressing=False
        self.game.hover=self.mask().contains(self.mapFromGlobal(pos.toPoint()))

    def poll_interaction(self):
        if self.press is None:return
        if not self.game.visible() or self.game.panel or not self.isVisible():self.cancel_interaction();return
        try:sample=self.mouse_grab.sample()
        except (OSError,AttributeError,RuntimeError,TypeError,ValueError):self.cancel_interaction();return
        if sample is None:return
        pos,down=sample
        if down:self._drag_to(pos)
        else:self._release_at(pos)

    def contextMenuEvent(self,event):self.cancel_interaction();self.menu_requested.emit(event.globalPos())
    def wheelEvent(self,event):
        if not self._release_prank_cursor():
            self.game.interact(dict(type='spin',value=event.angleDelta().y()/120*100))
    def cancel_interaction(self):
        self._restore_prank_cursor()
        prank=getattr(self.game,'cursor_prank',None)
        if prank is not None and prank.active:prank.cancel(self.game,time.monotonic())
        active=self.press is not None
        self.press=None;self.dragging=False;self.drag_position=None
        self.mouse_grab.stop()
        if active:self.game.interact({'type':'hold-end','cancelled':True})
        self.game.hover=False
    def event(self,event):
        if event.type()==QEvent.UngrabMouse and getattr(self,'press',None) is not None:
            if self.mouse_grab.pointer is None:self.cancel_interaction()
            else:self.poll_interaction()
        return super().event(event)
    def hideEvent(self,event):
        self.cancel_interaction();super().hideEvent(event)
    def closeEvent(self,event):
        self.cancel_interaction();self.visual.close();super().closeEvent(event)
