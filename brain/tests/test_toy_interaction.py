# SPDX-License-Identifier: GPL-3.0-only
"""Interações chegam ao cérebro real e preservam a física e o aprendizado."""
from pathlib import Path
import time
import pytest
from game import Game

CONTENT=Path(__file__).resolve().parents[2]/'assets/bolha/content'


def test_segurando_sem_arrastar_alimenta_drag_e_press_do_cerebro(tmp_path,monkeypatch):
    clock=[100.]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT)
    game.interact({'type':'hold-start'})
    before=game.body.x,game.body.y
    game.body.step(.05,game.bounds(),[])
    assert (game.body.x,game.body.y)==before and game.body.held
    for _ in range(15):
        clock[0]+=.1;game.think(.1,clock[0])
    assert game.inputs['DRAG']>.75
    assert 'PRESS' in game.conditioning.active
    assert game.brain.time_ms>0 and game.brain.N==470
    game.interact({'type':'hold-end'})
    assert not game.body.held and not game.senses.dragging and not game.state.pressing
    assert game.release_reaction['until']>clock[0]
    clock[0]+=2;game.conditioning.tick(clock[0])
    assert game.conditioning.V['PRESS']>0


@pytest.mark.parametrize('angry,settle,learned,expected',[
    (.9,.1,.1,'birra'),(.2,.7,.1,'sacudir'),(.2,.1,.8,'timido'),(.3,.1,.1,'bravo')])
def test_reacao_ao_soltar_depende_dos_motores_e_condicionamento(tmp_path,monkeypatch,angry,settle,learned,expected):
    clock=[100.];monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT)
    game.interact({'type':'hold-start'})
    game.state.tone.r.update(ANGRY=angry,SETTLE=settle)
    game.conditioning.V['PRESS']=learned
    clock[0]+=5
    game.interact({'type':'hold-end'})
    assert game.release_reaction['kind']==expected
    reaction=game.release_reaction.copy()
    game.interact({'type':'hold-end'})
    assert game.release_reaction==reaction  # Release e cancel não duplicam uma reação.
    game.interact({'type':'caress'})
    assert game.release_reaction['until']<reaction['until']
    assert game.release_reaction['intensity']<reaction['intensity']


@pytest.mark.parametrize('sensor',[True,False])
@pytest.mark.parametrize('angry,elapsed,kind',[(.3,2.,'bravo'),(.9,5.,'birra')])
def test_soltar_bravo_encara_ponteiro_apesar_de_glance_e_respeita_sensor(tmp_path,monkeypatch,sensor,angry,elapsed,kind):
    clock=[100.];monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT);game.configure({'senseCursor':sensor})
    game.body.x,game.body.y=500,300;game.cursor=(700,300)
    game.behavior.glance=(300,300);game.behavior.next_glance=1e9
    game.interact({'type':'hold-start'})
    game.state.tone.r['ANGRY']=angry
    clock[0]+=elapsed;game.interact({'type':'hold-end'})
    assert game.release_reaction['kind']==kind
    game.last_think=clock[0]
    game.behavior.tick(.016,clock[0],game.cursor,game.bounds(),game.prof)
    assert game.state.gaze==(-1.,0.)
    clock[0]+=.016;game.tick(.016,clock[0])
    assert game.state.gaze==((1.,0.) if sensor else (-1.,0.))
    assert game.body.y>300 and game.body.vy>0


@pytest.mark.parametrize('event',[{'type':'hide','value':True},{'type':'panic'}])
def test_cancelamento_escondido_libera_pega_sem_reacao(tmp_path,event):
    game=Game(tmp_path,CONTENT)
    game.interact({'type':'hold-start'})
    game.interact(event)
    assert not game.body.held and game.held_since is None
    assert not game.state.pressing and not game.senses.dragging
    assert not game.release_reaction


@pytest.mark.parametrize('event',[{'type':'hide','value':True},{'type':'panic'}])
def test_esconder_tambem_cancela_pega_do_brinquedo(tmp_path,event):
    game=Game(tmp_path,CONTENT)
    game.interact(dict(type='drag-start',id=game.ball.id,x=500,y=300))
    game.interact(event)
    assert not game.ball.body.held and not game.ball.dragging
    assert game.ball.body.vx==game.ball.body.vy==game.ball.body.omega==0
    assert not game.ball.body.grounded


def test_aparencia_do_brinquedo_nao_substitui_corpo_ou_aprendizado(tmp_path):
    game=Game(tmp_path,CONTENT);body=game.ball.body
    game.brain.learned[0,0]=.04
    game.configure({'toyAppearance':'ball'})
    assert game.ball.appearance=='ball'
    game.configure({'toyAppearance':'peanut'})
    assert game.ball.appearance=='peanut' and game.ball.body is body
    assert game.brain.learned[0,0]==pytest.approx(.04)


@pytest.mark.parametrize('target',[None,'toy'])
def test_soltar_ignora_velocidade_antiga_e_cai_no_primeiro_tick_do_game(tmp_path,target,monkeypatch):
    clock=[100.];monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT)
    item=game.ball if target else None
    body=item.body if item else game.body
    event={'id':item.id} if item else {}
    body.vx,body.vy,body.omega=900,-800,250
    body.grounded=True;body.platform=55
    game.interact(dict(event,type='drag-start',x=500,y=300))
    assert body.held and body.vx==body.vy==body.omega==0
    game.interact(dict(event,type='drag-end',x=500,y=300,vx=1800,vy=-1500))
    assert not body.held and not body.grounded and body.platform is None
    assert body.vx==body.vy==body.omega==0
    before=body.y
    clock[0]+=.016;game.tick(.016,clock[0])
    assert body.y>before and body.vy>0
    assert body.x==500 and body.vx==body.omega==0
    assert game.senses.pulse['THROW']==0


def test_pegar_no_notebook_desprende_e_cai_sem_esperar_pensamento(tmp_path,monkeypatch):
    clock=[100.];monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT)
    game.mesa.decisao.at_desk=True
    game.mesa.ancora=(game.mesa.caderno.x(),game.mesa.caderno.y())
    game.mesa.caderno.set_working(True)
    game.state.at_desk=True;game.state.desk_top=game.mesa.caderno.y()
    game.body.x,game.body.y=500,300;game.body.grounded=True
    game.interact({'type':'hold-start'})
    assert not game.mesa.sentado and not game.state.at_desk and game.state.desk_top is None
    assert not game.mesa.caderno.working
    game.last_think=100
    clock[0]+=.016;game.tick(.016,clock[0])
    assert game.body.y==300 and game.body.held
    game.interact({'type':'hold-end'})
    clock[0]+=.016;game.tick(.016,clock[0])
    assert game.body.x==500 and game.body.y>300 and game.body.vy>0
    assert not game.mesa.sentado


def test_proximidade_atencao_sem_impulso_e_sem_repetir_todo_quadro(tmp_path):
    game=Game(tmp_path,CONTENT)
    game.configure({'senseCursor':True})
    game.cursor=(game.ball.body.x+10,game.ball.body.y)
    before=vars(game.ball.body).copy()
    game._sense_toy_cursor(100)
    assert game.cursor_toy_near and game.senses.pulse['NOVELTY']==pytest.approx(.35)
    assert vars(game.ball.body)==before
    assert game.behavior.look[:2]==(game.ball.body.x,game.ball.body.y)
    game._sense_toy_cursor(100.016)
    assert game.senses.pulse['NOVELTY']==pytest.approx(.35)
    game.cursor=(0,0);game._sense_toy_cursor(100.1)
    game.cursor=(game.ball.body.x,game.ball.body.y);game._sense_toy_cursor(100.2)
    assert game.senses.pulse['NOVELTY']==pytest.approx(.35)
    game.cursor=(0,0);game._sense_toy_cursor(103)
    game.cursor=(game.ball.body.x,game.ball.body.y);game._sense_toy_cursor(103.1)
    assert game.senses.pulse['NOVELTY']==pytest.approx(.7)


@pytest.mark.parametrize('disabled',['sensor','hidden','dragging','panel'])
def test_proximidade_nao_observa_brinquedo_quando_desativado(tmp_path,disabled):
    game=Game(tmp_path,CONTENT)
    game.cursor=(game.ball.body.x,game.ball.body.y)
    if disabled=='sensor':game.configure({'senseCursor':False})
    elif disabled=='hidden':game.interact({'type':'ball'})
    elif disabled=='dragging':game.ball.dragging=True
    else:game.panel=True
    game._sense_toy_cursor(100)
    assert not game.cursor_toy_near and game.senses.pulse['NOVELTY']==0


def test_cenas_de_brincadeira_vem_do_resultado_e_dos_motores(tmp_path):
    game=Game(tmp_path,CONTENT)
    game.behavior.last_play=dict(started=100.,action=None)
    game._play_expression(100)
    assert game.play_reaction['kind']=='bote_erro'
    game.behavior.last_play=dict(started=110.,action='kick')
    game._play_expression(110)
    assert game.play_reaction['kind']=='comemorando'
    game.body.grounded=True;game.next_play_scene=0
    game.mesa.decisao.at_desk=True;game.behavior.play_pull=0
    game._play_expression(120)
    assert game.play_reaction['started']==110
    game.behavior.play_pull=.7;game._play_expression(121)
    assert game.play_reaction['kind']=='fingir_trabalho'
    game._play_expression(122)
    assert game.play_reaction['started']==121
    game.mesa.decisao.at_desk=False;game.next_play_scene=0
    game.ball.body.x,game.ball.body.y=game.body.x+40,game.body.y
    game.state.tone.r['STARTLE']=.7;game._play_expression(130)
    assert game.play_reaction['kind']=='brinquedo_susto'
    game.state.tone.r['STARTLE']=0;game.next_play_scene=0
    game.behavior.adaptive_goal='play';game._play_expression(140)
    assert game.play_reaction['kind']=='preparar_bote'


def test_sinais_de_proximidade_chegam_a_rede_sem_chutar_brinquedo(tmp_path,monkeypatch):
    clock=[100.];monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT);kicks=[]
    monkeypatch.setattr(game.ball,'kick',lambda *args:kicks.append(args))
    game.ball.body.x,game.ball.body.y=game.body.x+30,game.body.y
    game.cursor=(game.ball.body.x,game.ball.body.y)
    before=vars(game.ball.body).copy();game._sense_toy_cursor(clock[0])
    clock[0]+=.1;game.think(.1,clock[0])
    assert game.inputs['NOVELTY']>0 and game.inputs['TOY_NEAR']>0
    assert game.brain.time_ms>0 and not kicks
    assert vars(game.ball.body)==before


@pytest.mark.parametrize('random_value,expected',[(0.,'comemorando'),(1.,'bote_erro')])
def test_play_real_continua_neural_e_gera_reacao_da_tentativa(tmp_path,monkeypatch,random_value,expected):
    import pestinha.body.brincadeira as play_module
    monkeypatch.setattr(play_module.random,'random',lambda:random_value)
    game=Game(tmp_path,CONTENT)
    game.body.x,game.body.y=600,400;game.body.grounded=True
    game.ball.body.x,game.ball.body.y=650,400
    game.behavior.emotion='feliz';game.behavior.play_pull=0
    game.behavior.next_roam=1e9
    before=vars(game.ball.body).copy()
    game.behavior.tick(.016,100,game.cursor,game.bounds(),game.prof)
    assert game.behavior.last_play is None and vars(game.ball.body)==before
    game.behavior.play_pull=1
    game.behavior.tick(.016,101,game.cursor,game.bounds(),game.prof)
    assert game.behavior.last_play['started']==101
    game._play_expression(101)
    assert game.play_reaction['kind']==expected
    if random_value==0:
        assert game.ball.body.vx>0 and game.ball.body.vy<0
    else:assert vars(game.ball.body)==before
