# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Prévia reproduzível com os mesmos desenhos Qt usados pelo aplicativo."""
import math
import os
import sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QImage, QPainter, QColor, QFont
from PySide6.QtWidgets import QApplication
from bolha.character import draw_character
from bolha.objects import paint_notebook, paint_peanut
from bolha.speech import paint_bubble


def render(path, phase=0.):
    image=QImage(1080,670,QImage.Format_ARGB32_Premultiplied)
    image.fill(QColor('#17141f'))
    p=QPainter(image)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QColor('#fff1c7'));p.setFont(QFont('Sans Serif',22))
    p.drawText(36,48,'Bolha · prévia real do desenho Qt')
    p.setFont(QFont('Sans Serif',12));p.setPen(QColor('#c8badb'))
    p.drawText(36,78,'Olhos proporcionais em todas as direções • balões locais • notebook detalhado')
    for index,(gaze,label) in enumerate((((-1.,-.5),'Olhar à esquerda'),((0.,0.),'Olhar frontal'),((1.,.5),'Olhar à direita'))):
        x=180+index*350
        draw_character(p,x,195,scale=1.35,gaze=gaze)
        p.setPen(QColor('#c8badb'));p.drawText(QRectF(x-120,285,240,25),Qt.AlignCenter,label)
    paint_bubble(p,QRectF(60,355,300,90),'Mais um pouquinho desse carinho?',False,anchor=200)
    draw_character(p,260,530,scale=1.15,emotion='feliz')
    paint_bubble(p,QRectF(405,355,305,110),'Será que o cursor também se cansa?',True,anchor=110)
    draw_character(p,530,560,scale=1.15,emotion='curioso',gaze=(.8,-.6))
    paint_notebook(p,QRectF(760,405,270,180),True,phase=phase)
    paint_peanut(p,880,610,22,phase*.1)
    p.setPen(QColor('#c8badb'));p.drawText(QRectF(730,355,300,30),Qt.AlignCenter,'Notebook em atividade')
    p.end()
    if not image.save(str(path)):raise OSError('Não foi possível salvar a prévia.')


if __name__=='__main__':
    app=QApplication.instance() or QApplication([])
    directory=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/bolha-visual-previews')
    directory.mkdir(parents=True,exist_ok=True)
    render(directory/'visual-polish.png')
