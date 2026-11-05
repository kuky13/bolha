# SPDX-License-Identifier: GPL-3.0-only
"""Modelo da partida de pingue-pongue em coordenadas do desktop."""
from __future__ import annotations

import math


class PingPong:
    """Single-player rally model in desktop coordinates.

    ``area`` is the usable monitor rectangle ``(left, top, right, bottom)``.
    The ball is modeled as a circle; paddles are vertical segments with a small
    fixed width. ``cursor`` may be an ``(x, y)`` pair or a y coordinate.
    """
    HUD_TOP = 75.0
    HUD_BOTTOM = 40.0
    MIN_COURT_WIDTH = 220.0
    MIN_COURT_HEIGHT = 170.0
    PADDLE_WIDTH = 12.0

    def __init__(self, area, pet_radius, toy_radius):
        if len(area) != 4:
            raise ValueError("area must be (left, top, right, bottom)")
        self.area = tuple(map(float, area))
        left, top, right, bottom = self.area
        self.pet_radius = max(1.0, float(pet_radius))
        self.toy_radius = max(2.0, float(toy_radius))
        # Keep the playfield useful for unusually large avatar artwork.
        margin = max(18.0, self.pet_radius + 10.0)
        inset_x = max(margin, (right-left-1080.)/2)
        inset_y = max(0., (bottom-top-self.HUD_TOP-self.HUD_BOTTOM-600.)/2)
        self.court = (left + inset_x, top + self.HUD_TOP + inset_y,
                      right - inset_x, bottom - self.HUD_BOTTOM - inset_y)
        l, t, r, b = self.court
        if right <= left or bottom <= top or r - l < self.MIN_COURT_WIDTH or b - t < self.MIN_COURT_HEIGHT:
            raise ValueError("usable area is too small for ping-pong")
        self.player_half = max(25.0, min(self.pet_radius * .72, (b - t) * .24))
        self.player_x = r - self.PADDLE_WIDTH / 2
        self.pet_x = l + self.PADDLE_WIDTH / 2
        self.player_y = self.pet_y = (t + b) / 2
        self.ball_x = (l + r) / 2
        self.ball_y = (t + b) / 2
        self.vx = self.vy = 0.0
        self.player_score = self.pet_score = self.rally = self.best = 0
        self.serve_delay = .65
        self.finished = False
        self.winner = None
        self._serve_sign = 1
        self._reaction_delay = 0.

    def step(self, dt, cursor, vigor):
        """Advance by dt seconds and return a hit/point event, if one occurred."""
        if self.finished:
            return None
        dt = max(0.0, min(float(dt), .12))
        l, t, r, b = self.court
        vigor = max(0.0, min(1.0, float(vigor)))
        cy = cursor[1] if isinstance(cursor, (tuple, list)) else cursor
        try:
            cy = float(cy)
        except (TypeError, ValueError):
            cy = self.player_y
        self.player_y = self._clamp(cy, t + self.player_half, b - self.player_half)
        if self.serve_delay > 0:
            self.serve_delay = max(0.0, self.serve_delay - dt)
            if self.serve_delay == 0:
                self._start_serve()
            return None
        if dt == 0:
            return None

        # A Bolha volta ao centro e só tenta interceptar quando o brinquedo se aproxima.
        ai_speed = (145.0 + 125.0 * vigor) * min(1., (b-t)/600.)
        target = (t+b)/2
        self._reaction_delay = max(0., self._reaction_delay-dt)
        contact_x = self.pet_x + self.pet_radius + self.toy_radius
        distance = self.ball_x-contact_x
        if (self.vx < 0 and self._reaction_delay == 0.
                and distance <= min(310., (r-l)*.36)):
            anticipation = .45 + .35*vigor
            travel = max(0., distance / -self.vx)
            target = self._reflected_y(self.ball_y + self.vy*travel*anticipation,
                                       t+self.toy_radius,b-self.toy_radius)
        if self.vx >= 0 or self._reaction_delay == 0.:
            pet_margin = min(self.pet_radius, (b-t)/2.)
            target = self._clamp(target, t+pet_margin, b-pet_margin)
            self.pet_y += self._clamp(target - self.pet_y, -ai_speed * dt, ai_speed * dt)

        # Small deterministic substeps bound travel per step and prevent tunneling.
        max_step = max(1.0, self.toy_radius * .45)
        n = max(1, int(math.ceil(math.hypot(self.vx, self.vy) * dt / max_step)))
        h = dt / n
        event = None
        player_line = self.player_x - self.PADDLE_WIDTH / 2 - self.toy_radius
        for _ in range(n):
            previous_x = self.ball_x
            self.ball_x += self.vx * h
            self.ball_y += self.vy * h
            if self.ball_y - self.toy_radius < t:
                self.ball_y = 2 * (t + self.toy_radius) - self.ball_y
                self.vy = abs(self.vy)
            elif self.ball_y + self.toy_radius > b:
                self.ball_y = 2 * (b - self.toy_radius) - self.ball_y
                self.vy = -abs(self.vy)
            if (self.vx > 0 and previous_x <= player_line < self.ball_x
                    and abs(self.ball_y-self.player_y) <= self.player_half+self.toy_radius):
                self.ball_x = player_line
                self._bounce_from(self.player_y, self.player_half, -1)
                self.rally += 1
                self.best = max(self.best, self.rally)
                self._reaction_delay = .24 - .12 * vigor
                event = 'player_hit'
            elif (self.vx < 0 and self.ball_x >= self.pet_x
                  and math.hypot(self.ball_x-self.pet_x,self.ball_y-self.pet_y) <= self.pet_radius+self.toy_radius):
                radius = self.pet_radius+self.toy_radius
                dy = self.ball_y-self.pet_y
                self.ball_x = self.pet_x + math.sqrt(max(0., radius**2-dy**2))
                self._bounce_from(self.pet_y, self.pet_radius, 1)
                self.rally += 1
                self.best = max(self.best, self.rally)
                event = 'pet_hit'
            if self.ball_x - self.toy_radius > r:
                return self._point('pet_point')
            if self.ball_x + self.toy_radius < l:
                return self._point('player_point')
        return event

    def _bounce_from(self, center, half, direction):
        offset = self._clamp((self.ball_y - center) / max(1.0, half), -1.0, 1.0)
        speed = min(780.0, max(310.0, math.hypot(self.vx, self.vy) * 1.035))
        angle = offset * 0.92
        self.vx = direction * speed * math.cos(angle)
        self.vy = speed * math.sin(angle)

    def _point(self, event):
        if event == 'player_point':
            self.player_score += 1
            self._serve_sign = -1
        else:
            self.pet_score += 1
            self._serve_sign = 1
        self.rally = 0
        self.ball_x = (self.court[0] + self.court[2]) / 2
        self.ball_y = (self.court[1] + self.court[3]) / 2
        self.vx = self.vy = 0.0
        self._reaction_delay = 0.
        if max(self.player_score, self.pet_score) >= 5:
            self.finished = True
            self.winner = 'player' if self.player_score > self.pet_score else 'pet'
        else:
            self.serve_delay = .65
        return event

    def _start_serve(self):
        self.ball_x = (self.court[0] + self.court[2]) / 2
        self.ball_y = (self.court[1] + self.court[3]) / 2
        self.vx = self._serve_sign * 330.0
        self.vy = 90.0 if (self.player_score+self.pet_score) % 2 == 0 else -90.0

    @staticmethod
    def _clamp(value, low, high):
        return min(high, max(low, value))

    @staticmethod
    def _reflected_y(y, low, high):
        span = high - low
        if span <= 0:
            return (low + high) / 2
        z = (y - low) % (2 * span)
        return low + (z if z <= span else 2 * span - z)
