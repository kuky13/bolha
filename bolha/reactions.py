# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Reações locais offline em memória, geradas proceduralmente sob GPL-3.0-or-later."""
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
import math
from functools import lru_cache
import queue
import random
import struct
import threading


LOCAL_PROVIDER_ID = 'local'
LOCAL_ORIGIN = 'local-procedural'
LOCAL_AUTHOR = 'André Ribeiro Lima (KukySolutions)'
LOCAL_LICENSE_SPDX = 'GPL-3.0-or-later'
APPROVED_REACTION_LICENSES = frozenset((LOCAL_LICENSE_SPDX, 'CC0-1.0', 'CC-BY-4.0', 'CC-BY-SA-4.0'))

MAX_MEDIA_BYTES = 6 * 1024 * 1024
MAX_TOTAL_MEDIA_BYTES = 18 * 1024 * 1024
MAX_IMAGE_SIDE = 2048
MAX_IMAGE_PIXELS = 2048 * 2048
MAX_ANIMATION_FRAMES = 240
MAX_PENDING_JOBS = 4

LOCAL_REACTIONS = {
    'bravo': (
        ('greve', 'AVISO: BOLHA EM GREVE', 10, 'angry'),
        ('bico', 'NADA DE BOLINHA AGORA', 10, 'angry'),
    ),
    'triste': (
        ('nuvem', 'HOJE ACORDEI MEIO NUBLADA', 11, 'sad'),
        ('garoa', 'ACEITO UM CARINHO', 11, 'sad'),
    ),
    'feliz': (
        ('carinho', 'EU DEPOIS DE UM CARINHO', 9, 'happy'),
        ('brilho', 'ENERGIA BOA NO TALO', 9, 'happy'),
    ),
    'contente': (
        ('paz', 'ZERO ABAS NA MINHA CABEÇA', 8, 'calm'),
        ('leve', 'TUDO EM PAZ POR AQUI', 9, 'calm'),
    ),
    'curioso': (
        ('bug', 'SÓ VIM VER O QUE TÁ ROLANDO', 12, 'curious'),
        ('radar', 'ACHEI ALGO INTERESSANTE', 12, 'curious'),
    ),
    'observando': (
        ('cafe', 'SÓ MAIS CINCO MINUTINHOS', 8, 'watch'),
        ('vigia', 'TÔ DE OLHO DAQUI', 8, 'watch'),
    ),
    'assustado': (
        ('arremesso', 'EU NÃO SOU BOLINHA DE TÊNIS', 14, 'shocked'),
        ('susto', 'OPA! QUE SUSTO FOI ESSE', 14, 'shocked'),
    ),
    'dramatico': (
        ('drama', 'DRAMA EM 470 NEURÔNIOS', 13, 'dramatic'),
        ('suspiro', 'NINGUÉM COMPREENDE A BOLHA', 13, 'dramatic'),
    ),
    'dormindo': (
        ('soneca', 'MODO ECONOMIA DE ENERGIA', 11, 'sleep'),
        ('zzz', 'CARREGANDO BATERIA LOCAL', 14, 'sleep'),
    ),
    'sonolento': (
        ('bocejo', 'QUASE DORMINDO NO CANTO', 11, 'sleepy'),
        ('cochilo', 'OLHO FECHANDO SOZINHO', 14, 'sleepy'),
    ),
    'entediado': (
        ('tedio', 'ESPERANDO ALGO ACONTECER', 14, 'bored'),
        ('espera', 'CADÊ A BOLINHA?', 8, 'bored'),
    ),
    'timido': (
        ('corada', 'VOLTEI DEVAGARINHO', 15, 'shy'),
        ('canto', 'TÔ AQUI NO CANTINHO', 13, 'shy'),
    ),
    'atento': (
        ('foco', 'ATENÇÃO TOTAL NA TELA', 12, 'alert'),
        ('sinal', 'REDE NEURAL EM ALERTA', 8, 'alert'),
    ),
    'travesso': (
        ('arte', 'APRONTEI DE NOVO', 10, 'mischief'),
        ('sorriso', 'NÃO FUI EU', 8, 'mischief'),
    ),
    'comemorando': (
        ('festa', 'CONFETE LOCAL LIBERADO', 8, 'celebrate'),
        ('vitoria', 'MERECE COMEMORAÇÃO', 9, 'celebrate'),
    ),
    'trabalho': (
        ('codigo', 'TRABALHANDO NO NOTEBOOK', 14, 'work'),
        ('deploy', 'COMPILANDO IDEIAS LOCAIS', 12, 'work'),
    ),
}

# Paleta fixa de 16 cores (RGB) para GIF89a procedural sob GPL-3.0-or-later.
_PALETTE = (
    (0x11, 0x11, 0x16),  # 0 fundo escuro
    (0x23, 0x1f, 0x33),  # 1 moldura
    (0x1c, 0x1c, 0x26),  # 2 corpo interno
    (0x32, 0x30, 0x42),  # 3 brilho do corpo
    (0xe2, 0x45, 0xac),  # 4 anel magenta
    (0x78, 0x8e, 0xf2),  # 5 anel transição
    (0x00, 0xe1, 0xff),  # 6 anel ciano
    (0xee, 0xea, 0xf5),  # 7 branco suave
    (0xfe, 0xc8, 0x33),  # 8 dourado Bolha
    (0x43, 0xd9, 0xa3),  # 9 verde menta
    (0xf2, 0x72, 0x66),  # 10 coral
    (0x72, 0xa6, 0xf4),  # 11 azul
    (0x29, 0xd8, 0xec),  # 12 ciano
    (0xdb, 0x8f, 0xff),  # 13 lavanda
    (0xb0, 0xa0, 0xff),  # 14 lilás
    (0xf5, 0x93, 0xb8),  # 15 rosa rubor
)

@dataclass(frozen=True)
class ReactionCandidate:
    provider: str
    intent: str
    query: str
    title: str
    media_url: str
    source_url: str
    attribution: str
    origin: str
    author: str
    license_spdx: str
    commercial_verified: bool


@dataclass(frozen=True)
class ReactionPayload:
    candidate: ReactionCandidate
    content_type: str
    data: bytes


class ReactionProvider(ABC):
    """Contrato obrigatório para qualquer provedor de reações da Bolha."""

    provider_id: str
    origin: str
    author: str
    license_spdx: str
    commercial_verified: bool

    @abstractmethod
    def fetch(self, intent, kind='meme', recent_urls=()):
        """Retorna um ReactionPayload validado para a intenção informada."""


def validate_provider_contract(provider, *, require_commercial_verified=True):
    """Exige metadados explícitos de procedência, autoria, licença SPDX e verificação comercial."""
    if provider is None:
        raise ValueError('Provedor de reações ausente.')
    for field in ('origin', 'author', 'license_spdx'):
        value = getattr(provider, field, None)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'Contrato do provedor inválido: {field} ausente ou vazio.')
    if provider.license_spdx not in APPROVED_REACTION_LICENSES:
        raise ValueError('Licença não aprovada para reações da Bolha.')
    verified = getattr(provider, 'commercial_verified', None)
    if type(verified) is not bool:
        raise ValueError('Contrato do provedor inválido: commercial_verified deve ser booleano.')
    if require_commercial_verified and not verified:
        raise ValueError('Provedor de reações sem verificação comercial.')
    return True


def validate_candidate_contract(candidate, *, require_commercial_verified=True):
    """Garante que o candidato carregue procedência, autoria, licença e flag booleana válida."""
    if not isinstance(candidate, ReactionCandidate):
        raise ValueError('Candidato de reação inválido.')
    validate_provider_contract(candidate, require_commercial_verified=require_commercial_verified)
    return True


def map_intent(emotion, kind='meme'):
    key = 'trabalho' if kind == 'meme_trabalho' else str(emotion or '').strip().lower()
    return key if key in LOCAL_REACTIONS else 'observando'


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


def _lzw_encode(pixels, min_code_size=4):
    clear = 1 << min_code_size
    eoi = clear + 1
    code_size = min_code_size + 1
    max_code = (1 << code_size) - 1
    next_code = eoi + 1
    table = {(i,): i for i in range(clear)}

    bit_buffer = 0
    bit_count = 0
    out = bytearray()

    def emit(code):
        nonlocal bit_buffer, bit_count
        bit_buffer |= code << bit_count
        bit_count += code_size
        while bit_count >= 8:
            out.append(bit_buffer & 0xFF)
            bit_buffer >>= 8
            bit_count -= 8

    emit(clear)
    seq = ()
    for pixel in pixels:
        cand = seq + (pixel,)
        if cand in table:
            seq = cand
        else:
            emit(table[seq])
            if next_code <= 4095:
                table[cand] = next_code
                next_code += 1
                if next_code - 1 > max_code and code_size < 12:
                    code_size += 1
                    max_code = (1 << code_size) - 1
            else:
                emit(clear)
                table = {(i,): i for i in range(clear)}
                code_size = min_code_size + 1
                max_code = (1 << code_size) - 1
                next_code = eoi + 1
            seq = (pixel,)
    if seq:
        emit(table[seq])
    emit(eoi)
    if bit_count > 0:
        out.append(bit_buffer & 0xFF)

    blocks = bytearray([min_code_size])
    pos = 0
    while pos < len(out):
        chunk = out[pos:pos + 255]
        blocks.append(len(chunk))
        blocks.extend(chunk)
        pos += len(chunk)
    blocks.append(0)
    return bytes(blocks)


def _encode_gif(width, height, frames, delay_cs=16):
    header = bytearray(b'GIF89a')
    header.extend(struct.pack('<HHBBB', width, height, 0x83, 0, 0))
    for r, g, b in _PALETTE:
        header.extend((r, g, b))
    # Loop infinito NETSCAPE2.0
    header.extend(b'\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00')
    for pixels in frames:
        header.extend(b'\x21\xf9\x04\x09')
        header.extend(struct.pack('<HBB', delay_cs, 0, 0))
        header.extend(b'\x2c')
        header.extend(struct.pack('<HHHHB', 0, 0, width, height, 0))
        header.extend(_lzw_encode(pixels, 4))
    header.append(0x3B)
    return bytes(header)


def _fill_rounded_rect(buf, w, h, x0, y0, x1, y1, radius, color):
    x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(w, int(x1)), min(h, int(y1))
    r2 = radius * radius
    for y in range(y0, y1):
        row = y * w
        dy = (y0 + radius - 0.5 - y) if y < y0 + radius else (y - (y1 - radius - 0.5)) if y >= y1 - radius else 0
        if dy:
            dx = math.isqrt(max(0, int(r2 - dy * dy)))
            lx = max(x0, int(x0 + radius - dx))
            rx = min(x1, int(x1 - radius + dx))
        else:
            lx, rx = x0, x1
        if rx > lx:
            buf[row + lx:row + rx] = bytes((color,)) * (rx - lx)


def _fill_circle(buf, w, h, cx, cy, r, color):
    r2 = r * r
    y0 = max(0, int(math.floor(cy - r)))
    y1 = min(h, int(math.ceil(cy + r)) + 1)
    for y in range(y0, y1):
        dy = y - cy
        rem = r2 - dy * dy
        if rem < 0:
            continue
        dx = math.sqrt(rem)
        lx = max(0, int(math.ceil(cx - dx)))
        rx = min(w, int(math.floor(cx + dx)) + 1)
        if rx > lx:
            row = y * w
            buf[row + lx:row + rx] = bytes((color,)) * (rx - lx)


def _fill_ellipse(buf, w, h, cx, cy, rx, ry, color):
    if rx <= 0 or ry <= 0:
        return
    y0 = max(0, int(math.floor(cy - ry)))
    y1 = min(h, int(math.ceil(cy + ry)) + 1)
    for y in range(y0, y1):
        dy = (y - cy) / ry
        rem = 1.0 - dy * dy
        if rem < 0:
            continue
        span = rx * math.sqrt(rem)
        lx = max(0, int(math.ceil(cx - span)))
        rx_i = min(w, int(math.floor(cx + span)) + 1)
        if rx_i > lx:
            row = y * w
            buf[row + lx:row + rx_i] = bytes((color,)) * (rx_i - lx)


def _draw_line(buf, w, h, x0, y0, x1, y1, thickness, color):
    steps = max(1, int(math.hypot(x1 - x0, y1 - y0) * 1.5))
    radius = max(0.8, thickness / 2.0)
    for step in range(steps + 1):
        t = step / steps
        _fill_circle(buf, w, h, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, radius, color)


def _draw_ring(buf, w, h, cx, cy, r_in, r_out):
    r_out2 = r_out * r_out
    r_in2 = r_in * r_in
    y0 = max(0, int(math.floor(cy - r_out)))
    y1 = min(h, int(math.ceil(cy + r_out)) + 1)
    x0 = max(0, int(math.floor(cx - r_out)))
    x1 = min(w, int(math.ceil(cx + r_out)) + 1)
    for y in range(y0, y1):
        dy = y - cy
        dy2 = dy * dy
        row = y * w
        for x in range(x0, x1):
            dx = x - cx
            d2 = dx * dx + dy2
            if r_in2 <= d2 <= r_out2:
                diag = dx + dy
                buf[row + x] = 4 if diag < -26 else 5 if diag < 26 else 6


def _draw_arc_eyes(buf, w, h, cx, cy, color, *, happy=True, blink=False):
    for sx in (-1, 1):
        ex = cx + sx * 19
        if blink:
            _draw_line(buf, w, h, ex - 6, cy + 1, ex + 6, cy + 1, 2.2, color)
        elif happy:
            _draw_line(buf, w, h, ex - 6, cy + 3, ex, cy - 3, 2.5, color)
            _draw_line(buf, w, h, ex, cy - 3, ex + 6, cy + 3, 2.5, color)
        else:
            _draw_line(buf, w, h, ex - 6, cy - 2, ex, cy + 3, 2.5, color)
            _draw_line(buf, w, h, ex, cy + 3, ex + 6, cy - 2, 2.5, color)


def _draw_heart(buf, w, h, cx, cy, s, color):
    _fill_circle(buf, w, h, cx - s * 0.45, cy - s * 0.2, s * 0.55, color)
    _fill_circle(buf, w, h, cx + s * 0.45, cy - s * 0.2, s * 0.55, color)
    _draw_line(buf, w, h, cx - s * 0.9, cy, cx, cy + s * 0.95, s * 0.5, color)
    _draw_line(buf, w, h, cx + s * 0.9, cy, cx, cy + s * 0.95, s * 0.5, color)
    _fill_circle(buf, w, h, cx, cy + s * 0.15, s * 0.5, color)


@lru_cache(maxsize=8)
def _render_procedural_gif(variant_index, accent, mood):
    w = h = 160
    frames = []
    offsets = (0, -2, -3, -2, 0, 1) if variant_index % 2 == 0 else (1, 0, -2, -3, -1, 0)
    for idx in range(6):
        buf = bytearray(w * h)

        cy = 76 + offsets[idx]
        cx = 80
        pulse = 1 if idx in (2, 3) else 0
        _draw_ring(buf, w, h, cx, cy, 44, 51 + pulse)
        _fill_circle(buf, w, h, cx, cy, 44, 2)
        _fill_circle(buf, w, h, cx - 12, cy - 14, 16, 3)

        # Olhos, sobrancelhas e boca conforme a intenção emocional
        eye_y = cy - 4
        if mood in ('happy', 'celebrate'):
            _draw_arc_eyes(buf, w, h, cx, eye_y, accent, happy=True, blink=False)
            _fill_ellipse(buf, w, h, cx, cy + 12, 8, 4 + (idx % 2), accent)
        elif mood in ('sleep', 'sleepy'):
            _draw_arc_eyes(buf, w, h, cx, eye_y + 2, accent, happy=False, blink=(mood == 'sleep' or idx >= 3))
            _fill_circle(buf, w, h, cx, cy + 14, 3 + (idx % 2), accent)
        elif mood in ('angry',):
            _draw_line(buf, w, h, cx - 25, eye_y - 10, cx - 12, eye_y - 4, 2.8, accent)
            _draw_line(buf, w, h, cx + 25, eye_y - 10, cx + 12, eye_y - 4, 2.8, accent)
            _fill_ellipse(buf, w, h, cx - 18, eye_y + 2, 5, 6, accent)
            _fill_ellipse(buf, w, h, cx + 18, eye_y + 2, 5, 6, accent)
            _draw_line(buf, w, h, cx - 8, cy + 14, cx + 8, cy + 14, 2.4, accent)
        elif mood in ('sad', 'dramatic'):
            _draw_line(buf, w, h, cx - 24, eye_y - 4, cx - 12, eye_y - 9, 2.4, accent)
            _draw_line(buf, w, h, cx + 12, eye_y - 9, cx + 24, eye_y - 4, 2.4, accent)
            _fill_ellipse(buf, w, h, cx - 18, eye_y + 2, 5, 6, accent)
            _fill_ellipse(buf, w, h, cx + 18, eye_y + 2, 5, 6, accent)
            _fill_ellipse(buf, w, h, cx - 18, eye_y + 12 + (idx % 3) * 3, 2.2, 4, 11)
            _fill_ellipse(buf, w, h, cx + 18, eye_y + 12 + ((idx + 1) % 3) * 3, 2.2, 4, 11)
            _draw_line(buf, w, h, cx - 6, cy + 15, cx + 6, cy + 15, 2.2, accent)
        elif mood == 'shocked':
            _fill_circle(buf, w, h, cx - 18, eye_y, 8, accent)
            _fill_circle(buf, w, h, cx + 18, eye_y, 8, accent)
            _fill_circle(buf, w, h, cx - 18, eye_y, 3, 1)
            _fill_circle(buf, w, h, cx + 18, eye_y, 3, 1)
            _fill_ellipse(buf, w, h, cx, cy + 14, 5, 6 + (idx % 2), accent)
        elif mood == 'shy':
            _draw_arc_eyes(buf, w, h, cx, eye_y, accent, happy=True, blink=(idx == 4))
            _fill_ellipse(buf, w, h, cx - 24, cy + 7, 6, 3, 15)
            _fill_ellipse(buf, w, h, cx + 24, cy + 7, 6, 3, 15)
            _draw_line(buf, w, h, cx - 4, cy + 13, cx + 4, cy + 13, 2.0, accent)
        elif mood == 'mischief':
            _draw_arc_eyes(buf, w, h, cx - 2, eye_y, accent, happy=True, blink=False)
            _fill_ellipse(buf, w, h, cx + 18, eye_y + 1, 5, 6, accent)
            _draw_line(buf, w, h, cx - 7, cy + 12, cx + 7, cy + 10, 2.3, accent)
        elif mood == 'bored':
            _fill_ellipse(buf, w, h, cx - 18, eye_y + 2, 5, 3, accent)
            _fill_ellipse(buf, w, h, cx + 18, eye_y + 2, 5, 3, accent)
            _draw_line(buf, w, h, cx - 25, eye_y - 1, cx - 11, eye_y - 1, 2.4, 2)
            _draw_line(buf, w, h, cx + 11, eye_y - 1, cx + 25, eye_y - 1, 2.4, 2)
            _draw_line(buf, w, h, cx - 6, cy + 14, cx + 6, cy + 14, 2.2, accent)
        else:
            blink = (idx == 4)
            if blink:
                _draw_arc_eyes(buf, w, h, cx, eye_y, accent, happy=True, blink=True)
            else:
                shift = (-2 if idx in (1, 2) else 2 if idx in (4, 5) else 0) if mood == 'curious' else 0
                _fill_ellipse(buf, w, h, cx - 18 + shift, eye_y + 1, 5, 6.5, accent)
                _fill_ellipse(buf, w, h, cx + 18 + shift, eye_y + 1, 5, 6.5, accent)
                _fill_circle(buf, w, h, cx - 19 + shift, eye_y - 2, 1.8, 7)
                _fill_circle(buf, w, h, cx + 17 + shift, eye_y - 2, 1.8, 7)
            if mood == 'curious':
                _fill_circle(buf, w, h, cx + 2, cy + 14, 3, accent)
            else:
                _draw_line(buf, w, h, cx - 5, cy + 13, cx + 5, cy + 13, 2.1, accent)

        # Elementos animados secundários ligados à intenção
        if mood in ('happy', 'shy'):
            dy = (idx % 3) * 3
            _draw_heart(buf, w, h, 30, 32 - dy, 5.5, 15 if mood == 'shy' else 10)
            _draw_heart(buf, w, h, 130, 36 - ((idx + 1) % 3) * 3, 4.5, 15 if mood == 'shy' else 9)
        elif mood in ('sleep', 'sleepy'):
            zy = 30 - (idx % 3) * 4
            _draw_line(buf, w, h, 122, zy, 132, zy, 2.2, 11)
            _draw_line(buf, w, h, 132, zy, 122, zy + 9, 2.2, 11)
            _draw_line(buf, w, h, 122, zy + 9, 132, zy + 9, 2.2, 11)
        elif mood == 'angry':
            ax, ay = 128, 30 + (idx % 2) * 2
            _draw_line(buf, w, h, ax - 5, ay - 2, ax + 5, ay - 2, 2.0, 10)
            _draw_line(buf, w, h, ax - 2, ay - 5, ax - 2, ay + 5, 2.0, 10)
        elif mood in ('curious', 'alert'):
            _fill_circle(buf, w, h, 128, 28 - (idx % 2) * 2, 3.5, accent)
            _fill_circle(buf, w, h, 128, 38 - (idx % 2) * 2, 2.0, accent)
        elif mood == 'celebrate':
            for px, py, col in ((24, 28, 8), (134, 28, 6), (28, 122, 4), (132, 122, 9)):
                _fill_circle(buf, w, h, px, py + ((idx + px) % 3) * 2, 3.2, col)
        elif mood == 'work':
            _fill_rounded_rect(buf, w, h, 114, 112, 144, 132, 3, 14)
            _fill_rounded_rect(buf, w, h, 118, 116, 140, 126, 2, 1)
            _draw_line(buf, w, h, 120, 120, 128 + (idx % 3) * 3, 120, 2.0, 9)
        elif mood == 'shocked':
            _draw_line(buf, w, h, 128, 22, 128, 33 - (idx % 2) * 2, 2.6, 8)
            _fill_circle(buf, w, h, 128, 39, 2.0, 8)

        frames.append(bytes(buf))

    return _encode_gif(w, h, frames, delay_cs=16)


class LocalReactionProvider(ReactionProvider):
    """Provedor local offline de reações originais da Bolha sob GPL-3.0-or-later."""

    provider_id = LOCAL_PROVIDER_ID
    origin = LOCAL_ORIGIN
    author = LOCAL_AUTHOR
    license_spdx = LOCAL_LICENSE_SPDX
    commercial_verified = True

    def __init__(self):
        self._random = random.Random()

    def fetch(self, intent, kind='meme', recent_urls=()):
        intent_key = map_intent(intent, kind)
        variants = LOCAL_REACTIONS.get(intent_key, LOCAL_REACTIONS['observando'])
        candidates = []
        for idx, (slug, title, accent, mood) in enumerate(variants):
            media_url = f'local://bolha/reactions/{intent_key}/{slug}.gif'
            candidates.append((idx, slug, title, accent, mood, media_url))
        fresh = [item for item in candidates if item[5] not in recent_urls] or candidates
        idx, slug, title, accent, mood, media_url = self._random.choice(fresh)
        gif_bytes = _render_procedural_gif(idx, accent, mood)
        candidate = ReactionCandidate(
            provider=self.provider_id,
            intent=intent_key,
            query=intent_key,
            title=title,
            media_url=media_url,
            source_url='',
            attribution=f'Bolha (offline · {self.license_spdx}) · {title}',
            origin=self.origin,
            author=self.author,
            license_spdx=self.license_spdx,
            commercial_verified=self.commercial_verified,
        )
        validate_candidate_contract(candidate, require_commercial_verified=True)
        return ReactionPayload(candidate=candidate, content_type='image/gif', data=gif_bytes)


class InMemoryMedia:
    """Mantém QByteArray/QBuffer/QMovie/QImage exclusivamente em RAM e libera no close()."""
    def __init__(self, payload: ReactionPayload, target_size=220):
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSize, Qt
        from PySide6.QtGui import QImage, QImageReader, QMovie
        validate_candidate_contract(payload.candidate, require_commercial_verified=True)
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
            count = reader.imageCount()
            first = reader.read()
            if count > MAX_ANIMATION_FRAMES or first.isNull():
                self.release()
                raise ValueError('GIF inválido ou fora do limite de quadros.')
            self.buffer.seek(0)
            self.dimensions = (first.width(), first.height())
            self.frame_count = max(1, count)
            if count != 1:
                movie = QMovie(self.buffer, b'gif')
                movie.setCacheMode(QMovie.CacheNone)
                scale = min(1.0, bound / max(1, max(first.width(), first.height())))
                scaled = QSize(max(1, round(first.width() * scale)), max(1, round(first.height() * scale)))
                movie.setScaledSize(scaled)
                movie.start()
                self.movie = movie
                self.animated = True
            else:
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
        bound = max(64, min(320, int(target_size)))
        if bound == self._bound:
            return
        self._bound = bound
        width, height = self.dimensions
        if self.movie is not None and width and height:
            scale = min(1., bound / max(width, height))
            self.movie.setScaledSize(QSize(max(1, round(width * scale)), max(1, round(height * scale))))
        elif self.image is not None and not self.image.isNull():
            scale = min(1., bound / max(width, height, 1))
            if scale < 1.:
                self.image = self.image.scaled(QSize(max(1, round(width * scale)), max(1, round(height * scale))),
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


def fetch_reaction_payload(intent, kind='meme', recent_urls=(), provider=None):
    """Gera ou obtém reação exclusivamente pelo provedor local validado, sem rede externa."""
    active_provider = provider if provider is not None else LocalReactionProvider()
    validate_provider_contract(active_provider, require_commercial_verified=True)
    payload = active_provider.fetch(intent, kind=kind, recent_urls=recent_urls)
    validate_candidate_contract(payload.candidate, require_commercial_verified=True)
    validate_media_signature(payload.data, payload.content_type)
    return payload


class OfflineReactionFetcher:
    """Fila limitada em segundo plano para geração local, consultada em NativeScene.sync()."""

    def __init__(self, provider=None):
        self.provider = provider if provider is not None else LocalReactionProvider()
        validate_provider_contract(self.provider, require_commercial_verified=True)
        self._lock = threading.Lock()
        self._queue = deque()
        self._active = set()
        self._cancelled = set()
        self._results = queue.SimpleQueue()
        self._recent_urls = deque(maxlen=16)
        self._stopped = False
        self._worker_running = False

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
                threading.Thread(target=self._run, name='bolha-local-reactions', daemon=True).start()
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
            try:
                payload = fetch_reaction_payload(emotion, kind, provider=self.provider, recent_urls=recent)
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
