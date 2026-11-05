# SPDX-License-Identifier: GPL-3.0-only
import sys
import time
import json
import pytest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from game import Game

CONTENT = Path(__file__).resolve().parents[2] / 'assets/bolha/content'

def test_memoria_legada_continua_no_caminho_original(tmp_path):
    import numpy as np
    game=Game(tmp_path,CONTENT)
    game.brain.learned[0,0]=.06
    game.save()
    legacy=tmp_path/'drippy'
    (tmp_path/'bolha').rename(legacy)  # Fixture da pasta usada pela versão 0.1.
    reopened=Game(tmp_path,CONTENT)
    assert reopened.pet_paths.base==legacy
    assert np.isclose(reopened.brain.learned[0,0],.06)
    reopened.brain.learned[0,0]=.08
    reopened.save()
    assert not (tmp_path/'bolha').exists()
    assert legacy.is_dir()
    assert np.isclose(Game(tmp_path,CONTENT).brain.learned[0,0],.08)
    reopened.reset_learning()
    assert reopened.pet_paths.base==legacy
    assert not np.any(reopened.brain.learned)
    assert not (tmp_path/'bolha').exists()
    backup=next((tmp_path/'backups').glob('learning-*/nervous.json'))
    saved=json.loads(backup.read_text(encoding='utf-8'))
    assert saved['seed']==1313
    assert np.isclose(saved['learned'][reopened.brain.sensory_names[0]][reopened.brain.plastic_posts[0]],.08)


def test_pasta_bolha_tem_preferencia_quando_ambas_existem(tmp_path):
    import numpy as np
    game=Game(tmp_path,CONTENT)
    game.brain.learned[0,0]=.03
    game.save()
    legacy=tmp_path/'drippy';legacy.mkdir()
    game.brain.learned[0,0]=.09
    game.brain.save(legacy/'nervous.json')
    before=(legacy/'nervous.json').read_bytes()
    reopened=Game(tmp_path,CONTENT)
    assert reopened.pet_paths.base==tmp_path/'bolha'
    assert np.isclose(reopened.brain.learned[0,0],.03)
    assert (legacy/'nervous.json').read_bytes()==before
    reopened.reset_learning()
    assert reopened.pet_paths.base==tmp_path/'bolha'
    assert not np.any(reopened.brain.learned)
    assert (legacy/'nervous.json').read_bytes()==before


def test_corpo_circular_tomba_e_arrasto_tem_prioridade(tmp_path):
    game=Game(tmp_path,CONTENT)
    game.body.grounded=True;game.body.surface=760;game.body.angle=90
    assert game.snapshot()['pose']=='lying'
    assert game.body.extents()==(68,68)
    game.interact({'type':'drag-start','x':500,'y':300})
    assert game.snapshot()['pose']=='held'
    assert not hasattr(game,'burst')

def test_pausar_passeio_preserva_olhar_sem_movimento(tmp_path):
    game=Game(tmp_path,CONTENT)
    game.body.grounded=True;game.body.vx=100
    game.behavior.look_at(game.body.x+200,game.body.y,100.)
    game.behavior.tick(.016,100.,game.cursor,game.bounds(),game.prof,[],False)
    assert game.state.gaze==(1.,0.)
    assert game.body.vx==0

def test_monitor_neural_somente_quando_solicitado(tmp_path,monkeypatch):
    clock=[100.];monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT)
    assert 'neural' not in game.snapshot()
    game.interact({'type':'monitor','value':True})
    assert len(game.snapshot()['neural']['positions'])==470
    assert 'neural' not in game.snapshot()
    clock[0]+=.26
    assert 'neural' in game.snapshot()
    game.interact({'type':'monitor','value':False})
    assert 'neural' not in game.snapshot()

def test_arremessos_repetidos_com_estouro_desligado(tmp_path):
    game=Game(tmp_path,CONTENT)
    game.configure({'popEnabled': False})
    for _ in range(30):
        game.interact(dict(type='drag-start',x=500,y=300))
        game.interact(dict(type='drag-end',x=500,y=300,vx=1800,vy=-1500))
        assert game.pet_visible() and game.pet_interactive()
    assert not hasattr(game,'media')

def throw_pet(game, vx=900., **options):
    game.interact(dict(type='drag-start', x=500, y=300))
    game.interact(dict(type='drag-end', x=500, y=300, vx=vx, **options))

def test_estouro_retorno_e_carinho_alimentam_o_cerebro(tmp_path,monkeypatch):
    clock=[100.]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT)
    game.configure({'senseApp':False, 'senseIdle':False, 'senseCursor':False, 'senseWindows':False})
    for _ in range(11):
        throw_pet(game)
        assert game.pet_interactive()
        clock[0]+=1.

    throw_pet(game)
    assert game.pet_visible() and not game.pet_interactive()
    assert game.senses.pulse['IMPACT']>0.
    assert game.pop_return_at-clock[0]==30.
    assert game.body.vx==game.body.vy==0.
    before=game.brain.time_ms
    clock[0]+=.7
    game.tick(.016)
    assert game.visible() and not game.pet_visible()
    assert game.brain.time_ms>before

    game.desktop({'areas':[dict(x=-1000,y=-100,width=1000,height=700,id=2,scaleFactor=1.5)]})
    clock[0]=game.pop_return_at-.02
    game.tick(.016)
    assert not game.pet_visible()
    clock[0]=game.pop_return_at
    game.tick(.016)
    assert game.pet_visible() and game.pet_interactive()
    left,_,right,bottom=game.bounds()
    assert min(game.body.x-left,right-game.body.x)==game.body.half_w+16.
    assert game.body.y+game.body.half_h==bottom
    assert game.release_reaction['kind']=='pop_return'
    assert game.state.emotion=='timido'
    end=game.release_reaction['until']
    game.interact({'type':'caress'})
    assert game.release_reaction['until']<end

def test_estouro_conta_so_arremessos_fortes_da_bolha_no_ultimo_minuto(tmp_path,monkeypatch):
    clock=[100.]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game=Game(tmp_path,CONTENT)
    game.configure({'popThrowLimit':5})
    for _ in range(4):
        throw_pet(game)
    clock[0]+=60.01
    for _ in range(4):
        throw_pet(game)
    throw_pet(game, vx=100.)
    throw_pet(game, cancelled=True)
    game.interact(dict(type='drag-end', x=500, y=300, vx=900.))
    game.interact(dict(type='drag-start', x=500, y=300, id=game.ball.id))
    game.interact(dict(type='drag-end', x=500, y=300, vx=900., id=game.ball.id))
    assert game.pet_interactive()
    throw_pet(game)
    assert not game.pet_interactive()

@pytest.mark.parametrize(('angle','kind'), [
    (0, 'pouso_em_pe'), (90, 'pouso_de_lado'), (-90, 'pouso_de_lado'),
    (180, 'pouso_invertido'),
])
def test_pouso_usa_a_orientacao_no_contato_com_o_chao(tmp_path,angle,kind):
    game=Game(tmp_path,CONTENT)
    game.configure({'senseApp':False, 'senseIdle':False, 'senseCursor':False, 'senseWindows':False,
                    'roaming':False, 'mischiefEnabled':False})
    left,_,right,bottom=game.bounds()
    game.body.x=(left+right)/2.
    game.body.y=bottom-game.body.half_h-3.
    game.body.angle=angle
    game.body.grounded=False
    game.body.vy=450.
    game.tick(.016,time.monotonic())
    assert game.landing_reaction['kind']==kind
    assert game.body.vy<0.

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
