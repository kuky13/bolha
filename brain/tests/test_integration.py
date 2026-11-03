# SPDX-License-Identifier: GPL-3.0-only
import sys
import time
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from game import Game, Burst

CONTENT = Path(__file__).resolve().parents[2] / 'assets/drippy/content'

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
    assert (tmp_path/'drippy/nervous.json').exists()

def test_panic_congela_simulacao_e_nao_reaparece_sozinha(tmp_path):
    game=Game(tmp_path,CONTENT)
    game.interact({'type':'panic'})
    before=game.brain.time_ms
    game.tick(.05,time.monotonic()+50)
    assert game.brain.time_ms==before
    assert not game.snapshot()['visible']

def test_monitores_negativos_e_remocao_recolocam_corpo(tmp_path):
    game=Game(tmp_path,CONTENT)
    game.desktop({'areas':[dict(x=-1000,y=0,width=1000,height=700,id=1,scaleFactor=1),dict(x=0,y=0,width=1200,height=800,id=2,scaleFactor=1.5)]})
    game.body.x=-500;game.body.y=500
    game.desktop({'areas':[dict(x=0,y=0,width=1200,height=800,id=2,scaleFactor=1.5)]})
    assert 0<=game.body.x<1200 and 0<=game.body.y<800

def test_memes_novos_e_objetos_sem_qt(tmp_path):
    game=Game(tmp_path,CONTENT)
    options=game.mischief.available('feliz',dict(travessuras=True,memes=True,bilhetes=True,fotos=False))
    assert 'meme' in options and 'bilhete' in options
    item=game.mischief._make('meme','feliz',False)
    assert item.valida and item.image=='carinho'
    assert 'PySide6' not in sys.modules
