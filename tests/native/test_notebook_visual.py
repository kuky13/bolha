# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""A arte detalhada preserva escala, silhueta e anima somente quando em uso."""
import pytest
from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import QImage, QPainter, QPainterPathStroker
from bolha.objects import paint_notebook, notebook_shape


def render(width, height, working=False, phase=0.):
    image=QImage(width,height,QImage.Format_ARGB32_Premultiplied);image.fill(0)
    painter=QPainter(image);painter.setRenderHint(QPainter.Antialiasing)
    paint_notebook(painter,QRectF(0,0,width,height),working,phase)
    painter.end()
    return image


@pytest.mark.parametrize('size',[(66,42),(110,70),(198,126),(170,70),(110,115)])
@pytest.mark.parametrize('working',[False,True])
def test_art_stays_within_hit_silhouette_at_all_scales(qt_application,size,working):
    width,height=size
    image=render(width,height,working)
    path=notebook_shape(QRectF(0,0,width,height),working)
    # Inclui somente a cobertura parcial de antialias ao redor do contorno.
    stroker=QPainterPathStroker();stroker.setWidth(2.)
    covered=path.united(stroker.createStroke(path))
    visible=0
    for y in range(height):
        for x in range(width):
            if image.pixelColor(x,y).alpha()>20:
                visible+=1
                assert covered.contains(QPointF(x+.5,y+.5)),(size,working,x,y)
    assert visible>width*height*.2
    assert image.pixelColor(0,0).alpha()==0


def test_only_working_screen_animates_and_does_not_change_shell(qt_application):
    idle=render(110,70,False,0.)
    assert bytes(idle.bits())==bytes(render(110,70,False,.7).bits())
    a,b=render(110,70,True,0.),render(110,70,True,.7)
    changes=[(x,y) for y in range(70) for x in range(110) if a.pixel(x,y)!=b.pixel(x,y)]
    assert changes
    assert all(10<=x<=100 and 9<=y<=44 for x,y in changes)
    # A máscara e o quadro externo não tremem junto com o conteúdo da tela.
    assert a.copy(0,45,110,25)==b.copy(0,45,110,25)
