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
EMOTIONS = ('observando', 'contente', 'feliz', 'curioso', 'bravo', 'triste', 'assustado', 'dramatico', 'dormindo', 'sonolento', 'timido', 'atento', 'entediado', 'travesso')
GOLD = '#ffd364'


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
        'bravo':      (5.5, 3.0, .2, -14.0, -.3),
        'triste':     (5.0, 4.4, 1.3, 19.0, -2.0),
        'assustado':  (5.9, 8.1, -.3, -2.0, 2.2),
        'dramatico':  (5.7, 7.4, -.1, -11.0, 1.4),
        'dormindo':   (5.2, 6.4, 1.0, 21.0, -2.9),
        'sonolento':  (5.4, 3.2, 1.0, 12.0, -1.4),
        'timido':     (4.9, 4.8, 1.1, -11.0, -.5),
        'atento':     (5.4, 7.4, -.7, 0.0, 2.2),
        'entediado':  (5.7, 2.5, 1.1, 17.0, -2.1),
        'travesso':   (5.6, 4.7, -.1, -7.0, .9),
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
        else:
            height = ry * (1 - closing_eye) * max(1.0, opening) + .7 * closing_eye
            p.setPen(Qt.NoPen)
            p.setBrush(_color(GOLD, .12))
            p.drawEllipse(QPointF(x, y), rx + 1.0, height + 1.0)
            p.setBrush(QColor(GOLD))
            p.drawEllipse(QPointF(x, y), rx, height)
            if height > 3:
                p.setBrush(QColor('#fff4cf'))
                p.drawEllipse(QPointF(x - 1.2 + gx * .2, y - 2.0), 1.05, 1.05)
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
