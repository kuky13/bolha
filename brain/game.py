# SPDX-License-Identifier: GPL-3.0-only
"""Modelo único da Bolha: cérebro, comportamento e física do Pestinha."""
import math
import time
from pathlib import Path
from types import SimpleNamespace

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
from pestinha.store import read_json, write_json, preserve_invalid, clear_protection_after_backup
from pestinha.scene import set_scene, Ball, FloatingThing
from geometry import fullscreen_monitors
from intelligence import Intelligence


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
        self.scene_dragging = False
        self.panel = False
        self.hidden = False
        session=read_json(self.data_dir / 'session.json',default={})
        self.panicked = session.get('panicked') is True if isinstance(session,dict) else False
        self.monitor_open = False
        self.paused_at = None
        self.excluded = set()
        self.activity = 'IDLE'
        self.idle = 0.
        self.last_native = self.last_save = self.last_think = 0.
        memory = self.data_dir / 'bolha'
        legacy = self.data_dir / 'drippy'
        # Conserva o caminho original para a versão anterior continuar lendo após recuperação.
        if not memory.exists() and legacy.is_dir():
            memory = legacy
        self.pet_paths = PetPaths(memory)
        self.conteudo = ConteudoPaths(Path(content_dir), Path(content_dir))
        self.prof = dict(config.PROFILES['normal'])
        self.brain = LIFBrain(seed=1313, temperament={'CURIOUS': 1.3, 'PLAYFUL': 1.2, 'DRAG->FRUSTRATION': 0.45})
        if not self.brain.load(self.pet_paths.nervous) and self.pet_paths.nervous.exists():
            preserve_invalid(self.pet_paths.nervous,'Aprendizado neural inválido; original preservado e gravação protegida.')
        self.drives = Drives()
        if not self.drives.load(self.pet_paths.drives,self.prof) and self.pet_paths.drives.exists():
            preserve_invalid(self.pet_paths.drives,'Necessidades inválidas; original preservado e gravação protegida.')
        self.memory = EpisodicMemory(self.pet_paths.episodes, self.pet_paths.preferences)
        self.memory.load()
        self.conditioning = Conditioning(self.pet_paths.conditioning, self.prof['cond_rate'])
        self.conditioning.load()
        self.emotion = EmotionState()
        self.state = PetState()
        self.body = Body(950., 300., 68., 68., circular=True)
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
        self.cursor_toy_near = False
        self.next_toy_attention = 0.
        self.held_since = None
        self.release_reaction = {}
        self.play_reaction = {}
        self.last_play_attempt = None
        self.next_play_scene = 0.
        self.senses_app = None
        self.native_error = None
        self.quiet_until = 0.
        self.landing = 0.
        self.last_monitor_snapshot = -1.
        self.intelligence = Intelligence(self.memory, self.pet_paths.base / 'habits.json')
        self.last_intelligence = self.last_metrics = 0.
        self.app_rss_mib = 0.
        self.brain_array_mib = 0.

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
        return not self.hidden and not self.panicked and bool(self.available_areas())

    def configure(self, prefs):
        self.prefs.update(prefs)
        if self.prefs.get('toyAppearance','peanut') in ('peanut','ball'):
            self.ball.appearance=self.prefs.get('toyAppearance','peanut')
        self.intelligence.enabled = self.prefs.get('adaptiveBehavior', True)
        self.intelligence.learn_routine = self.prefs.get('learnRoutine', True)
        if not self.intelligence.enabled:
            self.intelligence.clear_goal()
            self.behavior.adaptive_goal = None
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
            self.idle = native.ocioso_segundos() if self.prefs.get('senseIdle', True) else None
            active = native.processo_ativo() if self.prefs.get('senseApp', True) else 'unknown'
            self.activity = detect_activity(active, self.idle or 0., self.prof['away_after'])
            self.senses.on_events(self.tracker.observe(active, self.activity))
            self.platforms = []
            previous_blocked=set(self.blocked)
            self.blocked.clear()
            if self.prefs.get('senseWindows', True):
                windows = []
                for hwnd, (left, top, right, _bottom), maximized in native.janelas_visiveis(self.excluded):
                    style = native.win32gui.GetWindowLong(hwnd, native.win32con.GWL_STYLE)
                    extended = native.win32gui.GetWindowLong(hwnd, native.win32con.GWL_EXSTYLE)
                    if extended & native.win32con.WS_EX_LAYERED:
                        continue
                    windows.append(((left, top, right, _bottom), maximized, bool(style & (native.win32con.WS_CAPTION | native.win32con.WS_THICKFRAME))))
                    left, top = self.native_point(left, top)
                    right, _ = self.native_point(right, _bottom)
                    if not maximized: self.platforms.append((hwnd, left + 10, right, top))
                self.blocked = fullscreen_monitors(windows, self.displays)
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
        if kind == 'panic':
            self.panicked = not self.panicked
            if self.panicked:self._cancel_holds(now)
            self.save();return
        if kind == 'hide':
            self.hidden = bool(event.get('value'))
            if self.hidden:self._cancel_holds(now)
            return
        if kind == 'monitor':
            self.monitor_open = bool(event.get('value'))
            self.last_monitor_snapshot = -1.
            return
        if kind == 'panel': self.panel = bool(event.get('value')); return
        if kind == 'hover': self.hover = bool(event.get('value')); return
        if kind == 'reset-memory': self.reset_learning(); return
        if kind == 'cursor':
            if self.prefs.get('senseCursor', True): self.cursor = (event['x'], event['y'])
            return
        if kind == 'hold-end':
            self._release_hold(now,event.get('cancelled',False) or self.panicked or self.hidden)
            return
        if self.panicked or self.hidden: return
        self.last_input = now
        if kind == 'hold-start':
            self._start_hold(now)
        elif kind in ('drag-start', 'drag', 'drag-end'):
            target = self.objects.get(str(event.get('id'))) if event.get('id') else None
            body = target.body if target and hasattr(target, 'body') else self.body
            if target and not hasattr(target, 'body'):
                self.scene_dragging = kind != 'drag-end'
                target.place(event['x'], event['y'])
                return
            body.held = kind != 'drag-end'
            body.vx=body.vy=body.omega=0.
            body.x, body.y = event['x'], event['y']
            if target: target.dragging = body.held; target.last_handled = now
            else:
                if kind!='drag-end':self._start_hold(now)
                self.senses.set_dragging(body.held)
                self.state.pressing = body.held
                self.drives.touched('drag')
                self.conditioning.outcome(now)
            self.fit(body)
            if kind == 'drag-end':
                body.grounded=False;body.platform=None
                if target is None:
                    self._release_hold(now)
        elif kind == 'poke':
            self.senses.poke(); self.drives.touched('poke'); self.drives.stimulate('poke'); self.memory.on_interaction(); self.conditioning.outcome(now)
            if self.sleep.asleep: self.sleep.wake(True)
        elif kind == 'caress':
            if self.intelligence.enabled: self.intelligence.feedback(.8, now)
            self.state.mark_caress(now); self.drives.touched('caress'); self.memory.on_interaction()
            if self.release_reaction.get('until',0)>now:
                self.release_reaction['until']=now+(self.release_reaction['until']-now)*.35
                self.release_reaction['intensity']*=.5
        elif kind == 'quiet':
            self.intelligence.feedback(-.8, now)
            self.quiet_until = now+30
            self.behavior.adaptive_goal = 'watch'
            self.behavior.drop_carried()
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

    def _start_hold(self,now):
        if self.held_since is None:
            self.held_since=now
            self.release_reaction={}
            self.drives.touched('drag')
            if self.mesa.sentado:
                self.mesa.levantar_arrancado(now)
                self.mesa.caderno.set_working(False)
                self.state.at_desk=False;self.state.desk_top=None
        self.body.held=True;self.state.pressing=True;self.senses.set_dragging(True)
        self.body.grounded=False;self.body.platform=None
        self.body.vx=self.body.vy=self.body.omega=0.
        self.conditioning.set_cue('PRESS',True,now)

    def _cancel_holds(self,now):
        self._release_hold(now,True)
        self.scene_dragging=False
        for item in self.objects.values():
            if hasattr(item,'body') and (item.body.held or item.dragging):
                item.body.held=item.dragging=False
                item.body.vx=item.body.vy=item.body.omega=0.
                item.body.grounded=False;item.body.platform=None

    def _release_hold(self,now,cancelled=False):
        started=self.held_since
        if self.body.held or started is not None:
            self.body.vx=self.body.vy=self.body.omega=0.
            self.body.grounded=False;self.body.platform=None
        self.body.held=False;self.state.pressing=False;self.senses.set_dragging(False)
        self.held_since=None
        if started is None:return
        elapsed=max(0.,now-started)
        if cancelled:
            self.release_reaction={}
        elif elapsed>=1.2:
            # O mesmo gesto muda com os motores e a associação aprendida de PRESS.
            motors=self.state.tone.r
            anger=motors.get('ANGRY',0)
            anticipation=self.conditioning.V.get('PRESS',0)
            intensity=min(1.,.45*anger+.35*min(1.,elapsed/5)+.2*anticipation)
            if anticipation>.55 or motors.get('SAD',0)>anger+.3:kind='timido'
            elif anger>.55 and elapsed>=4:kind='birra'
            elif motors.get('SETTLE',0)>.5 and anger<.4:kind='sacudir'
            else:kind='bravo'
            self.release_reaction=dict(kind=kind,started=now,until=now+2+3*intensity,intensity=intensity)
            self.conditioning.outcome(now)
        self.conditioning.set_cue('PRESS',False,now)

    def _sense_toy_cursor(self,now):
        near=(self.prefs.get('senseCursor',True) and not self.ball_stored and self.ball.isVisible()
              and not self.ball.dragging and not self.panel
              and math.dist(self.cursor,(self.ball.body.x,self.ball.body.y))<self.ball.body.half_w+24)
        if near and not self.cursor_toy_near and now>=self.next_toy_attention:
            self.senses.kick('NOVELTY',.35)
            self.behavior.look_at(self.ball.body.x,self.ball.body.y,now)
            self.next_toy_attention=now+2.5
        self.cursor_toy_near=near

    def _play_expression(self,now):
        attempt=self.behavior.last_play
        kind=None;duration=1.6
        if attempt and attempt['started']!=self.last_play_attempt:
            self.last_play_attempt=attempt['started']
            kind='comemorando' if attempt['action'] else 'bote_erro'
        elif (now>=self.next_play_scene and not self.body.held and self.body.grounded
                and not self.panel and not self.sleep.asleep and not self.state.caressing(now)):
            near=not self.ball_stored and self.ball.isVisible() and math.dist(
                (self.body.x,self.body.y),(self.ball.body.x,self.ball.body.y))<190
            if near and self.state.tone.r.get('STARTLE',0)>.35:
                kind='brinquedo_susto';duration=1.3
            elif self.mesa.sentado and self.behavior.play_pull>.5:
                kind='fingir_trabalho';duration=2.2
            elif near and self.behavior.adaptive_goal=='play' and self.behavior.play_pull>.3:
                kind='preparar_bote';duration=.8
        if kind:
            intensity=max(.35,min(1.,self.behavior.play_pull+self.state.tone.r.get('CHEER',0)*.3))
            self.play_reaction=dict(kind=kind,started=now,until=now+duration,intensity=intensity)
            self.next_play_scene=now+12

    def reset_learning(self):
        preferences, displays = dict(self.prefs), list(self.displays)
        panicked, excluded = self.panicked, list(self.excluded)
        import os
        backup = self.data_dir / 'backups' / ('learning-' + str(time.time_ns()))
        if self.pet_paths.base.exists():
            backup.parent.mkdir(parents=True,exist_ok=True)
            os.replace(self.pet_paths.base,backup)
            clear_protection_after_backup(self.pet_paths.base)
        # Reinicia a memória escolhida, sem cair numa pasta legada antiga após o backup.
        self.pet_paths.base.mkdir(parents=True,exist_ok=True)
        self.__init__(self.data_dir, self.conteudo.proprio)
        self.panicked = panicked
        self.configure(preferences)
        if displays: self.desktop(dict(areas=displays, exclude=excluded))
        self.save()

    def adapt(self, now):
        if now-self.last_intelligence < 1: return
        self.last_intelligence = now
        allowed = ['watch', 'rest']
        if self.prefs.get('roaming', True):
            allowed += ['explore']
            if not self.ball_stored: allowed += ['play']
            if self.prefs.get('senseCursor', True): allowed += ['attention']
        if not self.mesa.escondido and self.activity in ('PROGRAMMING', 'DESIGNING'): allowed += ['work']
        if self.panel or self.hover or self.body.held or self.sleep.asleep or self.castigo.dentro or self.castigo.fuga or self.protest.stage or self.sad.stage or self.behavior.mission: allowed = []
        before = self.intelligence.goal
        try:
            goal = self.intelligence.tick(now, time.time(), self.activity, self.state.emotion, self.rates, self.drives.energy, self.drives.contact, allowed, self.sleep.asleep)
            self.behavior.adaptive_goal = goal
            if goal and goal != before:
                area = self.bounds()
                self.behavior.adaptive_target = (area[0]+area[2])/2 if goal == 'explore' else max(area[0]+90, min(area[2]-90, self.cursor[0]+170))
                if goal == 'explore':
                    import random
                    self.behavior.adaptive_target = random.uniform(area[0]+90, area[2]-90)
        except Exception as error:
            self.intelligence.compatibility = f'Autonomia adicional pausada: {type(error).__name__}'
            self.intelligence.clear_goal()
            self.behavior.adaptive_goal = None
        if now-self.last_metrics >= 30:
            import psutil
            self.app_rss_mib = psutil.Process().memory_info().rss/1048576
            import numpy as np
            self.brain_array_mib = sum(v.nbytes for v in vars(self.brain).values() if isinstance(v,np.ndarray) and v.base is None)/1048576
            self.last_metrics = now

    def think(self, dt, now):
        moving = min(1., abs(self.body.vx) / 200 + (0 if self.body.grounded else 1))
        caressing = self.state.caressing(now)
        self.drives.update(dt, self.prof, self.sleep.asleep, moving, self.emotion.arousal, self.activity == 'AWAY', engaged=self.activity in ('PROGRAMMING', 'DESIGNING'), preso=self.castigo.dentro, visitado=self.castigo.visita > .5)
        if caressing: self.drives.stimulate('caress', dt); self.drives.touched('caress', dt)
        self.castigo.tick_lento(dt)
        inputs = self.senses.update(self.activity, self.idle if self.prefs.get('senseIdle',True) else None, self.drives.channels(), caressing, self.prefs.get('senseCursor',True) and math.dist(self.cursor,self.last_cursor) > 2)
        self.last_cursor = self.cursor
        self.conditioning.set_cue('PRESS', self.state.pressing, now)
        distance = math.dist(self.cursor,(self.body.x,self.body.y))
        self.conditioning.set_cue('APPROACH', self.prefs.get('senseCursor',True) and self.prev_distance is not None and distance < 220 and (self.prev_distance - distance) / max(.01,dt) > 500, now)
        self.prev_distance = distance
        self.conditioning.set_cue('PLACA', self.castigo.perto_da_placa(self.body), now)
        self.conditioning.tick(now)
        inputs['ANTICIPATE'] = self.conditioning.strength()
        inputs['ANTECIPA_PLACA'] = self.conditioning.strength(cues=('PLACA',))
        taken, near = self.toy_tracker.update((self.ball.body.x,self.ball.body.y),(self.body.x,self.body.y),self.ball.handled_by_user(now))
        if taken and not self.ball_stored: self.senses.kick('TOY_TAKEN', .9)
        inputs['TOY_NEAR'] = near if not self.ball_stored else 0
        inputs['PEDIDO'] = max(self.mesa.intensidade_pedido(now), .5 if self.behavior.adaptive_goal == 'work' else 0.)
        inputs.update(self.castigo.sinais(self.body))
        inputs['RECUSA'] = self.request_refused; self.request_refused = 0
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
        self.adapt(now)

    def tick(self, dt, now=None):
        now = time.monotonic() if now is None else now
        dt = min(.05, max(0.,dt))
        if not self.panicked and not self.hidden: self.read_context(now)
        frozen = self.panicked or self.hidden or not self.available_areas()
        if frozen:
            self._cancel_holds(now)
            self.cursor_toy_near=False
            if self.paused_at is None: self.paused_at = now
            return
        if self.paused_at is not None:
            elapsed = now - self.paused_at
            self.castigo.deslocar(elapsed); self.mesa.deslocar(elapsed)
            self.memory.deslocar(elapsed)
            self.intelligence.until += elapsed
            self.paused_at = None; self.last_think = now
        self._sense_toy_cursor(now)
        if now - self.last_think >= .1:
            self.think(min(.1,now-self.last_think),now); self.last_think = now
        area = self.bounds()
        areas = self.available_areas()
        monitors = [monitor for i, monitor in enumerate(self.monitors) if i not in self.blocked]
        self.behavior.screen_areas = areas
        self.behavior.toy = (self.ball.body.x,self.ball.body.y) if not self.ball_stored else None
        platforms = getattr(self,'platforms',[]) if self.prefs.get('senseWindows',True) else []
        self.castigo.act(now,self.body,area,self.cursor if self.prefs.get('senseCursor',True) else (1e9,1e9),self.state,self.rates,self.sleep.asleep)
        resting = self.hover or self.panel or now < self.quiet_until or not self.prefs.get('roaming',True)
        self.behavior.tick(dt,now,self.cursor,area,self.prof,platforms,not resting)
        self._play_expression(now)
        reaction=self.release_reaction
        if (reaction.get('until',0)>now and reaction.get('kind') in ('bravo','birra')
                and self.prefs.get('senseCursor',True) and not self.state.caressing(now)):
            dx,dy=self.cursor[0]-self.body.x,self.cursor[1]-self.body.y
            distance=math.hypot(dx,dy) or 1.
            angle=math.radians(self.body.angle)
            self.state.gaze=((dx*math.cos(angle)+dy*math.sin(angle))/distance,
                             (-dx*math.sin(angle)+dy*math.cos(angle))/distance)
        self.body.step(dt,area,platforms,areas,monitors,[d for i,d in enumerate(self.displays) if i not in self.blocked])
        if self.mesa.sentado and self.mesa.pin(self.body,now): self.mesa.levantar_arrancado(now); self.protest_ctl.provoke(.1)
        if not self.ball_stored:
            self.ball.step(dt,self.bounds((self.ball.body.x,self.ball.body.y)),areas,monitors,[d for i,d in enumerate(self.displays) if i not in self.blocked])
        impacts = self.body.pop_impacts()
        self.landing *= math.exp(-dt * 12)
        for strength in impacts:
            self.senses.impact(min(1.,strength / 1600))
            self.landing = max(self.landing,min(1.,strength / 1000))
        self.mesa.set_visible(not self.mesa.escondido)
        self.protest_ctl.carry(now,self.sleep.asleep); self.sad_ctl.carry(now,self.sleep.asleep)
        self.mischief.tick(dt,area[3])
        perms = dict(config.DEFAULT_PERMISSIONS, travessuras=self.prefs.get('mischiefEnabled',True), fotos=False)
        if not self.castigo.dentro and not self.hover and not self.panel and now >= self.quiet_until and self.intelligence.goal not in ('watch','rest','work'):
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
        self.intelligence.habits.save()
        self.protest_ctl.save(); self.sad_ctl.save(); self.castigo.salvar()
        write_json(self.data_dir / 'position.json',dict(x=self.body.x,y=self.body.y))

    def snapshot(self):
        now = time.monotonic()
        objects = []
        for obj in list(self.objects.values()):
            data = obj.snapshot()
            if obj.isVisible() and self.visible(): objects.append(data)
        pose = ('held' if self.body.held else 'airborne' if not self.body.grounded else
                'sleeping' if self.sleep.asleep else 'working' if self.mesa.sentado else
                'lying' if not self.body.upright() else 'idle')
        data = dict(ready=True,blocked=list(self.blocked),panicked=self.panicked,x=self.body.x,y=self.body.y,angle=self.body.angle,emotion=self.state.emotion,visible=self.visible(),held=self.body.held,caressing=self.state.feliz_fechado(now),gaze=self.state.gaze,objects=objects,energy=self.drives.energy,stimulation=self.drives.stimulation,lonely=self.drives.contact,protest=self.protest.stage,castigo=self.castigo.dentro,escapes=self.castigo.vitorias['fugir'],activity=self.activity,motors=self.rates,learned=[],neurons=self.brain.N,error=self.native_error,
                    pose=pose,grounded=self.body.grounded,surface=self.body.surface if self.body.grounded else self.bounds()[3],vx=self.body.vx,vy=self.body.vy,landing=self.landing)
        if self.monitor_open:
            if now - self.last_monitor_snapshot >= .25:
                data.update(
                    intelligence=dict(self.intelligence.summary(self.activity,time.time()),appRssMiB=self.app_rss_mib,brainArrayMiB=self.brain_array_mib),
                    learned=self.brain.learned_summary(8),
                    neural=dict(positions=self.brain.pos.tolist(),trace=self.brain.trace.tolist(),kind=self.brain.kind.tolist(),pools=self.brain.pool_rates()))
                self.last_monitor_snapshot = now
        return data
