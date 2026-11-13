# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Intenção de brincar com o ponteiro, escolhida pela política neural existente."""
import math

from pestinha.core.physics import GRAVITY


IDLE_SECONDS = 120.
COOLDOWN_SECONDS = 300.


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

    def pointer_moved(self, game, now):
        # A restauração é imediata. A escolha neural controla a reação que vem depois.
        if self.hidden_cursor:
            self.hidden_cursor = False
            picked = self._choose(game, 'release', ['spit', 'queasy', 'shake_off'],
                                  {'spit': .35, 'queasy': .25 + self.intensity * .25,
                                   'shake_off': .12}, 1.35)
            self.intensity = .9 if picked == 'queasy' else .6 if picked == 'spit' else .4
            self._enter('spit', now)
            if self.episode is not None and any(ep is self.episode for ep in game.memory.open):
                game.memory._resolve(self.episode, 'ponteiro escapou', 0.)
                self.recent_episode = self.episode['id']
                self.recent_until = now + 15.
            self.episode = None
        elif self.phase in ('approach', 'pounce') and not self.angry_attempt:
            self.cancel(game, now, 'ponteiro voltou a se mover')

    def _allowed(self, game):
        return (game.prefs.get('cursorPrankEnabled', False)
                and game.prefs.get('adaptiveBehavior', True)
                and game.prefs.get('senseCursor', True)
                and game.prefs.get('senseIdle', True)
                and not game.intelligence.compatibility
                and game.pet_visible()
                and not game.panel and not game.body.held and not game.scene_dragging
                and not game.sleep.asleep and not game.mesa.sentado
                and not game.castigo.dentro and not game.castigo.fuga
                and not game.protest.stage and not game.sad.stage
                and not game.behavior.mission and game.pingpong is None
                and game.pop_started is None)

    def update(self, game, dt, now):
        if not self._allowed(game) or now < game.quiet_until:
            if self.active:
                self.cancel(game, now)
            self.angry_since = None
            return False
        if (self.phase in ('approach', 'pounce') and not self.angry_attempt
                and float(game.idle or 0.) < IDLE_SECONDS):
            self.cancel(game, now, 'usuário voltou à atividade')
            return False
        angry = game.state.emotion == 'bravo' and game.state.tone.r.get('ANGRY', 0.) >= .72
        self.angry_since = (self.angry_since if self.angry_since is not None else now) if angry else None
        if not self.active:
            if now < self.next_attempt or now < self.next_offer or not game.body.grounded:
                return False
            self.angry_attempt = self.angry_since is not None and now - self.angry_since >= 1.6
            idle = float(game.idle or 0.) >= IDLE_SECONDS
            if not idle and not self.angry_attempt:
                return False
            self.next_offer = now + 15.
            self.intensity = min(1., .35 + .65 * game.state.tone.r.get('ANGRY', 0.))
            neural = min(1., game.rates.get('WATCH', 0.) / 30.)
            choice = self._choose(game, 'intent', ['watch', 'approach'],
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
                choice = self._choose(game, 'swallow', ['chew', 'spit'],
                                      {'chew': .55 + .2 * self.intensity, 'spit': .1})
                self._enter('chew' if choice == 'chew' else 'spit', now)
            return self.holds_position
        if self.phase == 'chew':
            game.body.vx = game.body.vy = game.body.omega = 0.
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
            choice = self._choose(game, 'capture', ['swallow', 'give_up'],
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
