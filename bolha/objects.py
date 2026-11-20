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
    """Notebook lavanda, com escrita e teclas no mesmo ritmo da Bolha."""
    phase=phase if math.isfinite(phase) else 0.
    key,tap,progress=typing_frame(phase) if working else (-1,0.,0)
    p.save();p.setTransform(notebook_transform(rect),True)
    shell=QLinearGradient(0,7,0,72)
    shell.setColorAt(0,QColor('#baaacc'));shell.setColorAt(1,QColor('#746780'))
    p.setPen(QPen(QColor('#d2c1e2'),1.1));p.setBrush(shell)
    p.drawRoundedRect(_NOTEBOOK_LID,9,9)
    glass=QLinearGradient(26,13,100,64)
    glass.setColorAt(0,QColor('#34374f'));glass.setColorAt(1,QColor('#182133'))
    p.setPen(QPen(QColor('#51465f'),.9));p.setBrush(glass)
    p.drawRoundedRect(QRectF(25.5,13,81,51),4,4)
    p.setPen(Qt.NoPen);p.setBrush(QColor('#3d3249'))
    p.drawEllipse(QPointF(66,9.8),.8,.8)
    p.setBrush(QColor('#83738f'));p.drawRoundedRect(QRectF(57,67,18,1.1),.5,.5)
    # Poucas linhas grandes continuam reconhecíveis na escala mínima.
    p.setBrush(QColor('#242b40'));p.drawRoundedRect(QRectF(31,18,70,40),2,2)
    p.setBrush(QColor('#817895'));p.drawRoundedRect(QRectF(35,22,17,1.5),.6,.6)
    p.setBrush(QColor('#ffd16e'));p.drawRoundedRect(QRectF(35,29,28,2.4),1,1)
    p.setBrush(QColor('#ddd3e8'));p.drawRoundedRect(QRectF(35,36,18,1.8),.7,.7)
    p.setBrush(QColor('#9f9ab9'));p.drawRoundedRect(QRectF(35,41,43,1.6),.6,.6)
    p.drawRoundedRect(QRectF(57,36,31,1.8),.7,.7)
    p.setBrush(QColor('#efd29b'))
    for index in range(progress):
        p.drawRoundedRect(QRectF(35+4.6*index,48,3,1.8),.6,.6)
    if not working or key>=0 or int(phase*2)%2==0:
        p.setBrush(QColor('#ffd16e'))
        p.drawRoundedRect(QRectF(35+4.6*progress,46.5,1.2,4.5),.5,.5)
    p.setBrush(QColor('#51465f'));p.drawRoundedRect(_NOTEBOOK_HINGE,4,4)
    p.setBrush(QColor('#c3b2d2'))
    for x in (28,96):p.drawRoundedRect(QRectF(x,69,8,4),1.5,1.5)
    base=QLinearGradient(0,72,0,91)
    base.setColorAt(0,QColor('#c6b8d7'));base.setColorAt(.8,QColor('#998ba9'));base.setColorAt(1,QColor('#6a5c7a'))
    p.setPen(QPen(QColor('#d2c1e2'),1));p.setBrush(base);p.drawPath(_notebook_base())
    p.setPen(QPen(QColor('#776785'),.7));p.drawLine(QPointF(8,88),QPointF(124,88))
    p.setPen(Qt.NoPen)
    for row in range(2):
        for col in range(8):
            pressed=tap if col==key and row==key%2 else 0.
            p.setBrush(QColor(round(77+178*pressed),round(66+143*pressed),round(92+18*pressed)))
            p.drawRoundedRect(QRectF(24+11*col-row,74.5+4*row+.35*pressed,7.8,2.6),.7,.7)
    p.setPen(QPen(QColor('#7a698a'),.65));p.setBrush(QColor('#d3c7df'))
    p.drawRoundedRect(QRectF(53,83,26,3.5),1,1)
    p.setPen(Qt.NoPen);p.setBrush(QColor('#ffd16e') if working else QColor('#756b80'))
    p.drawRoundedRect(QRectF(112.5,84.3,3,1.4),.7,.7)
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
