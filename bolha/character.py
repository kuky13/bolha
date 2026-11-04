# SPDX-License-Identifier: GPL-3.0-only
"""Desenho aprovado da Bolha nativa: somente olhos e orelhas.

O corpo e o rosto usam o mesmo centro, rotação e deformação. A expressão
permanece recortada ao interior da esfera em todos os quadros.
"""
import math
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient

RADIUS = 49.0
FACE_RADIUS = 43.0
HALO_RADIUS = 59.0
EMOTIONS = ('observando', 'contente', 'feliz', 'curioso', 'bravo', 'triste', 'assustado', 'dramatico', 'dormindo', 'sonolento', 'timido', 'atento', 'entediado', 'travesso', 'tonto', 'comemorando')
GOLD = '#ffd364'

# Espiral vetorial pequena: a geometria não precisa ser recalculada por quadro.
_DIZZY_EYE = QPainterPath()
for _index in range(41):
    _phase = _index / 40
    _radius = .25 + 5.6 * _phase
    _point = QPointF(math.cos(_phase * math.tau * 1.55) * _radius,
                     math.sin(_phase * math.tau * 1.55) * _radius)
    if _index == 0: _DIZZY_EYE.moveTo(_point)
    else: _DIZZY_EYE.lineTo(_point)


def _clamp(value, low, high):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return low
    return min(high, max(low, value)) if math.isfinite(value) else low


def _color(rgb, alpha=1.0):
    color = QColor(rgb)
    color.setAlphaF(alpha)
    return color


def _pen(color=GOLD, width=2.5, alpha=1.0):
    return QPen(_color(color, alpha), width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)


def _body(p):
    glow = QRadialGradient(QPointF(0, 0), HALO_RADIUS)
    for offset, color, alpha in ((0, '#6f59c8', 0), (.77, '#6f59c8', 0),
                                 (.82, '#6f59c8', .15), (.88, '#9474ec', .32),
                                 (.93, '#6b45ac', .14), (1, '#6b45ac', 0)):
        glow.setColorAt(offset, _color(color, alpha))
    p.setPen(Qt.NoPen)
    p.setBrush(glow)
    p.drawEllipse(QPointF(0, 0), HALO_RADIUS, HALO_RADIUS)
    ring = QLinearGradient(-47, -47, 47, 47)
    ring.setColorAt(0, QColor('#b45da6'))
    ring.setColorAt(.5, QColor('#8a79c1'))
    ring.setColorAt(1, QColor('#6c96b5'))
    p.setBrush(ring)
    p.drawEllipse(QPointF(0, 0), RADIUS, RADIUS)
    core = QRadialGradient(QPointF(-15, -19), 91)
    core.setColorAt(0, QColor('#25252c'))
    core.setColorAt(.55, QColor('#151519'))
    core.setColorAt(1, QColor('#0b0b0e'))
    p.setBrush(core)
    p.drawEllipse(QPointF(0, 0), 46.8, 46.8)


def _features(p, emotion, blink, gaze, ear_tilt=0.0, ear_raise=0.0, eye_open=1.0, blink_left=None, blink_right=None):
    """Desenha somente olhos e orelhas. A metade inferior do rosto fica vazia."""
    clip = QPainterPath()
    clip.addEllipse(QPointF(0, 0), FACE_RADIUS, FACE_RADIUS)
    p.save()
    p.setClipPath(clip, Qt.IntersectClip)
    p.setBrush(Qt.NoBrush)
    p.setPen(_pen())
    # Os ângulos das orelhas são espelhados, e os olhos mantêm formato idêntico.
    profiles = {
        'observando': (5.2, 6.4, 0.0, 0.0, 0.0),
        'contente':   (5.2, 6.0, 0.0, 2.0, .4),
        'feliz':      (5.2, 6.4, 0.0, 6.0, 1.0),
        'curioso':    (5.7, 7.2, -.4, -5.0, 1.7),
        'bravo':      (5.8, 5.4, .2, -26.0, -2.2),
        'triste':     (5.4, 6.1, 1.3, 28.0, -3.2),
        'assustado':  (6.1, 9.8, -.3, -6.0, 2.8),
        'dramatico':  (5.7, 7.4, -.1, -11.0, 1.4),
        'dormindo':   (5.2, 6.4, 1.0, 21.0, -2.9),
        'sonolento':  (5.4, 3.2, 1.0, 12.0, -1.4),
        'timido':     (4.9, 4.8, 1.1, -11.0, -.5),
        'atento':     (5.4, 7.4, -.7, 0.0, 2.2),
        'entediado':  (5.7, 2.5, 1.1, 17.0, -2.1),
        'travesso':   (5.6, 4.7, -.1, -7.0, .9),
        'tonto':      (5.8, 6.2, .2, 19.0, -.9),
        'comemorando':(6.4, 7.2, -.3, 7.0, 2.0),
    }
    rx, ry, eye_y, tilt, raise_units = profiles[emotion]
    tilt = _clamp(tilt + ear_tilt, -35, 35)
    raise_units = _clamp(raise_units + ear_raise, -5, 5)
    for side in (-1, 1):
        p.save()
        p.translate(side * 18, -19 - raise_units)
        p.rotate(side * tilt)
        ear = QPainterPath(QPointF(-4.8, -2))
        ear.quadTo(-1, -12, 0, -12)
        ear.quadTo(1, -12, 4.8, -2)
        p.drawPath(ear)
        p.restore()
    gx, gy = gaze
    opening = _clamp(eye_open, 0, 1.3)
    if emotion == 'dormindo': blink = 1.0
    closing = max(blink, 1 - min(1, opening))
    intentional = blink_left is not None or blink_right is not None
    for side in (-1, 1):
        individual = blink_left if side < 0 else blink_right
        closing_eye = closing if individual is None else max(closing,_clamp(individual,0,1))
        x, y = side * 18 + gx * 1.6, eye_y + gy * .9
        if closing_eye > .94 or emotion == 'feliz' and not intentional:
            happy = emotion == 'feliz' and closing_eye <= .94
            eye = QPainterPath(QPointF(x - 5.3, y + (2 if happy else -1)))
            eye.quadTo(x, y + (-5 if happy else 3), x + 5.3, y + (2 if happy else -1))
            p.setBrush(Qt.NoBrush)
            p.setPen(_pen())
            p.drawPath(eye)
        elif emotion == 'tonto':
            p.save()
            p.translate(x, y)
            p.scale(1, max(.12, (1 - closing_eye) * opening))
            p.setBrush(Qt.NoBrush)
            p.setPen(_pen(width=1.9))
            p.drawPath(_DIZZY_EYE)
            p.restore()
        elif emotion == 'comemorando':
            eye = QPainterPath(QPointF(x, y - 7 * (1 - closing_eye)))
            for dx, dy in ((1.9, -2.2), (6.3, 0), (1.9, 2.2), (0, 7),
                           (-1.9, 2.2), (-6.3, 0), (-1.9, -2.2)):
                eye.lineTo(x + dx, y + dy * (1 - closing_eye))
            eye.closeSubpath()
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(GOLD))
            p.drawPath(eye)
        else:
            height = ry * (1 - closing_eye) * max(1.0, opening) + .7 * closing_eye
            eye = QPainterPath()
            eye.addEllipse(QPointF(x, y), rx, height)
            if emotion in ('bravo', 'triste', 'entediado', 'sonolento', 'travesso'):
                # As pálpebras fazem parte dos olhos, sem acrescentar boca ou sobrancelhas.
                slope = side * (-.43 if emotion == 'bravo' else .26 if emotion == 'triste' else 0)
                lid_y = y - height * (.14 if emotion == 'bravo' else .30 if emotion == 'triste' else .48)
                lid = QPainterPath(QPointF(x-rx-1, lid_y + slope*(-rx-1)))
                lid.lineTo(x+rx+1, lid_y + slope*(rx+1))
                lid.lineTo(x+rx+1, y+height+1)
                lid.lineTo(x-rx-1, y+height+1)
                lid.closeSubpath()
                eye = eye.intersected(lid)
            p.setPen(Qt.NoPen)
            p.setBrush(_color(GOLD, .12))
            p.drawEllipse(QPointF(x, y), rx + 1.0, height + 1.0)
            p.setBrush(QColor(GOLD))
            p.drawPath(eye)
            if height > 3:
                p.save()
                p.setClipPath(eye, Qt.IntersectClip)
                p.setBrush(QColor('#fff4cf'))
                p.drawEllipse(QPointF(x - 1.2 + gx * .2, y - 2.0), 1.05, 1.05)
                p.restore()
    p.restore()


def draw_character(painter, cx, cy, scale=1.0, angle=0.0, emotion='observando',
                   blink=0.0, gaze=(0.0, 0.0), squash=0.0,
                   ear_tilt=0.0, ear_raise=0.0, eye_open=1.0, body_opacity=1.0, blink_left=None, blink_right=None):
    """Pinta Bolha somente com olhos e orelhas: nunca desenha boca.

    ``blink``: 0 aberto, 1 fechado; ``eye_open``: abertura 0..1.3;
    ``ear_tilt``: graus espelhados; ``ear_raise``: elevação canônica.
    Escala, rotação e squash afetam corpo e rosto juntos.
    """
    scale = _clamp(scale, .05, 20)
    squash = _clamp(squash, -.25, .25)
    emotion = {'calma': 'observando', 'tímido': 'timido', 'dramático': 'dramatico'}.get(emotion, emotion)
    emotion = emotion if emotion in EMOTIONS else 'observando'
    gaze = (_clamp(gaze[0], -1, 1), _clamp(gaze[1], -1, 1))
    painter.save()
    painter.translate(cx, cy)
    painter.rotate(_clamp(angle, -100000, 100000))
    painter.scale(scale * (1 + squash), scale * (1 - squash))
    painter.save()
    painter.setOpacity(painter.opacity() * _clamp(body_opacity, .2, 1))
    _body(painter)
    painter.restore()
    _features(painter, emotion, _clamp(blink, 0, 1), gaze,
              _clamp(ear_tilt, -35, 35), _clamp(ear_raise, -5, 5), _clamp(eye_open, 0, 1.3),blink_left,blink_right)
    painter.restore()


def draw_sleep_marks(painter, cx, cy, scale=1.0, phase=0.0, strength=1.0):
    """Três zzz vetoriais sobem em 2,4s; decoração em espaço de tela, sem entrada."""
    strength = _clamp(strength, 0, 1)
    if strength == 0: return
    phase = _clamp(phase, -1000000000, 1000000000)
    painter.save()
    painter.translate(cx, cy)
    painter.scale(_clamp(scale, .05, 20), _clamp(scale, .05, 20))
    painter.setBrush(Qt.NoBrush)
    for index in range(3):
        progress = (phase / 2.4 + index / 3) % 1
        opacity = min(1, progress / .2, (1-progress) / .25) * strength
        size = 4.2 + progress * 2.3
        x, y = 31 + progress * 8, -25 - progress * 20
        mark = QPainterPath(QPointF(x, y-size))
        mark.lineTo(x+size*.8, y-size)
        mark.lineTo(x, y)
        mark.lineTo(x+size*.8, y)
        painter.setPen(_pen(width=1.25, alpha=opacity))
        painter.drawPath(mark)
    painter.restore()


def draw_reaction_marks(painter, cx, cy, scale=1.0, phase=0.0, kind='carinho', strength=1.0):
    """Pequenos corações, estrelas e risquinhos; decoração vetorial sem hitbox."""
    strength = _clamp(strength, 0, 1)
    if strength == 0 or kind not in ('carinho', 'tonto', 'bravo'): return
    phase = _clamp(phase, -1000000000, 1000000000)
    painter.save()
    painter.translate(cx, cy)
    size_scale = _clamp(scale, .05, 20)
    painter.scale(size_scale, size_scale)
    if kind == 'carinho':
        for index in range(3):
            progress = (phase / 1.8 + index / 3) % 1
            opacity = min(1, progress / .2, (1-progress) / .3) * strength
            x = (-34 if index % 2 == 0 else 35) + math.sin(progress*math.pi)*2
            y = -24 - progress*20
            size = 3.7 + progress*1.8
            heart = QPainterPath(QPointF(x, y+size))
            heart.cubicTo(x-size*2, y-size*.2, x-size, y-size*1.7, x, y-size*.5)
            heart.cubicTo(x+size, y-size*1.7, x+size*2, y-size*.2, x, y+size)
            painter.setPen(Qt.NoPen)
            painter.setBrush(_color(GOLD, opacity))
            painter.drawPath(heart)
    elif kind == 'tonto':
        painter.setPen(Qt.NoPen)
        painter.setBrush(_color(GOLD, strength*.85))
        for index in range(3):
            orbit = phase*2.6 + index*math.tau/3
            x, y = math.cos(orbit)*40, -41+math.sin(orbit)*6
            size = 3.1 + .5*math.sin(orbit*2)
            star = QPainterPath(QPointF(x, y-size))
            for dx, dy in ((.7,-.7),(size,0),(.7,.7),(0,size),(-.7,.7),(-size,0),(-.7,-.7)):
                star.lineTo(x+dx,y+dy)
            star.closeSubpath()
            painter.drawPath(star)
    else:
        painter.setBrush(Qt.NoBrush)
        painter.setPen(_pen(width=1.55, alpha=strength*.85))
        for side in (-1, 1):
            for index in range(2):
                offset = math.sin(phase*18+index)*.8*strength
                mark = QPainterPath(QPointF(side*(42+index*5), -19-index*4+offset))
                mark.lineTo(side*(45+index*5), -23-index*4+offset)
                mark.lineTo(side*(43+index*5), -27-index*4+offset)
                painter.drawPath(mark)
    painter.restore()




WINK_DURATION = 1.12

def wink_state(progress):
    """Dois gestos rápidos com120ms totalmente fechados e final aberto."""
    progress=_clamp(progress,0,1);t=progress*WINK_DURATION
    def pulse(start):
        local=t-start
        if local<0 or local>=.34:return 0.
        if local<.10:return .5-.5*math.cos(math.pi*local/.10)
        if local<.22:return 1.
        return .5+.5*math.cos(math.pi*(local-.22)/.12)
    left,right=pulse(.03),pulse(.43)
    envelope=math.sin(math.pi*progress)**2
    return dict(blink_left=left,blink_right=right,ear_tilt=10*math.sin(progress*math.tau)*envelope,
                ear_raise=1.8*envelope,tilt=5*math.sin(progress*math.tau)*envelope)
