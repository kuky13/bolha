# SPDX-License-Identifier: GPL-3.0-only
"""Expressões reais respeitam cérebro, relógio e a única autoridade física."""
from pathlib import Path
import random
import pytest
from game import Game
from bolha.motion import animation_pose, ExpressionMotion, QUIRK_SECONDS

CONTENT = Path(__file__).resolve().parents[2] / 'assets/bolha/content'


def game_at_rest(tmp_path):
    game = Game(tmp_path, CONTENT)
    game.body.grounded = True
    game.body.vx = game.body.vy = game.body.omega = 0
    return game


def test_segurar_irrita_aos_poucos_e_atividade_neural_modula_gesto(tmp_path):
    game = game_at_rest(tmp_path);motion = ExpressionMotion(100)
    before = vars(game.body).copy()
    early = motion.update(game, 100.1, 100)
    late = motion.update(game, 104.2, 100)
    assert early['emotion'] == 'curioso' and late['emotion'] == 'bravo'
    assert late['eye_open'] < early['eye_open'] and late['ear_raise'] < early['ear_raise']
    assert late['effect_strength'] > early['effect_strength']
    calm = ExpressionMotion(100).update(game, 102, 100)
    game.state.tone.r['ANGRY'] = 1
    irritated = ExpressionMotion(100).update(game, 102, 100)
    assert irritated['eye_open'] < calm['eye_open']
    assert irritated['effect_strength'] > calm['effect_strength']
    assert vars(game.body) == before


def test_adormecer_fecha_olhos_gradualmente_respira_e_so_entao_soltar_zzz(tmp_path):
    game = game_at_rest(tmp_path);motion = ExpressionMotion(100)
    game.sleep.asleep = True
    first = motion.update(game, 100)
    middle = motion.update(game, 100.9)
    asleep = motion.update(game, 102.1)
    breathe = motion.update(game, 103.1)
    assert first['eye_open'] > middle['eye_open'] > asleep['eye_open']
    assert first['zzz_strength'] == middle['zzz_strength'] == 0
    assert asleep['zzz_strength'] > 0 and asleep['emotion'] == 'dormindo'
    assert asleep['squash'] != breathe['squash']
    held = motion.update(game, 103.2, 103.2)
    assert held['zzz_strength'] == 0 and motion.mode == 'held'


def test_manias_variadas_tem_pausa_sem_repetir_e_cedem_as_interacoes(tmp_path):
    game = game_at_rest(tmp_path);motion = ExpressionMotion(100, random.Random(17))
    motion.next_wink = 1e9;seen = []
    for index in range(20):
        now = 100 + index * 10
        motion.next_quirk = now
        motion.update(game, now);seen.append(motion.mode)
        assert motion.mode in QUIRK_SECONDS
        motion.update(game, now + QUIRK_SECONDS[motion.mode] + .01)
        assert motion.quirk is None and motion.next_quirk > now + 30
    assert len(set(seen)) == len(QUIRK_SECONDS) - 1
    assert all(left != right for left, right in zip(seen, seen[1:]))
    motion.next_quirk = 500;motion.update(game, 500)
    assert motion.quirk is not None
    motion.update(game, 500.1, 500.1)
    assert motion.quirk is None and motion.mode == 'held'
    game.panel = True;motion.next_quirk = 501;motion.update(game, 501)
    assert motion.quirk is None


def test_reacao_de_soltura_vem_do_cerebro_e_carinho_tem_prioridade(tmp_path):
    game = game_at_rest(tmp_path);motion = ExpressionMotion(100)
    game.release_reaction = dict(kind='birra', started=100, until=104, intensity=.9)
    pose = motion.update(game, 100.4)
    assert motion.mode == 'birra' and pose['emotion'] == 'bravo'
    game.state.mark_caress(100.5)
    pose = motion.update(game, 100.6)
    assert motion.mode == 'caress' and pose['effect'] == 'carinho'
    game.state.feliz_ate = 0
    pose = motion.update(game, 105)
    assert motion.mode == game.state.emotion


def test_cena_comedia_vem_da_brincadeira_real_e_nao_escolhe_politica_na_view(tmp_path):
    game = game_at_rest(tmp_path);motion = ExpressionMotion(100)
    game.play_reaction = dict(kind='bote_erro', started=100, until=102, intensity=.9)
    assert motion.update(game, 100.6)['emotion'] == 'tonto'
    assert motion.mode == 'bote_erro'
    game.play_reaction = dict(kind='fingir_trabalho', started=101, until=103, intensity=.9)
    assert motion.update(game, 101.9)['emotion'] == 'atento'
    assert motion.mode == 'fingir_trabalho'
    assert motion.update(game, 104)['emotion'] == game.state.emotion


@pytest.mark.parametrize('reason',['ungrab','hidden'])
def test_cancelar_segurada_imovel_libera_corpo_e_hover(qt_application,tmp_path,reason):
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QEnterEvent, QMouseEvent
    from bolha.pet import PetWindow
    game = game_at_rest(tmp_path)
    game.configure({'senseCursor':False,'toyAppearance':'ball'})
    preferences = dict(game.prefs);pet = PetWindow(game)
    local = QPointF(pet.width()/2,pet.height()/2)
    position = QPointF(game.body.x,game.body.y)
    try:
        qt_application.sendEvent(pet,QEnterEvent(local,local,position))
        qt_application.sendEvent(pet,QMouseEvent(QEvent.MouseButtonPress,local,position,
                                                Qt.LeftButton,Qt.LeftButton,Qt.NoModifier))
        assert game.body.held and game.senses.dragging and not pet.dragging and game.hover
        qt_application.sendEvent(pet,QEvent(QEvent.Leave))
        assert game.hover
        if reason=='ungrab':
            qt_application.sendEvent(pet,QEvent(QEvent.UngrabMouse))
        else:
            game.interact({'type':'hide','value':True});pet.sync()
            game.interact({'type':'hide','value':False});pet.sync()
            assert pet.isVisible()
        assert not game.body.held and game.held_since is None and pet.press is None
        assert not game.hover and not game.state.pressing and not game.senses.dragging
        assert game.prefs == preferences
    finally:pet.close()


def test_soltar_apos_arrasto_herda_movimento_recente_sem_poke(qt_application,tmp_path,monkeypatch):
    import time
    from PySide6.QtCore import QPointF, Qt
    from types import SimpleNamespace
    from bolha.pet import PetWindow
    clock=[100.];monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    game = game_at_rest(tmp_path);pet = PetWindow(game);events=[]
    original=game.interact
    def interact(event):events.append(event.copy());return original(event)
    game.interact=interact
    def mouse(x,y):return SimpleNamespace(button=lambda:Qt.LeftButton,globalPosition=lambda:QPointF(x,y))
    try:
        game.body.vx,game.body.vy,game.body.omega=400,-500,300
        pet.mousePressEvent(mouse(game.body.x+8,game.body.y+9))
        clock[0]+=.08
        pet.mouseMoveEvent(mouse(game.body.x+128,game.body.y-71))
        position=(game.body.x,game.body.y)
        pet.mouseReleaseEvent(mouse(game.body.x+8,game.body.y+9))
        assert not game.body.held and not game.body.grounded
        assert (game.body.x,game.body.y)==position
        assert game.body.vx==pytest.approx(1500)
        assert game.body.vy==pytest.approx(-1000)
        assert game.body.omega==pytest.approx(525)
        assert [event['type'] for event in events]==['hold-start','drag-start','drag-end','hold-end']
        assert 'vx' in events[-2] and 'vy' in events[-2]
    finally:pet.close()


@pytest.mark.parametrize('mode', ['held', 'sleeping', 'caress', 'airborne', 'impact',
                                 'tonto', 'comemorando', 'birra', 'sacudir', 'preparar_bote',
                                 'bote_erro', 'brinquedo_susto', 'fingir_trabalho', *QUIRK_SECONDS])
def test_deformacoes_limitadas_e_sem_movimento_do_centro(mode):
    for frame in range(181):
        pose = animation_pose(mode, frame / 30)
        assert -.25 <= pose['squash'] <= .25
        assert 0 <= pose['eye_open'] <= 1.3
        assert 'x' not in pose and 'y' not in pose


def test_janela_visual_com_geleia_preserva_centro_e_mascara_fisica(qt_application,tmp_path):
    from bolha.pet import PetWindow
    game = game_at_rest(tmp_path);game.configure(dict(avatarSize=200))
    pet = PetWindow(game)
    try:
        assert pet.width() == pet.height() == 256
        assert pet.visual.width() == pet.visual.height() == 320
        assert pet.x() + pet.width() / 2 == pet.visual.x() + pet.visual.width() / 2 == game.body.x
        assert pet.y() + pet.height() / 2 == pet.visual.y() + pet.visual.height() / 2 == game.body.y
        mask = pet.mask()
        for t in (.5, 1, 1.4):
            pet.motion.pose = animation_pose('stretch', t)
            image = pet.visual.grab().toImage()
            assert all(image.pixelColor(x, 0).alpha() == image.pixelColor(x, 319).alpha() == 0 for x in range(320))
            assert all(image.pixelColor(0, y).alpha() == image.pixelColor(319, y).alpha() == 0 for y in range(320))
            assert pet.mask() == mask
    finally:pet.close()
