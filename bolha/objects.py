# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Desenhos GPL do Pestinha, mille-okws e contribuidores.

Notebook e bolinha adaptados de world/notebook.py e body/bolinha.py
do Pestinha no commit ca03a48136d2f97b9b58bbc7ae4e307bb408048d.
O notebook foi redesenhado para a Bolha. O amendoim é um desenho próprio.
"""
import math
from PySide6.QtCore import QPointF,QRectF,Qt
from PySide6.QtGui import QColor,QLinearGradient,QRadialGradient,QPen,QPainterPath,QPainterPathStroker,QTransform
from pestinha.scene import NOTEBOOK_W,NOTEBOOK_H
from .desk import typing_frame
BALL_RADIUS=18


def notebook_transform(rect):
    scale=min(rect.width()/NOTEBOOK_W,rect.height()/NOTEBOOK_H)
    x=rect.x()+(rect.width()-NOTEBOOK_W*scale)/2
    y=rect.y()+(rect.height()-NOTEBOOK_H*scale)/2
    return QTransform().translate(x,y).scale(scale,scale)


def _notebook_base():
    path=QPainterPath(QPointF(17,49))
    path.lineTo(93,49);path.lineTo(108,61)
    path.quadTo(109,66,104,66);path.lineTo(6,66)
    path.quadTo(1,66,2,61);path.closeSubpath()
    return path


def notebook_shape(rect,working=False):
    path=QPainterPath();path.setFillRule(Qt.WindingFill)
    half_pen=1.25 if working else .6
    path.addRoundedRect(QRectF(16,10,78,43).adjusted(-half_pen,-half_pen,half_pen,half_pen),6+half_pen,6+half_pen)
    base=_notebook_base()
    edge=QPainterPathStroker();edge.setWidth(.8)
    path.addPath(base.united(edge.createStroke(base)))
    return notebook_transform(rect).map(path)


def paint_notebook(p,rect,working=False,phase=0.):
    """Notebook de brinquedo, com tampa baixa e teclado em perspectiva."""
    phase=phase if math.isfinite(phase) else 0.
    key,tap,progress=typing_frame(phase) if working else (-1,0.,0)
    p.save();p.setTransform(notebook_transform(rect),True)
    tampa=QRectF(16,10,78,43)
    metal=QLinearGradient(tampa.topLeft(),tampa.bottomRight())
    metal.setColorAt(0.,QColor('#817293'));metal.setColorAt(1.,QColor('#353043'))
    p.setPen(QPen(QColor('#c6a8ee') if working else QColor('#91829e'),2.5 if working else 1.2))
    p.setBrush(metal);p.drawRoundedRect(tampa,6,6)
    screen=QRectF(21,16,68,29)
    p.setPen(QPen(QColor('#171522'),1));p.setBrush(QColor('#1e1d2e'))
    p.drawRoundedRect(screen,3,3)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor('#37304b'));p.drawRoundedRect(QRectF(22,17,66,5),2,2)
    for x,color in ((26,'#d49cb9'),(30,'#ffd364'),(34,'#90d9c9')):
        p.setBrush(QColor(color));p.drawEllipse(QPointF(x,19.5),.8,.8)
    for row,(indent,length,color) in enumerate(((0,24,'#cbb6f2'),(5,29,'#91c8c7'),(5,19,'#cbb6f2'))):
        p.setBrush(QColor(color));p.drawRoundedRect(QRectF(28+indent,26+row*4,length,1.6),.6,.6)
    length=7+progress*3.5
    p.setBrush(QColor(255,211,100,round(125+115*tap) if working else 85))
    p.drawRoundedRect(QRectF(33,39,length,1.7),.7,.7)
    if working and (key>=0 or int(phase*2)%2==0):
        p.fillRect(QRectF(34+length,37.8,1,4.3),QColor('#fff0bb'))
    p.setBrush(QColor('#181622'));p.drawEllipse(QPointF(55,13),.9,.9)
    # A tecla iluminada acompanha o toque; o resto do notebook fica estável.
    base=QLinearGradient(0,49,0,66)
    base.setColorAt(0.,QColor('#68617f'));base.setColorAt(.76,QColor('#9389a9'))
    base.setColorAt(1.,QColor('#49435b'))
    p.setPen(QPen(QColor('#4f455f'),.8));p.setBrush(base);p.drawPath(_notebook_base())
    p.setPen(QPen(QColor('#2a2435'),.5))
    for row in range(2):
        for col in range(8):
            pressed=tap if row==key%2 and col==key else 0.
            p.setBrush(QColor(round(74+178*pressed),round(65+138*pressed),round(90+20*pressed)))
            p.drawRoundedRect(QRectF(24-row*3+col*(8.2+row*.8),51+row*4+.3*pressed,6.6+row*.4,2.6),.7,.7)
    p.setBrush(QColor('#786e8a'));p.drawRoundedRect(QRectF(44,60,22,4),1,1)
    p.setPen(Qt.NoPen);p.setBrush(QColor('#4b3e5e'))
    p.drawEllipse(QPointF(20,62),4.5,2)
    p.setBrush(QColor('#ffd364'))
    for x in (18.6,21.4):p.drawEllipse(QPointF(x,61.8),.65,.65)
    p.setBrush(QColor('#ffd364') if working else QColor('#625776'))
    p.drawEllipse(QPointF(94,62),.85,.85)
    p.restore()


def paint_ball(p,cx,cy,radius=BALL_RADIUS,angle=0.,paper=False):
    """Gradiente, faixa e vincos originais; ``angle`` continua em radianos."""
    p.save();p.translate(cx,cy);p.scale(radius/BALL_RADIUS,radius/BALL_RADIUS)
    c=QPointF(0,0);RADIUS=BALL_RADIUS
    if paper:
        p.setPen(QPen(QColor('#6b6657'),1.2));p.setBrush(QColor('#f1ecd9'));p.drawEllipse(c,RADIUS,RADIUS)
        p.setPen(QPen(QColor('#9c967f'),1))
        for k in range(4):
            a=angle+k*1.2
            p.drawLine(c+QPointF(math.cos(a)*3,math.sin(a)*3),c+QPointF(math.cos(a+.9)*RADIUS*.8,math.sin(a+.9)*RADIUS*.8))
    else:
        grad=QRadialGradient(c.x()-5,c.y()-6,RADIUS*1.4)
        grad.setColorAt(0.,QColor('#f4fff6'));grad.setColorAt(.5,QColor('#63e56f'));grad.setColorAt(1.,QColor('#1f7a36'))
        p.setPen(QPen(QColor('#14401f'),1.5));p.setBrush(grad);p.drawEllipse(c,RADIUS,RADIUS)
        p.save();p.translate(c);p.rotate(math.degrees(angle));p.setPen(QPen(QColor('#14401f'),2))
        p.drawLine(QPointF(-RADIUS*.8,0),QPointF(RADIUS*.8,0));p.restore()
    p.restore()


def peanut_shape(cx,cy,radius=BALL_RADIUS,angle=0.):
    """Casca de duas metades dentro do mesmo espaço físico do brinquedo original."""
    shape=QPainterPath(QPointF(-16,0))
    shape.cubicTo(-18,-12,-11,-16,-5,-11)
    shape.quadTo(0,-7,5,-11)
    shape.cubicTo(11,-16,18,-12,16,0)
    shape.cubicTo(18,12,11,16,5,11)
    shape.quadTo(0,7,-5,11)
    shape.cubicTo(-11,16,-18,12,-16,0)
    shape.closeSubpath()
    transform=QTransform().translate(cx,cy).rotate(math.degrees(angle)).scale(radius/17,radius/17)
    return transform.map(shape)


def paint_peanut(p,cx,cy,radius=BALL_RADIUS,angle=0.):
    """Amendoim vetorial próprio, sem imagem externa ou nova física."""
    p.save();p.translate(cx,cy);p.rotate(math.degrees(angle));p.scale(radius/17,radius/17)
    shape=peanut_shape(0,0,17)
    gradient=QLinearGradient(-9,-13,8,13)
    gradient.setColorAt(0,QColor('#f2d9a2'));gradient.setColorAt(.5,QColor('#d6aa65'));gradient.setColorAt(1,QColor('#b57b3e'))
    p.setPen(QPen(QColor('#7d512a'),1.3));p.setBrush(gradient);p.drawPath(shape)
    p.setClipPath(shape);p.setPen(QPen(QColor('#a57742'),.65))
    for offset in range(-30,31,6):
        p.drawLine(QPointF(offset-18,-20),QPointF(offset+18,20))
        p.drawLine(QPointF(offset+18,-20),QPointF(offset-18,20))
    seam=QPainterPath(QPointF(-15,0));seam.cubicTo(-8,-1,8,1,15,0)
    p.setPen(QPen(QColor('#f8dfa8'),.9));p.drawPath(seam);p.restore()
