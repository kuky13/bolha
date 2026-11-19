# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Curvas faciais compartilhadas por Qt e Android."""
import math

# rx, ry, eye y, ear tilt, ear height; eyelid height/slope are appended below.
FEATURE_PROFILES = {
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


def feature_profile(emotion, anger=0.):
    profile = FEATURE_PROFILES.get(emotion, FEATURE_PROFILES['observando'])
    if emotion == 'bravo':
        lid, slope = .14-.12*anger, -.43-.14*anger
    elif emotion == 'triste':
        lid, slope = .30, .26
    elif emotion in ('entediado', 'sonolento', 'travesso'):
        lid, slope = .48, 0.
    else:
        lid, slope = 1., 0.
    return (*profile, lid, slope)


MOUTH_PROFILES = {
    'feliz': .88, 'contente': .55, 'curioso': .12, 'atento': .04,
    'bravo': -.55, 'triste': -.72, 'assustado': -.12, 'dramatico': -.35,
    'dormindo': .12, 'sonolento': -.08, 'timido': .3, 'entediado': -.14,
    'travesso': .66, 'tonto': -.38, 'comemorando': .95,
}

def mouth_state(emotion):
    return dict(mouth_open=0., mouth_curve=MOUTH_PROFILES.get(emotion, .25),
                mouth_chew=0., mouth_width=1., mouth_skew=0., tongue=0.,
                cursor_inside=False, cursor_spit=0.)


def _clamp(value, low, high):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return low
    return min(high, max(low, value)) if math.isfinite(value) else low


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
