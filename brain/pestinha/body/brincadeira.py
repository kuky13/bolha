# SPDX-License-Identifier: GPL-3.0-or-later
# Adapted from Pestinha by @mille-okws and contributors; see NOTICE.md.
"""
BRINCADEIRA - como o pet brinca: chuta a bolinha, arremessa no cursor, cola post-its.

Um pet só faz tudo. O que muda de um pet para outro são os PESOS, no campo
"brincadeira" de pets/*.json, por exemplo:

    "brincadeira": {"bola": 1.0, "arremesso": 0.6, "postit": 0.5}

Peso 0 desliga aquele jeito de brincar. Quem decide se ele brinca agora é a
emoção (vinda da rede): bola quando está feliz/curioso/contente, arremesso
quando está bravo, e tudo quando está em revolução.

Na revolução, além da bolinha, ele arremessa bolinhas de papel no cursor.
"""

import math

from ..core.physics import GRAVITY
from ..ajustes import (
    ALCANCE_BRINCADEIRA as REACH,
    TEMPO_VOO_ARREMESSO as FLIGHT_TIME,
    INTERVALO_BRINCADEIRA as PLAY_EVERY,
    INTERVALO_PAPEL as PAPER_EVERY,
)

DEFAULT_WEIGHTS = {"bola": 1.0, "arremesso": 0.6, "postit": 0.5}


def weights_of(value):
    """Aceita o formato novo (dict) e o antigo (nome do estilo)."""
    if isinstance(value, dict):
        return {k: float(v) for k, v in value.items()}
    presets = {
        "bola": {"bola": 1.0},
        "arremesso": {"arremesso": 1.0},
        "postit": {"postit": 1.0},
        "quieto": {},
    }
    return presets.get(value, dict(DEFAULT_WEIGHTS))


class Play:
    """Escolhe as brincadeiras do pet (bola, arremesso, post-it) e quando cada uma pode acontecer, com os pesos do .json."""
    def __init__(self, weights):
        """Guarda os pesos de cada brincadeira (0 desliga) e o próximo instante permitido."""
        self.w = weights_of(weights)
        self.next_at = 0.0
        self.next_paper = 0.0
        self.policy = None
        self.rates = {}
        self.energy = 1.
        self.contact = 0.
        self.requested_action = None
        self.chase_until = 0.
        self.toy_in_reach = False
        self.last_tease = -math.inf
        self.teases = 0

    def weight(self, key):
        """Peso de uma brincadeira pelo nome (0 se não existir)."""
        return self.w.get(key, 0.0)

    def notice_toy_move(self, now, body, ball):
        """Um movimento do jogador convida para brincar e pode tirar a bola do alcance."""
        if self.weight('bola') <= 0.:
            return None
        started = now >= self.chase_until
        if started:
            self.toy_in_reach = False
        self.chase_until = now + 10.
        distance = math.hypot(ball.body.x-body.x, ball.body.y-body.y)
        reach = body.half_w + ball.body.half_w + 34.
        if distance <= reach:
            self.toy_in_reach = True
        elif distance > reach + 42. and self.toy_in_reach:
            self.toy_in_reach = False
            if now-self.last_tease > 10.:
                self.teases = 0
            self.last_tease = now
            self.teases += 1
            return 'taken'
        return 'started' if started else None

    def stop_chase(self):
        self.chase_until = 0.
        self.toy_in_reach = False

    def follow(self, dt, now, body, ball, cursor, tone, emotion):
        """Corre e salta atrás do brinquedo, devolvendo apenas quando o alcança."""
        if (now >= self.chase_until or not ball.isVisible() or self.energy <= .18):
            return None
        toy = ball.body
        dx, dy = toy.x-body.x, toy.y-body.y
        reach = body.half_w + toy.half_w
        distance = math.hypot(dx, dy)
        held = toy.held or ball.dragging
        if distance <= reach+34.:
            self.toy_in_reach = True
        if not held and distance <= reach+20.:
            player_side = cursor[0]-toy.x if cursor is not None else 0.
            direction = math.copysign(1., player_side if abs(player_side)>40. else dx or 1.)
            style = self.policy.choose('toy_return', ['tap','lob'], rates=self.rates, emotion=emotion,
                                       energy=self.energy, contact=self.contact,
                                       weights={'tap':.25, 'lob':.14+.55*tone.vigor()}) if self.policy else 'tap'
            speed = max(170., min(360., abs(player_side)*2.5)) if abs(player_side)>40. else 260.
            ball.kick(direction*speed, -470. if style=='lob' else -365.)
            self.stop_chase()
            self.next_at = now+2.2
            if body.grounded:
                body.jump(body.vx*.3, -235.)
            return 'return'
        if body.grounded:
            speed = min(510., max(310., tone.speed()*2.))
            desired = max(-speed, min(speed, dx*5.)) if abs(dx)>reach*.72 else 0.
            change = 1800.*dt
            body.vx += max(-change,min(change,desired-body.vx))
            if -160. <= dy < -28. and abs(dx) < reach+90.:
                body.jump(body.vx, max(-770., min(-440., -tone.hop_power())))
                return 'hop'
        return 'chase'

    def tick(self, now, body, ball, cursor, emotion, pull=1.0):
        """
        Devolve 'kick' ou 'throw' quando brinca com a bolinha, senão None.
        pull (0..1): quanto a rede quer brincar agora (distração acima do foco). Zero, ele trabalha.
        """
        happy = emotion == "feliz"
        if ball is None or not ball.isVisible() or now < self.next_at:
            return None
        if getattr(ball, "dragging", False):      # a bolinha está na mão do usuário: não é dele
            return None
        if math.hypot(ball.body.x - body.x, ball.body.y - body.y) > REACH * (1.4 if happy else 1.0):
            return None
        if self.requested_action:
            action, self.requested_action = self.requested_action, None
            self.next_at = now + (PLAY_EVERY[0]+PLAY_EVERY[1])/2
            if action == 'kick':
                side = 1 if ball.body.x >= body.x else -1
                ball.kick(side * 500., -410.)
                return 'kick'
            if action == 'throw':
                return self.throw_at(ball, cursor, FLIGHT_TIME, ball.body.x, ball.body.y) and 'throw'
        if pull <= 0.0:
            return None
        if math.hypot(ball.body.x-body.x, ball.body.y-body.y) > body.half_w+ball.body.half_w+12.:
            return None
        choices = ['kick'] if emotion in ("feliz", "curioso", "contente") and self.weight("bola") > 0 else []
        if emotion == 'bravo' and self.weight('arremesso') > 0: choices.append('throw')
        choices.append('wait')
        weights = {'kick': .7*self.weight('bola')*pull, 'throw': .6*self.weight('arremesso')*pull, 'wait': .15}
        if self.policy:
            action = self.policy.choose('toy_play', choices, rates=self.rates, emotion=emotion,
                                        energy=self.energy, contact=self.contact,
                                        duration=(PLAY_EVERY[0]+PLAY_EVERY[1])/2, weights=weights)
        else:
            action = 'wait'
        lo, hi = PLAY_EVERY
        self.next_at = now + ((lo+hi)/2 if happy else (lo+hi))

        if action == 'kick':
            side = 1 if ball.body.x >= body.x else -1          # chuta para o lado oposto a ele
            ball.kick(side * 500.0, -410.0)
            return "kick"

        if action == 'throw':
            return self.throw_at(ball, cursor, FLIGHT_TIME, ball.body.x, ball.body.y) and "throw"
        return None

    def throw_at(self, ball, cursor, flight, x0, y0):
        """Arremessa algo de (x0, y0) para o cursor, com trajetória que chega até ele."""
        T = flight
        dx = cursor[0] - x0
        dy = cursor[1] - y0
        vx = max(-1400.0, min(1400.0, dx / T))
        vy = (dy - 0.5 * GRAVITY * T * T) / T
        ball.kick(vx, vy)
        return True

    def paper_due(self, now, revolution, body):
        """Na revolução, uma bolinha de papel a cada PAPER_EVERY s, se ele ainda tiver peso para isso."""
        if not revolution or self.weight("arremesso") <= 0 or now < self.next_paper:
            return False
        self.next_paper = now + PAPER_EVERY
        return True
