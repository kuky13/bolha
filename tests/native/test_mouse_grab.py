# SPDX-License-Identifier: GPL-3.0-only
"""Estado físico mockado exercita os mesmos gestos usados pelo frame nativo."""
import ctypes
import time
from collections import deque
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QEvent,QPoint,QPointF,Qt

from game import Game
from bolha.app import NativeApp
from bolha.pet import PetWindow
from bolha.scene import NativeScene,ObjectWindow
import bolha.grab as grab_module
import bolha.platform as platform

CONTENT=Path(__file__).resolve().parents[2]/'assets/bolha/content'


def mouse(x,y,button=Qt.LeftButton):
    return SimpleNamespace(button=lambda:button,globalPosition=lambda:QPointF(x,y))


class Pointer:
    def __init__(self):self.point=QPointF(508.5,291.75);self.down=True;self.reads=0;self.error=None
    def sample(self):
        self.reads+=1
        if self.error:raise self.error
        return self.point,self.down


@pytest.fixture(params=['pet','toy'])
def held_window(request,qt_application,tmp_path,monkeypatch):
    pointer=Pointer();monkeypatch.setattr(grab_module,'drag_pointer',lambda:pointer)
    game=Game(tmp_path,CONTENT);game.configure({'senseCursor':False,'senseWindows':False,'roaming':False})
    game.body.x,game.body.y=500,300
    game.ball.body.x,game.ball.body.y=500,300;game.ball.place()
    window=PetWindow(game) if request.param=='pet' else ObjectWindow(NativeScene(game),game.ball)
    window.sync();body=game.body if request.param=='pet' else game.ball.body
    body.vx,body.vy,body.omega=900,-800,300
    events=[];interact=game.interact
    def record(event):events.append(event.copy());return interact(event)
    game.interact=record
    window.mousePressEvent(mouse(508.5,291.75))
    try:yield window,game,body,pointer,events
    finally:window.close()


def active(window):return window.press is not None if isinstance(window,PetWindow) else window.offset is not None


def test_pega_imovel_longa_mantem_inicio_e_velocidade_zero(held_window):
    window,game,body,pointer,events=held_window
    started=game.held_since;position=body.x,body.y;cursor=game.cursor
    for frame in range(180):
        window.poll_interaction()
        game.tick(.016,time.monotonic()+frame*.016)
    assert active(window) and body.held and (body.x,body.y)==position
    assert body.vx==body.vy==body.omega==0 and game.cursor==cursor
    assert game.held_since==started and len(events)==1
    assert window.windowFlags()&Qt.WindowDoesNotAcceptFocus
    assert window.testAttribute(Qt.WA_ShowWithoutActivating)


def test_ungrab_com_botao_down_segue_fora_da_mascara_sem_repegar(held_window,monkeypatch):
    window,game,body,pointer,events=held_window
    captures=[];monkeypatch.setattr(window,'grabMouse',lambda:captures.append(True))
    pointer.point=QPointF(1012.5,191.25)
    window.event(QEvent(QEvent.UngrabMouse))
    assert active(window) and body.held
    assert (body.x,body.y)==(1004,199.5)
    pointer.point=QPointF(1100.5,401.75);window.poll_interaction()
    assert (body.x,body.y)==(1092,410)
    assert not captures and not any(event['type'].endswith('end') for event in events)


@pytest.mark.parametrize('finish',['poll','ungrab'])
def test_up_sem_release_qt_aplica_ultima_posicao_e_cai_no_primeiro_tick(held_window,finish):
    window,game,body,pointer,events=held_window
    pointer.point=QPointF(710.75,211.5);pointer.down=False
    if finish=='poll':window.poll_interaction()
    else:window.event(QEvent(QEvent.UngrabMouse))
    assert not active(window) and not body.held
    assert (body.x,body.y)==(702.25,219.75)
    assert body.vx==body.vy==body.omega==0
    reads=pointer.reads;count=len(events)
    window.poll_interaction();window.mouseReleaseEvent(mouse(10,10));window.event(QEvent(QEvent.UngrabMouse))
    assert pointer.reads==reads and len(events)==count
    game.tick(.016,time.monotonic())
    assert body.x==702.25 and body.y>219.75 and body.vy>0


def test_release_qt_falso_nao_encerra_enquanto_botao_fisico_down(held_window):
    window,game,body,pointer,events=held_window
    window.mouseReleaseEvent(mouse(10,10))
    assert active(window) and body.held
    assert not any(event['type'].endswith('end') for event in events)
    pointer.down=False;pointer.point=QPointF(705,205)
    window.mouseReleaseEvent(mouse(10,10))
    assert not active(window) and (body.x,body.y)==(696.5,213.25)


def test_press_duplicado_e_botao_secundario_preservam_ancora(held_window):
    window,game,body,pointer,events=held_window
    window.mousePressEvent(mouse(600,400));window.mousePressEvent(mouse(600,400,Qt.RightButton))
    window.mouseReleaseEvent(mouse(600,400,Qt.RightButton))
    pointer.point=QPointF(600,400);window.poll_interaction()
    assert active(window) and (body.x,body.y)==(591.5,408.25)
    assert sum(event['type'] in ('hold-start','drag-start') for event in events)==(2 if isinstance(window,PetWindow) else 1)


@pytest.mark.parametrize('error',[OSError('dispositivo'),RuntimeError('desktop'),ValueError('posição')])
def test_falha_ao_ler_dispositivo_cancela_sem_fantasma(held_window,error):
    window,game,body,pointer,events=held_window
    pointer.error=error;window.poll_interaction()
    assert not active(window) and not body.held and not game.scene_dragging
    assert body.vx==body.vy==body.omega==0 and not game.hover
    reads=pointer.reads;count=len(events)
    window.poll_interaction();window.cancel_interaction()
    assert reads==pointer.reads and count==len(events)


@pytest.mark.parametrize('reason',['hide','window-hide','panic','close','menu','suspend'])
def test_interrupcao_cancela_e_nao_reativa_com_botao_ainda_down(held_window,reason):
    window,game,body,pointer,events=held_window
    if reason in ('hide','panic'):
        game.interact(dict(type='hide',value=True) if reason=='hide' else dict(type='panic'));window.sync()
    elif reason=='close':window.close()
    elif reason=='window-hide':window.hide()
    elif reason=='menu':
        controller=SimpleNamespace(game=game,cancel_interactions=window.cancel_interaction)
        NativeApp._panel_opened(controller)
    else:
        controller=SimpleNamespace(cancel_interactions=window.cancel_interaction)
        NativeApp._application_state_changed(controller,Qt.ApplicationSuspended)
        assert controller.suspended
    assert not active(window) and not body.held and not game.hover
    reads=pointer.reads;window.poll_interaction()
    assert pointer.reads==reads and body.vx==body.vy==body.omega==0


def test_ancora_preserva_fracao_e_coordenadas_negativas_apos_limite(held_window):
    window,game,body,pointer,events=held_window
    game.desktop(dict(areas=[dict(id=0,x=-1800,y=-600,width=1800,height=1600,scaleFactor=1.5)]))
    pointer.point=QPointF(-1799.5,-599.75);window.poll_interaction()
    assert body.x>=-1800+body.half_w and body.y>=-600+body.half_h
    pointer.point=QPointF(-800.25,-300.5);window.poll_interaction()
    assert (body.x,body.y)==(-808.75,-292.25)
    pointer.down=False;window.poll_interaction()
    assert not active(window) and body.vx==body.vy==body.omega==0


def test_sem_provider_eventos_qt_aplicam_release_final_sem_ultimo_move(qt_application,tmp_path,monkeypatch):
    monkeypatch.setattr(grab_module,'drag_pointer',lambda:None)
    game=Game(tmp_path,CONTENT);game.body.x,game.body.y=500,300
    window=PetWindow(game)
    try:
        window.mousePressEvent(mouse(508,309));window.mouseReleaseEvent(mouse(708,209))
        assert (game.body.x,game.body.y)==(700,200) and not game.body.held
    finally:window.close()


def test_provider_nao_le_sem_gesto_e_falha_no_inicio_nao_prende(qt_application,tmp_path,monkeypatch):
    calls=[]
    def failure():calls.append(True);raise OSError('API indisponível')
    monkeypatch.setattr(grab_module,'drag_pointer',failure)
    game=Game(tmp_path,CONTENT);window=PetWindow(game)
    try:
        window.poll_interaction();window.mouseMoveEvent(mouse(0,0))
        assert not calls
        window.mousePressEvent(mouse(game.body.x,game.body.y))
        assert calls==[True] and not active(window) and not game.body.held
        window.poll_interaction();assert calls==[True]
    finally:window.close()


@pytest.mark.parametrize('swapped,key',[(0,1),(1,2)])
def test_windows_usa_so_highbit_e_fixa_botao_primario_no_inicio(monkeypatch,swapped,key):
    class Function:
        def __init__(self,result):self.result=result;self.calls=[]
        def __call__(self,arg):self.calls.append(arg);return self.result
    metrics=Function(swapped);state=Function(1)
    monkeypatch.setattr(ctypes,'windll',SimpleNamespace(user32=SimpleNamespace(GetSystemMetrics=metrics,GetAsyncKeyState=state)),raising=False)
    monkeypatch.setattr(platform.QCursor,'pos',lambda:QPoint(-850,-225))
    pointer=platform.WindowsDragPointer()
    assert pointer.sample()==(QPoint(-850,-225),False)
    state.result=-32768;metrics.result=not swapped
    assert pointer.sample()==(QPoint(-850,-225),True)
    assert metrics.calls==[23] and state.calls==[key,key]
    assert state.argtypes==[ctypes.c_int] and state.restype==ctypes.c_short


def test_provider_fora_do_windows_ou_offscreen_e_unsupported(monkeypatch):
    monkeypatch.setattr(platform.sys,'platform','linux')
    assert platform.drag_pointer() is None
    monkeypatch.setattr(platform.sys,'platform','win32')
    monkeypatch.setattr(platform.QGuiApplication,'platformName',lambda:'offscreen')
    assert platform.drag_pointer() is None


def test_frame_existente_le_pega_antes_fisica_com_sensor_cursor_desligado(qt_application,tmp_path,monkeypatch):
    import bolha.app as app_module
    pointer=Pointer();monkeypatch.setattr(grab_module,'drag_pointer',lambda:pointer)
    game=Game(tmp_path,CONTENT);game.configure({'senseCursor':False,'senseWindows':False,'roaming':False})
    game.body.x,game.body.y=500,300;pet=PetWindow(game);scene=NativeScene(game)
    controller=SimpleNamespace(quitting=False,updating=False,suspended=False,last_tick=time.monotonic()-.016,
        frame_times=deque(),pet=pet,scene=scene,game=game,store=SimpleNamespace(preferences=game.prefs))
    monkeypatch.setattr(app_module.QCursor,'pos',lambda:pytest.fail('sensor de contexto desativado'))
    try:
        pet.mousePressEvent(mouse(508.5,291.75));pointer.point=QPointF(708.5,191.75)
        NativeApp.tick(controller)
        assert (game.body.x,game.body.y)==(700,200) and game.body.held
        assert game.cursor==(700,200)  # O contexto desativado continua no centro, sem ler o ponteiro.
        pointer.down=False;NativeApp.tick(controller)
        assert not game.body.held and game.body.x==700 and game.body.y>200
        assert game.prefs['senseCursor'] is False
    finally:scene.close();pet.close()


def test_posicao_invalida_cancela_sem_contaminar_fisica(held_window):
    window,game,body,pointer,events=held_window
    pointer.point=QPointF(float('nan'),100);window.poll_interaction()
    assert not active(window) and not body.held
    assert (body.x,body.y)==(500,300)


def test_captura_qt_somente_no_inicio_e_release_reentrante_idempotente(qt_application,tmp_path,monkeypatch):
    from PySide6.QtWidgets import QWidget
    pointer=Pointer();monkeypatch.setattr(grab_module,'drag_pointer',lambda:pointer)
    game=Game(tmp_path,CONTENT);game.body.x,game.body.y=500,300;window=PetWindow(game)
    calls=[]
    monkeypatch.setattr(grab_module.QGuiApplication,'platformName',lambda:'windows')
    monkeypatch.setattr(window,'grabMouse',lambda:calls.append('grab'))
    monkeypatch.setattr(QWidget,'mouseGrabber',lambda:window)
    def release():
        calls.append('release');window.event(QEvent(QEvent.UngrabMouse))
    monkeypatch.setattr(window,'releaseMouse',release)
    try:
        window.mousePressEvent(mouse(508.5,291.75));assert calls==['grab']
        window.event(QEvent(QEvent.UngrabMouse));assert active(window) and calls==['grab']
        pointer.down=False;window.poll_interaction()
        assert not active(window) and not game.body.held and calls==['grab','release']
        window.mouseReleaseEvent(mouse(508.5,291.75));assert calls==['grab','release']
    finally:
        monkeypatch.setattr(QWidget,'mouseGrabber',lambda:None);window.close()
