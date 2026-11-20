# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Expressões visuais no relógio já existente; nunca modifica o corpo físico."""
import math
from .facial_motion import WINK_DURATION, wink_state, mouth_state, feature_profile
from .desk import TYPING_SECONDS, typing_frame
from cursor_prank import CHEW_SECONDS

QUIRK_SECONDS = dict(stretch=2.3, sneeze=1.65, hiccup=1.6, doze=3.3,
                     ear_wiggle=1.5, wink=WINK_DURATION)
LANDING_POSES = ('pouso_em_pe', 'pouso_de_lado', 'pouso_invertido')
FLOOR_POSES = (*LANDING_POSES, 'deitada', 'embaixadinha', 'brinquedo_perseguindo')


def _unit(value):
    return max(0., min(1., value))


def _ease(value):
    value = _unit(value)
    return value * value * (3 - 2 * value)


def _mouth_pulse(t, duration, attack=.08):
    return _ease(t/attack) * (1.-_ease((t-attack)/(duration-attack)))


def animation_pose(mode, seconds, strength=1.):
    """Quadro determinístico compartilhado pelo aplicativo e pelas prévias Qt.

    Os campos de desenho mantêm a API do personagem. Os offsets e efeitos
    giram e deformam com a esfera, sem deslocar o centro físico.
    """
    t = max(0., float(seconds));strength = _unit(strength)
    pose = dict(emotion=mode, eye_open=1., ear_tilt=0., ear_raise=0., squash=0.,
                gaze=None, blink=0., blink_left=None, blink_right=None,
                angle_offset=0., zzz_strength=0., zzz_phase=t,
                effect=None, effect_strength=0., effect_phase=t, effect_angle=0., anger=0.,
                body_opacity=1.,visual_scale=1.)
    if mode == 'cursor_approach':
        pose.update(emotion='travesso', eye_open=.83, ear_tilt=-7., ear_raise=1.,
                    angle_offset=3. * math.sin(t * 3.), mouth_curve=.75)
    elif mode == 'cursor_pounce':
        pose.update(emotion='atento', eye_open=1.2, ear_raise=2.7,
                    squash=-.15 * strength, mouth_open=.44*_mouth_pulse(t,.23),
                    mouth_curve=.6)
    elif mode == 'cursor_swallow':
        progress = _unit(t / .32)
        pose.update(emotion='atento', eye_open=1.1, ear_raise=2.,
                    squash=.11*math.sin(progress*math.pi), mouth_open=1.-_ease(progress),
                    mouth_curve=.6, cursor_inside=progress < .65)
    elif mode == 'cursor_chew':
        # Duas mastigadas pequenas; o mesmo prazo encerra o gesto no cérebro.
        chew = math.sin(math.pi * 2. * _unit(t / CHEW_SECONDS)) ** 2
        pose.update(emotion='atento', eye_open=1.08, ear_tilt=2.*chew,
                    ear_raise=.7, squash=.022*chew, mouth_open=0.,
                    mouth_curve=.12+.12*chew, mouth_chew=.48*chew,
                    mouth_width=.92+.08*chew, mouth_skew=0.)
    elif mode == 'cursor_spit':
        progress = _unit(t / 1.35)
        pulse = math.sin(math.pi * _unit(t / .35)) if t < .35 else 0.
        pose.update(emotion='tonto', eye_open=.55+.3*progress,
                    ear_raise=-2.8*(1.-progress), ear_tilt=12.*math.sin(t*13.)*(1.-progress),
                    angle_offset=9.*math.sin(t*12.)*(1.-progress),
                    squash=.13*pulse, mouth_open=.78*_mouth_pulse(t,.32,.04), mouth_curve=-.7,
                    tongue=.75*pulse,
                    cursor_spit=_unit(t/.35) if t < .35 else 0.,
                    effect='tonto', effect_strength=.55*(1.-progress))
    elif mode == 'cursor_recover':
        recovery = 1.-_unit(t)
        pose.update(emotion='contente', mouth_curve=-.25*recovery,
                    ear_raise=-1.2*recovery,
                    angle_offset=2.5*math.sin(t*7.)*recovery)
    elif mode == 'held':
        irritation = _ease((t - .7) / 3.)
        rage = _ease((t - 1.1) / 2.6) * (.55 + .45 * strength)
        pulse = .88 + .12 * math.sin(t * 14)
        pose.update(emotion='curioso' if t < .7 else 'entediado' if irritation < .3 else 'bravo',
                    eye_open=1.12 - .76 * irritation, ear_raise=1. - 5.4 * irritation,
                    ear_tilt=(16. + 2. * math.sin(t * 18) * rage) * irritation,
                    squash=.03 * irritation * math.sin(t * 6),
                    angle_offset=irritation * (math.sin(t * 5) + .5 * math.sin(t * 8)),
                    effect='bravo', effect_strength=irritation * strength,
                    anger=_unit((.22 * irritation + .78 * rage) * pulse))
    elif mode == 'sleeping':
        closing = _ease(t / 1.8);breath = math.sin(t * math.tau / 4.2)
        pose.update(emotion='sonolento' if t < 1.8 else 'dormindo',
                    eye_open=1. - closing, blink=closing,
                    ear_raise=-1. - 1.5 * closing + .7 * breath, ear_tilt=5. * closing,
                    squash=.055 * breath, angle_offset=1.4 * breath,
                    zzz_strength=_ease((t - 1.4) / 1.2))
    elif mode in ('caress', 'comemorando'):
        joy = .7 + .3 * strength
        pose.update(emotion='feliz' if mode == 'caress' else 'comemorando',
                    ear_raise=1.8 + 1.2 * math.sin(t * 10), ear_tilt=10 * math.sin(t * 11),
                    squash=-.13 * math.sin(t * 8) * joy, angle_offset=5. * math.sin(t * 6) * joy,
                    effect='carinho' if mode == 'caress' else 'comemorando', effect_strength=joy)
    elif mode == 'airborne':
        pose.update(emotion='assustado', eye_open=1.25, ear_raise=2.4,
                    squash=-.15 * strength, angle_offset=2 * math.sin(t * 7))
    elif mode == 'impact':
        rebound = math.exp(-t * 7) * math.cos(t * 18)
        pose.update(emotion='assustado', blink=max(0., 1 - t / .11),
                    ear_raise=-2. * rebound, squash=.23 * rebound * strength,
                    angle_offset=5. * math.exp(-t * 6) * math.sin(t * 16) * strength)
    elif mode == 'bravo':
        rage=(.55+.45*strength)*(.92+.08*math.sin(t*11.))
        pose.update(eye_open=.48-.10*rage,ear_raise=-3.5*rage,
                    ear_tilt=11.*rage,squash=.025*math.sin(t*17.)*rage,
                    angle_offset=2.2*math.sin(t*19.)*rage,
                    anger=rage,effect='bravo',effect_strength=.75*rage)
    elif mode == 'tonto':
        pose.update(emotion='tonto', ear_raise=-1.5, ear_tilt=9 * math.sin(t * 7),
                    squash=.07 * math.sin(t * 9), angle_offset=7 * math.sin(t * 5),
                    effect='tonto', effect_strength=.8)
    elif mode in ('birra', 'sacudir'):
        envelope = math.exp(-t * (1.1 if mode == 'birra' else 2.))
        pulse = .9 + .1 * math.sin(t * 18)
        pose.update(emotion='bravo' if mode == 'birra' else 'contente',
                    eye_open=.48 if mode == 'birra' else 1.,
                    blink=.95 if mode == 'sacudir' and t < .3 else 0.,
                    ear_tilt=18 * math.sin(t * 17) * envelope,
                    ear_raise=-2.6 * envelope if mode == 'birra' else -2 * envelope,
                    squash=.2 * math.sin(t * 15) * envelope * strength,
                    angle_offset=12 * math.sin(t * 16) * envelope * strength,
                    effect='bravo' if mode == 'birra' else None,
                    effect_strength=strength * envelope if mode == 'birra' else 0.,
                    anger=_unit((.45 + .55 * strength) * envelope * pulse) if mode == 'birra' else 0.)
    elif mode == 'preparar_bote':
        crouch = _ease(t / .8)
        pose.update(emotion='atento', eye_open=1.15 - .4 * crouch,
                    ear_raise=-1.5 * crouch, ear_tilt=-6 * crouch,
                    squash=.19 * crouch, angle_offset=4 * math.sin(t * 11) * crouch,
                    mouth_curve=.54+.24*crouch, mouth_width=1.12)
    elif mode == 'brinquedo_frustrado':
        # O abalo cresce com a intensidade, mas a esfera continua no mesmo centro.
        cooldown = 1. - _ease((t-2.05) / .75)
        rage = _ease(t / .24) * (.72 + .28 * strength) * cooldown
        pulse = .89 + .11 * math.sin(t * 9)
        pose.update(emotion='bravo', eye_open=.46 - .08 * rage,
                    ear_raise=-2.8 - 1.1 * rage,
                    ear_tilt=12 * math.sin(t * 22) * rage,
                    squash=.07 * math.sin(t * 19) * rage,
                    angle_offset=6.5 * math.sin(t * 20) * rage,
                    effect='bravo', effect_strength=_unit(rage * strength),
                    anger=_unit(rage * pulse))
    elif mode in ('correndo','brinquedo_perseguindo'):
        stride = t*math.tau*2.
        push = math.sin(stride)
        playing = mode == 'brinquedo_perseguindo'
        press, spring = max(0.,-push)**1.3, max(0.,push)**1.3
        # Uma abertura breve a cada duas passadas; o sorriso também corre junto.
        breath = _mouth_pulse(t%1.-.10,.22,.065)
        pose.update(emotion='contente' if playing else 'atento',
                    eye_open=1.08+.14*spring,
                    ear_raise=-1.4*strength+1.1*push,
                    ear_tilt=-9.-6.*strength-3.*math.cos(stride-.6),
                    squash=(.045*push-.035)*strength,
                    angle_offset=(9.+2.7*math.sin(stride-.3))*strength,
                    mouth_curve=.66+.12*spring-.10*press,
                    mouth_open=(.16+.14*strength)*breath,
                    mouth_width=1.04+.08*spring-.04*press,
                    effect='perseguindo',effect_strength=.28+.4*strength)
        if playing:
            ear_swing = math.sin(stride-.65)
            pose.update(squash=(.11*press-.083*spring)*strength,
                        ear_raise=.65+2.5*ear_swing*strength,
                        ear_tilt=-5.-7.*ear_swing*strength,
                        angle_offset=(7.5+3.8*math.sin(stride-.42))*strength,
                        mouth_curve=.82+.14*spring-.05*press,
                        mouth_open=(.24+.16*strength)*breath,
                        mouth_width=1.10+.06*spring-.02*press)
    elif mode == 'brinquedo_esperando':
        spring = .5+.5*math.sin(t*6.)
        pose.update(emotion='contente', eye_open=1.13+.10*spring,
                    ear_raise=.5+1.5*spring, ear_tilt=-3.+3.*spring,
                    squash=.025*spring, mouth_curve=.85, mouth_width=1.1,
                    mouth_open=.18*_mouth_pulse(t,.55,.14))
    elif mode in ('pingpong_rebatida','brinquedo_rebatida'):
        impact = 1. - _ease(t/.09)
        stretch = _ease((t-.035)/.085)*(1.-_ease((t-.13)/.22))
        grin = _ease((t-.035)/.12)
        pose.update(emotion='atento' if t<.115 else 'contente',
                    eye_open=1.-.56*impact+.24*stretch,
                    ear_raise=-3.2*impact+3.3*stretch,
                    ear_tilt=12.*impact-11.*stretch,
                    squash=(-.20*impact+.17*stretch)*strength,
                    angle_offset=(-5.5*impact+7.5*stretch)*strength,
                    effect='rebatida', effect_strength=strength*(1.-_ease((t-.035)/.22)),
                    mouth_open=(.47+.17*strength)*_mouth_pulse(t,.38,.09),
                    mouth_curve=.62+.38*grin, mouth_width=1.08+.11*grin,
                    mouth_skew=.24*grin)
    elif mode == 'embaixadinha':
        tap = _mouth_pulse(t,.31,.045)
        laugh = _mouth_pulse(t-.11,.26,.085)
        pose.update(emotion='feliz' if .155<=t<.31 else 'contente',
                    eye_open=1.04+.22*tap, squash=-.084*tap,
                    ear_raise=3.4*tap, ear_tilt=-12.*tap,
                    gaze=(0.,-.75), mouth_open=.66*tap+.13*laugh,
                    mouth_curve=.88+.12*tap, mouth_width=1.14)
    elif mode == 'ponto_bolha':
        laugh = max(_mouth_pulse(t,.39,.085),.62*_mouth_pulse(t-.39,.33,.09))
        lift = _mouth_pulse(t,.89,.22)
        pose.update(emotion='feliz' if .08<t<.7 else 'contente',
                    ear_raise=3.*lift, ear_tilt=-9.*lift+5.*math.sin(t*15)*laugh,
                    squash=.07*math.sin(t*16)*lift, angle_offset=6.*math.sin(t*9)*lift,
                    mouth_curve=.98, mouth_width=1.17, mouth_open=.71*laugh)
    elif mode == 'brinquedo_escapou':
        gasp = _mouth_pulse(t,.37,.06)
        recovery = _mouth_pulse(t-.30,.78,.24)
        smile = _ease((t-.22)/.30)
        pose.update(emotion='assustado' if t<.29 else 'contente',
                    eye_open=1.07+.23*gasp+.09*recovery,
                    ear_raise=2.8*gasp+1.3*recovery,
                    ear_tilt=-10.*gasp-4.*recovery, squash=-.065*gasp+.025*recovery,
                    mouth_open=.6*gasp, mouth_curve=.1+.76*smile,
                    mouth_width=.65+.47*smile)
    elif mode == 'pop':
        rupture = t-.13
        squeeze = _ease(t/.075)*(1.-_ease((t-.075)/.055))
        swell = _ease((t-.075)/.055)*(1.-_ease(rupture/.13))
        dissolve = _ease(rupture/.13)
        pose.update(emotion='assustado',eye_open=1.+.3*swell-.4*squeeze,
                    blink=_ease(rupture/.085),ear_raise=2.8*swell-4.*squeeze,
                    ear_tilt=12.*squeeze*math.sin(t*85.),
                    angle_offset=5.*squeeze*math.sin(t*65.),
                    squash=.22*squeeze-.08*swell,
                    body_opacity=1.-dissolve,visual_scale=1.-.08*squeeze+.15*swell,
                    effect='pop',effect_phase=max(0.,rupture),effect_strength=float(rupture>=0.))
    elif mode == 'pop_return':
        pose.update(emotion='timido',eye_open=.98-.11*strength,
                    blink=math.exp(-((t-.73)/.095)**2),
                    ear_raise=-2.*strength,ear_tilt=5.*strength)
    elif mode in LANDING_POSES:
        settle = math.exp(-t*5.2)
        bounce = math.cos(t*20.)*settle
        force = .58+.42*strength
        if mode == 'pouso_em_pe':
            pose.update(emotion='atento',blink=max(0.,1.-t/.105),
                        eye_open=1.+.18*_ease(t/.14)*settle,
                        ear_raise=-3.6*bounce*force,ear_tilt=4.*math.sin(t*21.)*settle,
                        squash=.21*bounce*force)
        elif mode == 'pouso_de_lado':
            relax = _ease((t-.23)/.57)
            rock = math.cos(t*14.)*math.exp(-t*4.4)
            pose.update(emotion='assustado' if t<.22 else 'contente',
                        blink=1.-_ease(t/.18),eye_open=1.08-.37*relax,
                        ear_raise=-3.8*settle-1.4*relax,ear_tilt=14.*rock+5.*relax,
                        angle_offset=-19.*rock*force,squash=.28*bounce*force+.09*relax)
        else:
            pose.update(emotion='assustado' if t<.12 else 'tonto',
                        blink=max(0.,1.-t/.10),ear_raise=-3.7*settle,
                        ear_tilt=10.*math.sin(t*23.)*settle,
                        angle_offset=7.*math.sin(t*23.)*settle,
                        squash=.23*bounce*force,effect='tonto',
                        effect_strength=_ease((t-.08)/.12)*settle)
    elif mode == 'deitada':
        breath = .5-.5*math.cos(t*math.tau/2.4)
        blink = math.exp(-((t%4.7-2.9)/.16)**2)
        pose.update(emotion='contente',blink=blink,eye_open=.71+.13*breath,
                    ear_raise=-1.4+.7*breath,ear_tilt=5.+2.*breath,squash=.09-.027*breath)
    elif mode == 'bote_erro':
        flump = math.exp(-((t - .25) / .16) ** 2)
        wobble = math.sin(t * 13) * math.exp(-t * 1.8)
        pose.update(emotion='tonto' if .3 < t < 1.15 else 'timido',
                    blink=flump, ear_raise=-3 * flump, ear_tilt=12 * wobble,
                    squash=.24 * flump + .10 * wobble,
                    angle_offset=14 * wobble, effect='tonto',
                    effect_strength=.65 * _ease(t / .4) * (1 - _ease((t - 1.) / .6)))
    elif mode == 'brinquedo_susto':
        shock = math.exp(-t * 3)
        pose.update(emotion='assustado', eye_open=1.25, ear_raise=3 * shock,
                    ear_tilt=-12 * shock, squash=-.22 * shock,
                    angle_offset=10 * math.sin(t * 16) * shock)
    elif mode == 'digitando':
        pose.update(emotion='contente', gaze=(.16,.52), mouth_curve=.56)
    elif mode == 'fingir_trabalho':
        caught = _ease((t - .45) / .3)
        pose.update(emotion='entediado' if t < .45 else 'assustado' if t < .8 else 'atento',
                    eye_open=.5 + .7 * caught, ear_raise=-1 + 3 * caught,
                    gaze=(.15 * math.sin(t * 8), .65),
                    squash=.065 * math.sin(t * 15) * caught,
                    angle_offset=2.5 * math.sin(t * 12) * caught)
    elif mode == 'stretch':
        envelope = math.sin(math.pi * _unit(t / QUIRK_SECONDS[mode])) ** 2
        pose.update(emotion='contente', blink=envelope, ear_raise=4. * envelope,
                    ear_tilt=-12 * envelope, squash=-.24 * envelope,
                    angle_offset=9. * math.sin(t * 2.6) * envelope)
    elif mode == 'sneeze':
        anticipation = _ease(t / .7) * (1 - _ease((t - .85) / .25))
        burst = math.exp(-((t - .95) / .12) ** 2)
        recovery = math.exp(-max(0., t - 1.) * 7) * math.sin(max(0., t - 1.) * 19) if t > 1 else 0.
        pose.update(emotion='assustado' if t < .85 else 'contente', blink=_unit(anticipation + burst),
                    ear_raise=2.5 * anticipation - 3 * burst,
                    squash=-.15 * anticipation + .24 * burst + .10 * recovery,
                    angle_offset=-7 * anticipation + 13 * burst + 4 * recovery)
    elif mode == 'hiccup':
        pulse = math.exp(-((t - .35) / .09) ** 2) + .7 * math.exp(-((t - .95) / .09) ** 2)
        pose.update(emotion='curioso', eye_open=1. + .25 * pulse, ear_raise=3 * pulse,
                    squash=-.21 * pulse, angle_offset=7 * pulse)
    elif mode == 'doze':
        closing = _ease(t / 1.25) * (1 - _ease((t - 2.25) / .45))
        startle = math.exp(-((t - 2.65) / .15) ** 2)
        pose.update(emotion='sonolento' if t < 2.5 else 'assustado', blink=closing,
                    ear_raise=-2. * closing + 3. * startle, eye_open=1. + .2 * startle,
                    squash=.13 * closing - .18 * startle, angle_offset=12 * closing - 9 * startle)
    elif mode == 'ear_wiggle':
        envelope = math.sin(math.pi * _unit(t / QUIRK_SECONDS[mode])) ** 2
        pose.update(emotion='curioso', ear_tilt=23 * math.sin(t * 17) * envelope,
                    ear_raise=2. * math.sin(t * 11) * envelope,
                    angle_offset=4 * math.sin(t * 8) * envelope)
    elif mode == 'wink':
        wink = wink_state(_unit(t / WINK_DURATION))
        pose.update(emotion='contente', **{key: value for key, value in wink.items() if key != 'tilt'})
        pose['angle_offset'] = wink['tilt']
    elif mode == 'triste':
        pose.update(ear_raise=-1.2 + .35 * math.sin(t * 2), eye_open=.8,
                    gaze=(0., .8), squash=.045 * math.sin(t * 2), angle_offset=2. * math.sin(t * 1.5))
    elif mode in ('curioso', 'atento', 'travesso'):
        pose.update(ear_tilt=8 * math.sin(t * 3.5), ear_raise=1.1 * math.sin(t * 4),
                    angle_offset=4 * math.sin(t * 2.2), eye_open=1. + .08 * math.sin(t * 3))
    elif mode in ('sonolento', 'entediado'):
        pose.update(ear_raise=-.6, eye_open=.65 + .13 * math.sin(t * 1.8),
                    squash=.045 * math.sin(t * 2), angle_offset=2. * math.sin(t * 1.6))
    elif mode == 'assustado':
        pose.update(eye_open=1.2, ear_raise=1.8, squash=-.08 * math.exp(-t * 2),
                    angle_offset=3. * math.sin(t * 11) * math.exp(-t * 2))
    elif mode in ('contente', 'feliz', 'timido', 'observando', 'dramatico'):
        pose.update(ear_raise=.7 * math.sin(t * 3.2), squash=.025 * math.sin(t * 3),
                    angle_offset=1.5 * math.sin(t * 2))
    for key, value in mouth_state(pose['emotion']).items():
        pose.setdefault(key, value)
    if mode in ('caress', 'feliz', 'comemorando'):
        pose['mouth_open'] = (.2 if mode != 'comemorando' else .38)*_mouth_pulse(t,.46)*strength
    elif mode in ('assustado', 'airborne', 'impact', 'brinquedo_susto'):
        pose['mouth_open'] = .43*_mouth_pulse(t,.32,.04)*strength
        pose['mouth_width'] = .68
    elif mode == 'doze':
        pose['mouth_open'] = .32*_mouth_pulse(t-.22,.56,.12)
        pose['mouth_width'] = .73
    elif mode in ('hiccup', 'sneeze'):
        pose['mouth_open'] = .38*min(1., pulse if mode == 'hiccup' else burst)
        pose['mouth_width'] = .6
    elif mode == 'held':
        pose['mouth_open'] = .15*_mouth_pulse(t,.26,.04)
        pose['mouth_width'] = .9+.18*irritation
    elif mode in ('wink', 'cursor_approach'):
        pose['mouth_skew'] = .34*_mouth_pulse(t,.96,.16) if mode == 'wink' else .3
    elif mode in ('sleeping', 'dormindo', 'timido', 'pop_return'):
        pose['mouth_width'] = .72
    pose['squash'] = max(-.25, min(.25, pose['squash']))
    return pose


class ExpressionMotion:
    """Seleciona a expressão a partir do cérebro e dos gestos, sem outra física."""
    def __init__(self, now):
        self.mode = 'observando';self.started = now;self.held_since = None;self.sleep_since = None
        self.last_landing = 0.;self.impact_since = -1e9;self.dizzy_until = 0.
        self.quirk = None;self.quirk_since = now;self.last_quirk = None
        self.blink_until = 0.
        self.run_phase = 0.
        self.run_tick = now
        self.run_transition = None
        self.irritation = None
        self.pose = animation_pose(self.mode, 0)

    def update(self, game, now, press_since=None):
        body, state = game.body, game.state
        expression_dt = max(0., now-self.run_tick)
        previous_pose = self.pose
        run_dt = min(.05, expression_dt)
        self.run_tick = now
        self.run_phase += abs(body.vx)*run_dt/max(24.,body.half_w)/3.4
        tones = state.tone.r
        held = press_since is not None or body.held
        if held and self.held_since is None:self.held_since = press_since if press_since is not None else now
        if not held:self.held_since = None
        if game.sleep.asleep and not held:
            if self.sleep_since is None:self.sleep_since = now
        else:self.sleep_since = None
        landing = game.landing
        if landing > .18 and self.last_landing < .08:self.impact_since = now
        self.last_landing = landing
        if state.dizzy(now) or abs(body.omega) > 450:self.dizzy_until = now + .8
        mode = state.emotion;strength = 1.;elapsed = None
        reaction = getattr(game, 'release_reaction', None) or {}
        returning = reaction.get('kind')=='pop_return'
        arriving = returning and now<reaction['arrives']
        landing_reaction = getattr(game, 'landing_reaction', None) or {}
        play_reaction = getattr(game, 'play_reaction', None) or {}
        pop_age = game.pop_effect_age(now)
        prank = getattr(game, 'cursor_prank', None)
        if pop_age is not None:
            mode='pop';elapsed=pop_age
        elif held:
            mode = 'held';elapsed = now - self.held_since
            # A irritação neural acelera o gesto; o relógio só interpola seus quadros.
            strength = .6 + .4 * tones['ANGRY'];elapsed *= .8 + .5 * tones['ANGRY']
        elif prank is not None and prank.active:
            mode='cursor_'+prank.phase;elapsed=now-prank.started;strength=prank.intensity
        elif game.play.count_text(now) is not None:
            if game.play.finishing_juggle(now) and game.play.juggle_count < game.play.juggle_target:
                mode='brinquedo_escapou';elapsed=now-game.play.juggle_finished_at
            else:
                mode='embaixadinha';elapsed=now-game.play.juggle_at
        elif arriving:
            mode='pop_return';elapsed=now-reaction['started'];strength=_unit(reaction['intensity'])
        elif self.sleep_since is not None:mode = 'sleeping';elapsed = now - self.sleep_since
        elif state.feliz_fechado(now):mode = 'caress';strength = .5 + .5 * tones['CHEER']
        elif state.at_desk:mode = 'digitando'
        elif returning and now<reaction['until']:
            mode='pop_return';elapsed=now-reaction['started'];strength=_unit(reaction['intensity'])
        elif now < landing_reaction.get('until',0):
            mode=landing_reaction['kind'];elapsed=now-landing_reaction['started'];strength=_unit(landing_reaction['intensity'])
        elif now < self.dizzy_until:mode = 'tonto'
        elif not body.grounded and math.hypot(body.vx, body.vy) > 500:
            mode = 'airborne';strength = _unit(math.hypot(body.vx, body.vy) / 1500)
        elif now - self.impact_since < .5:mode = 'impact';elapsed = now - self.impact_since;strength = max(.35, landing)
        elif now < reaction.get('until',0):
            mode=reaction['kind'];elapsed=now-reaction['started'];strength=_unit(reaction['intensity'])
        elif now < play_reaction.get('until',0):
            mode=play_reaction['kind'];elapsed=now-play_reaction['started'];strength=_unit(play_reaction['intensity'])
        elif game.festa.fogos.isVisible():mode = 'comemorando';strength = tones['CHEER']
        elif game.pingpong is not None and not game.pingpong.finished and not game.pingpong_paused():
            mode = 'brinquedo_esperando'
        elif mode == 'bravo':strength = .35 + .65 * tones['ANGRY']
        elif (body.grounded and 55.<=abs((body.angle+180.)%360.-180.)<=125.
              and mode in ('observando','contente','curioso','feliz','entediado','atento','neutro')):
            mode = 'deitada'
        elif (game.pingpong is None and body.grounded and body.upright() and abs(body.vx)>35.
              and mode in ('observando','contente','curioso','feliz','entediado','atento','neutro')):
            mode='correndo'
        running = (mode in ('correndo','brinquedo_perseguindo') and body.grounded
                   and body.upright() and abs(body.vx)>35.)
        if running:
            strength=_unit(abs(body.vx)/360.)
            elapsed=self.run_phase
        elif mode=='brinquedo_perseguindo':
            # A perseguição pode continuar enquanto ela espera o brinquedo chegar.
            mode='brinquedo_esperando'
        eligible = (game.visible() and body.grounded and not held and not game.hover and not game.panel
                    and mode in ('observando', 'contente', 'curioso', 'feliz', 'entediado'))
        if self.quirk is not None and (not eligible or now - self.quirk_since >= QUIRK_SECONDS[self.quirk]):
            self.quirk = None
        if eligible:
            choices = ['blink'] if self.quirk is not None else [key for key in (*QUIRK_SECONDS, 'blink') if key != self.last_quirk]
            choice = game.choose_expression(choices, now)
            if choice == 'blink':
                self.blink_until = now + .13
            elif choice in QUIRK_SECONDS:
                self.quirk = choice
                self.quirk_since = now;self.last_quirk = choice
        if self.quirk is not None:mode = self.quirk;elapsed = now - self.quirk_since
        if mode != self.mode:
            changing_run = self.mode in ('correndo','brinquedo_perseguindo') or running
            settling = mode in ('correndo','brinquedo_perseguindo','brinquedo_esperando',
                                'observando','contente','curioso','feliz','entediado','atento','neutro')
            self.run_transition = previous_pose if changing_run and settling else None
            self.mode = mode;self.started = now
        self.pose = animation_pose(mode, elapsed if elapsed is not None else now - self.started, strength)
        if mode in ('brinquedo_esperando','brinquedo_escapou','preparar_bote'):
            toy = game.ball.body
            angle = math.atan2(toy.y-body.y,toy.x-body.x)-math.radians(body.angle+self.pose['angle_offset'])
            focus = .56 if mode == 'brinquedo_escapou' else .68
            self.pose['gaze'] = focus*math.cos(angle), focus*math.sin(angle)
        if mode == 'embaixadinha' and game.play.finishing_juggle(now):
            proud = _mouth_pulse(now-game.play.juggle_finished_at-.3,.62,.14)
            self.pose['mouth_open'] += .34*proud
            self.pose['ear_raise'] += 1.6*proud
            settle = _ease((now-game.play.juggle_finished_at-.25)/.7)
            toy = game.ball.body
            look_x = max(-.9,min(.9,(toy.x-body.x)/180.))
            look_y = max(-.75,min(.5,(toy.y-body.y)/180.))
            gaze_mix = _ease((now-game.play.juggle_finished_at)/.4)
            self.pose['gaze'] = tuple(
                (start+(look-start)*gaze_mix)*(1.-settle)+goal*settle
                for start,look,goal in zip((0.,-.75),(look_x,look_y),state.gaze))
            for key,value in mouth_state(state.emotion).items():
                if key in ('mouth_curve','mouth_width'):
                    self.pose[key] += (value-self.pose[key])*settle
        if (prank is not None and prank.angry_attempt
                and mode in ('cursor_approach','cursor_pounce','cursor_swallow','cursor_chew')):
            anger = max(.72, tones['ANGRY'])
            chewing = mode in ('cursor_swallow', 'cursor_chew')
            self.pose.update(emotion='atento' if chewing else 'bravo', anger=anger,
                             eye_open=1.08 if chewing else min(.8,self.pose['eye_open']),
                             ear_raise=min(-1.8,self.pose['ear_raise']), mouth_curve=-.55)
            if mode in ('cursor_approach','cursor_pounce'):
                self.pose.update(effect='bravo', effect_strength=.65*anger)
        if mode=='digitando':
            key, tap, _ = typing_frame(now)
            side = (-1 if key<4 else 1) if key>=0 else 0
            phase = now % TYPING_SECONDS
            breath = math.sin(now*2.8)
            proud = _mouth_pulse(phase - 2.35, 1., .35)
            facing = game.mesa.lado
            self.pose.update(angle_offset=180.-(body.angle+180.)%360.+facing*(8.+2.*tap)+side*tap,
                             squash=.029*tap+.012*breath,
                             gaze=(facing*(.76-.16*proud)+.09*side*tap,.34+.26*tap-.3*proud),
                             ear_raise=-.85+.65*tap+1.65*proud, ear_tilt=2.4*side*tap,
                             blink=_mouth_pulse(phase - 2.2,.18,.07),
                             mouth_curve=.52-.27*tap+.38*proud)
        if mode == 'pouso_de_lado' and landing_reaction.get('angle',0.) < 0.:
            self.pose['angle_offset'] *= -1.
        if mode == 'deitada':
            self.pose['gaze'] = tuple(.65*component for component in state.gaze)
        if running:
            direction=math.copysign(1.,body.vx)
            heading=0. if direction>0 else 180.
            # Physical roll can contain full turns or lean against the next stride.
            visual_angle = self.pose['angle_offset']*direction
            self.pose['angle_offset'] = visual_angle - ((body.angle+180.)%360.-180.)
            local_angle=math.radians(heading-visual_angle)
            focus=.86
            if mode == 'brinquedo_perseguindo':
                toy = game.ball.body
                forward = (toy.x-body.x)*direction
                pitch = max(-.45,min(.45,math.atan2(toy.y-body.y,max(80.,forward))))
                local_angle = math.atan2(math.sin(pitch),direction*math.cos(pitch))-math.radians(visual_angle)
                focus=.8
            self.pose['gaze']=(math.cos(local_angle)*focus,math.sin(local_angle)*focus)
            self.pose['effect_angle'] = heading-visual_angle
        if mode == 'pop_return':
            inward = reaction['inward']
            glance = .47+.22*math.sin(elapsed*5.)*math.exp(-elapsed)
            self.pose['gaze'] = (inward*glance,.13*strength)
            if arriving:
                phase = _unit(elapsed/(reaction['arrives']-reaction['started']))
                peek = _ease(phase/.23)
                retreat = _ease((phase-.40)/.13)
                emerge = _ease((phase-.56)/.44)
                depth = -1.21+.99*peek-(.12+.12*strength)*retreat
                self.pose['corner_peek'] = (inward,depth,emerge)
                self.pose['angle_offset'] = inward*10.*peek*(1.-emerge)
        if mode in ('pingpong_rebatida','brinquedo_rebatida'):
            heading = play_reaction.get('heading',0.)
            follow = math.sin(math.pi*_unit(elapsed/.42))
            self.pose['angle_offset'] += 10.*math.sin(math.radians(heading))*follow
            local_angle = heading-body.angle-self.pose['angle_offset']
            impact_angle = play_reaction.get('impact_angle', heading)
            self.pose['effect_angle'] = impact_angle-body.angle-self.pose['angle_offset']
            aim = math.radians(local_angle)
            self.pose['gaze'] = math.cos(aim),math.sin(aim)
        if 'impact_point' in play_reaction and not held and pop_age is None:
            age = now - play_reaction['started']
            if 0. <= age < .255:
                self.pose['impact_point'] = play_reaction['impact_point']
                self.pose['impact_angle'] = play_reaction['impact_angle']
                self.pose['impact_phase'] = age
                self.pose['impact_strength'] = play_reaction['intensity'] * (1.-_ease((age-.035)/.22))
        self._ease_irritation(game, now, expression_dt, previous_pose)
        if self.run_transition is not None and self.pose['anger'] < .03:
            blend = _ease((now-self.started)/.18)
            for key in ('eye_open','ear_raise','ear_tilt','mouth_curve','mouth_width','mouth_open'):
                start = self.run_transition[key]
                self.pose[key] = start+(self.pose[key]-start)*blend
            before = self.run_transition.get('face_profile', feature_profile(self.run_transition['emotion']))
            self.pose['face_profile'] = tuple(start+(end-start)*blend
                for start,end in zip(before,self.pose['face_profile']))
            if blend >= 1.:self.run_transition = None
        self.pose['blink'] = max(self.pose['blink'], float(now < self.blink_until))
        self.pose['mouth_enabled'] = game.prefs.get('mouthEnabled', True)
        return self.pose


    def _ease_irritation(self, game, now, dt, previous):
        """Interpola o desenho; o tom neural continua decidindo o quanto está brava."""
        pose = self.pose
        previous_anger = self.irritation or 0.
        calming = self.mode in ('caress', 'sleeping', 'pop', 'pop_return')
        reactive = pose['anger'] > .03 or previous_anger > .03 or game.state.emotion == 'bravo'
        neural = game.state.tone.r['ANGRY'] if reactive and not calming else 0.
        reaction = getattr(game, 'release_reaction', {})
        release = (reaction.get('intensity', 0.) if now < reaction.get('until', 0.)
                   and reaction.get('kind') in ('bravo', 'birra') and not calming else 0.)
        target = max(pose['anger'], neural, release)
        first_frame = self.irritation is None
        response = .16 if target > previous_anger else .32 if calming else .85
        blend = 1. - math.exp(-dt / response)
        self.irritation = target if first_frame else previous_anger + (target-previous_anger)*blend
        pose['anger'] = self.irritation
        chewing = self.mode in ('cursor_swallow', 'cursor_chew')
        if self.irritation > .03 and not calming and not chewing:
            weight = _ease((self.irritation-.08)/.62)
            if weight > .2:
                pose['emotion'] = 'bravo'
            for key, angry in (('eye_open', .42), ('ear_raise', -3.8), ('mouth_curve', -.55)):
                pose[key] += (min(pose[key], angry)-pose[key])*weight
            pose['ear_tilt'] += (max(pose['ear_tilt'], 10.)-pose['ear_tilt'])*weight
            if pose['effect'] in (None, 'bravo'):
                pose['effect'] = 'bravo'
                pose['effect_strength'] = max(pose['effect_strength'], .7*self.irritation)
        pose['face_profile'] = feature_profile(pose['emotion'], self.irritation)
        # A troca de modo físico não deve trocar os olhos/orelhas em um só quadro.
        if not first_frame and max(previous_anger, self.irritation) > .03:
            facial_blend = 1. - math.exp(-dt / .14)
            for key in ('eye_open', 'ear_raise', 'ear_tilt', 'mouth_curve', 'mouth_width'):
                pose[key] = previous[key] + (pose[key]-previous[key])*facial_blend
            before = previous.get('face_profile', feature_profile(previous['emotion'], previous_anger))
            pose['face_profile'] = tuple(start+(end-start)*facial_blend
                                         for start, end in zip(before, pose['face_profile']))
