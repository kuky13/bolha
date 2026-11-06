"""
BEHAVIOR - como a rede e a emoção viram movimento.

Divisão de trabalho (v7.1):
    emoção          ALTO nível: para onde ir (cursor, cantinho, longe), missões
    tom motor       COMO: velocidade, pulinhos, giros, tremor, olhar, hesitação
                    (motor.py lê direto as populações motoras da rede)

Ele não tem pernas: "andar" é deslizar, "pular" é um impulso.
Estados de missão (entregar meme, atravessar a tela) passam na frente do
passeio normal; cair, ser segurado ou estar tombado passam na frente de tudo.
"""

import math

from ..core.physics import CLOSE_BUTTONS, GRAVITY, wrap_angle

STILL = ("assustado", "dramatico", "dormindo")     # emoções que não passeiam
GLANCE_EVERY = 1.2          # s: a cada olhada, decide se fixa o cursor ou olha em volta

LOOK_SECONDS = 2.5          # quanto tempo ele encara a janela que você acabou de abrir
MAX_CLIMB = 800             # px: altura máxima de um pulo até uma janela

CURIOUS_DISTANCE = 170      # o curioso chega perto do cursor, mas não em cima
DELIVER_TIMEOUT = 14.0
CARRY_GAP = 14
CROSS_SCREEN_CHANCE = 0.3  # em parte dos passeios, visita deliberadamente um monitor lateral
CROSS_SCREEN_SPEED = 180.0


class Behavior:
    """Comportamento do corpo: para onde olha, para onde anda, quando pega ou entrega objetos. Ele só executa; quem decide é a rede."""
    def __init__(self, body, state, mischief):
        """Guarda o corpo, o estado do pet e a lista de objetos de travessura."""
        self.body = body
        self.policy = None
        self.rates = {}
        self.energy = 1.
        self.contact = 0.
        self.state = state          # PetState: gaze, shake, tontura, carinho, tom motor
        self.mischief = mischief
        self.target_x = None
        self.next_roam = 0.0
        self.crossing_screen = False
        self.emotion = "observando"
        self.tipped_since = None
        self.mission = None         # ("deliver", thing, x, prazo) | ("cross", x, prazo)
        self.look = None            # (x, y, até) ponto que ele encara
        self.tone = state.tone      # o app atualiza com a rede a cada 100 ms
        self.glance = None          # ponto qualquer quando não está fixando o cursor
        self.state.protest_stage = 0      # 0 em paz; 1 reclamação; 2 manifestação; 3 greve; 4 revolução
        self.toy = None             # (x, y) da bolinha, quando ela está na tela
        self.ball = None            # a bolinha (toy.Ball), ligada pelo app
        self.play = None            # Play: estilo de brincadeira do pet, ligado pelo app
        self.play_pull = 0.0        # 0..1, da rede: quanto ele quer brincar agora (ver mesa.pull)
        self.last_play = None      # último resultado real, usado pela expressão da Bolha
        self.toy_action = None
        self.canto = False          # o neurônio CANTO está disparando: ele vai para o cantinho
        self.fuga_alvo = None       # x para onde ele está fugindo do cantinho (None: não está fugindo)
        self.march_dir = 1
        self.next_glance = 0.0
        self.cursor = (0., 0.)
        self.screen_areas = []      # áreas de todos os monitores, atualizadas pelo app
        self.adaptive_goal = None
        self.adaptive_target = None

    def look_at(self, x, y, now):
        """Olha para um ponto da tela por alguns segundos."""
        self.look = (x, y, now + LOOK_SECONDS)

    def _decide(self, name, choices, now, weights=None):
        if self.policy is None:
            return choices[0] if choices else None
        labels = {str(value): value for value in choices}
        selected = self.policy.choose(name, list(labels), rates=self.rates, emotion=self.emotion,
                                      energy=self.energy, contact=self.contact, duration=3.,
                                      weights={str(k): v for k, v in (weights or {}).items()})
        if name == 'roam_duration' and selected is not None:
            self.policy.current_decision['duration'] = float(selected)
        return labels.get(selected)

    def _sample(self, name, probability, now, dt=None):
        if self.policy is None: return False
        if dt is None:
            return self.policy.sample(name, probability, rates=self.rates, emotion=self.emotion,
                                      energy=self.energy, contact=self.contact)
        return self.policy.event(name, probability, 1., dt, rates=self.rates,
                                 emotion=self.emotion, energy=self.energy, contact=self.contact)

    def on_emotion(self, emotion, now):
        """Troca de emoção: ajusta o olhar e os gestos de cada emoção."""
        if emotion == self.emotion:
            return
        self.emotion = emotion
        self.next_roam = now     # reage na hora
        if emotion == "assustado" and self.body.grounded:
            power = self.tone.startle_power()       # pulo do tamanho do disparo de STARTLE
            lateral = self._decide('startle_direction', [-150,0,150], now)
            spin = self._decide('startle_spin', [-200,0,200], now)
            self.body.jump(lateral, -power, spin)
        elif emotion == "dramatico" and self.body.grounded:
            spin = self._decide('dramatic_spin', [-540,540], now)
            self.body.jump(0.0, -500.0, spin)

    def start_mission(self, plan, bounds, cursor, now):
        """Começa uma missão (levar um objeto para algum lugar), conforme o plano que a rede escolheu."""
        kind, thing = plan
        left, _top, right, _bottom = bounds
        margin = 140
        far_x = right - margin if self.body.x < (left + right) / 2 else left + margin
        if kind == "cross":
            self.mission = ("cross", far_x, now + DELIVER_TIMEOUT)
        elif kind == "deliver":
            # leva o objeto até um ponto longe do cursor
            options = [round(left+margin+(right-left-2*margin)*i/5, 2) for i in range(6)]
            x = float(self._decide('deliver_target', [str(value) for value in options], now,
                                   {str(value):abs(value-cursor[0]) for value in options}))
            direction = 1 if x > self.body.x else -1
            ex, ey = self.body.extents()
            thing.carried = True
            self.mischief.attach(
                thing,
                self.body.x - direction * (ex + thing.width() / 2 + CARRY_GAP),
                self.body.y + ey - thing.height() / 2,
            )
            self.mission = ("deliver", thing, x, now + DELIVER_TIMEOUT)

    def drop_carried(self):
        """Solta o objeto que ele estava carregando (se houver)."""
        if self.mission and self.mission[0] == "deliver":
            thing = self.mission[1]
            if thing in self.mischief.things:
                self.mischief.release(thing)
        self.mission = None

    def tick(self, dt, now, cursor, bounds, prof, platforms=(), allow_roaming=True, sense_cursor=True):
        """Um passo do comportamento: anda, mexe na bolinha e reage ao cursor, respeitando as plataformas."""
        body = self.body
        st = self.state
        self.cursor = cursor
        self.toy_action = None

        # olhar: janela recém-aberta > cursor; virado, olha para "cima" do mundo (indignado)
        if self.look and now > self.look[2]:
            self.look = None
        dizzy = st.dizzy(now)
        if dizzy:
            gaze = (math.cos(now * 14.0), math.sin(now * 14.0))     # olhinhos rodando
        elif body.upright() and self.state.protest_stage == 3 and self.emotion == "triste":
            gaze = (0.0, 0.9)                           # abandonado: olha para o chão
        elif body.upright() and self.state.protest_stage == 3:
            side = 1 if cursor[0] < body.x else -1          # greve: vira o rosto para longe de você
            gaze = (side * 0.9, 0.4)
        elif body.upright() and self.state.protest_stage in (1, 4):
            dx, dy = cursor[0] - body.x, cursor[1] - body.y  # reclamação/revolução: encara você
            dist = math.hypot(dx, dy) or 1.0
            gaze = (dx / dist, dy / dist)
        elif body.upright():
            if now >= self.next_glance:                 # WATCH alto: fixa o cursor; baixo: olha em volta
                self.next_glance = now + GLANCE_EVERY
                gaze_action = self._sample('gaze_cursor', self.tone.watch(), now)
                points = [(body.x+dx, body.y+dy) for dx,dy in ((-600,-400),(0,-400),(600,-400),(-600,150),(0,150),(600,150))]
                self.glance = None if gaze_action else self._decide(
                    'gaze_point', [str(point) for point in points], now)
                if self.glance is not None:
                    self.glance = tuple(float(value.strip()) for value in self.glance.strip('()').split(','))
            point = self.look[:2] if self.look else (self.glance or cursor)
            dx, dy = point[0] - body.x, point[1] - body.y
            dist = math.hypot(dx, dy) or 1.0
            gaze = (dx / dist, dy / dist)
            if self.emotion == "triste":
                gaze = (gaze[0] * 0.3, 0.8)
        else:
            a = math.radians(body.angle)
            gaze = (-math.sin(a), -math.cos(a))
        st.gaze = gaze
        st.shake = self.tone.shake()

        if body.held:
            self.drop_carried()
            self.tipped_since = None
            return

        if not allow_roaming:
            if body.grounded:body.vx = 0.0
            return

        if (self.play is not None and self.ball is not None and not self.play.requested_action
                and not self.mission and self.fuga_alvo is None and not self.canto
                and not st.castigo and not st.protest_stage and not st.at_desk
                and self.emotion not in STILL and not dizzy and not st.caressing(now) and body.upright()):
            self.toy_action = self.play.follow(dt, now, body, self.ball, cursor if sense_cursor else None,
                                              self.tone, self.emotion)
            if self.toy_action == 'return':
                self.last_play = dict(started=now, action='return')
            if self.toy_action:
                return

        # objeto carregado acompanha (e solta se o pet cair/voar)
        if self.mission and self.mission[0] == "deliver":
            thing = self.mission[1]
            if thing not in self.mischief.things:
                self.mission = None
            elif not body.grounded and abs(body.vy) > 600:
                self.drop_carried()
            else:
                direction = 1 if self.mission[2] > body.x else -1
                ex, ey = body.extents()
                self.mischief.follow(
                    thing,
                    body.x - direction * (ex + thing.width() / 2 + CARRY_GAP),
                    body.y + ey - thing.height() / 2,
                    dt,
                )

        if not body.grounded:
            return

        # fugindo do cantinho: o destino da fuga vale até ele chegar (nada sobrescreve a direção)
        if self.fuga_alvo is not None:
            if abs(body.x - self.fuga_alvo) < 20:
                self.fuga_alvo = None
            else:
                self._slide_to(self.fuga_alvo, 160.0)
                return

        # no cantinho do castigo: parado; missões pendentes são canceladas e protesto não move
        if st.castigo:
            self.drop_carried()
            body.vx = 0.0
            self.next_roam = now + 1.0
            return

        # tonto, dormindo ou ganhando carinho: fica paradinho
        if st.at_desk:                                  # sentado no notebook: trabalha, sem passear
            body.vx = 0.0
            st.gaze = (0.0, 0.9)
            self.next_roam = now + 1.0
            return
        if dizzy or self.emotion == "dormindo" or (st.caressing(now) and not self.mission):
            body.vx = 0.0
            self.next_roam = now + 1.0
            return

        # tombado: tenta se endireitar (triste prefere ficar caído)
        if not body.upright():
            if self.tipped_since is None:
                self.tipped_since = now
            if self.emotion != "triste" and now - self.tipped_since > prof["righting_after"]:
                turn = -wrap_angle(body.angle)
                body.jump(0.0, -650.0, turn * 1.6)
                self.tipped_since = None
            return
        self.tipped_since = None

        left, _top, right, _bottom = bounds

        # neurônio CANTO disparando (tristeza): vai para o cantinho e fica lá
        if self.canto:
            corner = left + 90 if body.x - left < right - body.x else right - 90
            if abs(body.x - corner) > 12:
                self._slide_to(corner, 110.0)
            else:
                body.vx = 0.0
            return

        # missões
        if self.mission:
            if self.mission[0] == "deliver":
                target, deadline = self.mission[2], self.mission[3]
                if abs(body.x - target) < 20 or now > deadline:
                    self.drop_carried()
                    self.next_roam = now + 2.0
                else:
                    self._slide_to(target, 190.0 * max(0.5, self.tone.vigor()))
                    return
            elif self.mission[0] == "cross":
                target, deadline = self.mission[1], self.mission[2]
                if abs(body.x - target) < 20 or now > deadline:
                    self.mission = None
                    self.next_roam = now + 2.0
                else:
                    self._slide_to(target, 260.0)
                    return

        if self.state.protest_stage:
            self._protest_move(dt, now, left, right)
            return

        if self.adaptive_goal in ('watch', 'rest', 'work'):
            body.vx = 0.
            return

        # brincar com a bolinha (chutar ou arremessar, conforme o estilo do pet)
        if self.play is not None and self.ball is not None and self.emotion not in STILL and not st.at_desk:
            previous=self.play.next_at
            action=self.play.tick(now, body, self.ball, cursor, self.emotion, self.play_pull)
            if self.play.next_at!=previous:self.last_play=dict(started=now,action=action)
            if action:
                body.jump(0.0, -180.0)              # pulinho de quem acabou de chutar

        if self.adaptive_goal and self.emotion not in STILL:
            target = self.toy[0] if self.adaptive_goal == 'play' and self.toy else self.adaptive_target
            if target is not None and abs(target-body.x) > 16:
                self._slide_to(target, self.tone.speed())
            else:
                body.vx = 0.
            if self.adaptive_goal == 'explore' and now >= self.next_roam:
                self.next_roam = now+3
                if platforms and self._sample('explore_climb', self.tone.climb_chance(), now) and self._jump_to_window(platforms): return
                if self._sample('explore_hop', self.tone.hop_chance(), now): body.jump(body.vx, -self.tone.hop_power())
            return

        # passeio: a emoção escolhe o destino, o tom motor escolhe o jeito
        tone = self.tone
        if self.emotion in STILL:
            return
        if now >= self.next_roam and not self.crossing_screen:
            interval = self._decide('roam_duration', [str(value) for value in prof['roam_interval']], now)
            self.next_roam = now + float(interval) * tone.roam_scale()
            self.target_x = self._pick_target(cursor, left, right, now)
            self.crossing_screen = bool(
                self.target_x is not None and not (left + 80 <= self.target_x <= right - 80)
            )
            if platforms and self._sample('roam_climb',tone.climb_chance(),now) and self._jump_to_window(platforms):
                return
            if self._sample('roam_hop',tone.hop_chance(),now):
                spin = self._decide('spin', [-720,0,720], now, {0:1-tone.spin_chance(),-720:tone.spin_chance()/2,720:tone.spin_chance()/2})
                body.jump(body.vx, -tone.hop_power(), spin)
                return

        if self.target_x is not None:
            chegou = abs(body.x - self.target_x) < 12
            hesitou = not self.crossing_screen and self._sample('hesitate',tone.hesitation(),now,dt)
            if chegou or hesitou:
                self.target_x = None            # chegou, ou hesitou no meio (curioso com sono)
                self.crossing_screen = False
            else:
                speed = max(CROSS_SCREEN_SPEED, tone.speed()) if self.crossing_screen else tone.speed()
                self._slide_to(self.target_x, speed)

    def walk_to(self, x, speed):
        """Anda até x (usado por quem decide para onde ele vai, como a fuga do cantinho)."""
        self._slide_to(x, speed)

    def _protest_move(self, dt, now, left, right):
        """Marcha (2 e 4), greve no cantinho (3), ou parado encarando (1)."""
        body = self.body
        stage = self.state.protest_stage
        if stage == 1:
            body.vx = 0.0
            return
        if stage == 3:
            corner = left + 90 if body.x - left < right - body.x else right - 90
            if abs(body.x - corner) > 12:
                self._slide_to(corner, 130.0)
            else:
                body.vx = 0.0                       # sentado, em greve
            return
        # marcha de um lado ao outro, pulando de indignação
        edge = right - 120 if self.march_dir > 0 else left + 120
        if (self.march_dir > 0 and body.x >= edge) or (self.march_dir < 0 and body.x <= edge):
            self.march_dir *= -1
        self._slide_to(right if self.march_dir > 0 else left, 150.0 if stage == 2 else 105.0)
        if self._sample('protest_hop',1.4 if stage == 2 else .6,now,dt):
            body.jump(body.vx, -330.0 if stage == 2 else -220.0)

    def _pick_target(self, cursor, left, right, now=0.):
        """Escolhe um ponto de destino no chão: perto da bolinha se ele está brincando, senão ao acaso."""
        x = self.body.x
        walk_left, walk_right = self._movement_limits(left, right)
        if self.toy and self.emotion in ("feliz", "curioso", "contente") and self._sample('roam_toy',.75,now):
            if abs(self.toy[0] - x) > 40:                  # brincando: vai atrás da bolinha
                return min(walk_right - 80, max(walk_left + 80, self.toy[0]))
        if self.emotion == "curioso":
            side = 1 if x > cursor[0] else -1
            return min(walk_right - 80, max(walk_left + 80, cursor[0] + side * CURIOUS_DISTANCE))
        if self.canto:
            return left + 80 if x - left < right - x else right - 80   # cantinho mais perto
        if self.emotion == "observando" and self._sample('roam_wait',1.0-self.tone.drive(),now):
            return None                         # às vezes só fica olhando mesmo
        vizinhos = self._lateral_neighbors(left, right)
        if vizinhos and self._sample('roam_cross_screen',CROSS_SCREEN_CHANCE,now):
            v_left, v_right = self._decide('roam_monitor', vizinhos, now)
            candidates = [v_left+100+(v_right-v_left-200)*i/4 for i in range(5)]
            return float(self._decide('cross_monitor_target', [str(round(v,2)) for v in candidates], 0.))
        reach = 120 + 450 * self.tone.drive()
        choices = [min(walk_right-80,max(walk_left+80,x+offset)) for offset in (-reach,-reach/2,0,reach/2,reach)]
        return float(self._decide('roam_position', [str(round(value,2)) for value in choices], now))

    def _movement_limits(self, left, right):
        """Amplia o passeio para monitores encostados à esquerda ou à direita do atual."""
        walk_left, walk_right = left, right
        for a_left, a_right in self._lateral_neighbors(left, right):
            walk_left = min(walk_left, a_left)
            walk_right = max(walk_right, a_right)
        return walk_left, walk_right

    def _lateral_neighbors(self, left, right):
        """Faixas horizontais dos monitores laterais alcançáveis na altura atual do pet."""
        vizinhos = []
        y = self.body.y
        for a_left, a_top, a_right, a_bottom in self.screen_areas:
            if not (a_top <= y < a_bottom):
                continue
            if abs(a_right - left) <= 1 or abs(a_left - right) <= 1:
                vizinhos.append((a_left, a_right))
        return vizinhos

    def _jump_to_window(self, platforms):
        """Pulo balístico até a barra de título de uma janela próxima."""
        body = self.body
        ex, ey = body.extents()
        bottom = body.y + ey
        options = []
        for hwnd, p_left, p_right, p_top in platforms:
            if hwnd == body.platform:
                continue
            lo, hi = p_left + ex, p_right - CLOSE_BUTTONS - ex
            if hi - lo < 20 or not (-MAX_CLIMB < bottom - p_top < MAX_CLIMB):
                continue
            choices = [min(hi,max(lo,body.x+offset)) for offset in (-200,-100,0,100,200)]
            tx = float(self._decide('window_jump_target', [str(round(value,2)) for value in choices], 0.))
            if abs(tx - body.x) < 1400:
                options.append((tx, p_top))
        if not options:
            return False
        selected = self._decide('window_jump_target', [str(i) for i in range(len(options))], 0.)
        tx, p_top = options[int(selected)]
        apex = min(bottom, p_top) - 70
        t_up = math.sqrt(2 * (bottom - apex) / GRAVITY)
        t_down = math.sqrt(2 * (p_top - apex) / GRAVITY)
        spin = self._decide('window_jump_spin', [-90,0,90], 0.)
        body.jump((tx - body.x) / (t_up + t_down), -GRAVITY * t_up, spin)
        return True

    def _slide_to(self, target, speed):
        """Anda devagar até `target` com a velocidade dada."""
        direction = 1 if target > self.body.x else -1
        self.body.vx = direction * speed
