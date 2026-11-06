# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Testes das reações online (ReactionGIFs e Nekos.best) exclusivamente em RAM."""
import json
from pathlib import Path
from types import SimpleNamespace
import time
import pytest
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QPoint, QPointF, Qt
from PySide6.QtGui import QImage, QMovie, QPainter

from game import Game
from pestinha import config
from bolha.dialogs import SettingsDialog
from bolha.preferences import PreferencesStore
from bolha.reactions import (
    InMemoryMedia, MAX_MEDIA_BYTES, NEKOS_HOSTS, OnlineReactionFetcher,
    REACTIONGIFS_HOSTS, ReactionCandidate, ReactionPayload, ReactionTransport,
    USER_AGENT, extract_reactiongifs_images, fetch_reaction_payload,
    map_intent, parse_nekos_results, parse_reactiongifs_posts,
    validate_media_signature, validate_reaction_url,
)
from bolha.scene import NativeScene, ObjectWindow

CONTENT = Path(__file__).resolve().parents[2] / 'assets/bolha/content'

# GIF89a sintético em memória com 2 quadros (2x2 pixels, vermelho e azul)
SYNTHETIC_TWO_FRAME_GIF = (
    b'GIF89a'
    b'\x02\x00\x02\x00\x91\x00\x00'
    b'\xff\x00\x00\x00\x00\xff\x00\xff\x00\x00\x00\x00'
    b'!\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00'
    b'!\xf9\x04\x04\x02\x00\x00\x00'
    b',\x00\x00\x00\x00\x02\x00\x02\x00\x00\x02\x02\x84Q\x00'
    b'!\xf9\x04\x04\x02\x00\x00\x00'
    b',\x00\x00\x00\x00\x02\x00\x02\x00\x00\x02\x02\x8cS\x00;'
)


def make_payload(provider='reactiongifs', intent='bravo', query='angry',
                 title='Fuming Angry', media_url='https://www.reactiongifs.com/r/fuming.gif',
                 source_url='https://www.reactiongifs.com/fuming-angry/',
                 data=SYNTHETIC_TWO_FRAME_GIF, content_type='image/gif'):
    candidate = ReactionCandidate(
        provider=provider,
        intent=intent,
        query=query,
        title=title,
        media_url=media_url,
        source_url=source_url,
        attribution=f'ReactionGIFs · {title}' if provider == 'reactiongifs' else f'Nekos.best (anime) · {title}',
    )
    return ReactionPayload(candidate=candidate, content_type=content_type, data=data)


class ImmediateFetcher:
    """Fetcher síncrono de teste que não faz chamadas reais de rede."""
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.submitted = []
        self.cancelled = []
        self.cleared = 0
        self.stopped = False
        self._ready = []

    def submit(self, item_id, emotion, kind='meme'):
        self.submitted.append((str(item_id), emotion, kind))
        if self.payload is not None or self.error is not None:
            self._ready.append((str(item_id), self.payload, self.error))
        return True

    def cancel(self, item_id):
        self.cancelled.append(str(item_id))
        self._ready = [r for r in self._ready if r[0] != str(item_id)]

    def clear(self):
        self.cleared += 1
        self._ready.clear()

    def stop(self):
        self.stopped = True
        self.clear()

    def poll(self):
        out = list(self._ready)
        self._ready.clear()
        return out


def test_mapeamento_de_intencao_usa_apenas_termos_publicos_sem_vazar_contexto():
    intent, keywords, categories = map_intent('bravo', 'meme')
    assert intent == 'bravo'
    assert 'angry' in keywords and 'angry' in categories
    # Qualquer string estranha cai em observando e nunca vai para a query
    secret = 'C:\\Users\\Alice\\DocumentoSecreto.docx chrome.exe 1920x1080'
    fallback_intent, fb_keywords, fb_categories = map_intent(secret, 'meme')
    assert fallback_intent == 'observando'
    assert all(secret not in w and 'Alice' not in w for w in fb_keywords + fb_categories)
    work_intent, work_kw, _ = map_intent('feliz', 'meme_trabalho')
    assert work_intent == 'trabalho' and 'working' in work_kw


def test_extracao_html_reactiongifs_e_allowlist_https():
    html = (
        '<p><img src="http://www.reactiongifs.com/r/2013/06/fuming-angry.gif" alt="Angry" />'
        '<img src="https://evil.example.com/steal.gif" />'
        '<script>alert(1)</script></p>'
    )
    urls = extract_reactiongifs_images(html)
    assert urls == ['https://www.reactiongifs.com/r/2013/06/fuming-angry.gif']
    with pytest.raises(ValueError):
        validate_reaction_url('http://nekos.best/api/v2/angry/001.gif', NEKOS_HOSTS, upgrade_http=False)
    with pytest.raises(ValueError):
        validate_reaction_url('https://reactiongifs.com.evil.example/a.gif', REACTIONGIFS_HOSTS)
    with pytest.raises(ValueError):
        validate_reaction_url('https://user:pass@www.reactiongifs.com/a.gif', REACTIONGIFS_HOSTS)


def test_parse_reactiongifs_e_fallback_nekos_com_stub_de_transporte():
    posts = [
        {
            'id': 25087,
            'link': 'https://www.reactiongifs.com/unrelated/',
            'title': {'rendered': 'Unrelated post'},
            'content': {'rendered': '<p><img src="https://www.reactiongifs.com/r/unrelated.gif"/></p>'},
        },
        {
            'id': 25088,
            'link': 'https://www.reactiongifs.com/fuming-angry/',
            'title': {'rendered': 'Fuming &amp; Angry'},
            'content': {'rendered': '<p><img src="http://www.reactiongifs.com/r/fuming.gif"/></p>'},
        }
    ]
    parsed = parse_reactiongifs_posts(json.dumps(posts).encode('utf-8'), 'bravo', 'angry')
    assert len(parsed) == 1
    assert parsed[0].title == 'Fuming & Angry'
    assert parsed[0].media_url == 'https://www.reactiongifs.com/r/fuming.gif'
    assert parsed[0].source_url == 'https://www.reactiongifs.com/fuming-angry/'

    irrelevant_only = [dict(posts[0])]
    assert parse_reactiongifs_posts(json.dumps(irrelevant_only).encode(), 'bravo', 'angry') == []

    # Simula falha no ReactionGIFs e sucesso no fallback Nekos.best
    calls = []
    class StubTransport:
        def get_bytes(self, url, allowed_hosts, max_bytes, accept='application/json', upgrade_http=False):
            calls.append(url)
            if 'reactiongifs.com' in url:
                raise OSError('ReactionGIFs temporariamente indisponível')
            if 'nekos.best/api/v2/' in url and url.endswith('.gif'):
                return SYNTHETIC_TWO_FRAME_GIF, 'image/gif', url
            nekos_json = {
                'results': [
                    {
                        'anime_name': 'K-On!',
                        'url': 'https://nekos.best/api/v2/angry/001.gif',
                        'dimensions': {'width': 2, 'height': 2},
                    }
                ]
            }
            return json.dumps(nekos_json).encode('utf-8'), 'application/json', url

    payload = fetch_reaction_payload('bravo', 'meme', transport=StubTransport())
    assert payload.candidate.provider == 'nekos.best'
    assert 'Nekos.best (anime)' in payload.candidate.attribution
    assert 'K-On!' in payload.candidate.attribution
    assert payload.data == SYNTHETIC_TWO_FRAME_GIF
    assert any('reactiongifs.com' in u for u in calls)
    assert any('nekos.best' in u for u in calls)


def test_limites_de_payload_assinatura_e_redirecionamento_bloqueado():
    with pytest.raises(ValueError):
        validate_media_signature(b'<html>not an image</html>', 'text/html')
    with pytest.raises(ValueError):
        validate_media_signature(b'GIF89a' + b'\x00' * (MAX_MEDIA_BYTES + 10), 'image/gif')
    with pytest.raises(ValueError):
        validate_media_signature(SYNTHETIC_TWO_FRAME_GIF, 'text/plain')


def test_qbuffer_qmovie_em_memoria_reproduz_pausa_e_libera_sem_arquivos(qt_application, tmp_path, monkeypatch):
    import tempfile
    monkeypatch.setattr(tempfile, 'NamedTemporaryFile', lambda *a, **kw: (_ for _ in ()).throw(AssertionError('NamedTemporaryFile proibido')))
    monkeypatch.setattr(tempfile, 'mkstemp', lambda *a, **kw: (_ for _ in ()).throw(AssertionError('mkstemp proibido')))

    payload = make_payload()
    media = InMemoryMedia(payload, target_size=180)
    assert media.animated and media.movie is not None
    assert media.movie.cacheMode() == QMovie.CacheNone
    assert media.dimensions == (2, 2)
    assert media.frame_count >= 2
    img0 = media.current_image()
    assert not img0.isNull()
    media.set_paused(True)
    assert media.movie.state() == QMovie.Paused
    media.set_paused(False)
    assert media.movie.state() == QMovie.Running
    media.release()
    assert media.movie is None and media.buffer is None and media.byte_array is None and media.image is None
    assert not list(tmp_path.iterdir())


def test_midia_retangular_preserva_proporcao_em_imagem_estatica_e_gif_unico(qt_application):
    image = QImage(400, 200, QImage.Format.Format_RGB32)
    image.fill(0xFF336699)
    encoded = QByteArray()
    buffer = QBuffer(encoded)
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, 'PNG')
    buffer.close()

    static_media = InMemoryMedia(make_payload(data=bytes(encoded), content_type='image/png'), target_size=100)
    assert static_media.image.width() == 100
    assert static_media.image.height() == 50
    static_media.release()

    one_frame_gif = SYNTHETIC_TWO_FRAME_GIF[:SYNTHETIC_TWO_FRAME_GIF.rfind(b'!\xf9\x04')] + b';'
    gif_media = InMemoryMedia(make_payload(data=one_frame_gif), target_size=100)
    assert gif_media.movie is None
    assert gif_media.image.width() == 2
    assert gif_media.image.height() == 2
    gif_media.release()


def test_janela_meme_exibe_midia_online_abre_origem_e_nao_desenha_placa_antiga(qt_application, tmp_path, monkeypatch):
    import bolha.character as char_module
    drawn_character = []
    orig_draw = char_module.draw_character
    monkeypatch.setattr(char_module, 'draw_character', lambda *a, **kw: (drawn_character.append(1), orig_draw(*a, **kw)))

    game = Game(tmp_path, CONTENT)
    fetcher = ImmediateFetcher(payload=make_payload())
    scene = NativeScene(game, reaction_fetcher=fetcher)
    item = game.mischief._make('meme', 'bravo', False)
    item.place(400, 300)
    game.mischief._add(item)
    scene.sync()

    window = scene.windows[item.id]
    assert window.isVisible()
    assert window.reaction_media is not None
    assert item.source_url == 'https://www.reactiongifs.com/fuming-angry/'
    assert 'Fuming Angry' in item.attribution

    # Renderiza em QImage para garantir que paintEvent desenha a mídia real e não a placa antiga com personagem
    canvas = QImage(window.width(), window.height(), QImage.Format_ARGB32_Premultiplied)
    canvas.fill(0)
    window.render(canvas)
    assert not drawn_character
    assert window.mask().boundingRect().width()==window.width()  # GIF ocupa a janela sem moldura ou rodapé
    assert canvas.pixelColor(0,0).alpha()>0

    # Snapshot do Game não vaza bytes de mídia
    snap = game.snapshot()
    snap_json = json.dumps(snap)
    assert 'GIF89a' not in snap_json

    # Menu de contexto oferece 'Guardar objeto' e 'Abrir origem'
    opened_urls = []
    import bolha.scene as scene_module
    monkeypatch.setattr(scene_module.QDesktopServices, 'openUrl', lambda qurl: (opened_urls.append(qurl.toString()), True)[1])

    class OpenSourceMenu:
        def __init__(self, parent):
            self.actions = {}
        def addAction(self, text):
            obj = object()
            self.actions[text] = obj
            return obj
        def exec(self, point):
            assert 'Guardar objeto' in self.actions
            assert 'Abrir origem' in self.actions
            assert 'ReactionGIFs · Fuming Angry' in self.actions
            assert len(self.actions) == 3
            return self.actions['Abrir origem']

    monkeypatch.setattr(scene_module, 'QMenu', OpenSourceMenu)
    window.contextMenuEvent(SimpleNamespace(globalPos=lambda: QPoint(400, 300)))
    assert opened_urls == ['https://www.reactiongifs.com/fuming-angry/']
    assert not item.closed

    # Esconder/fechar libera mídia
    scene.close()
    assert window.reaction_media is None


def test_falha_offline_ou_sem_resultado_descarta_sem_placa_antiga_e_sem_penalizar_cerebro(qt_application, tmp_path):
    game = Game(tmp_path, CONTENT)
    game.configure(dict(maxObjects=1))
    fetcher = ImmediateFetcher(payload=None, error='offline')
    scene = NativeScene(game, reaction_fetcher=fetcher)

    item = game.mischief._make('meme', 'feliz', False)
    item.place(400, 300)
    game.mischief._add(item)
    game.memory.start('IDLE|feliz', 'meme', item)

    # Sincroniza: a falha de rede deve abortar o item silenciosamente
    scene.sync()
    assert item.closed
    assert item not in game.mischief.things
    assert item.id not in game.objects
    assert item.id not in scene.windows
    # Não penalizou o cérebro como dispensa do usuário
    assert not game.mischief_ctl.dismiss_times
    assert game.mischief_ctl.penalty_until == 0.0
    assert not any(ep['thing'] is item for ep in game.memory.open)
    assert not any(r['acao'] == 'meme' and r['valencia'] < 0 for r in game.memory.recent)
    # Limite de objetos foi liberado imediatamente
    game.mischief.last_act = -1e9
    perms = dict(config.DEFAULT_PERMISSIONS, travessuras=True, memes=True, online_reactions=True)
    assert game.mischief.allowed(perms, game.prof, False)
    scene.close()


def test_preferencia_online_reactions_desligada_impede_requisicoes_e_limpa_memes_ativos(qt_application, tmp_path, monkeypatch):
    game = Game(tmp_path, CONTENT)
    fetcher = ImmediateFetcher(payload=make_payload())
    scene = NativeScene(game, reaction_fetcher=fetcher)

    item = game.mischief._make('meme', 'curioso', False)
    item.place(400, 300)
    game.mischief._add(item)
    note = game.mischief._make('bilhete', 'curioso', False)
    note.place(250, 300)
    game.mischief._add(note)
    scene.sync()
    assert item.id in scene.windows and scene.windows[item.id].reaction_media is not None
    assert note.id in scene.windows

    # Desliga reações online: remove meme ativo, preserva bilhete e não faz novas requisições
    game.configure(dict(onlineReactions=False))
    scene.sync()
    assert item.closed and item not in game.mischief.things
    assert not note.closed and note in game.mischief.things
    perms = dict(config.DEFAULT_PERMISSIONS, travessuras=True, memes=False, online_reactions=False, bilhetes=True)
    options = game.mischief.available('feliz', perms)
    assert 'meme' not in options and 'bilhete' in options
    assert game.mischief._make('meme', 'feliz', False) is None
    scene.close()


def test_job_atrasado_apos_fechamento_ou_panico_e_descartado_sem_vazar_ram(qt_application, tmp_path):
    game = Game(tmp_path, CONTENT)
    delayed = ImmediateFetcher()
    scene = NativeScene(game, reaction_fetcher=delayed)

    item = game.mischief._make('meme', 'bravo', False)
    item.place(400, 300)
    game.mischief._add(item)
    scene.sync()
    # Ainda carregando: janela existe mas não está visível
    assert item.id in scene.windows
    assert not scene.windows[item.id].isVisible()

    # Usuário fecha/dispensa ou entra em pânico antes do download terminar
    game.interact(dict(type='panic'))
    scene.sync()
    assert item.closed or item.id not in scene.windows

    # Chega resultado atrasado na fila: deve ser ignorado sem criar janela nem mídia
    delayed._ready.append((str(item.id), make_payload(), None))
    scene.sync()
    assert scene._total_media_bytes() == 0
    scene.close()


def test_worker_assincrono_real_processa_sem_bloquear_ui(qt_application, tmp_path):
    class StubTransport:
        def get_bytes(self, url, allowed_hosts, max_bytes, accept='application/json', upgrade_http=False):
            if 'wp-json' in url:
                posts = [{
                    'id': 25088,
                    'link': 'https://www.reactiongifs.com/fuming-angry/',
                    'title': {'rendered': 'Fuming Angry'},
                    'content': {'rendered': '<img src="https://www.reactiongifs.com/r/fuming.gif"/>'},
                }]
                return json.dumps(posts).encode('utf-8'), 'application/json', url
            return SYNTHETIC_TWO_FRAME_GIF, 'image/gif', url

    fetcher = OnlineReactionFetcher(transport=StubTransport(), min_interval=0.0)
    game = Game(tmp_path, CONTENT)
    scene = NativeScene(game, reaction_fetcher=fetcher)
    try:
        item = game.mischief._make('meme', 'bravo', False)
        item.place(400, 300)
        game.mischief._add(item)
        t0 = time.perf_counter()
        scene.sync()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert elapsed_ms < 50  # sync() nunca bloqueia esperando o worker
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            scene.sync()
            if item.id in scene.windows and scene.windows[item.id].reaction_media is not None:
                break
            time.sleep(0.01)
        assert scene.windows[item.id].reaction_media is not None
        assert scene.windows[item.id].isVisible()
    finally:
        scene.close()


def test_cancelamento_worker_bloqueado_limpa_tombstones_e_descarta_payload_tardio(monkeypatch):
    import threading
    import bolha.reactions as reactions

    started = threading.Event()
    finish = threading.Event()
    payload = make_payload()

    def blocking_fetch(*args, **kwargs):
        started.set()
        assert finish.wait(2.0)
        return payload

    monkeypatch.setattr(reactions, 'fetch_reaction_payload', blocking_fetch)
    fetcher = OnlineReactionFetcher(min_interval=0.0)
    assert fetcher.submit('active-id', 'bravo')
    assert started.wait(1.0)
    fetcher.cancel('active-id')
    for index in range(5000):
        fetcher.cancel(f'closed-{index}')
    assert len(fetcher._cancelled) == 1

    finish.set()
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and fetcher._active:
        time.sleep(0.005)
    assert fetcher._active == set()
    assert fetcher._cancelled == set()
    assert fetcher.poll() == []
    fetcher.stop()

