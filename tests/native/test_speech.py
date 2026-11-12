# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Falhas de fala, privacidade, repetição e limites reais da janela Qt."""
from pathlib import Path
import pytest
from PySide6.QtCore import QRectF, QPointF
from game import Game
from bolha.speech import Dialogue, LINES, SpeechWindow, bubble_path

CONTENT = Path(__file__).resolve().parents[2]/'assets/bolha/content'


def test_conteudo_tem_categorias_distintas_e_ampla_variedade():
    assert {'ambiente', 'casual', 'pensamento', 'bravo', 'carinho', 'brincando'} <= LINES.keys()
    lines = [line for category in LINES.values() for line in category]
    assert len(lines) >= 70
    assert len(lines) == len(set(lines))


def test_selecao_neural_elimina_repeticao_antes_de_esgotar_categoria(tmp_path):
    game = Game(tmp_path, CONTENT)
    dialogue = Dialogue()
    selected = [dialogue.choose(game, 'casual') for _ in range(len(LINES['casual']))]
    assert len(set(selected)) == len(selected)
    assert dialogue.choose(game, 'casual') != selected[-1]
    assert game.intelligence.history[-1]['source'] == 'local_dialogue_policy'


def test_reacoes_observam_acao_real_e_nao_repetem_por_quadro(tmp_path):
    game = Game(tmp_path, CONTENT)
    dialogue = Dialogue()
    dialogue.next_ambient = 1000.
    game.body.held = True
    result = dialogue.update(game, 100.)
    assert result[0] in LINES['segurando']
    for now in (100.016, 100.5, 103., 110.):
        assert dialogue.update(game, now) is None
    game.body.held = False
    game.state.mark_caress(111.)
    assert dialogue.update(game, 111.)[0] in LINES['carinho']


def test_politica_pode_escolher_silencio_e_categorias_ambiente_nao_repetem(tmp_path, monkeypatch):
    game = Game(tmp_path, CONTENT)
    dialogue = Dialogue()
    calls=[]
    def choose(action, candidates, **kwargs):
        calls.append((action, candidates))
        return 'silencio' if action == 'dialogue_intent' else candidates[0]
    monkeypatch.setattr(game.intelligence, 'choose', choose)
    assert dialogue.update(game, 100.) is None
    assert calls[0][0] == 'dialogue_intent'
    assert dialogue.next_ambient == 150.
    monkeypatch.setattr(game.intelligence, 'choose', lambda action, candidates, **kwargs: candidates[0])
    first = dialogue.update(game, 150.)
    assert first[0] in LINES['ambiente']
    second = dialogue.update(game, 200.)
    assert second[0] in LINES['casual']


@pytest.mark.parametrize('block', ['panel', 'hidden', 'panicked', 'quiet', 'fullscreen'])
def test_falas_ocultas_em_pausa_privacidade_ou_todas_telas_ocupadas(qt_application, tmp_path, block):
    game = Game(tmp_path, CONTENT)
    window = SpeechWindow(game)
    window.present('Teste local', now=100.)
    if block == 'fullscreen':
        game.blocked = {0}
    elif block == 'quiet':
        game.quiet_until = 120.
    else:
        setattr(game, block, True)
    window.sync(101.)
    assert not window.isVisible()
    assert window.until == 0.
    window.close()


@pytest.mark.parametrize('position', [(-1190., 80.), (-500., 80.), (-1190., 750.), (-500., 750.)])
def test_balao_acompanha_bolha_e_fica_na_area_util_negativa(qt_application, tmp_path, position):
    game = Game(tmp_path, CONTENT)
    game.areas = [(-1280., 0., 0., 800.)]
    game.monitors = list(game.areas)
    game.body.x, game.body.y = position
    window = SpeechWindow(game)
    window.dialogue.next_ambient = 1000.
    window.present('Meu cantinho acompanha minhas orelhas.', now=100.)
    window.sync(101.)
    geo = window.geometry()
    assert -1280 <= geo.left() < geo.right() <= 0
    assert 0 <= geo.top() < geo.bottom() <= 800
    first_x = window.x()
    game.body.x = -800.
    window.sync(102.)
    assert window.x() != first_x
    assert window.isVisible()
    window.sync(108.)
    assert not window.isVisible()
    window.close()


def test_entrada_e_saida_possuem_transicao_suave(qt_application, tmp_path):
    game = Game(tmp_path, CONTENT)
    window = SpeechWindow(game)
    window.dialogue.next_ambient = 1000.
    window.present('Oi, estou aqui.', now=100.)
    window.sync(100.11)
    assert .49 <= window.alpha <= .51
    window.sync(100.5)
    assert window.alpha == 1.
    window.sync(window.until-.15)
    assert .49 <= window.alpha <= .51
    window.close()


@pytest.mark.parametrize('thought', [False, True])
@pytest.mark.parametrize('tail_top', [False, True])
def test_silhueta_tem_ponta_de_fala_ou_pontos_de_pensamento(thought, tail_top):
    rect = QRectF(0, 0, 220, 90)
    path = bubble_path(rect, thought, anchor=110, tail_top=tail_top)
    bounds = path.boundingRect()
    assert rect.contains(bounds)
    assert path.contains(QPointF(110, 45))
    assert path.elementCount() > 20


def test_reacao_de_brincadeira_expirada_nao_dispara_fala(tmp_path):
    game = Game(tmp_path, CONTENT)
    dialogue = Dialogue()
    dialogue.next_ambient = 1000.
    game.play_reaction = dict(kind='brinquedo_perseguindo', until=99.)
    assert dialogue.update(game, 100.) is None
    game.play_reaction['until'] = 105.
    assert dialogue.update(game, 101.)[0] in LINES['brincando']


def test_desligar_travessuras_impede_fala_ambiente_mas_preserva_carinho(tmp_path):
    game = Game(tmp_path, CONTENT)
    game.configure({'mischiefEnabled': False})
    dialogue = Dialogue()
    assert dialogue.update(game, 100.) is None
    assert dialogue.update(game, 200.) is None
    game.state.mark_caress(201.)
    assert dialogue.update(game, 201.)[0] in LINES['carinho']
