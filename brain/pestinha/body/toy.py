# SPDX-License-Identifier: GPL-3.0-or-later
# Adapted from Pestinha by @mille-okws and contributors; see NOTICE.md.
"""
TOY - a bolinha dele.

A bolinha tem gravidade e quica no chão. Você pode pegá-la, arrastar e jogar.
Ele reage a ela pela rede, não por regra:
    TOY_NEAR   a bolinha está perto dele (brincadeira: PLAYFUL, CURIOUS)
    TOY_TAKEN  você levou a bolinha para longe dele (pulso: ALERT, FRUSTRATION, GLOOM)

O mesmo "tirou a bolinha" pode deixar um pet triste ou bravo. Isso vem do
temperamento (pets/*.json), não de um código por pet.
"""

import math

from ..ajustes import (
    INTERVALO_CURSOR as CURSOR_COOLDOWN,
    LONGE_BOLINHA as FAR,
    PERTO_BOLINHA as NEAR,
    RAIO_BOLINHA as RADIUS,
    REPOUSO_BATIDA as REST,
)


class ToyTracker:
    """Decide: a bolinha foi levada (uma vez por vez) e quão perto ela está."""

    def __init__(self):
        """Começa sabendo que a bolinha não está longe do pet."""
        self.away = False

    def update(self, ball_xy, pet_xy, user_handled):
        """Diz se a bolinha foi levada para longe do pet (você a pegou), e avisa a rede quando isso acontece."""
        d = math.hypot(ball_xy[0] - pet_xy[0], ball_xy[1] - pet_xy[1])
        taken = False
        if d > FAR and user_handled and not self.away:
            self.away = True
            taken = True
        if d < NEAR:
            self.away = False
        near = max(0.0, min(1.0, (NEAR * 1.5 - d) / (NEAR * 1.5 - NEAR * 0.3)))
        return taken, near




def bounce_off(ball, rects):
    """Colisão círculo x retângulo. rects: [(x, y, w, h)] em coordenadas globais."""
    b = ball.body
    for rx, ry, rw, rh in rects:
        nx = max(rx, min(b.x, rx + rw))
        ny = max(ry, min(b.y, ry + rh))
        dx, dy = b.x - nx, b.y - ny
        d2 = dx * dx + dy * dy
        if d2 >= RADIUS * RADIUS:
            continue
        if d2 < 1e-12:                            # o centro já entrou no retângulo: sai pela face mais próxima
            options = [(b.x - rx, -1, 0), (rx + rw - b.x, 1, 0), (b.y - ry, 0, -1), (ry + rh - b.y, 0, 1)]
            dist, ux, uy = min(options)
            b.x += ux * (dist + RADIUS)
            b.y += uy * (dist + RADIUS)
        else:
            d = math.sqrt(d2)
            ux, uy = dx / d, dy / d
            push = RADIUS - d
            b.x += ux * push
            b.y += uy * push
        vn = b.vx * ux + b.vy * uy
        if vn < 0:
            b.vx -= (1 + REST) * vn * ux
            b.vy -= (1 + REST) * vn * uy
            if abs(b.vy) < 40 and uy < -0.5:      # apoiada sobre o post-it: para de tremer
                b.vy = 0.0
    ball.place()


def kick(ball, vx, vy):
    """Chuta a bolinha com a velocidade (vx, vy) dada."""
    ball.body.vx = vx
    ball.body.vy = vy
    ball.body.grounded = False
    ball.body.platform = None




def push_from_cursor(ball, cursor, cursor_vel, now, last_push, radius=RADIUS + 6, *, max_speed=1200.):
    """
    O cursor também bate na bolinha: se o ponteiro encosta nela, ela sai na direção
    em que o ponteiro vinha (ou para longe do ponteiro, se ele estava parado).
    Devolve o instante do último empurrão (ou o mesmo, se não empurrou).
    """
    if (ball.dragging or getattr(ball.body, "held", False)
            or not ball.isVisible() or now - last_push < CURSOR_COOLDOWN):
        return last_push
    b = ball.body
    dx, dy = b.x - cursor[0], b.y - cursor[1]
    d = math.hypot(dx, dy)
    if d >= radius:
        return last_push
    cursor_vx, cursor_vy = cursor_vel
    if ball.kind == 'ball' and dy <= 4. and cursor_vy < -160. and abs(cursor_vx) <= -cursor_vy*.45:
        # O movimento de baixo para cima preserva a direção do gesto.
        ball.kick(max(-110., min(110., cursor_vx*.35)), -max(430., min(780., -cursor_vy*.65)))
        return now
    speed_in = math.hypot(cursor_vel[0], cursor_vel[1])
    if d > 1e-6:
        nx, ny = dx / d, dy / d
    elif speed_in > 1e-6:
        nx, ny = cursor_vel[0] / speed_in, cursor_vel[1] / speed_in
    else:
        nx, ny = 1.0, 0.0
    if speed_in > 50:                                 # o ponteiro estava se movendo: leva a bolinha junto
        vx_dir, vy_dir = cursor_vel[0] / speed_in, cursor_vel[1] / speed_in
        ux = nx + (vx_dir if nx * vx_dir >= -1e-6 else 0.0)
        uy = ny + (vy_dir if ny * vy_dir >= -1e-6 else 0.0)
    else:                                             # ponteiro parado: a bolinha só se afasta
        ux, uy = nx, ny
    if abs(ux) < 0.5:
        sign = -1.0 if (ux < -1e-6 or (abs(ux) <= 1e-6 and cursor_vel[0] < -1e-6)) else 1.0
        ux = sign * 0.6
    norm = math.hypot(ux, uy) or 1.0
    ux, uy = ux / norm, uy / norm
    speed = max(260.0, min(max_speed, speed_in * 0.8))
    lift = min(-120.0, uy * speed - 120.0)
    if cursor_vel[1] < -160.0 and dy <= 4.0:
        # Um toque de baixo para cima levanta o brinquedo de propósito.
        lift = min(lift, -max(320.0, min(570.0, -cursor_vel[1] * .66)))
    ball.kick(ux * speed, lift)
    return now
