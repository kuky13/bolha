# SPDX-License-Identifier: GPL-3.0-or-later
"""A interface Android usa a mesma física, memória e rede neural da Bolha."""
import json
import math
import time
from game import Game

game = None
size = None
say_until = next_speech = 0.
say_text = ''


def start(data, content):
    global game
    if game is None:
        game = Game(data, content)
        game.configure(dict(senseApp=False, senseWindows=False, senseIdle=False,
                            senseCursor=True, onlineReactions=False))


def resize(width, height):
    global size
    if width < 80 or height < 100 or size == (width, height):
        return
    game.configure(dict(avatarSize=min(136, max(64, width*.31))))
    game.desktop(dict(areas=[dict(x=0, y=0, width=width, height=height, scaleFactor=1)]))
    size = width, height


def action(kind, target='', x=0., y=0., vx=0., vy=0.):
    global say_until, next_speech, say_text
    event = dict(type=kind, x=x, y=y, vx=vx, vy=vy)
    if target in ('toy', 'cancel-toy'):
        event['id'] = game.ball.id
    if kind == 'drag-end' and target.startswith('cancel-'):
        event['cancelled'] = True
    if kind == 'toy-style':
        game.configure(dict(toyAppearance='ball' if game.ball.appearance == 'peanut' else 'peanut'))
        return
    if kind in ('lift', 'kick'):
        event.update(type='play', trick=kind)
    game.interact(event)
    now = time.monotonic()
    if kind in ('caress', 'wake') and now >= next_speech:
        say_text = 'Gostei do carinho.' if kind == 'caress' else 'Vamos brincar?'
        say_until, next_speech = now + 3., now + 45.


def tick(dt):
    now = time.monotonic()
    game.tick(min(.05, dt), now)
    pet, toy = game.body, game.ball.body
    reaction = game.play_reaction
    impact = reaction.get('impact_point', (toy.x, toy.y))
    return json.dumps(dict(x=pet.x, y=pet.y, radius=pet.half_w, angle=pet.angle,
        emotion=game.state.emotion, gaze=game.state.gaze, asleep=game.sleep.asleep,
        caressing=game.state.caressing(now), toyX=toy.x, toyY=toy.y, toyRadius=toy.half_w,
        toyAngle=math.degrees(game.ball.roll_angle), toyVisible=game.ball.isVisible(),
        toyAppearance=game.ball.appearance, impactX=impact[0], impactY=impact[1],
        notebook=game.mesa.caderno.snapshot() if game.mesa.caderno.isVisible() else None,
        impact=reaction.get('started',0.) if reaction.get('kind')=='brinquedo_rebatida' else 0.,
        text=say_text if now < say_until else '', energy=game.drives.energy, neurons=game.brain.N))


def save():
    if game is not None:
        game.save()
