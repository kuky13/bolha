# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Reações online (memes e GIFs) em memória, sem credenciais e sem gravar arquivos."""
from collections import deque
from dataclasses import dataclass, replace
from html import unescape
from html.parser import HTMLParser
import json
import queue
import random
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


USER_AGENT = 'Bolha (https://github.com/kuky13/bolha)'
REACTIONGIFS_API = 'https://www.reactiongifs.com/wp-json/wp/v2/posts'
NEKOS_API = 'https://nekos.best/api/v2'
REACTIONGIFS_HOSTS = frozenset(('reactiongifs.com', 'www.reactiongifs.com'))
NEKOS_HOSTS = frozenset(('nekos.best', 'www.nekos.best'))

TIMEOUT_SECONDS = 3.0
MAX_JSON_BYTES = 256 * 1024
MAX_MEDIA_BYTES = 6 * 1024 * 1024
MAX_TOTAL_MEDIA_BYTES = 18 * 1024 * 1024
MAX_IMAGE_SIDE = 2048
MAX_IMAGE_PIXELS = 2048 * 2048
MAX_ANIMATION_FRAMES = 240
MAX_PENDING_JOBS = 4
MIN_REQUEST_INTERVAL = 1.0

INTENT_KEYWORDS = {
    'bravo': ('angry', 'mad', 'rage'),
    'triste': ('sad', 'crying'),
    'feliz': ('happy', 'celebrate', 'excited'),
    'contente': ('happy', 'hug', 'smile'),
    'curioso': ('confused', 'thinking'),
    'observando': ('waiting', 'watching', 'bored'),
    'assustado': ('shocked', 'scared', 'surprised'),
    'dramatico': ('dramatic', 'crying', 'tableflip'),
    'dormindo': ('sleep', 'tired'),
    'sonolento': ('sleep', 'yawn'),
    'entediado': ('bored', 'waiting'),
    'timido': ('blush',),
    'atento': ('watching', 'thinking'),
    'travesso': ('laugh', 'smug'),
    'comemorando': ('celebrate', 'happy'),
    'trabalho': ('working', 'typing', 'tired'),
}

NEKOS_CATEGORIES = {
    'bravo': ('angry', 'pout', 'tableflip'),
    'triste': ('cry',),
    'feliz': ('happy', 'laugh'),
    'contente': ('happy', 'hug', 'smile'),
    'curioso': ('think', 'shrug'),
    'observando': ('bored', 'stare', 'think'),
    'assustado': ('shocked', 'nope'),
    'dramatico': ('cry', 'tableflip', 'pout'),
    'dormindo': ('sleep',),
    'sonolento': ('sleep', 'yawn'),
    'entediado': ('bored', 'yawn'),
    'timido': ('blush',),
    'atento': ('stare', 'think'),
    'travesso': ('laugh', 'smug'),
    'comemorando': ('happy', 'thumbsup'),
    'trabalho': ('bored', 'think', 'sleep'),
}

SAFE_KEYWORDS = frozenset(word for words in INTENT_KEYWORDS.values() for word in words)
SAFE_CATEGORIES = frozenset(cat for cats in NEKOS_CATEGORIES.values() for cat in cats)


@dataclass(frozen=True)
class ReactionCandidate:
    provider: str
    intent: str
    query: str
    title: str
    media_url: str
    source_url: str
    attribution: str


@dataclass(frozen=True)
class ReactionPayload:
    candidate: ReactionCandidate
    content_type: str
    data: bytes


def map_intent(emotion, kind='meme'):
    """Converte somente o rótulo interno de emoção/tipo em palavras públicas fixas."""
    key = 'trabalho' if kind == 'meme_trabalho' else str(emotion or 'observando').strip().lower()
    if key not in INTENT_KEYWORDS:
        key = 'observando'
    return key, INTENT_KEYWORDS[key], NEKOS_CATEGORIES.get(key, ('bored',))


def validate_reaction_url(url, allowed_hosts, upgrade_http=False):
    if not isinstance(url, str) or not url.strip():
        raise ValueError('URL de reação vazia.')
    parsed = urlsplit(url.strip())
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError('URL de reação com credenciais ou fragmento não permitida.')
    host = (parsed.hostname or '').lower()
    if host not in allowed_hosts:
        raise ValueError(f'Host não autorizado para reação: {host}')
    scheme = parsed.scheme.lower()
    if scheme == 'http' and upgrade_http:
        if parsed.port not in (None, 80, 443):
            raise ValueError('Porta não autorizada.')
        netloc = host
        return urlunsplit(('https', netloc, parsed.path, parsed.query, ''))
    if scheme != 'https' or parsed.port not in (None, 443):
        raise ValueError('URL de reação precisa usar HTTPS padrão.')
    return urlunsplit(('https', host, parsed.path, parsed.query, ''))


class _SafeHostRedirect(HTTPRedirectHandler):
    def __init__(self, allowed_hosts, upgrade_http=False):
        self.allowed_hosts = allowed_hosts
        self.upgrade_http = upgrade_http

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_url = validate_reaction_url(newurl, self.allowed_hosts, upgrade_http=self.upgrade_http)
        redirected = super().redirect_request(req, fp, code, msg, headers, safe_url)
        if redirected is not None:
            redirected.headers['User-Agent'] = USER_AGENT
        return redirected


class _ImgParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'img':
            return
        attr_map = {k.lower(): v for k, v in attrs if k and v}
        src = attr_map.get('src') or attr_map.get('data-src')
        if src:
            self.urls.append(src.strip())


def extract_reactiongifs_images(html_text):
    if not isinstance(html_text, str) or not html_text:
        return []
    parser = _ImgParser()
    parser.feed(html_text)
    parser.close()
    valid = []
    for raw in parser.urls:
        try:
            url = validate_reaction_url(raw, REACTIONGIFS_HOSTS, upgrade_http=True)
        except ValueError:
            continue
        path = urlsplit(url).path.lower()
        if path.endswith(('.gif', '.png', '.jpg', '.jpeg', '.webp')) and url not in valid:
            valid.append(url)
    return valid


def _clean_title(raw):
    if not isinstance(raw, str):
        return ''
    text = unescape(raw).replace('\r', ' ').replace('\n', ' ').strip()
    return text[:90]


def parse_reactiongifs_posts(payload_bytes, intent, keyword):
    try:
        posts = json.loads(payload_bytes.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('JSON inválido do ReactionGIFs.') from error
    if not isinstance(posts, list):
        raise ValueError('Formato inesperado do ReactionGIFs.')
    candidates = []
    needle = keyword.lower()
    for post in posts:
        if not isinstance(post, dict):
            continue
        link = post.get('link') or 'https://www.reactiongifs.com/'
        try:
            source_url = validate_reaction_url(link, REACTIONGIFS_HOSTS, upgrade_http=True)
        except ValueError:
            source_url = 'https://www.reactiongifs.com/'
        title_obj = post.get('title')
        title = _clean_title(title_obj.get('rendered', '') if isinstance(title_obj, dict) else '')
        content_obj = post.get('content')
        rendered = content_obj.get('rendered', '') if isinstance(content_obj, dict) else ''
        images = extract_reactiongifs_images(rendered)
        if not images:
            continue
        relevant = needle in title.lower() or needle in rendered.lower() or needle in source_url.lower()
        if not relevant:
            continue
        label = f'ReactionGIFs · {title}' if title else 'ReactionGIFs'
        candidates.append(ReactionCandidate(
            provider='reactiongifs',
            intent=intent,
            query=keyword,
            title=title or keyword.capitalize(),
            media_url=images[0],
            source_url=source_url,
            attribution=label,
        ))
    return candidates


def parse_nekos_results(payload_bytes, intent, category, available_endpoints=None):
    try:
        data = json.loads(payload_bytes.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('JSON inválido do Nekos.best.') from error
    if not isinstance(data, dict) or not isinstance(data.get('results'), list):
        raise ValueError('Formato inesperado do Nekos.best.')
    candidates = []
    for entry in data['results']:
        if not isinstance(entry, dict):
            continue
        raw_url = entry.get('url')
        try:
            media_url = validate_reaction_url(raw_url, NEKOS_HOSTS, upgrade_http=False)
        except ValueError:
            continue
        path = urlsplit(media_url).path.lower()
        if not path.endswith(('.gif', '.png', '.jpg', '.jpeg', '.webp')):
            continue
        anime = _clean_title(entry.get('anime_name') or entry.get('artist_name') or category)
        label = f'Nekos.best (anime) · {anime}' if anime else 'Nekos.best (anime)'
        source_url = media_url
        candidates.append(ReactionCandidate(
            provider='nekos.best',
            intent=intent,
            query=category,
            title=anime or category.capitalize(),
            media_url=media_url,
            source_url=source_url,
            attribution=label,
        ))
    return candidates


class ReactionTransport:
    def __init__(self, timeout=TIMEOUT_SECONDS):
        self.timeout = timeout

    def get_bytes(self, url, allowed_hosts, max_bytes, accept='application/json', upgrade_http=False):
        safe_url = validate_reaction_url(url, allowed_hosts, upgrade_http=upgrade_http)
        opener = build_opener(_SafeHostRedirect(allowed_hosts, upgrade_http=upgrade_http))
        request = Request(safe_url, headers={
            'User-Agent': USER_AGENT,
            'Accept': accept,
        })
        with opener.open(request, timeout=self.timeout) as response:
            final_url = validate_reaction_url(response.geturl(), allowed_hosts, upgrade_http=upgrade_http)
            status = getattr(response, 'status', 200)
            if status != 200:
                raise ValueError(f'Status HTTP inesperado: {status}')
            content_type = (response.headers.get('Content-Type') or '').split(';', 1)[0].strip().lower()
            declared = response.headers.get('Content-Length')
            if declared is not None:
                try:
                    if int(declared) > max_bytes:
                        raise ValueError('Payload excede o limite em RAM.')
                except ValueError as error:
                    if 'excede' in str(error):
                        raise
            chunks = []
            total = 0
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError('Payload excede o limite em RAM.')
                chunks.append(chunk)
        data = b''.join(chunks)
        if not data:
            raise ValueError('Resposta vazia.')
        return data, content_type, final_url


def validate_media_signature(data, content_type=''):
    if not isinstance(data, (bytes, bytearray)) or len(data) < 12 or len(data) > MAX_MEDIA_BYTES:
        raise ValueError('Bytes de mídia inválidos ou fora do limite.')
    head = bytes(data[:16])
    is_gif = head.startswith((b'GIF87a', b'GIF89a'))
    is_png = head.startswith(b'\x89PNG\r\n\x1a\n')
    is_jpg = head.startswith(b'\xff\xd8\xff')
    is_webp = head[:4] == b'RIFF' and head[8:12] == b'WEBP'
    if not (is_gif or is_png or is_jpg or is_webp):
        raise ValueError('Formato de imagem/GIF não suportado.')
    if content_type and not (content_type.startswith('image/') or content_type == 'application/octet-stream'):
        raise ValueError(f'Content-Type inválido para mídia: {content_type}')
    return 'gif' if is_gif else 'image'


class InMemoryMedia:
    """Mantém QByteArray/QBuffer/QMovie/QImage exclusivamente em RAM e libera no close()."""
    def __init__(self, payload: ReactionPayload, target_size=220):
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSize, Qt
        from PySide6.QtGui import QImage, QImageReader, QMovie
        kind = validate_media_signature(payload.data, payload.content_type)
        self.candidate = payload.candidate
        self.byte_size = len(payload.data)
        self.byte_array = QByteArray(payload.data)
        self.buffer = QBuffer(self.byte_array)
        if not self.buffer.open(QIODevice.ReadOnly):
            self.release()
            raise ValueError('Não foi possível abrir QBuffer em memória.')
        reader = QImageReader(self.buffer)
        size = reader.size()
        if size.isValid():
            if size.width() <= 0 or size.height() <= 0 or size.width() > MAX_IMAGE_SIDE or size.height() > MAX_IMAGE_SIDE:
                self.release()
                raise ValueError('Dimensões da imagem excedem o limite seguro.')
            if size.width() * size.height() > MAX_IMAGE_PIXELS:
                self.release()
                raise ValueError('Contagem de pixels excede o limite seguro.')
        self.buffer.seek(0)
        self.movie = None
        self.image = None
        self.animated = False
        self.frame_count = 1
        self.dimensions = (0, 0)
        self._bound = 0
        bound = max(64, min(320, int(target_size)))
        self._bound = bound
        if kind == 'gif':
            movie = QMovie(self.buffer, b'gif')
            movie.setCacheMode(QMovie.CacheNone)
            count = movie.frameCount()
            if count > MAX_ANIMATION_FRAMES:
                movie.stop()
                self.release()
                raise ValueError('GIF excede o limite de quadros.')
            if not movie.jumpToFrame(0):
                movie.stop()
                self.release()
                raise ValueError('GIF inválido.')
            first = movie.currentImage()
            if first.isNull() or first.width() > MAX_IMAGE_SIDE or first.height() > MAX_IMAGE_SIDE:
                movie.stop()
                self.release()
                raise ValueError('Quadro inicial do GIF inválido.')
            self.dimensions = (first.width(), first.height())
            self.frame_count = max(1, count)
            if count != 1:
                scale = min(1.0, bound / max(1, max(first.width(), first.height())))
                scaled = QSize(max(1, round(first.width() * scale)), max(1, round(first.height() * scale)))
                movie.setScaledSize(scaled)
                movie.start()
                self.movie = movie
                self.animated = True
            else:
                movie.stop()
                self.image = first.scaled(QSize(bound, bound), Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation) if max(first.width(), first.height()) > bound else first
                self.buffer.close()
                self.buffer = None
                self.byte_array = None
        else:
            img = QImage.fromData(self.byte_array)
            if img.isNull() or img.width() <= 0 or img.height() <= 0 or img.width() > MAX_IMAGE_SIDE or img.height() > MAX_IMAGE_SIDE:
                self.release()
                raise ValueError('Imagem estática inválida.')
            if img.width() * img.height() > MAX_IMAGE_PIXELS:
                self.release()
                raise ValueError('Imagem excede limite de pixels.')
            self.dimensions = (img.width(), img.height())
            if max(img.width(), img.height()) > bound:
                img = img.scaled(QSize(bound, bound), Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
            self.image = img
            self.buffer.close()
            self.buffer = None
            self.byte_array = None

    def current_image(self):
        if self.movie is not None:
            return self.movie.currentImage()
        return self.image

    def frame_number(self):
        if self.movie is not None:
            return self.movie.currentFrameNumber()
        return 0 if self.image is not None else -1

    def set_paused(self, paused: bool):
        if self.movie is not None:
            self.movie.setPaused(bool(paused))

    def set_target_size(self, target_size):
        """Redimensiona mídia em memória ao mudar escala, sem buscar novamente."""
        from PySide6.QtCore import QSize, Qt
        bound=max(64,min(320,int(target_size)))
        if bound==self._bound:return
        self._bound=bound
        width,height=self.dimensions
        if self.movie is not None and width and height:
            scale=min(1.,bound/max(width,height))
            self.movie.setScaledSize(QSize(max(1,round(width*scale)),max(1,round(height*scale))))
        elif self.image is not None and not self.image.isNull():
            scale=min(1.,bound/max(width,height,1))
            if scale<1.:
                self.image=self.image.scaled(QSize(max(1,round(width*scale)),max(1,round(height*scale))),
                                             Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)

    def release(self):
        if getattr(self, 'movie', None) is not None:
            try:
                self.movie.stop()
                self.movie.setDevice(None)
                self.movie.deleteLater()
            except RuntimeError:
                pass
            self.movie = None
        if getattr(self, 'buffer', None) is not None:
            try:
                self.buffer.close()
                self.buffer.deleteLater()
            except RuntimeError:
                pass
            self.buffer = None
        if getattr(self, 'byte_array', None) is not None:
            try:
                self.byte_array.clear()
            except RuntimeError:
                pass
            self.byte_array = None
        self.image = None
        self.animated = False


def fetch_reaction_payload(intent, kind='meme', transport=None, recent_urls=(), nekos_endpoints=None):
    """Busca candidato e bytes de mídia em ReactionGIFs e, se falhar, Nekos.best."""
    transport = transport or ReactionTransport()
    intent_key, keywords, categories = map_intent(intent, kind)
    keyword_list = [w for w in keywords if w in SAFE_KEYWORDS] or ['happy']
    # 1. ReactionGIFs (busca pública WordPress REST API)
    for keyword in keyword_list[:1]:
        api_url = (f'{REACTIONGIFS_API}?search={quote(keyword)}'
                   '&orderby=relevance&per_page=6&_fields=id,link,title,content')
        try:
            raw_json, content_type, _ = transport.get_bytes(
                api_url, REACTIONGIFS_HOSTS, MAX_JSON_BYTES, accept='application/json')
            candidates = parse_reactiongifs_posts(raw_json, intent_key, keyword)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            candidates = []
        fresh = [c for c in candidates if c.media_url not in recent_urls] or candidates
        if fresh:
            random.shuffle(fresh)
            for candidate in fresh[:2]:
                try:
                    media_bytes, media_type, final_media_url = transport.get_bytes(
                        candidate.media_url, REACTIONGIFS_HOSTS, MAX_MEDIA_BYTES,
                        accept='image/gif,image/*;q=0.9,*/*;q=0.5', upgrade_http=True)
                    validate_media_signature(media_bytes, media_type)
                    updated = replace(candidate, media_url=final_media_url)
                    return ReactionPayload(updated, media_type, media_bytes)
                except (HTTPError, URLError, TimeoutError, OSError, ValueError):
                    continue

    # 2. Nekos.best (fallback de categoria anime sem chave)
    cat_list = [c for c in categories if c in SAFE_CATEGORIES] or ['bored']
    if isinstance(nekos_endpoints, (set, frozenset)) and nekos_endpoints:
        filtered = [c for c in cat_list if c in nekos_endpoints]
        if filtered:
            cat_list = filtered
    # Some categories may be temporarily empty or unavailable. Use a known
    # GIF category as a final fallback in the same request.
    categories = list(dict.fromkeys([*cat_list[:2], 'happy']))
    last_error = None
    for category in categories:
        try:
            raw_json, _, _ = transport.get_bytes(f'{NEKOS_API}/{quote(category)}?amount=3',
                NEKOS_HOSTS, MAX_JSON_BYTES, accept='application/json')
            candidates = parse_nekos_results(raw_json, intent_key, category, nekos_endpoints)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            last_error = error
            continue
        fresh = [c for c in candidates if c.media_url not in recent_urls] or candidates
        random.shuffle(fresh)
        for candidate in fresh[:2]:
            try:
                media_bytes, media_type, final_media_url = transport.get_bytes(
                    candidate.media_url, NEKOS_HOSTS, MAX_MEDIA_BYTES,
                    accept='image/gif,image/*;q=0.9,*/*;q=0.5')
                validate_media_signature(media_bytes, media_type)
                updated = replace(candidate, media_url=final_media_url)
                return ReactionPayload(updated, media_type, media_bytes)
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
                last_error = error
    raise ValueError(f'Falha ao carregar reação online: {last_error}')


class OnlineReactionFetcher:
    """Fila limitada em segundo plano, consultada no ciclo já existente de NativeScene.sync()."""
    def __init__(self, transport=None, min_interval=MIN_REQUEST_INTERVAL):
        self.transport = transport or ReactionTransport()
        self.min_interval = min_interval
        self._lock = threading.Lock()
        self._queue = deque()
        self._active = set()
        self._cancelled = set()
        self._results = queue.SimpleQueue()
        self._recent_urls = deque(maxlen=16)
        self._stopped = False
        self._worker_running = False
        self._last_request = 0.0

    def submit(self, item_id, emotion, kind='meme'):
        item_id = str(item_id)
        with self._lock:
            if self._stopped or item_id in self._active:
                return False
            if any(job[0] == item_id for job in self._queue):
                return False
            if len(self._queue) + len(self._active) >= MAX_PENDING_JOBS:
                return False
            self._cancelled.discard(item_id)
            self._queue.append((item_id, str(emotion or 'observando'), str(kind or 'meme')))
            if not self._worker_running:
                self._worker_running = True
                threading.Thread(target=self._run, name='bolha-online-reactions', daemon=True).start()
            return True

    def cancel(self, item_id):
        item_id = str(item_id)
        with self._lock:
            self._cancelled.discard(item_id)
            self._queue = deque(job for job in self._queue if job[0] != item_id)
            if item_id in self._active:
                self._cancelled.add(item_id)
            self._discard_results_locked(item_id)

    def clear(self):
        with self._lock:
            self._queue.clear()
            self._cancelled.intersection_update(self._active)
            self._cancelled.update(self._active)
            self._discard_results_locked()

    def _discard_results_locked(self, item_id=None):
        kept = []
        while True:
            try:
                result = self._results.get_nowait()
            except queue.Empty:
                break
            if item_id is None or result[0] == item_id:
                continue
            kept.append(result)
        for result in kept:
            self._results.put(result)

    def stop(self):
        with self._lock:
            self._stopped = True
        self.clear()

    def poll(self):
        ready = []
        while True:
            with self._lock:
                try:
                    item_id, payload, error = self._results.get_nowait()
                except queue.Empty:
                    break
                if item_id in self._cancelled or self._stopped:
                    continue
            ready.append((item_id, payload, error))
        return ready

    def _run(self):
        while True:
            with self._lock:
                if self._stopped or not self._queue:
                    self._worker_running = False
                    return
                item_id, emotion, kind = self._queue.popleft()
                if item_id in self._cancelled:
                    self._cancelled.discard(item_id)
                    continue
                self._active.add(item_id)
                recent = tuple(self._recent_urls)
                wait = max(0.0, self.min_interval - (time.monotonic() - self._last_request))
            if wait > 0:
                time.sleep(min(wait, 1.5))
            with self._lock:
                if self._stopped or item_id in self._cancelled:
                    self._active.discard(item_id)
                    self._cancelled.discard(item_id)
                    continue
                self._last_request = time.monotonic()
            try:
                payload = fetch_reaction_payload(emotion, kind, transport=self.transport, recent_urls=recent)
                error = None
            except Exception as exc:
                payload = None
                error = str(exc)
            with self._lock:
                self._active.discard(item_id)
                if self._stopped or item_id in self._cancelled:
                    self._cancelled.discard(item_id)
                    continue
                if payload is not None:
                    self._recent_urls.append(payload.candidate.media_url)
                self._results.put((item_id, payload, error))
