# SPDX-License-Identifier: GPL-3.0-only
"""Rotina compacta e objetivos; reutiliza o bandit e os episódios do Pestinha."""
import math
import random
import time
import copy
from collections import deque
from datetime import datetime
from pestinha.store import read_json, write_json

ACTIVITIES = {'IDLE', 'AWAY', 'PROGRAMMING', 'DESIGNING', 'GAMING', 'BROWSING', 'SOCIAL', 'MUSIC'}
GOALS = ('explore', 'play', 'watch', 'rest', 'work', 'attention')
LABELS = dict(explore='Explorar', play='Brincar', watch='Observar', rest='Descansar', work='Trabalhar junto', attention='Procurar carinho')
MAX_SLOTS = 256
HALF_LIFE = 30 * 86400


class Habits:
    def __init__(self, path):
        self.path = path
        self.slots = {}
        saved = read_json(path, default={})
        rows = saved.get('slots', {}) if isinstance(saved, dict) else {}
        if isinstance(rows, dict):
            for key, row in list(rows.items())[-MAX_SLOTS:]:
                parts = key.split('|')
                if len(parts) != 3 or parts[2] not in ACTIVITIES or not parts[0].isdigit() or not parts[1].isdigit(): continue
                if not (0 <= int(parts[0]) < 7 and 0 <= int(parts[1]) < 24): continue
                if not isinstance(row, list) or len(row) != 4: continue
                if all(type(n) in (int, float) and math.isfinite(n) for n in row) and 0 <= row[1] <= row[0] <= 120 and 0 <= row[2] <= row[0] and 0 <= row[3] <= 1e13:
                    self.slots[key] = row

    @staticmethod
    def key(activity, wall):
        local = datetime.fromtimestamp(wall)
        return f'{local.weekday()}|{local.hour}|{activity if activity in ACTIVITIES else "IDLE"}'

    def observe(self, activity, interacted, asleep, wall):
        key = self.key(activity, wall)
        n, attention, rest, previous = self.slots.pop(key, [0., 0., 0., wall])
        decay = .5 ** (max(0., wall-previous) / HALF_LIFE)
        scale = min(decay, 119 / n) if n else decay
        self.slots[key] = [n*scale+1, attention*scale+bool(interacted), rest*scale+bool(asleep), wall]
        while len(self.slots) > MAX_SLOTS:
            del self.slots[next(iter(self.slots))]

    def tendency(self, activity, wall):
        n, attention, rest, previous = self.slots.get(self.key(activity, wall), [0., 0., 0., wall])
        confidence = min(1., n / 8) * .5 ** (max(0., wall-previous) / HALF_LIFE)
        return dict(attention=attention/max(1., n)*confidence, rest=rest/max(1., n)*confidence, familiarity=confidence)

    def save(self):
        write_json(self.path, dict(version=1, slots=self.slots))


class Intelligence:
    def __init__(self, memory, habits_path, rng=None):
        self.memory = memory
        self.habits = Habits(habits_path)
        self.rng = rng or getattr(memory, 'rng', None) or random.Random(1313)
        self.goal = None
        self.until = self.next_choice = self.next_sample = 0.
        self.episode = None
        self.last_interaction = -1e9
        self.last_goal = None
        self.repeats = 0
        self.enabled = True
        self.learn_routine = True
        self.compatibility = ''
        self.cpu_seconds = 0.
        self.decisions = 0
        self.memory_strikes = 0
        self.current_decision = None
        self.history = deque(maxlen=32)
        self.expression_until = 0.
        self.next_blink = self.next_quirk = self.next_wink = 0.

    def feedback(self, value, now):
        self.last_interaction = now
        if self.episode is not None and any(ep is self.episode for ep in self.memory.open):
            self.memory._resolve(self.episode, 'carinho' if value > 0 else 'pedido de sossego', value)
        self.episode = None
        if value < 0:
            self.goal, self.until, self.next_choice = 'watch', now+30, now+30

    def clear_goal(self):
        if self.episode is not None and any(ep is self.episode for ep in self.memory.open):
            self.memory._resolve(self.episode, 'interrompido', 0.)
        self.episode = None
        self.goal = None
        self.until = 0.
        self.current_decision = None

    def snapshot(self):
        """Small serializable trace of the policy's real current choice."""
        return dict(current=copy.deepcopy(self.current_decision), history=copy.deepcopy(list(self.history)))

    def choose(self, action, candidates, *, rates=None, emotion='observando', energy=1., contact=0.,
               duration=0., source='lif_policy', weights=None):
        """Shared categorical action selector; keeps the actual alternatives and influences."""
        if not candidates:
            return None
        rates = rates or {}
        neural = {k: float(v) for k, v in rates.items() if isinstance(v, (int,float))}
        weights = weights or {}
        context = f'{action}|{emotion}'
        values = {str(candidate): float(weights.get(candidate, 0.)) for candidate in candidates}
        if self.enabled and not self.compatibility:
            selected = self.memory.choose(context, [str(candidate) for candidate in candidates], .05, values)
            estimate = self.memory.estimate(context, selected)
        else:
            best = max(values.values())
            selected = self.rng.choice([key for key, score in values.items() if score == best])
            estimate = 0.
        self.current_decision = dict(action=str(action), target=selected, intensity=max(0., min(1., values.get(selected, 0.))),
                                     duration=float(duration), source=source,
                                     factors=dict(neural=neural, policy_weights=values, emotion=emotion,
                                                  drives=dict(energy=energy, contact=contact),
                                                  memory=dict(context=context, action=selected,
                                                              estimate=estimate)))
        self.history.append(dict(self.current_decision))
        return selected

    def sample(self, action, probability, *, rates=None, emotion='observando', energy=1., contact=0.,
               duration=0., source='lif_policy'):
        """Policy-owned Bernoulli action for real firing-rate events."""
        base_probability = max(0., min(1., float(probability)))
        context = f'{action}|{emotion}'
        use_memory = self.enabled and not self.compatibility
        estimate = self.memory.estimate(context, 'act') if use_memory else 0.
        factor = max(.5, min(1.5, 1. + estimate - .1)) if use_memory else 1.
        probability = min(1., base_probability * factor)
        if probability <= 0. or self.rng.random() >= probability:
            return False
        neural = {k: float(v) for k,v in (rates or {}).items() if isinstance(v,(int,float))}
        self.current_decision = dict(action=action, target='act', intensity=probability,
                                     duration=float(duration), source=source,
                                     factors=dict(neural=neural, policy_weights={'base_probability':base_probability,
                                                  'memory_factor':factor,'applied_probability':probability},
                                                  emotion=emotion, drives=dict(energy=energy,contact=contact),
                                                  memory=dict(context=context, estimate=estimate)))
        self.history.append(copy.deepcopy(self.current_decision))
        return True

    def event(self, action, rate_hz, gain, dt, *, rates=None, emotion='observando', energy=1., contact=0.):
        """Convert a LIF firing rate to a frame-rate invariant hazard and sample it centrally."""
        if not all(math.isfinite(float(v)) for v in (rate_hz, gain, dt)) or dt <= 0 or rate_hz <= 0 or gain <= 0:
            return False
        probability = -math.expm1(-rate_hz * gain * dt)
        return self.sample(action, probability, rates=rates, emotion=emotion, energy=energy,
                           contact=contact, duration=dt, source='lif_hazard')

    def choose_expression(self, candidates, rates, emotion, energy, contact, now):
        """Choose an optional expression using the same learned, continuous state."""
        if not candidates or self.compatibility:
            return None
        if now < self.expression_until:
            return None
        due = []
        if 'blink' in candidates and now >= self.next_blink: due.append('blink')
        due.extend(key for key in candidates if key not in ('blink','wink') and now >= self.next_quirk)
        if 'wink' in candidates and now >= self.next_wink: due.append('wink')
        if not due: return None
        neural = {k: float(rates.get(k, 0.)) for k in ('CHEER', 'WATCH', 'DROWSE', 'ANGRY')}
        normalized = {k: min(1., max(0., value / 30.)) for k,value in neural.items()}
        factors = dict(neural=neural, emotion=emotion, energy=energy, contact=contact)
        weights = {name: (normalized['CHEER'] if name in ('wink','stretch','ear_wiggle') else
                          normalized['DROWSE'] + (1-energy) if name in ('doze','hiccup') else
                          normalized['WATCH'] if name in ('sneeze','hiccup') else .1)
                   for name in candidates}
        context = 'expression|' + emotion
        if self.enabled:
            action = self.memory.choose(context, due, .05, weights)
        else:
            action = max(due, key=lambda key: weights[key])
        factors['memory'] = dict(context=context, estimate=self.memory.estimate(context, action) if self.enabled else 0.)
        factors['policy_weights'] = weights
        duration = .13 if action == 'blink' else 2.3 if action == 'stretch' else 1.65 if action == 'sneeze' else 1.6 if action == 'hiccup' else 3.3 if action == 'doze' else 1.5 if action == 'ear_wiggle' else 1.81
        self.expression_until = now + duration
        if action == 'blink': self.next_blink = now + self.rng.uniform(3.2, 5.2)
        elif action == 'wink': self.next_wink = now + self.rng.uniform(90, 180)
        else: self.next_quirk = now + self.rng.uniform(35, 80)
        self.current_decision = dict(action=action, target=None, intensity=max(.1, weights[action]),
                                     duration=duration, source='expression_policy', factors=factors)
        self.history.append(dict(self.current_decision))
        return action

    def budget(self, rss_mib, limit=100_000_000/1048576):
        self.memory_strikes = self.memory_strikes+1 if rss_mib > limit else 0
        if self.memory_strikes >= 3:
            self.compatibility = 'Cérebro acima do orçamento: autonomia adicional em pausa.'
            self.clear_goal()

    def tick(self, now, wall, activity, emotion, rates, energy, lonely, allowed, asleep=False):
        started = time.process_time()
        try:
            if not self.enabled or self.compatibility:
                self.clear_goal()
                return None
            if self.learn_routine and now >= self.next_sample:
                self.habits.observe(activity, self.last_interaction >= self.next_sample-30, asleep, wall)
                self.next_sample = now+30
            if not allowed:
                self.clear_goal()
                return None
            if self.goal in allowed and now < self.until:
                return self.goal
            if now < self.next_choice: return None
            self.clear_goal()
            habit = self.habits.tendency(activity, wall) if self.learn_routine else dict(attention=0., rest=0., familiarity=0.)
            neural = lambda key: min(1., max(0., rates.get(key, 0.)/30))
            bias = dict(explore=.16*neural('WANDER'), play=.18*neural('CHEER'), watch=.08,
                        rest=.25*(1-energy)+.12*habit['rest'],
                        work=(.2 if activity in ('PROGRAMMING', 'DESIGNING') else 0.)+.1*neural('SENTAR'),
                        attention=.18*lonely+.12*habit['attention'])
            if self.last_goal and self.repeats >= 2: bias[self.last_goal] -= .2
            prefix = f'rotina:{datetime.fromtimestamp(wall).hour//6}' if self.learn_routine else 'objetivo'
            ctx = f'{prefix}|{activity}|{emotion}'
            actions = ['goal:'+g for g in allowed if g in GOALS]
            if not actions: return None
            action = self.memory.choose(ctx, actions, .12, {'goal:'+g:v for g,v in bias.items()})
            self.goal = action[5:]
            self.repeats = self.repeats+1 if self.last_goal == self.goal else 1
            self.last_goal = self.goal
            duration = self.rng.uniform(12, 32)
            self.until = now+duration
            self.next_choice = now+1
            self.episode = self.memory.start(ctx, action)
            self.decisions += 1
            factors = dict(neural={key: float(rates.get(key,0.)) for key in ('WANDER','CHEER','SENTAR')},
                           emotion=emotion, drives=dict(energy=energy, contact=lonely),
                           memory=dict(context=ctx, action=action,
                                       estimate=self.memory.estimate(ctx, action)),
                           habit=habit)
            self.current_decision = dict(action=self.goal, target=None, intensity=max(0., min(1., bias.get(self.goal, 0.))),
                                         duration=duration, source='lif+episodic_policy', factors=factors)
            self.history.append(dict(self.current_decision))
            return self.goal
        finally:
            self.cpu_seconds += time.process_time()-started

    def summary(self, activity, wall):
        return dict(enabled=self.enabled and not bool(self.compatibility), goal=self.goal,
                    label=LABELS.get(self.goal, 'Seguindo os impulsos da rede'), until=self.until,
                    routine=self.habits.tendency(activity, wall) if self.learn_routine else None,
                    slots=len(self.habits.slots), episodes=len(self.memory.recent),
                    decisions=self.decisions, cpuSeconds=self.cpu_seconds, compatibility=self.compatibility)
