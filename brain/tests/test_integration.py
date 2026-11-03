# SPDX-License-Identifier: GPL-3.0-only
import sys
import time
import json
import pytest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from game import Game, Burst

CONTENT = Path(__file__).resolve().parents[2] / 'assets/bolha/content'

def test_nome_novo_preserva_memoria_e_nao_sobrescreve_destino(tmp_path):
    import numpy as np
    game=Game(tmp_path,CONTENT)
    game.brain.learned[0,0]=.06
    game.save()
    legacy=tmp_path/'drippy'
    (tmp_path/'bolha').rename(legacy)
    reopened=Game(tmp_path,CONTENT)
    assert np.isclose(reopened.brain.learned[0,0],.06)
    assert not legacy.exists()
    legacy.mkdir()
    marker=legacy/'preservar.txt';marker.write_text('não sobrescrever')
    Game(tmp_path,CONTENT)
    assert marker.read_text()=='não sobrescrever'

def test_rosto_deita_levanta_e_arrasto_interrompe_descanso(tmp_path,monkeypatch):
    monkeypatch.setattr(time,'monotonic',lambda:100.)
    game=Game(tmp_path,CONTENT)
    game.body.grounded=True;game.body.surface=760
    game.interact({'type':'rest'})
    assert game.snapshot()['pose']=='lying'
    assert game.snapshot()['surface']==760
    game.interact({'type':'rest'})
    assert game.snapshot()['pose']=='idle'
    game.body.angle=90
    game.interact({'type':'rest'})
    assert game.snapshot()['pose']=='idle'
    game.interact({'type':'rest'})
    game.interact({'type':'drag-start','x':500,'y':300})
    assert game.snapshot()['pose']=='held'
    assert game.lying_until==0

def test_pausar_passeio_preserva_olhar_sem_movimento(tmp_path):
    game=Game(tmp_path,CONTENT)
    game.body.grounded=True;game.body.vx=100
    game.behavior.look_at(game.body.x+200,game.body.y,100.)
    game.behavior.tick(.016,100.,game.cursor,game.bounds(),game.prof,[],False)
    assert game.state.gaze==(1.,0.)
    assert game.body.vx==0

def test_envio_prioriza_arrasto_e_envia_neural_apenas_quatro_vezes_por_segundo(tmp_path,monkeypatch):
    clock=[100.];monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT)
    for body in (game.body,game.ball.body): body.grounded=True
    assert game.output_interval()==.1
    game.body.held=True
    assert game.output_interval()==pytest.approx(1/60)
    game.body.held=False;game.body.grounded=False
    assert game.output_interval()==pytest.approx(1/30)
    game.interact({'type':'monitor','value':True})
    assert len(game.snapshot()['neural']['positions'])==470
    assert 'neural' not in game.snapshot()
    clock[0]+=.26
    assert 'neural' in game.snapshot()
    game.interact({'type':'monitor','value':False})
    clock[0]+=1
    assert 'neural' not in game.snapshot()
    game.panicked=True
    assert game.output_interval()==1

def test_estouro_temporario_somente_por_arremessos_fortes():
    burst=Burst()
    for i in range(50): assert not burst.throw(100+i*.2,300,12)
    for i in range(11): assert not burst.throw(200+i,1400,12)
    assert burst.throw(211,1400,12)
    assert burst.phase(211.2)=='burst'
    assert burst.phase(225)=='away'
    assert burst.phase(241)=='shy'
    burst.caress(20)
    assert burst.phase(241)=='normal'

def test_janela_de_arremessos_expira():
    burst=Burst()
    for i in range(11): assert not burst.throw(i*10,1500,12)
    assert burst.away_until==0

def test_cerebro_original_aprende_salva_e_reabre(tmp_path,monkeypatch):
    clock=[100.]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT)
    assert game.brain.N==470
    game.interact({'type':'corner'})
    game.interact({'type':'work'})
    for i in range(200):
        clock[0]+=.02
        if i%20==0:game.interact({'type':'caress'})
        game.tick(.02)
    assert game.brain.learned_summary()
    game.save()
    learned=game.brain.learned.copy()
    reopened=Game(tmp_path,CONTENT)
    import numpy as np
    assert np.allclose(reopened.brain.learned,learned,atol=1e-6)
    assert (tmp_path/'bolha/nervous.json').exists()

def test_panic_congela_simulacao_e_nao_reaparece_sozinha(tmp_path):
    game=Game(tmp_path,CONTENT)
    game.interact({'type':'panic'})
    before=game.brain.time_ms
    game.tick(.05,time.monotonic()+50)
    assert game.brain.time_ms==before
    assert not game.snapshot()['visible']
    assert Game(tmp_path,CONTENT).panicked is True

def test_monitores_negativos_e_remocao_recolocam_corpo(tmp_path):
    game=Game(tmp_path,CONTENT)
    game.desktop({'areas':[dict(x=-1000,y=0,width=1000,height=700,id=1,scaleFactor=1),dict(x=0,y=0,width=1200,height=800,id=2,scaleFactor=1.5)]})
    game.body.x=-500;game.body.y=500
    game.desktop({'areas':[dict(x=0,y=0,width=1200,height=800,id=2,scaleFactor=1.5)]})
    assert 0<=game.body.x<1200 and 0<=game.body.y<800

def test_passagem_entre_monitores_livres_quando_primeiro_esta_ocupado(tmp_path):
    game=Game(tmp_path,CONTENT)
    game.desktop({'areas':[dict(x=-1920,y=0,width=1920,height=1040,id=0,scaleFactor=1,monitorHeight=1080),
                           dict(x=0,y=0,width=1920,height=1040,id=1,scaleFactor=1,monitorHeight=1080),
                           dict(x=1920,y=0,width=1280,height=680,id=2,scaleFactor=1.5,monitorHeight=720)]})
    game.blocked={0}
    game.read_context=lambda *_:None
    game.think=lambda *_:None
    game.behavior.tick=lambda *_:None
    game.body.x,game.body.y=1800,400
    game.body.half_w=game.body.half_h=10
    for i in range(100):
        game.body.vx=450
        game.tick(.016,100+i*.016)
    assert game.body.x>1920

def test_memes_novos_e_objetos_sem_qt(tmp_path):
    game=Game(tmp_path,CONTENT)
    options=game.mischief.available('feliz',dict(travessuras=True,memes=True,bilhetes=True,fotos=False))
    assert 'meme' in options and 'bilhete' in options
    item=game.mischief._make('meme','feliz',False)
    assert item.valida and item.image=='carinho'
    assert 'PySide6' not in sys.modules


def test_castigo_fuga_aprendida_e_perdao(tmp_path,monkeypatch):
    clock=[100.]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT)
    game.castigo.toggle(game.bounds())
    plaque=game.castigo.plaquinha
    game.body.x=plaque.x()+plaque.width()/2
    game.body.y=game.bounds()[3]-game.body.half_h
    game.body.grounded=True
    game.body.held=True
    game.castigo.act(clock[0],game.body,game.bounds(),game.cursor,game.state,game.rates)
    clock[0]+=.1;game.body.held=False
    game.castigo.act(clock[0],game.body,game.bounds(),game.cursor,game.state,game.rates)
    assert game.castigo.dentro and game.state.castigo
    game.castigo._iniciar_fuga(clock[0],game.bounds())
    zone=game.castigo.zona_fuga
    game.body.x=zone[1]+50 if game.castigo.fuga_para_direita else zone[0]-50
    game.castigo._checar_fuga(clock[0]+1,game.body)
    assert game.castigo.vitorias['fugir']==1
    assert json.loads(game.pet_paths.castigo.read_text())['vitorias']['fugir']==1
    game.castigo._entrar(clock[0]+2,game.state)
    game.castigo._decidir(clock[0]+2,.1,game.body,game.bounds(),{'ACEITAR':20.})
    assert not game.castigo.dentro and not game.state.castigo
