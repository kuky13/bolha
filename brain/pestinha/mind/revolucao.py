# SPDX-License-Identifier: GPL-3.0-or-later
# Adapted from Pestinha by @mille-okws and contributors; see NOTICE.md.
"""A política neural decide os lançamentos; limites mantêm a cena discreta."""
import math

from ..body.bolinha import Ball
from ..ajustes import GANHO_PAPEL
from ..body.toy import bounce_off, push_from_cursor

MAXIMO_PAPEIS = 6
VIDA_PAPEL = 5.0
INTERVALO_MINIMO = .6


class RevolucaoController:
    def __init__(self, play, debug):
        self.play = play
        self.papeis = []
        self.debug = debug
        self.policy = None
        self.rates = {}
        self.energy = 1.
        self.contact = 0.
        self.last_throw = -math.inf

    def tick(self, now, dt, limites, cursor, vel_cursor, corpo, visivel, revoltado,
             obstaculos, papel_hz, *, toy_appearance='peanut', enabled=True,
             sense_cursor=True, areas=None, monitors=None, displays=None):
        if not (enabled and visivel and revoltado):
            self.fechar()
            return
        areas = list([limites] if areas is None else areas)
        if not areas:
            self.fechar()
            return
        self._mover(now, dt, limites, cursor, vel_cursor, obstaculos,
                    sense_cursor, areas, monitors, displays)
        if len(self.papeis) >= MAXIMO_PAPEIS or now-self.last_throw < INTERVALO_MINIMO:
            return
        fire = self.policy.event('paper_throw', papel_hz, GANHO_PAPEL, dt,
                                rates=self.rates, emotion='revolta', energy=self.energy,
                                contact=self.contact) if self.policy else False
        if fire:
            target = self._target(corpo, cursor, sense_cursor, areas)
            self._atirar(now, target, corpo, toy_appearance, areas)

    def _target(self, body, cursor, sense_cursor, areas):
        def contains(area, point):
            return area[0] <= point[0] < area[2] and area[1] <= point[1] < area[3]
        # Não mira num vão, numa tela bloqueada ou num sensor desligado.
        if sense_cursor and any(contains(area, cursor) for area in areas):
            area = next(area for area in areas if contains(area, cursor))
            target = cursor
        else:
            area = next((area for area in areas if contains(area, (body.x, body.y))), areas[0])
            left, top, right, bottom = area
            side = -1 if body.x-left > right-body.x else 1
            target = (body.x+side*min(240., (right-left)*.35), body.y-min(130.,(bottom-top)*.25))
            options = {'left': (left+(right-left)*.2, top+(bottom-top)*.45),
                       'up': ((left+right)/2, top+(bottom-top)*.2),
                       'right': (right-(right-left)*.2, top+(bottom-top)*.45)}
            if self.policy:
                choice = self.policy.choose('revolution_target', list(options), rates=self.rates,
                    emotion='revolta', energy=self.energy, contact=self.contact,
                    weights={key:max(.1,math.dist((body.x,body.y),point)/300.) for key,point in options.items()})
                target = options.get(choice, target)
        left, top, right, bottom = area
        margin = min(30., (right-left)/4, (bottom-top)/4)
        return (max(left+margin, min(right-margin, target[0])),
                max(top+margin, min(bottom-margin, target[1])))

    def _atirar(self, now, target, body, toy_appearance, areas):
        area = next((area for area in areas if area[0] <= body.x < area[2]
                     and area[1] <= body.y < area[3]), areas[0])
        radius = 17.
        x = max(area[0]+radius, min(area[2]-radius, body.x))
        y = max(area[1]+radius, min(area[3]-radius, body.y-body.half_h*.6))
        ball = Ball(x, y, kind='projectile')
        ball.appearance = 'ball' if toy_appearance == 'peanut' else 'peanut'
        self.play.throw_at(ball, target, .8, x, y)
        ball.show()
        self.papeis.append({'bola':ball, 'nascimento':now, 'ultimo_empurrao':-math.inf})
        self.last_throw = now

    def _mover(self, now, dt, limites, cursor, vel_cursor, obstacles,
               sense_cursor, areas, monitors, displays):
        alive = []
        for entry in self.papeis:
            ball = entry['bola']
            if now-entry['nascimento'] >= VIDA_PAPEL:
                ball.deleteLater()
                continue
            area = next((area for area in areas if area[0] <= ball.body.x < area[2]
                         and area[1] <= ball.body.y < area[3]), None)
            if area is None:
                # A tela foi desconectada/bloqueada: descarte o efeito, sem teleportá-lo.
                ball.deleteLater()
                continue
            ball.step(dt, area, areas, monitors, displays)
            bounce_off(ball, obstacles)
            if sense_cursor:
                entry['ultimo_empurrao'] = push_from_cursor(
                    ball, cursor, vel_cursor, now, entry['ultimo_empurrao'])
            alive.append(entry)
        self.papeis = alive

    def janelas(self):
        return [entry['bola'] for entry in self.papeis]

    def esconder(self):
        for entry in self.papeis:
            entry['bola'].hide()

    def fechar(self):
        for entry in self.papeis:
            entry['bola'].deleteLater()
        self.papeis.clear()
