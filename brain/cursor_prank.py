# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Intenção de brincar com o ponteiro, escolhida pela política neural existente."""
import math

from pestinha.core.physics import GRAVITY


IDLE_SECONDS = 120.
COOLDOWN_SECONDS = 300.
CHEW_SECONDS = .8


class CursorPrank:
    def __init__(self):
        self.phase = None
        self.started = 0.
        self.attempt_started = 0.
        self.next_attempt = 0.
        self.next_offer = 0.
        self.angry_since = None
        self.angry_attempt = False
        self.hidden_cursor = False
        self.anchor = None
        self.episode = None
        self.recent_episode = None
        self.recent_until = 0.
        self.intensity = .5
        self.guided = False
        self.target = None

    @property
    def active(self):
        return self.phase is not None

    @property
    def holds_position(self):
        return self.phase in ('swallow', 'chew')

    def _choose(self, game, name, choices, weights, duration=0.):
        picked = game.intelligence.choose(
            'cursor_prank_' + name, choices, rates=game.rates,
            emotion=game.state.emotion, energy=game.drives.energy,
            contact=game.drives.contact, duration=duration,
            source='cursor_prank_policy', weights=weights)
        decision = game.intelligence.current_decision
        if decision and decision.get('source') == 'cursor_prank_policy':
            decision['factors']['idleSeconds'] = float(game.idle or 0.)
            decision['factors']['angryAttempt'] = self.angry_attempt
        return picked if picked in choices else None

    def _enter(self, phase, now):
        self.phase, self.started = phase, now
        self.hidden_cursor = phase in ('swallow', 'chew')

    def cancel(self, game, now, result='interrompido', reward=0.):
        self.hidden_cursor = False
        self.guided = False
        self.target = None
        self.phase = None
        self.anchor = None
        if self.episode is not None and any(ep is self.episode for ep in game.memory.open):
            game.memory._resolve(self.episode, result, reward)
            self.recent_episode = self.episode['id']
            self.recent_until = now + 15.
        self.episode = None
        self.next_offer = max(self.next_offer, now + 10.)

    def feedback(self, game, value, now):
        if self.episode is not None and any(ep is self.episode for ep in game.memory.open):
            game.memory._resolve(self.episode, 'carinho' if value > 0 else 'pedido de sossego', value)
        elif self.recent_episode is not None and now <= self.recent_until:
            game.memory._revisar(self.recent_episode, 'carinho' if value > 0 else 'pedido de sossego', value)
        self.recent_episode = None
        self.episode = None
        if value < 0:
            self.cancel(game, now)

    def _spit(self, game, now, result):
        # A restauração é imediata. A escolha neural controla a reação que vem depois.
        self.hidden_cursor = False
        picked = self._choose(game, 'release', ['spit', 'queasy', 'shake_off'],
                              {'spit': .35, 'queasy': .25 + self.intensity * .25,
                               'shake_off': .12}, 1.35)
        self.intensity = .9 if self.angry_attempt or picked == 'queasy' else .6 if picked == 'spit' else .4
        self._enter('spit', now)
        if self.episode is not None and any(ep is self.episode for ep in game.memory.open):
            game.memory._resolve(self.episode, result, 0.)
            self.recent_episode = self.episode['id']
            self.recent_until = now + 15.
        self.episode = None

    def pointer_moved(self, game, now):
        if self.guided:
            return
        if self.hidden_cursor:
            self._spit(game, now, 'ponteiro escapou')
        elif self.phase in ('approach', 'pounce') and not self.angry_attempt:
            self.cancel(game, now, 'ponteiro voltou a se mover')

    def _allowed(self, game, now):
        return (game.prefs.get('cursorPrankEnabled', False)
                and game.prefs.get('adaptiveBehavior', True)
                and game.prefs.get('senseCursor', True)
                and not game.intelligence.compatibility
                and game.pet_visible()
                and not game.panel and not game.body.held and not game.scene_dragging
                and not game.sleep.asleep and not game.mesa.sentado
                and not game.castigo.dentro and not game.castigo.fuga
                and not (game.prefs.get('protestsEnabled', True)
                         and (game.protest.stage or game.sad.stage))
                and not game.behavior.mission and game.pingpong is None
                and not game.play.juggling() and not game.play.finishing_juggle(now)
                and game.pop_started is None)

    def start_finder(self, game, now):
        if (not game.pet_interactive() or game.panel or game.body.held
                or game.scene_dragging or game.castigo.dentro or game.castigo.fuga):
            return False
        if self.active:
            self.cancel(game, now)
        game.play.stop_chase()
        game.play.stop_juggle()
        game.stop_pingpong()
        if game.mesa.sentado:
            game.mesa.levantar_arrancado(now)
            game._sync_desk_pose()
        if game.sleep.asleep:
            game.sleep.wake(startled=False)
        self.guided = True
        self.angry_attempt = False
        self.intensity = .68
        self._enter('approach', now)
        return True

    def release_finder(self, game, now):
        if not self.guided or self.phase in ('spit', 'recover'):
            return
        if self.holds_position:
            self._enter('spit', now)
        else:
            self.cancel(game, now)

    def _follow_finder(self, game, dt, now):
        if not game.pet_interactive() or game.panel or game.body.held or game.sleep.asleep:
            self.cancel(game, now)
            return False
        if self.phase == 'spit':
            if now - self.started >= 1.35:
                self.cancel(game, now)
            return False
        if self.target is None:
            return False
        x, y, area, reachable = self.target
        areas = game.available_areas()
        if area not in areas:
            return True
        body = game.body
        body.angle *= math.exp(-16. * dt)
        offset = body.half_w * 18. / 49.
        hop = 0. if self.holds_position else 13. * abs(math.sin((now-self.started)*9.))
        left, top, right, bottom = area
        radius = body.half_w
        goal_x = min(right-radius, max(left+radius, x)) if right-left > 2*radius else (left+right)/2
        goal_y = min(bottom-radius, max(top+radius, y-offset-hop)) if bottom-top > 2*radius else (top+bottom)/2
        distance = math.hypot(goal_x-body.x, goal_y-body.y)
        travel = min(distance, (380. + min(1420., distance * 2.6))*dt)
        if distance > 0.:
            body.x += (goal_x-body.x) * travel / distance
            body.y += (goal_y-body.y) * travel / distance
        # O vão do desktop e telas cheias não podem prender a Bolha no caminho.
        # Nesse caso ela reaparece no lado seguro da tela de destino.
        if not any(l <= body.x < r and t <= body.y < b for l, t, r, b in areas):
            body.x, body.y = goal_x, goal_y
        body.vx = body.vy = body.omega = 0.
        body.grounded = False
        body.platform = None
        game.state.gaze = (max(-1., min(1., (x-body.x)/max(radius,1.))),
                           max(-1., min(1., (y-body.y)/max(radius,1.))))
        if self.phase == 'approach' and reachable and distance <= max(10., hop + 4.):
            self._enter('swallow', now)
        elif self.phase == 'swallow' and now - self.started >= .32:
            self._enter('chew', now)
        return True

    def update(self, game, dt, now):
        if self.guided:
            return self._follow_finder(game, dt, now)
        idle = game.prefs.get('senseIdle', True) and float(game.idle or 0.) >= IDLE_SECONDS
        if (not self._allowed(game, now) or now < game.quiet_until
                or (self.active and not self.angry_attempt and not game.prefs.get('senseIdle', True))):
            if self.active:
                self.cancel(game, now)
            self.angry_since = None
            return False
        if (self.phase in ('approach', 'pounce') and not self.angry_attempt
                and not idle):
            self.cancel(game, now, 'usuário voltou à atividade')
            return False
        anger = game.state.tone.r.get('ANGRY', 0.)
        angry = game.state.emotion == 'bravo' and anger >= .72
        self.angry_since = (self.angry_since if self.angry_since is not None else now) if angry else None
        if not self.active:
            if now < self.next_attempt or not game.body.grounded or game.state.caressing(now):
                return False
            reactions = (game.release_reaction, game.play_reaction)
            frustration = max((reaction['intensity'] for reaction in reactions
                               if reaction.get('kind') in ('bravo','birra','brinquedo_frustrado')
                               and now < reaction['until']), default=0.)
            sustained = self.angry_since is not None and now-self.angry_since >= 1.6
            self.angry_attempt = sustained or frustration >= .60
            if not self.angry_attempt and (not idle or now < self.next_offer):
                return False
            self.next_offer = now + 15.
            self.intensity = min(1., .35 + .65 * max(anger, frustration))
            neural = min(1., game.rates.get('WATCH', 0.) / 30.)
            choices = ['approach'] if self.angry_attempt else ['watch', 'approach']
            choice = self._choose(game, 'intent', choices,
                                  {'watch': .12 + .3 * (1. - game.drives.energy),
                                   'approach': .18 + .18 * neural + .38 * self.intensity
                                   + .12 * game.drives.contact}, 8.)
            if choice != 'approach':
                return False
            self.next_attempt = now + COOLDOWN_SECONDS
            self.attempt_started = now
            self.anchor = tuple(game.cursor)
            self._enter('approach', now)
            game.play.stop_chase()
            decision = game.intelligence.current_decision
            game.intelligence.clear_goal()
            game.intelligence.current_decision = decision
            game.behavior.adaptive_goal = None
            self.episode = game.memory.start('cursor_prank_intent|' + game.state.emotion, 'approach')

        if self.phase in ('approach', 'pounce'):
            if now - self.attempt_started > 8.:
                self._choose(game, 'finish', ['give_up'], {'give_up': 1.})
                self.cancel(game, now, 'ponteiro fora de alcance')
                return False
            return self._pursue(game, dt, now)
        if self.phase == 'swallow':
            game.body.vx = game.body.vy = game.body.omega = 0.
            if now - self.started >= .32:
                choices = ['chew'] if self.angry_attempt else ['chew', 'spit']
                choice = self._choose(game, 'swallow', choices,
                                      {'chew': .55 + .2 * self.intensity, 'spit': .1})
                self._enter('chew' if choice == 'chew' else 'spit', now)
            return self.holds_position
        if self.phase == 'chew':
            game.body.vx = game.body.vy = game.body.omega = 0.
            if now-self.started >= CHEW_SECONDS:
                self._spit(game, now, 'cuspiu o ponteiro')
                return False
            return True
        if self.phase == 'spit' and now - self.started >= 1.35:
            self._choose(game, 'recover', ['recover'], {'recover': 1.}, 1.)
            self._enter('recover', now)
        elif self.phase == 'recover' and now - self.started >= 1.:
            self.cancel(game, now, 'brincadeira encerrada')
        return False

    @staticmethod
    def mouth_position(body):
        """Mesmo centro e rotação usados no desenho, em coordenadas da área de trabalho."""
        angle = math.radians(body.angle)
        offset = body.half_w * 18. / 49.
        return body.x - math.sin(angle) * offset, body.y + math.cos(angle) * offset

    def _pursue(self, game, dt, now):
        body = game.body
        target_x, target_y = game.cursor
        # A boca fica abaixo dos olhos. A captura exige contato real com o corpo.
        mouth_x, mouth_y = self.mouth_position(body)
        distance = math.hypot(target_x - mouth_x, target_y - mouth_y)
        if distance <= max(12., body.half_w * .27):
            choices = ['swallow'] if self.angry_attempt else ['swallow', 'give_up']
            choice = self._choose(game, 'capture', choices,
                                  {'swallow': .65 + self.intensity * .2, 'give_up': .08}, .32)
            if choice == 'swallow':
                self.anchor = tuple(game.cursor)
                self._enter('swallow', now)
                body.vx = body.vy = body.omega = 0.
                body.grounded = False
                body.platform = None
                return True
            self.cancel(game, now, 'preferiu soltar o ponteiro')
            return False
        dx = target_x - mouth_x
        desired_y = target_y - (mouth_y - body.y)
        speed = 175. + 230. * self.intensity
        body.vx = max(-speed, min(speed, dx * 3.5))
        if self.phase == 'approach' and abs(dx) < 230.:
            choice = self._choose(game, 'bote', ['pounce', 'wait'],
                                  {'pounce': .45 + self.intensity * .2, 'wait': .1}, .6)
            if choice == 'pounce':
                self._enter('pounce', now)
                if body.grounded:
                    height = max(32., body.y - desired_y)
                    vy = -min(1450., math.sqrt(2. * GRAVITY * height))
                    flight = max(.2, abs(vy) / GRAVITY)
                    body.jump(max(-900., min(900., dx / flight)), vy)
        elif self.phase == 'pounce' and body.grounded and now - self.started > .45:
            self._enter('approach', now)
        return False

    def snapshot(self):
        return dict(phase=self.phase, started=self.started, intensity=self.intensity,
                    cursorHidden=self.hidden_cursor, angry=self.angry_attempt,
                    cursor=self.anchor)
