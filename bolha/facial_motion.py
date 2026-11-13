# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Curvas faciais compartilhadas por Qt e Android."""
import math

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
