# SPDX-License-Identifier: GPL-3.0-only
"""Regressões que protegem dados, privacidade, pintura e interação nativa."""
import io
import math
import os
from pathlib import Path
import sys
import time
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pestinha.core.physics import Body
from pestinha import store


def display(x,width,scale,native_x,y=0,height=700,native_y=0):
    return dict(x=x,y=y,width=width,height=height,monitorX=x,monitorY=y,monitorWidth=width,
                monitorHeight=height,scaleFactor=scale,nativeX=native_x,nativeY=native_y,
                nativeWidth=width*scale,nativeHeight=height*scale)

def test_costura_qt_windows_com_vazio_artificial_e_escalas_diferentes():
    displays=[display(0,1536,1.25,0,height=864),display(1920,1280,1.5,1920,height=720)]
    areas=[(0,0,1536,864),(1920,0,3200,720)]
    body=Body(1535,300,10,10,circular=True);body.vx=400
    body.step(.016,areas[0],[],areas,areas,displays)
    assert 1920<body.x<1940
    assert body.y==pytest.approx((300+1600*.016*.016)/1.2,abs=1)
    assert body.vx>0
    for _ in range(4):body.step(.016,areas[1],[],areas,areas,displays)
    assert body.x>1920

def test_monitor_negativo_adjacente_e_vazio_real_colide():
    displays=[display(-1920,1536,1.25,-1920,height=864),display(0,1280,1.5,0,height=720)]
    areas=[(-1920,0,-384,864),(0,0,1280,720)]
    body=Body(-385,300,10,10,circular=True);body.vx=400
    body.step(.016,areas[0],[],areas,areas,displays)
    assert 0<body.x<20
    displays[1]['nativeX']=100
    body=Body(-400,300,10,10,circular=True);body.vx=1600
    body.step(.016,areas[0],[],areas,areas,displays)
    assert body.x<=areas[0][2]-10 and body.vx<0

def test_gravacao_usa_texto_imutavel_e_repete_falha_sem_esconder_outra(tmp_path,monkeypatch):
    from bolha.persistence import PersistenceWriter
    import bolha.persistence as persistence
    original=persistence.atomic_write_text;blocked={tmp_path/'a.json',tmp_path/'b.json'}
    def flaky(path,text,append=False):
        if path in blocked:raise OSError('disco indisponível')
        original(path,text,append)
    monkeypatch.setattr(persistence,'atomic_write_text',flaky)
    writer=PersistenceWriter();writer.submit(tmp_path/'a.json','{"v":1}');writer.submit(tmp_path/'b.json','{"v":2}')
    assert not writer.flush()
    blocked.remove(tmp_path/'a.json');writer.retry();assert not writer.flush()
    assert (tmp_path/'a.json').read_text()=='{"v":1}'
    blocked.clear();writer.retry();assert writer.flush()
    assert (tmp_path/'b.json').read_text()=='{"v":2}'
    assert writer.close()

def test_snapshot_serializado_antes_da_thread(tmp_path):
    from bolha.persistence import PersistenceWriter
    writer=PersistenceWriter();store.set_dispatcher(writer.submit)
    try:
        value={'memory':[1,2]};store.write_json(tmp_path/'memory.json',value);value['memory'].append(999)
        assert writer.flush();assert store.read_json(tmp_path/'memory.json')['memory']==[1,2]
    finally:writer.close();store.set_dispatcher(None)

def test_backup_corrompido_unico_e_original_preservado(tmp_path):
    path=tmp_path/'memory.json';path.write_text('{corrompido')
    assert store.read_json(path,{})=={}
    assert store.read_json(path,{})=={}
    assert path.read_text()=='{corrompido'
    assert len(list(tmp_path.glob('memory.json.corrompido*')))==2

def test_log_coracao_sem_terminal_e_cp1252(tmp_path,monkeypatch):
    from pestinha import log
    log.setup(tmp_path/'safe.log')
    monkeypatch.setattr(sys,'stderr',None);log.log('carinho ♡')
    raw=io.BytesIO();terminal=io.TextIOWrapper(raw,encoding='cp1252',write_through=True)
    monkeypatch.setattr(sys,'stderr',terminal);log.log('carinho ♡')
    assert 'carinho ♡' in (tmp_path/'safe.log').read_text(encoding='utf-8')
    log.desligar_arquivo()

def test_sensor_ociosidade_desligado_nao_simula_digitacao():
    from pestinha.sense.senses import ComputerSenses
    signals=ComputerSenses().update('IDLE',None,{},False,False)
    assert signals.get('TYPING',0)==0

@pytest.fixture(scope='module')
def qapp():
    from PySide6.QtWidgets import QApplication
    existing=QApplication.instance()
    assert existing is None or isinstance(existing,QApplication),'Testes Qt exigem QApplication, nunca QCoreApplication.'
    return existing or QApplication([])

def test_renderer_sem_boca_contido_em_todos_os_angulos(qapp):
    from PySide6.QtGui import QImage,QPainter,QColor
    from bolha.character import draw_character,EMOTIONS
    for angle in range(0,360,45):
        for emotion in EMOTIONS:
            for blink in (0,1):
                image=QImage(160,160,QImage.Format_ARGB32);image.fill(0)
                p=QPainter(image);draw_character(p,80,80,angle=angle,emotion=emotion,blink=blink);p.end()
                for y in range(160):
                    for x in range(160):
                        c=image.pixelColor(x,y)
                        if c.red()>180 and c.green()>110 and c.blue()<150:
                            assert math.hypot(x-80,y-80)<44.5
    # Região inferior local deve permanecer sem geometria dourada (sem boca).
    image=QImage(160,160,QImage.Format_ARGB32);image.fill(0)
    p=QPainter(image);draw_character(p,80,80);p.end()
    assert not any((c:=image.pixelColor(x,y)).red()>180 and c.green()>110 and c.blue()<150 for y in range(91,120) for x in range(45,116))

def test_piscadinha_fechamento_sustentado_e_reset():
    from bolha.character import wink_state,WINK_DURATION
    for start,eye,other in ((.13,'blink_left','blink_right'),(.53,'blink_right','blink_left')):
        for millisecond in range(120):
            state=wink_state((start+millisecond/1000)/WINK_DURATION)
            assert state[eye]==1 and state[other]==0
    for progress in (0,1,2):
        state=wink_state(progress);assert state['blink_left']==state['blink_right']==0

def test_janela_interativa_tem_mascara_circular_sem_foco(qapp,tmp_path):
    from game import Game
    from bolha.pet import PetWindow
    from PySide6.QtCore import Qt,QPoint
    game=Game(tmp_path,Path(__file__).resolve().parents[2]/'assets/bolha/content')
    pet=PetWindow(game)
    assert pet.body is game.body
    assert pet.mask().contains(QPoint(128,128))
    assert not pet.mask().contains(QPoint(50,50))
    assert pet.windowFlags()&Qt.WindowDoesNotAcceptFocus
    assert pet.visual.windowFlags()&Qt.WindowTransparentForInput
    pet.close()

def test_enumwindows_falha_registra_sem_nameerror(monkeypatch):
    import ctypes
    import importlib
    import types
    for name in ('pywintypes','win32api','win32con','win32gui','win32process'):
        monkeypatch.setitem(sys.modules,name,types.ModuleType(name))
    monkeypatch.setattr(ctypes,'windll',types.SimpleNamespace(user32=types.SimpleNamespace()),raising=False)
    module=importlib.import_module('pestinha.plataforma.windows')
    records=[];monkeypatch.setattr(module,'log',records.append)
    def broken(*_):raise OSError('EnumWindows indisponível')
    monkeypatch.setattr(module.win32gui,'EnumWindows',broken,raising=False)
    assert module.janelas_visiveis(set())==[]
    assert 'EnumWindows indisponível' in records[0]
    monkeypatch.delitem(sys.modules,'pestinha.plataforma.windows')

def test_memoria_semanticamente_invalida_nao_sobrescreve_original(tmp_path):
    from game import Game
    path=tmp_path/'bolha'/'nervous.json';path.parent.mkdir();path.write_text('{"version":999,"seed":1313}')
    game=Game(tmp_path,Path(__file__).resolve().parents[2]/'assets/bolha/content')
    with pytest.raises(OSError):game.save()
    assert path.read_text()=='{"version":999,"seed":1313}'
    assert list(path.parent.glob('nervous.json.corrompido.*'))

def test_todos_os_sensores_desligados_nao_chamam_apis_windows(tmp_path,monkeypatch):
    from game import Game
    import types
    module=types.ModuleType('pestinha.plataforma.windows')
    def forbidden(*_):raise AssertionError('sensor desligado foi consultado')
    module.ocioso_segundos=module.processo_ativo=module.janelas_visiveis=forbidden
    monkeypatch.setitem(sys.modules,'pestinha.plataforma.windows',module)
    import pestinha.plataforma
    monkeypatch.setattr(pestinha.plataforma,'windows',module,raising=False)
    game=Game(tmp_path,Path(__file__).resolve().parents[2]/'assets/bolha/content')
    game.configure(dict(senseIdle=False,senseApp=False,senseWindows=False,senseCursor=False))
    with monkeypatch.context() as platform:
        platform.setattr(sys,'platform','win32');game.read_context(100.)
    assert game.idle is None and game.native_error is None


def test_app_health_dialogo_reaberto_e_cursor_desligado(qapp,tmp_path,monkeypatch):
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QCursor
    from bolha.app import NativeApp
    monkeypatch.setenv('BOLHA_TEST','1')
    controller=NativeApp(qapp,tmp_path)
    controller.save_preferences(dict(senseApp=False,senseIdle=False,senseWindows=False,senseCursor=False))
    monkeypatch.setattr(QCursor,'pos',lambda:(_ for _ in ()).throw(AssertionError('cursor desligado')))
    deadline=time.monotonic()+1
    while time.monotonic()<deadline:qapp.processEvents();time.sleep(.002)
    assert controller.healthy and not controller.errors
    assert controller.metrics()['pid']==os.getpid()>0
    controller.show_settings();qapp.processEvents();controller.dialogs[0].close();qapp.processEvents()
    assert not controller.game.panel
    controller.show_settings();assert controller.game.panel
    controller.quit()
