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


_NOTEBOOK_LID=QRectF(21,7,90,65)
_NOTEBOOK_HINGE=QRectF(12,68,108,10)


def _notebook_base():
    path=QPainterPath(QPointF(18,72))
    path.lineTo(114,72);path.quadTo(119,72,121,76)
    path.lineTo(130,85);path.quadTo(131,91,125,91);path.lineTo(7,91)
    path.quadTo(1,91,2,85);path.lineTo(11,76);path.quadTo(14,72,18,72)
    path.closeSubpath()
    return path


def notebook_shape(rect):
    path=QPainterPath();path.setFillRule(Qt.WindingFill)
    path.addRoundedRect(_NOTEBOOK_LID.adjusted(-.55,-.55,.55,.55),9.55,9.55)
    path.addRoundedRect(_NOTEBOOK_HINGE,4,4)
    base=_notebook_base()
    edge=QPainterPathStroker();edge.setWidth(1.)
    path.addPath(base.united(edge.createStroke(base)))
    return notebook_transform(rect).map(path)


def paint_notebook(p,rect,working=False,phase=0.):
    """Mini terminal grafite, com cursor e teclas ligados ao ritmo da Bolha."""
    phase=phase if math.isfinite(phase) else 0.
    key,tap,progress=typing_frame(phase) if working else (-1,0.,0)
    p.save();p.setTransform(notebook_transform(rect),True)
    shell=QLinearGradient(0,7,0,72)
    shell.setColorAt(0,QColor('#493e60'));shell.setColorAt(1,QColor('#242031'))
    p.setPen(QPen(QColor('#a494bd'),1.1));p.setBrush(shell)
    p.drawRoundedRect(_NOTEBOOK_LID,9,9)
    glass=QLinearGradient(0,14,0,63)
    glass.setColorAt(0,QColor('#242034'));glass.setColorAt(1,QColor('#0b0e15'))
    p.setPen(QPen(QColor('#51445e'),1));p.setBrush(glass)
    p.drawRoundedRect(QRectF(27,14,78,49),6,6)
    p.setPen(Qt.NoPen);p.setBrush(QColor('#131520'))
    p.drawRoundedRect(QRectF(34,21,64,33),4,4)
    for x,color in ((34,'#db99ad'),(39,'#ffd16e'),(44,'#89d3bf')):
        p.setBrush(QColor(color));p.drawEllipse(QPointF(x,19),1.2,1.2)
    p.setPen(QPen(QColor('#ffd16e'),2,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin));p.setBrush(Qt.NoBrush)
    prompt=QPainterPath(QPointF(43,32));prompt.lineTo(49,37);prompt.lineTo(43,42)
    p.drawPath(prompt)
    p.setPen(Qt.NoPen);p.setBrush(QColor('#b98b64'))
    for index in range(progress):
        p.drawEllipse(QPointF(55+3.5*index,37),.8,.8)
    if not working or key>=0 or int(phase*2)%2==0:
        p.setPen(QPen(QColor('#ffd16e'),2,Qt.SolidLine,Qt.RoundCap))
        x=54+3.5*progress
        p.drawLine(QPointF(x,43),QPointF(x+9,43))
    p.setPen(Qt.NoPen);p.setBrush(QColor('#55425d'))
    for x in (84,90):p.drawEllipse(QPointF(x,48),1,1)
    p.setBrush(QColor('#24202e'));p.drawRoundedRect(_NOTEBOOK_HINGE,4,4)
    base=QLinearGradient(0,72,0,91)
    base.setColorAt(0,QColor('#665a79'));base.setColorAt(1,QColor('#2a2638'))
    p.setPen(QPen(QColor('#9383ae'),1));p.setBrush(base);p.drawPath(_notebook_base())
    p.setPen(Qt.NoPen)
    for col in range(8):
        pressed=tap if col==key else 0.
        p.setBrush(QColor(round(50+205*pressed),round(43+164*pressed),round(64+57*pressed)))
        p.drawRoundedRect(QRectF(24+11*col,76+.35*pressed,7.5,3.4),1,1)
    p.setBrush(QColor('#81708b'));p.drawRoundedRect(QRectF(53,82.5,26,4),1,1)
    p.setBrush(QColor('#ffd16e') if working else QColor('#8a7161'))
    p.drawEllipse(QPointF(114,85),1.3,1.3)
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
