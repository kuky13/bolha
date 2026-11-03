# SPDX-License-Identifier: GPL-3.0-only
import json
import random
import time
import tracemalloc
from datetime import datetime, timedelta
from pathlib import Path
from intelligence import Habits, Intelligence, MAX_SLOTS
from pestinha.core.episodic import EpisodicMemory, KEEP_EPISODES, MAX_CONTEXTS
from game import Game

WALL = datetime(2026, 11, 3, 14).timestamp()

def memory_at(path):
    memory = EpisodicMemory(path/'events.jsonl', path/'preferences.json')
    memory.load()
    return memory

def test_silencio_neutro_carinho_positivo_dispensa_negativa(tmp_path):
    memory = memory_at(tmp_path)
    thing = object()
    episode = memory.start('IDLE|feliz', 'meme', thing)
    memory.tick(episode['inicio']+31, 30, 40)
    assert memory.recent[-1]['valencia'] == 0
    episode = memory.start('IDLE|feliz', 'meme', thing)
    memory.on_interaction()
    memory.tick(episode['inicio']+31, 30, 40)
    assert memory.recent[-1]['valencia'] > 0
    memory.start('IDLE|feliz', 'meme', thing)
    memory.on_dismiss(thing, 1., 30.)
    assert memory.recent[-1]['valencia'] < 0

def test_bandit_aprende_sem_superar_permissoes(tmp_path):
    memory = memory_at(tmp_path)
    for _ in range(25):
        memory._learn('ctx', 'goal:play', .8)
        memory._learn('ctx', 'goal:explore', -.8)
    random.seed(1313)
    choices = [memory.choose('ctx', ['goal:play', 'goal:explore'], .1) for _ in range(500)]
    assert choices.count('goal:play') > 440
    assert {memory.choose('ctx', ['goal:watch'], .1) for _ in range(50)} == {'goal:watch'}

def test_habitos_horario_decaimento_retencao_e_reabertura(tmp_path):
    habits = Habits(tmp_path/'habits.json')
    for _ in range(12): habits.observe('PROGRAMMING', True, False, WALL)
    assert habits.tendency('PROGRAMMING', WALL)['attention'] == 1
    assert habits.tendency('PROGRAMMING', WALL+3600)['attention'] == 0
    assert habits.tendency('PROGRAMMING', WALL+28*86400)['attention'] < .6
    for day in range(7):
        for hour in range(24):
            for activity in ('IDLE','AWAY','PROGRAMMING','DESIGNING','GAMING','BROWSING','SOCIAL','MUSIC'):
                stamp=(datetime(2026,11,2)+timedelta(days=day,hours=hour)).timestamp()
                habits.observe(activity, False, False, stamp)
    habits.save()
    assert len(habits.slots) == MAX_SLOTS
    assert len(Habits(habits.path).slots) == MAX_SLOTS
    assert habits.path.stat().st_size < 50000

def test_habitos_arquivo_corrompido_nao_interrompe(tmp_path):
    path=tmp_path/'habits.json'
    path.write_text('{broken')
    assert Habits(path).slots == {}
    path.write_text(json.dumps({'slots':{'0|1|IDLE':[3,99,0,1], '0|1|PROGRAMMING':[4,2,1,WALL]}}))
    assert list(Habits(path).slots) == ['0|1|PROGRAMMING']

def test_objetivo_persiste_e_interrompe_quando_nao_permitido(tmp_path):
    mind=Intelligence(memory_at(tmp_path), tmp_path/'habits.json', random.Random(3))
    pick=lambda now,allowed:mind.tick(now,WALL,'IDLE','feliz',{},.8,.3,allowed)
    goal=pick(100,['explore','watch'])
    assert goal in ('explore','watch')
    assert pick(105,['explore','watch']) == goal
    assert mind.decisions == 1
    assert pick(106,[]) is None
    assert mind.memory.recent[-1]['valencia'] == 0

def test_modo_compativel_e_desligamento(tmp_path):
    mind=Intelligence(memory_at(tmp_path), tmp_path/'habits.json')
    mind.tick(100,WALL,'IDLE','feliz',{},.8,.3,['play'])
    mind.enabled=False
    assert mind.tick(101,WALL,'IDLE','feliz',{},.8,.3,['play']) is None
    assert mind.goal is None
    mind.enabled=True
    mind.budget(101);mind.budget(101)
    assert not mind.compatibility
    mind.budget(90)
    assert mind.memory_strikes == 0
    mind.budget(101);mind.budget(101);mind.budget(101)
    assert mind.compatibility and mind.tick(200,WALL,'IDLE','feliz',{},.8,.3,['play']) is None

def test_desligar_rotina_remove_influencia_do_horario(tmp_path):
    mind=Intelligence(memory_at(tmp_path), tmp_path/'habits.json')
    mind.learn_routine=False
    mind.tick(100,WALL,'PROGRAMMING','feliz',{},.8,.3,['watch'])
    assert not mind.habits.slots
    assert mind.episode['contexto'] == 'objetivo|PROGRAMMING|feliz'

def test_episodios_ilegivel_e_linha_grande_sao_tolerados(tmp_path,monkeypatch):
    memory=memory_at(tmp_path)
    record=dict(id='1',quando='2026',contexto='IDLE|feliz',acao='meme',resultado='sem resposta',valencia=0.)
    memory.episodes_path.write_text('x'*100000+'\n'+json.dumps(record)+'\n')
    memory.dirty=False
    assert memory._read_episodes() == [record]
    original=Path.open
    def denied(path,*args,**kwargs):
        if path == memory.episodes_path: raise PermissionError('teste')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',denied)
    memory.load()
    assert memory.recent == []

def test_memoria_limitada_persistencia_em_lotes(tmp_path):
    memory=memory_at(tmp_path)
    for i in range(800):
        episode=memory.start(f'ctx{i}', 'goal:play')
        memory._resolve(episode,'carinho', .8)
    assert len(memory.recent) == KEEP_EPISODES
    assert len(memory.table) <= MAX_CONTEXTS
    assert not memory.episodes_path.exists()
    memory.save()
    reopened=memory_at(tmp_path)
    assert len(reopened.recent) == KEEP_EPISODES
    assert len(reopened.table) <= MAX_CONTEXTS
    assert reopened.estimate('ctx799','goal:play') > .5

def test_custo_incremental_limitado_em_simulacao_longa(tmp_path):
    tracemalloc.start()
    started=time.process_time()
    mind=Intelligence(memory_at(tmp_path), tmp_path/'habits.json', random.Random(3))
    for i in range(3000):
        mind.tick(i*40,WALL+i*40,'IDLE','feliz',{},.8,.3,['explore','play','watch'])
        if i%5==0: mind.feedback(.8,i*40)
    _, peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak < 8*1048576
    assert len(mind.memory.open) <= 12 and len(mind.memory.recent) <= KEEP_EPISODES
    # Margem para runners lentos; o benchmark separado informa CPU e RAM reais.
    assert time.process_time()-started < 15

def test_apagar_todo_aprendizado_preserva_preferencias(tmp_path):
    content=Path(__file__).resolve().parents[2]/'assets/bolha/content'
    game=Game(tmp_path, content)
    game.configure({'adaptiveBehavior':False,'learnRoutine':False,'avatarSize':152})
    game.brain.learned[0,0]=.05
    game.intelligence.habits.observe('IDLE', True, False, WALL)
    game.save()
    backup=game.pet_paths.nervous.with_name('nervous.json.corrompido')
    backup.write_text('aprendizado anterior')
    game.reset_learning()
    assert game.prefs['avatarSize'] == 152 and not game.intelligence.enabled
    assert not game.brain.learned.any()
    assert not game.intelligence.habits.slots and not game.memory.recent
    assert not backup.exists()
