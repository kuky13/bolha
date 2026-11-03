# SPDX-License-Identifier: GPL-3.0-only
from geometry import fullscreen_monitors

DISPLAYS=[dict(x=0,y=0,width=1920,height=1040,monitorWidth=1920,monitorHeight=1080,scaleFactor=1),
          dict(x=1920,y=0,width=1280,height=693,monitorX=1920,monitorY=0,monitorWidth=1280,monitorHeight=720,nativeX=1920,nativeY=0,scaleFactor=1.5)]

def test_tela_cheia_em_dois_monitores_com_escalas_diferentes():
    windows=[((0,0,1920,1080),False,False),((1920,0,3840,1080),False,False)]
    assert fullscreen_monitors(windows,DISPLAYS)=={0,1}

def test_janela_maximizada_normal_nao_e_tela_cheia():
    windows=[((0,0,1920,1040),True,True),((0,0,1920,1080),False,False)]
    assert fullscreen_monitors(windows,DISPLAYS)==set()

def test_so_monitor_ocupado_e_bloqueado():
    assert fullscreen_monitors([((0,0,1920,1080),False,False)],DISPLAYS)=={0}
