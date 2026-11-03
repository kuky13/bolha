# SPDX-License-Identifier: GPL-3.0-only
"""Uma Drippy: cérebro e física originais, cena enviada para Electron."""
import math
import time
from pathlib import Path
from types import SimpleNamespace
from collections import deque

from pestinha import config
from pestinha.core.nervous_system import LIFBrain
from pestinha.core.homeostasis import Drives
from pestinha.core.emotion import EmotionState
from pestinha.core.episodic import EpisodicMemory
from pestinha.core.conditioning import Conditioning
from pestinha.core.protesto import Protesto
from pestinha.core.physics import Body
from pestinha.body.behavior import Behavior
from pestinha.body.pet_state import PetState
from pestinha.body.brincadeira import Play
from pestinha.body.toy import ToyTracker, bounce_off
from pestinha.mind.sleep import SleepController
from pestinha.mind.mesa import MesaController, pull
from pestinha.mind.protest_ctl import ProtestController
from pestinha.mind.castigo_ctl import CastigoController
from pestinha.mind.mischief_ctl import MischiefController
from pestinha.mind.festa import FestaController
from pestinha.mind.revolucao import RevolucaoController
from pestinha.world.mischief import MischiefEngine
from pestinha.sense.senses import ComputerSenses, ActivityTracker, detect_activity
from pestinha.paths import PetPaths, ConteudoPaths
from pestinha.store import read_json, write_json
from pestinha.scene import set_scene, Ball, FloatingThing


class Burst:
    def __init__(self):
        self.throws = deque()
        self.away_until = 0.0
        self.shy_until = 0.0
        self.started = 0.0

    def throw(self, now, speed, limit):
        if speed < 900 or now < self.away_until: return False
        while self.throws and now - self.throws[0] >= 60: self.throws.popleft()
        self.throws.append(now)
        if len(self.throws) < limit: return False
        self.throws.clear()
        self.started = now
        self.away_until = now + 30
        self.shy_until = now + 90
        return True

    def phase(self, now):
        if self.started and now < self.started + 0.7: return 'burst'
        if now < self.away_until: return 'away'
        if now < self.shy_until: return 'shy'
        return 'normal'

    def caress(self, dt): self.shy_until -= dt * 4


class Game:
    def __init__(self, data_dir, content_dir):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.objects = {}
        self.next_id = 1
        set_scene(self)
        self.prefs = {}
        self.areas = [(0., 0., 1280., 760.)]
        self.monitors = list(self.areas)
        self.displays = []
        self.blocked = set()
        self.cursor = (640., 350.)
        self.last_cursor = self.cursor
        self.last_input = time.monotonic()
        self.mouse_moved_at = 0.
        self.hover = False
        self.panel = False
        self.hidden = False
        session=read_json(self.data_dir / 'session.json',default={})
        self.panicked = session.get('panicked') is True if isinstance(session,dict) else False
        self.monitor_open = False
        self.media_playing = False
        self.paused_at = None
        self.burst = Burst()
        self.recovered = True
        self.excluded = set()
        self.activity = 'IDLE'
        self.idle = 0.
        self.last_native = self.last_save = self.last_think = 0.
        self.speech = ''
        self.speech_until = 0.
        self.pet_paths = PetPaths(self.data_dir / 'drippy')
        self.conteudo = ConteudoPaths(Path(content_dir), Path(content_dir))
        self.prof = dict(config.PROFILES['normal'])
        self.brain = LIFBrain(seed=1313, temperament={'CURIOUS': 1.3, 'PLAYFUL': 1.2, 'DRAG->FRUSTRATION': 0.45})
        self.brain.load(self.pet_paths.nervous)
        self.drives = Drives()
        self.drives.load(self.pet_paths.drives, self.prof)
        self.memory = EpisodicMemory(self.pet_paths.episodes, self.pet_paths.preferences)
        self.memory.load()
        self.conditioning = Conditioning(self.pet_paths.conditioning, self.prof['cond_rate'])
        self.conditioning.load()
        self.emotion = EmotionState()
        self.state = PetState()
        self.body = Body(950., 300., 68., 68.)
        saved_position=read_json(self.data_dir / 'position.json',default={})
        if isinstance(saved_position,dict) and all(isinstance(saved_position.get(k),(int,float)) and math.isfinite(saved_position[k]) for k in ('x','y')):
            self.body.x,self.body.y=saved_position['x'],saved_position['y']
        self.pet = SimpleNamespace(body=self.body, isVisible=self.visible, raise_=lambda: None)
        self.senses = ComputerSenses()
        self.tracker = ActivityTracker()
        self.mischief = MischiefEngine(self.conteudo)
        self.behavior = Behavior(self.body, self.state, self.mischief)
        self.play = Play({'bola': 1., 'arremesso': 0.5, 'postit': 0.5})
        self.behavior.play = self.play
        self.ball = Ball(800., 650.)
        self.ball.show()
        self.behavior.ball = self.ball
        self.toy_tracker = ToyTracker()
        self.sleep = SleepController(self.emotion, self.drives, self.memory, lambda: False)
        self.protest = Protesto(self.conteudo.signs, self.pet_paths.protest)
        self.protest.load(self.prof)
        self.sad = Protesto(self.conteudo.signs, self.pet_paths.sad_protest, 'tristeza')
        self.sad.load(self.prof)
        self.protest_ctl = ProtestController(self.protest, self.body, self.behavior, self.senses, self.drives, self.state, lambda: False)
        self.sad_ctl = ProtestController(self.sad, self.body, self.behavior, self.senses, self.drives, self.state, lambda: False)
        self.mesa = MesaController(lambda: False, self)
        self.mischief_ctl = MischiefController(self.mischief, self.memory, self.drives, self.senses, self.behavior, self.emotion, lambda: False)
        self.mischief.dismissed.connect(lambda thing, elapsed: self.mischief_ctl.on_dismissed(thing, elapsed, self.prof, time.monotonic()))
        self.castigo = CastigoController(self, lambda: False)
        self.festa = FestaController(lambda: False, self)
        self.revolucao = RevolucaoController(self.play, lambda: False)
        self.rates = self.brain.motor_activity()
        self.inputs = {}
        self.in_flight = False
        self.ball_stored = False
        self.request_refused = 0.
        self.prev_distance = None
        self.senses_app = None
        self.native_error = None

    def available_areas(self):
        return [area for i, area in enumerate(self.areas) if i not in self.blocked]

    def bounds(self, point=None):
        areas = self.available_areas() or self.areas
        x, y = point or (self.body.x, self.body.y)
        for area in areas:
            if area[0] <= x < area[2] and area[1] <= y < area[3]: return area
        return min(areas, key=lambda a: math.hypot(x - (a[0] + a[2]) / 2, y - (a[1] + a[3]) / 2))

    def fit(self, body):
        a = self.bounds((body.x, body.y))
        ex, ey = body.extents()
        old = (body.x, body.y)
        body.x = max(a[0] + ex + 4, min(a[2] - ex - 4, body.x))
        body.y = max(a[1] + ey + 4, min(a[3] - ey - 4, body.y))
        if old != (body.x, body.y): body.grounded = False; body.platform = None

    def visible(self):
        return not self.hidden and not self.panicked and bool(self.available_areas()) and self.burst.phase(time.monotonic()) not in ('burst', 'away')

    def configure(self, prefs):
        self.prefs.update(prefs)
        size = float(self.prefs.get('avatarSize', 136)) / 2
        self.body.half_w = self.body.half_h = max(40., min(100., size))
        self.mischief.interval = self.prefs.get('mischiefInterval', 300)
        self.mischief.max_objects = self.prefs.get('maxObjects', 3)
        if not self.prefs.get('mischiefEnabled', True): self.mischief_ctl.clear()
        self.fit(self.body)

    def desktop(self, data):
        self.displays = data['areas']
        self.areas = [(a['x'], a['y'], a['x'] + a['width'], a['y'] + a['height']) for a in self.displays]
        self.monitors = [(a.get('monitorX', a['x']), a.get('monitorY', a['y']), a.get('monitorX', a['x']) + a.get('monitorWidth', a['width']), a.get('monitorY', a['y']) + a.get('monitorHeight', a['height'])) for a in self.displays]
        self.blocked.clear()
        self.excluded = set(data.get('exclude', []))
        self.fit(self.body)
        self.fit(self.ball.body)
        for obj in self.objects.values():
            if isinstance(obj, FloatingThing):
                area = self.bounds((obj._cx, obj._cy))
                obj.place(max(area[0] + obj.width()/2, min(area[2] - obj.width()/2, obj._cx)), max(area[1] + obj.height()/2, min(area[3] - obj.height()/2, obj._cy)))
        if self.mesa.sentado: self.mesa.ancora = (self.mesa.caderno.x(), self.mesa.caderno.y())

    def native_point(self, x, y):
        for a in self.displays:
            scale = a.get('scaleFactor', 1)
            nx, ny = a.get('nativeX', a['x']), a.get('nativeY', a['y'])
            if nx <= x < nx + a.get('monitorWidth', a['width']) * scale and ny <= y < ny + a.get('monitorHeight', a['height']) * scale:
                return a.get('monitorX', a['x']) + (x - nx) / scale, a.get('monitorY', a['y']) + (y - ny) / scale
        return x, y

    def read_context(self, now):
        if now - self.last_native < .5: return
        self.last_native = now
        import sys
        if sys.platform != 'win32': return
        try:
            from pestinha.plataforma import windows as native
            self.idle = native.ocioso_segundos() if self.prefs.get('senseIdle', True) else 0.
            active = native.processo_ativo() if self.prefs.get('senseApp', True) else 'unknown'
            self.activity = detect_activity(active, self.idle, self.prof['away_after'])
            self.senses.on_events(self.tracker.observe(active, self.activity))
            self.platforms = []
            previous_blocked=set(self.blocked)
            self.blocked.clear()
            if self.prefs.get('senseWindows', True):
                for hwnd, (left, top, right, _bottom), maximized in native.janelas_visiveis(self.excluded):
                    left, top = self.native_point(left, top)
                    right, _ = self.native_point(right, _bottom)
                    if not maximized: self.platforms.append((hwnd, left + 10, right - 65, top))
                if native.win32gui.GetForegroundWindow() not in self.excluded and native.tela_cheia():
                    rect = native.retangulo_ativo()
                    if rect:
                        x, y = self.native_point((rect[0]+rect[2])/2, (rect[1]+rect[3])/2)
                        self.blocked = {i for i,a in enumerate(self.areas) if a[0] <= x < a[2] and a[1] <= y < a[3]}
            if self.available_areas():
                if previous_blocked != self.blocked:
                    self.fit(self.body)
                    self.fit(self.ball.body)
                    for obj in self.objects.values():
                        area=self.bounds((obj._cx,obj._cy))
                        obj.place(max(area[0]+obj.width()/2,min(area[2]-obj.width()/2,obj._cx)),max(area[1]+obj.height()/2,min(area[3]-obj.height()/2,obj._cy)))
                    if self.mesa.sentado:self.mesa.ancora=(self.mesa.caderno.x(),self.mesa.caderno.y())
            self.native_error = None
        except Exception as error:
            self.native_error = str(error)

    def interact(self, event):
        now = time.monotonic()
        kind = event.get('type')
        if kind == 'panic': self.panicked = not self.panicked; self.save(); return
        if kind == 'hide': self.hidden = bool(event.get('value')); return
        if kind == 'monitor': self.monitor_open = bool(event.get('value')); self.brain.recording = self.monitor_open; return
        if kind == 'panel': self.panel = bool(event.get('value')); return
        if kind == 'hover': self.hover = bool(event.get('value')); return
        if kind == 'music': self.media_playing = bool(event.get('value')); return
        if kind == 'cursor':
            if self.prefs.get('senseCursor', True): self.cursor = (event['x'], event['y'])
            return
        if self.panicked or self.hidden or self.burst.phase(now) in ('burst', 'away'): return
        self.last_input = now
        if kind in ('drag-start', 'drag', 'drag-end'):
            target = self.objects.get(str(event.get('id'))) if event.get('id') else None
            body = target.body if target and hasattr(target, 'body') else self.body
            if target and not hasattr(target, 'body'):
                target.place(event['x'], event['y'])
                return
            body.held = kind != 'drag-end'
            body.x, body.y = event['x'], event['y']
            if target: target.dragging = body.held; target.last_handled = now
            else:
                self.senses.set_dragging(body.held)
                self.state.pressing = body.held
                self.drives.touched('drag')
                self.conditioning.outcome(now)
            self.fit(body)
            if kind == 'drag-end':
                vx = max(-1800., min(1800., event.get('vx', 0)))
                vy = max(-1800., min(1800., event.get('vy', 0)))
                body.jump(vx, vy, vx * .12)
                if target is None:
                    speed = math.hypot(vx, vy)
                    self.senses.thrown(min(1., speed / 1800))
                    self.drives.stimulate('throw')
                    if self.burst.throw(now, speed, self.prefs.get('burstLimit', 12)):
                        self.behavior.drop_carried(); self.castigo.pausar(self.state); self.recovered = False
                    self.say('Uuuui! Segura minhas orelhas!')
        elif kind == 'poke':
            self.senses.poke(); self.drives.touched('poke'); self.drives.stimulate('poke'); self.memory.on_interaction(); self.conditioning.outcome(now)
            if self.sleep.asleep: self.sleep.wake(True)
            self.say('Ei! Eu estava pensando em... bolinhas.')
        elif kind == 'caress':
            self.state.mark_caress(now); self.drives.touched('caress'); self.memory.on_interaction(); self.say('Tá, esse carinho eu aceito. ♡')
        elif kind == 'spin': self.body.omega += max(-500, min(500, event.get('value', 0)))
        elif kind == 'sleep': self.drives.energy = .1
        elif kind == 'work': self.mesa.pedir(now)
        elif kind == 'notebook': self.mesa.alternar_notebook()
        elif kind == 'corner': self.castigo.toggle(self.bounds())
        elif kind == 'ball': self.ball_stored = not self.ball_stored; self.ball.setVisible(not self.ball_stored)
        elif kind == 'mischief': self.mischief_ctl.pedir(now)
        elif kind == 'dismiss':
            obj = self.objects.get(str(event.get('id')))
            if obj and obj.kind in ('meme','note','sign'): obj.clicked.emit(obj)

    def say(self, text):
        self.speech, self.speech_until = text, time.monotonic() + 4

    def think(self, dt, now):
        moving = min(1., abs(self.body.vx) / 200 + (0 if self.body.grounded else 1))
        caressing = self.state.caressing(now)
        self.drives.update(dt, self.prof, self.sleep.asleep, moving, self.emotion.arousal, self.activity == 'AWAY', engaged=self.activity in ('PROGRAMMING', 'DESIGNING'), preso=self.castigo.dentro, visitado=self.castigo.visita > .5)
        if caressing: self.drives.stimulate('caress', dt); self.drives.touched('caress', dt); self.burst.caress(dt)
        self.castigo.tick_lento(dt)
        inputs = self.senses.update(self.activity, self.idle, self.drives.channels(), caressing, math.dist(self.cursor,self.last_cursor) > 2)
        self.last_cursor = self.cursor
        self.conditioning.set_cue('PRESS', self.state.pressing, now)
        distance = math.dist(self.cursor,(self.body.x,self.body.y))
        self.conditioning.set_cue('APPROACH', self.prev_distance is not None and distance < 220 and (self.prev_distance - distance) / max(.01,dt) > 500, now)
        self.prev_distance = distance
        self.conditioning.set_cue('PLACA', self.castigo.perto_da_placa(self.body), now)
        self.conditioning.tick(now)
        inputs['ANTICIPATE'] = self.conditioning.strength()
        inputs['ANTECIPA_PLACA'] = self.conditioning.strength(cues=('PLACA',))
        taken, near = self.toy_tracker.update((self.ball.body.x,self.ball.body.y),(self.body.x,self.body.y),self.ball.handled_by_user(now))
        if taken and not self.ball_stored: self.senses.kick('TOY_TAKEN', .9)
        inputs['TOY_NEAR'] = near if not self.ball_stored else 0
        inputs['PEDIDO'] = self.mesa.intensidade_pedido(now)
        inputs.update(self.castigo.sinais(self.body))
        inputs['RECUSA'] = self.request_refused; self.request_refused = 0
        if self.media_playing: inputs['SOUND'] = max(.8,inputs.get('SOUND',0))
        self.brain.stimulate(inputs)
        self.brain.step(min(100, max(1, round(dt * 1000))))
        self.inputs = inputs
        self.rates = self.brain.motor_activity()
        self.state.tone.update(self.rates,dt)
        for controller in (self.protest_ctl,self.sad_ctl):
            change = controller.tick(dt,self.state.tone,self.prof,caressing,now,self.drives.channels()['LONELY'])
            if change: controller.on_stage(*change)
        self.state.protest_stage = self.protest.stage if not self.sleep.asleep else 0
        reward = (1. if caressing else 0.) - (1. if self.mischief_ctl.penalty_active(now) else 0.) + self.castigo.punicao(now)
        self.brain.learn(reward,dt,self.prof['learn_rate'])
        emotion = self.emotion.update(self.rates,dt,self.prof,now)
        if self.state.dizzy(now): emotion = 'dramatico'
        self.state.emotion = emotion
        self.behavior.on_emotion(emotion,now)
        self.behavior.canto = self.rates.get('CANTO',0) > 5 and self.sad.stage > 0
        can_sit = self.body.grounded and not self.body.held and not self.sleep.asleep and not self.castigo.dentro and self.castigo.fuga is None
        self.mesa.tick(now,self.brain.pool_rates(),self.rates['SENTAR'],can_sit,self.play)
        self.state.at_desk = self.mesa.sentado
        self.state.desk_top = self.mesa.caderno.y() if self.mesa.sentado else None
        self.behavior.play_pull = pull(self.brain.pool_rates())
        if self.mesa.pop_recusa(): self.request_refused = min(1., .4 + .2 * self.mesa.pedidos_recentes())
        self.sleep.tick(now,self.body,self.in_flight,self.protest.stage,self.behavior.mission)
        if self.sleep.asleep: self.state.emotion = 'dormindo'; self.behavior.on_emotion('dormindo',now)

    def tick(self, dt, now=None):
        now = time.monotonic() if now is None else now
        dt = min(.05, max(0.,dt))
        if not self.panicked and not self.hidden: self.read_context(now)
        frozen = self.panicked or self.hidden or not self.available_areas()
        if frozen:
            self.body.held = False; self.ball.body.held = False; self.ball.dragging = False; self.senses.set_dragging(False)
            if self.paused_at is None: self.paused_at = now
            return
        if self.paused_at is not None:
            elapsed = now - self.paused_at
            self.castigo.deslocar(elapsed); self.mesa.deslocar(elapsed)
            self.burst.away_until += elapsed if self.burst.phase(now) == 'away' else 0
            self.paused_at = None; self.last_think = now
        if self.burst.phase(now) in ('away','burst'): return
        if not self.recovered:
            area = self.bounds()
            self.body.x,self.body.y = area[0] + self.body.half_w + 14,area[3] - self.body.half_h - 14
            self.body.vx = self.body.vy = self.body.omega = self.body.angle = 0
            self.body.grounded = True; self.recovered = True
            self.say('Voltei... posso ficar aqui no cantinho um pouquinho?')
        if now - self.last_think >= .1:
            self.think(min(.1,now-self.last_think),now); self.last_think = now
        area = self.bounds()
        areas = self.available_areas()
        self.behavior.screen_areas = areas
        self.behavior.toy = (self.ball.body.x,self.ball.body.y) if not self.ball_stored else None
        platforms = getattr(self,'platforms',[]) if self.prefs.get('senseWindows',True) else []
        self.castigo.act(now,self.body,area,self.cursor,self.state,self.rates,self.sleep.asleep)
        resting = self.hover or self.panel or not self.prefs.get('roaming',True) or self.burst.phase(now) == 'shy' and self.burst.shy_until-now>30
        if resting and not self.body.held: self.body.vx = 0
        elif not self.body.held: self.behavior.tick(dt,now,self.cursor,area,self.prof,platforms)
        if self.burst.phase(now)=='shy': self.body.vx *= max(.1,1-(self.burst.shy_until-now)/60)
        self.body.step(dt,area,platforms,areas,self.monitors)
        if self.mesa.sentado and self.mesa.pin(self.body,now): self.mesa.levantar_arrancado(now); self.protest_ctl.provoke(.1)
        if not self.ball_stored:
            self.ball.step(dt,self.bounds((self.ball.body.x,self.ball.body.y)),areas,self.monitors)
            self.play.tick(now,self.body,self.ball,self.cursor,self.state.emotion,self.behavior.play_pull)
        for strength in self.body.pop_impacts(): self.senses.impact(min(1.,strength / 1600))
        self.mesa.set_visible(not self.mesa.escondido)
        self.protest_ctl.carry(now,self.sleep.asleep); self.sad_ctl.carry(now,self.sleep.asleep)
        self.mischief.tick(dt,area[3])
        perms = dict(config.DEFAULT_PERMISSIONS, travessuras=self.prefs.get('mischiefEnabled',True), fotos=False)
        if not self.castigo.dentro and not self.hover:
            self.mischief_ctl.maybe_act(now,dt,area,self.cursor,self.body,motores=self.rates,activity=self.activity,emotion=self.state.emotion,perms=perms,prof=self.prof,fullscreen=False,asleep=self.sleep.asleep,protest_stage=self.protest.stage,working=self.activity in ('PROGRAMMING','DESIGNING') and not self.mesa.sentado)
        self.festa.tick(now,self.rates,self.state.emotion,self.body,self.visible() and not self.sleep.asleep,dt)
        self.revolucao.tick(now,dt,area,self.cursor,(0,0),self.body,self.visible(),self.protest.stage == 4,[],self.rates.get('PAPEL',0))
        self.memory.tick(now,self.prof["episode_ok"],self.prof["episode_window"])
        if now - self.last_save >= 30: self.save(); self.last_save = now

    def save(self):
        write_json(self.data_dir / 'session.json',dict(panicked=self.panicked))
        self.brain.save(self.pet_paths.nervous)
        self.drives.save(self.pet_paths.drives)
        self.conditioning.save()
        self.memory.save()
        self.protest_ctl.save(); self.sad_ctl.save(); self.castigo.salvar()
        write_json(self.data_dir / 'position.json',dict(x=self.body.x,y=self.body.y))

    def snapshot(self):
        now = time.monotonic()
        objects = []
        for obj in list(self.objects.values()):
            data = obj.snapshot()
            if obj.isVisible() and self.visible(): objects.append(data)
        data = dict(ready=True,blocked=list(self.blocked),panicked=self.panicked,shyness=max(0.,min(1.,(self.burst.shy_until-now)/60)) if self.burst.phase(now)=='shy' else 0.,x=self.body.x,y=self.body.y,angle=self.body.angle,emotion=self.state.emotion,phase=self.burst.phase(now),visible=self.visible(),held=self.body.held,caressing=self.state.feliz_fechado(now),gaze=self.state.gaze,speech=self.speech if now < self.speech_until else '',objects=objects,energy=self.drives.energy,stimulation=self.drives.stimulation,lonely=self.drives.contact,protest=self.protest.stage,castigo=self.castigo.dentro,escapes=self.castigo.vitorias['fugir'],activity=self.activity,motors=self.rates,learned=self.brain.learned_summary(8),neurons=self.brain.N,error=self.native_error)
        if self.monitor_open:
            snap = self.brain.snapshot()
            data['neural'] = dict(positions=snap['pos'].tolist(),trace=snap['trace'].tolist(),kind=snap['kind'].tolist(),pools=snap['pool_rate'])
        return data
