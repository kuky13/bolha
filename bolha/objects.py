# SPDX-License-Identifier: GPL-3.0-or-later
"""Desenhos GPL do Pestinha, mille-okws e contribuidores.

Notebook e bolinha extraídos de world/notebook.py:_paint_desenho e body/bolinha.py:paintEvent
no commit ca03a48136d2f97b9b58bbc7ae4e307bb408048d. Sem sprites ou assets.
O amendoim é um desenho vetorial próprio da Bolha.
"""
import math
from PySide6.QtCore import QPointF,QRectF,Qt
from PySide6.QtGui import QColor,QLinearGradient,QRadialGradient,QPen,QPainterPath,QTransform
NOTEBOOK_W,NOTEBOOK_H=110,70
BALL_RADIUS=18


def notebook_transform(rect):
    scale=min(rect.width()/NOTEBOOK_W,rect.height()/NOTEBOOK_H)
    x=rect.x()+(rect.width()-NOTEBOOK_W*scale)/2
    y=rect.y()+(rect.height()-NOTEBOOK_H*scale)/2
    return QTransform().translate(x,y).scale(scale,scale)


def notebook_shape(rect,working=False):
    path=QPainterPath();path.setFillRule(Qt.WindingFill)
    half_pen=1.25 if working else .6
    path.addRoundedRect(QRectF(4,3,NOTEBOOK_W-8,NOTEBOOK_H-14).adjusted(-half_pen,-half_pen,half_pen,half_pen),6+half_pen,6+half_pen)
    path.addRoundedRect(QRectF(2,NOTEBOOK_H-13,NOTEBOOK_W-4,9).adjusted(-.5,-.5,.5,.5),3,3)
    return notebook_transform(rect).map(path)


def paint_notebook(p,rect,working=False):
    """Mesmo desenho original110x70, ajustado somente com escala uniforme."""
    p.save();p.setTransform(notebook_transform(rect),True)
    tampa=QRectF(4,3,NOTEBOOK_W-8,NOTEBOOK_H-14)
    gradiente=QLinearGradient(tampa.topLeft(),tampa.bottomLeft())
    gradiente.setColorAt(0.,QColor('#5d6165'));gradiente.setColorAt(1.,QColor('#3b3e41'))
    borda=QColor('#63e56f') if working else QColor('#24272a')
    p.setPen(QPen(borda,2.5 if working else 1.2));p.setBrush(gradiente)
    p.drawRoundedRect(tampa,6,6)
    base=QRectF(2,NOTEBOOK_H-13,NOTEBOOK_W-4,9)
    prata=QLinearGradient(base.topLeft(),base.bottomLeft())
    prata.setColorAt(0.,QColor('#d9dcdf'));prata.setColorAt(1.,QColor('#959a9f'))
    p.setPen(QPen(QColor('#5a5e62'),1));p.setBrush(prata);p.drawRoundedRect(base,3,3)
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
