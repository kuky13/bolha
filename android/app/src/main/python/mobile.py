# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Same behavioral model and expression clock as the desktop native interface."""
import copy
import json
import math
from pathlib import Path
import shutil
import time

from game import Game
from pestinha.sense.senses import detect_activity
from bolha import VERSION
from bolha.dialogue import Dialogue
from bolha.migration import atomic_json, read_json
from bolha.motion import ExpressionMotion, animation_pose, QUIRK_SECONDS
from bolha.preferences import defaults, sanitize, number
from bolha.reactions import OnlineReactionFetcher, MAX_TOTAL_MEDIA_BYTES, validate_media_signature

EXPRESSION_NAMES = [
    'observando', 'feliz', 'curioso', 'triste', 'bravo', 'entediado', 'held',
    'sleeping', 'caress', 'airborne', 'impact', 'tonto', 'birra', 'sacudir',
    'preparar_bote', 'brinquedo_frustrado', 'brinquedo_susto', 'brinquedo_rebatida',
    'pingpong_rebatida', 'pouso_em_pe', 'pouso_de_lado', 'pouso_invertido',
    'deitada', 'correndo', 'comemorando', 'pop', 'pop_return', *QUIRK_SECONDS,
]
game = None
preferences = None
settings_path = None
size = None
motion_clock = None
dialogue = None
fetcher = None
media_cache = {}
media_requested = set()
monitor_cache = {}
selected_neuron = None
last_diagnostic = 0.
diagnostic = ''
last_error = ''
last_motion = -100.
preview = None
say_until = say_started = 0.
say_text = ''
say_thought = False
last_gaze = last_ear_gaze = (0., 0.)


def _mobile_preferences(patch, previous=None):
    values = sanitize(patch, previous)
    base = previous or {}
    for key, fallback in (('shakeEnabled', False), ('hapticsEnabled', True), ('speechEnabled', True)):
        values[key] = patch[key] if type(patch.get(key)) is bool else base.get(key, fallback)
    sensitivity = patch.get('shakeSensitivity', base.get('shakeSensitivity', 1.))
    values['shakeSensitivity'] = max(.5, min(2., float(sensitivity))) if number(sensitivity) else 1.
    values['senseWindows'] = False
    values['cursorPrankEnabled'] = False
    return values


def start(data, content):
    global game, preferences, settings_path, motion_clock, dialogue, fetcher, last_error
    if game is not None:
        return
    settings_path = Path(data) / 'config.json'
    initial = dict(defaults(), avatarSize=120, senseApp=False, senseWindows=False,
                   senseIdle=True, onlineReactions=False)
    try:
        saved = read_json(settings_path)
        if not isinstance(saved, dict) or not isinstance(saved.get('preferences'), dict):
            raise ValueError('Estrutura de preferências inválida.')
        initial.update(saved['preferences'])
    except FileNotFoundError:
        pass
    except (ValueError, UnicodeError) as error:
        backup = settings_path.with_name('config-corrompida-' + str(time.time_ns()) + '.json')
        shutil.copy2(settings_path, backup)
        last_error = 'Preferências ilegíveis preservadas em backup. ' + str(error)
        initial.update(senseApp=False, senseIdle=False, senseCursor=False, shakeEnabled=False)
    preferences = _mobile_preferences(initial)
    game = Game(data, content)
    game.configure(preferences)
    motion_clock = ExpressionMotion(time.monotonic())
    dialogue = Dialogue()
    fetcher = OnlineReactionFetcher()


def configure(value):
    global preferences
    patch = json.loads(value) if isinstance(value, str) else value
    if not isinstance(patch, dict):
        raise ValueError('Preferências precisam ser um objeto.')
    updated = _mobile_preferences(patch, preferences)
    atomic_json(settings_path, dict(schemaVersion=1, preferences=updated))
    preferences = updated
    _apply_size()
    if not preferences['onlineReactions'] or not preferences['mischiefEnabled']:
        fetcher.clear()
        media_cache.clear()
        media_requested.clear()


def _apply_size():
    applied = copy.deepcopy(preferences)
    if size:
        applied['avatarSize'] = min(applied['avatarSize'], max(48., min(size[:2]) - 24.))
    game.configure(applied)


def resize(width, height, density=1.):
    global size
    if not all(number(value) for value in (width, height, density)) or width < 80 or height < 100:
        return
    if size == (width, height, density):
        return
    size = width, height, density
    _apply_size()
    game.desktop(dict(areas=[dict(x=0., y=0., width=width, height=height, scaleFactor=1.)]))


def context(package_name, idle_seconds):
    idle = max(0., float(idle_seconds)) if number(idle_seconds) else 0.
    game.idle = idle if preferences['senseIdle'] else None
    program = str(package_name).rsplit('.', 1)[-1] if preferences['senseApp'] else 'unknown'
    game.activity = detect_activity(program, game.idle or 0., game.prof['away_after'])
    game.senses.on_events(game.tracker.observe(program, game.activity))


def action(kind, target='', x=0., y=0., vx=0., vy=0.):
    if not all(number(value) for value in (x, y, vx, vy)):
        return
    event = dict(type=kind, x=float(x), y=float(y), vx=float(vx), vy=float(vy))
    clean_target = str(target).removeprefix('cancel-')
    if clean_target == 'toy':
        event['id'] = game.ball.id
    elif clean_target not in ('', 'pet', 'paddle'):
        event['id'] = clean_target.removeprefix('object:')
    if kind == 'drag-end' and str(target).startswith('cancel-'):
        event['cancelled'] = True
    if kind == 'toy-style':
        configure(dict(toyAppearance='ball' if game.ball.appearance == 'peanut' else 'peanut'))
        return
    if kind in ('lift', 'kick'):
        event.update(type='play', trick=kind)
    game.interact(event)


def control(value):
    global preview, selected_neuron, monitor_cache, last_error
    event = json.loads(value) if isinstance(value, str) else value
    if not isinstance(event, dict):
        raise ValueError('Comando precisa ser um objeto.')
    kind = event.get('type')
    if kind == 'suspend':
        game._cancel_holds(time.monotonic())
        return
    if kind == 'reaction-failed':
        ident = str(event.get('id', ''))
        item = game.objects.get(ident)
        if item is not None and item.kind == 'meme':
            game.mischief_ctl.abort_thing(item)
            media_cache.pop(ident, None)
            media_requested.discard(ident)
            last_error = 'Não foi possível exibir esta reação online.'
        return
    if kind == 'expression':
        name = event.get('name')
        preview = (name, time.monotonic(), 4.) if name in EXPRESSION_NAMES else None
        return
    if kind in ('stop-expression', 'expression-clear'):
        preview = None
        return
    if kind == 'inspect-neuron':
        value = event.get('index')
        selected_neuron = value if type(value) is int and 0 <= value < game.brain.N else None
        game.last_monitor_snapshot = -1.
        return
    if kind == 'reset-appearance':
        configure(dict(avatarSize=120, opacity=1., objectScales=defaults()['objectScales']))
        return
    if kind == 'stop-pingpong':
        game.stop_pingpong()
        return
    if kind == 'reset-memory':
        monitor_cache.clear()
    game.interact(event)


def motion(ax, ay, shake=False):
    global last_motion
    now = time.monotonic()
    if (shake is not True or not preferences['shakeEnabled'] or now - last_motion < .85
            or not game.pet_visible() or game.pop_started is not None or game.panel
            or not number(ax) or not number(ay)):
        return
    last_motion = now
    game.stop_pingpong()
    ax, ay = max(-24., min(24., ax)), max(-24., min(24., ay))
    intensity = min(1., math.hypot(ax, ay) / 22.)
    if game.mesa.sentado and not game.body.held:
        game.mesa.levantar_arrancado(now)
        game.state.at_desk = False
        game.state.desk_top = None
    for body in (game.body, game.ball.body):
        if body.held:
            continue
        body.grounded = False
        body.platform = None
        body.vx = max(-1000., min(1000., body.vx - ax * 27.))
        body.vy = max(-700., min(1100., -ay * 22. - 100.))
        body.omega = max(-900., min(900., body.omega - ax * 33.))
    game.senses.thrown(intensity)
    game.drives.stimulate('throw')
    if not game.body.held:
        game.in_flight = True
    game.intelligence.choose('phone_motion_reaction', ['atento', 'assustado', 'tonto', 'sacudir'],
        rates=game.rates, emotion=game.state.emotion, energy=game.drives.energy,
        contact=game.drives.contact, source='phone_motion_neural_policy',
        weights={'assustado': .25*intensity, 'tonto': .2*intensity})
    chosen = game.intelligence.current_decision
    if chosen and chosen['target'] in ('tonto', 'sacudir'):
        game.play_reaction = dict(kind=chosen['target'], started=now, until=now+1.8, intensity=intensity)


def _update_reactions(now, dt):
    global last_error
    active = {key for key, item in game.objects.items() if item.kind == 'meme' and not item.closed}
    media_requested.intersection_update(active)
    for key in list(media_cache):
        if key not in active:
            media_cache.pop(key)
            media_requested.discard(key)
    if not preferences['onlineReactions'] or not preferences['mischiefEnabled']:
        return
    for key in active:
        item = game.objects[key]
        if key not in media_requested and item.isVisible():
            if fetcher.submit(key, item.emotion, item.reaction_kind):
                media_requested.add(key)
    for key, payload, error in fetcher.poll():
        item = game.objects.get(key)
        if item is None or key not in active:
            continue
        if error or payload is None or sum(len(row[0].data) for row in media_cache.values()) + len(payload.data) > MAX_TOTAL_MEDIA_BYTES:
            last_error = 'Reação online indisponível. ' + str(error or 'Limite de memória atingido.')
            game.mischief_ctl.abort_thing(item)
            continue
        kind = validate_media_signature(payload.data, payload.content_type)
        media_cache[key] = payload, 15., kind
        item.source_url = payload.candidate.source_url
        item.provider = payload.candidate.provider
        item.attribution = payload.candidate.attribution
    for key, (payload, remaining, kind) in list(media_cache.items()):
        if not game.panel:
            remaining -= dt
        media_cache[key] = payload, remaining, kind
        if remaining <= 0:
            item = game.objects.get(key)
            if item:
                game.mischief_ctl.abort_thing(item)
            media_cache.pop(key)
            media_requested.discard(key)


def media(ident):
    entry = media_cache.get(str(ident))
    return entry[0].data if entry else b''


def _neural_snapshot(data):
    if not game.monitor_open:
        monitor_cache.clear()
        return
    if 'neural' in data:
        monitor_cache.update({key: data[key] for key in ('neural', 'intelligence', 'learned') if key in data})
        neural = monitor_cache['neural']
        if selected_neuron is not None:
            import numpy as np
            matrix = game.brain.W
            candidates = [(float(abs(matrix[selected_neuron, target])), selected_neuron, int(target), float(matrix[selected_neuron, target]))
                          for target in np.flatnonzero(matrix[selected_neuron])]
            candidates += [(float(abs(matrix[source, selected_neuron])), int(source), selected_neuron, float(matrix[source, selected_neuron]))
                           for source in np.flatnonzero(matrix[:, selected_neuron])]
            candidates.sort(reverse=True)
            neural['connections'] = [dict(source=source, target=target, weight=weight)
                                     for _, source, target, weight in candidates[:70]]
            neural['selected'] = selected_neuron
        monitor_cache['decisionLog'] = game.intelligence.snapshot()['history']
    data.update(monitor_cache)


def tick(dt):
    global say_until, say_started, say_text, say_thought, preview, last_gaze, last_ear_gaze
    global last_diagnostic, diagnostic
    now = time.monotonic()
    dt = max(0., min(.05, float(dt)))
    game.tick(dt, now)
    pose = dict(motion_clock.update(game, now))
    pose['mouth_enabled'] = preferences.get('mouthEnabled', True)
    if preview:
        name, began, duration = preview
        if now-began < duration:
            pose = animation_pose(name, now-began)
            pose['mouth_enabled'] = preferences.get('mouthEnabled', True)
        else:
            preview = None
    goal = pose.get('gaze') or game.state.gaze
    if pose['effect'] == 'perseguindo':
        last_gaze = last_ear_gaze = goal
    else:
        last_gaze = tuple(value+(target-value)*(1.-math.exp(-22.*dt)) for value,target in zip(last_gaze,goal))
        last_ear_gaze = tuple(value+(target-value)*(1.-math.exp(-12.*dt)) for value,target in zip(last_ear_gaze,goal))
    note_visible = game.mischief.has_note()
    if note_visible:
        say_until = 0.
    if preferences['speechEnabled'] and not note_visible:
        line = dialogue.update(game, now)
        if line:
            say_text, say_thought = line
            say_started = now
            say_until = now + max(2.6, min(5., 1.7+len(say_text)/18.))
    _update_reactions(now, dt)
    data = game.snapshot()
    _neural_snapshot(data)
    for item in data['objects']:
        item['emotion'] = getattr(game.objects[item['id']], 'emotion', 'observando')
        item['mediaReady'] = item['id'] in media_cache
        if item['mediaReady']:
            payload, _, kind = media_cache[item['id']]
            item.update(mediaType=kind, sourceUrl=payload.candidate.source_url,
                        attribution=payload.candidate.attribution, provider=payload.candidate.provider)
    pet, toy = game.body, game.ball.body
    reaction = game.play_reaction
    impact = reaction.get('impact_point', (toy.x, toy.y))
    data.update(version=VERSION, radius=pet.half_w, phase=now, pose=pose,
        poseMode=preview[0] if preview else motion_clock.mode, gaze=last_gaze, earGaze=last_ear_gaze,
        bounds=game.bounds(), cursor=game.cursor, deskTop=game.state.desk_top, visible=game.pet_visible(now),
        interactive=game.pet_interactive(), preferences=copy.deepcopy(preferences),
        asleep=game.sleep.asleep, caressing=game.state.feliz_fechado(now),
        toyX=toy.x, toyY=toy.y, toyRadius=toy.half_w, toyAngle=math.degrees(game.ball.roll_angle),
        toyVisible=game.ball.isVisible() and game.visible(), toyAppearance=game.ball.appearance,
        notebook=game.mesa.caderno.snapshot() if game.mesa.caderno.isVisible() else None,
        impactX=impact[0], impactY=impact[1],
        impact=reaction.get('started', 0.) if reaction.get('kind') == 'brinquedo_rebatida' else 0.,
        text=say_text if preferences['speechEnabled'] and now < say_until and not game.panel else '',
        thought=say_thought, speechStarted=say_started,
        speechAlpha=max(0., min(1., (now-say_started)/.22, (say_until-now)/.3)),
        expressionNames=EXPRESSION_NAMES)
    if game.pingpong:
        match = game.pingpong
        data['pingpong'] = dict(area=match.area, cursor=game.cursor, paddleRadius=match.cursor_radius,
            playerScore=match.player_score, petScore=match.pet_score, rally=match.rally, best=match.best,
            paused=game.pingpong_paused(), finished=match.finished, winner=match.winner)
    else:
        data['pingpong'] = None
    if now-last_diagnostic >= .5:
        diagnostic = (f'Bolha {VERSION}\nAndroid · cérebro Python local · 470 neurônios\n'
            f'Humor {game.state.emotion} · energia {game.drives.energy:.0%}\n'
            f'Objetivo {game.intelligence.goal or "observando"}\n'
            f'Arrays neurais {game.brain_array_mib:.2f} MiB\n'
            f'Leituras opcionais · aplicativo {preferences["senseApp"]} · toque {preferences["senseCursor"]}'
            f' · ociosidade {preferences["senseIdle"]} · movimento {preferences["shakeEnabled"]}\n'
            f'Aviso local {last_error or "nenhum"}')
        last_diagnostic = now
    data['diagnostics'] = diagnostic
    return json.dumps(data, allow_nan=False)


def save():
    if game is not None:
        game.save()
