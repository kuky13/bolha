# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Desenhos GPL do Pestinha, mille-okws e contribuidores.

Notebook e bolinha extraídos de world/notebook.py:_paint_desenho e body/bolinha.py:paintEvent
no commit ca03a48136d2f97b9b58bbc7ae4e307bb408048d. Sem sprites ou assets.
A silhueta do notebook vem do Pestinha; os detalhes, materiais e animações
da tela foram redesenhados para a Bolha. O amendoim é um desenho próprio.
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


def paint_notebook(p,rect,working=False,phase=0.):
    """Notebook derivado do Pestinha, com materiais e detalhes próprios da Bolha.

    ``phase`` é tempo em segundos; somente a tela em uso muda entre quadros.
    A silhueta e a escala continuam compartilhadas com a máscara de entrada.
    """
    phase=float(phase)
    if not math.isfinite(phase):phase=0.
    p.save();p.setTransform(notebook_transform(rect),True)
    tampa=QRectF(4,3,NOTEBOOK_W-8,NOTEBOOK_H-14)
    metal=QLinearGradient(tampa.topLeft(),tampa.bottomRight())
    metal.setColorAt(0.,QColor('#625c77'));metal.setColorAt(.45,QColor('#393644'))
    metal.setColorAt(1.,QColor('#25242d'))
    p.setPen(QPen(QColor('#c6a8ee') if working else QColor('#91829e'),2.5 if working else 1.2))
    p.setBrush(metal);p.drawRoundedRect(tampa,6,6)
    # A moldura escura mantém os detalhes legíveis mesmo na escala pequena.
    screen=QRectF(10,9,90,35)
    p.setPen(QPen(QColor('#16141d'),1.5));p.setBrush(QColor('#11131d'))
    p.drawRoundedRect(screen,2,2)
    p.save()
    clip=QPainterPath();clip.addRoundedRect(screen,2,2);p.setClipPath(clip)
    glass=QLinearGradient(screen.topLeft(),screen.bottomRight())
    glass.setColorAt(0.,QColor('#29283b'));glass.setColorAt(1.,QColor('#151823'))
    p.fillRect(screen,glass)
    p.fillRect(QRectF(11,10,15,33),QColor('#242132'))
    p.setPen(QPen(QColor('#746484'),.7));p.drawLine(QPointF(27,10),QPointF(27,43))
    p.setPen(Qt.NoPen)
    for row,length in enumerate((8,6,9,5)):
        p.setBrush(QColor('#b6a0d3') if row==0 else QColor('#665c7c'))
        p.drawRoundedRect(QRectF(14,14+row*6,length,1.5),.6,.6)
    for row,(indent,length,color) in enumerate(((0,27,'#bca6e5'),(4,37,'#e6c779'),
                                               (4,22,'#8baab0'),(8,31,'#bca6e5'),
                                               (4,18,'#8baab0'))):
        p.setBrush(QColor(color));p.drawRoundedRect(QRectF(33+indent,14+row*5,length,1.6),.7,.7)
    if working:
        pulse=.5+.5*math.sin(phase*2.)
        p.setBrush(QColor(255,211,100,round(115+100*pulse)))
        p.drawRoundedRect(QRectF(33,39,7+20*pulse,1.8),.7,.7)
        if int(phase*2)%2==0:
            p.fillRect(QRectF(57,33,1,4),QColor('#fff0bb'))
    # Reflexo estreito e fixo, sem brilho atravessando a área inteira da tela.
    sheen=QPainterPath(QPointF(10,9));sheen.lineTo(55,9);sheen.lineTo(27,44);sheen.lineTo(10,44);sheen.closeSubpath()
    p.setBrush(QColor(224,217,255,10));p.drawPath(sheen);p.restore()
    p.setPen(Qt.NoPen);p.setBrush(QColor('#11121a'));p.drawEllipse(QPointF(55,6.2),.9,.9)
    p.setBrush(QColor('#a491bb'));p.drawEllipse(QPointF(55,6.),.3,.3)
    # Dobradiças, teclas e pequenos riscos no apoio dão escala ao objeto.
    p.setPen(QPen(QColor('#aaa0b8'),1.2))
    for x in (18,80):p.drawLine(QPointF(x,47),QPointF(x+12,47))
    p.setPen(QPen(QColor('#17151f'),.5));p.setBrush(QColor('#766f85'))
    for row in range(2):
        for col in range(11):
            p.drawRoundedRect(QRectF(16+col*7.2,50+row*3.4,5.6,2.2),.6,.6)
    base=QRectF(2,NOTEBOOK_H-13,NOTEBOOK_W-4,9)
    silver=QLinearGradient(base.topLeft(),base.bottomLeft())
    silver.setColorAt(0.,QColor('#b6afc5'));silver.setColorAt(.5,QColor('#827d92'))
    silver.setColorAt(1.,QColor('#4d4a5c'))
    p.setPen(QPen(QColor('#464151'),1));p.setBrush(silver);p.drawRoundedRect(base,3,3)
    p.setPen(QPen(QColor('#5a536b'),.6));p.setBrush(QColor('#a29aaf'))
    p.drawRoundedRect(QRectF(42,59,26,3.5),1,1)
    p.setPen(QPen(QColor('#d8cfdf'),.5))
    for x,y,length in ((10,60,5),(91,62,3),(15,63,3)):
        p.drawLine(QPointF(x,y),QPointF(x+length,y-.6))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor('#ffd364') if working else QColor('#695f7e'))
    p.drawEllipse(QPointF(98,61.5),1,1)
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
