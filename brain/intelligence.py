# SPDX-License-Identifier: GPL-3.0-only
"""Rotina compacta e objetivos; reutiliza o bandit e os episódios do Pestinha."""
import math
import random
import time
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
        self.rng = rng or random.Random()
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
            bias = dict(explore=.16*neural('ANDA'), play=.18*neural('PULA'), watch=.08,
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
            self.until = now+self.rng.uniform(12, 32)
            self.next_choice = now+1
            self.episode = self.memory.start(ctx, action)
            self.decisions += 1
            return self.goal
        finally:
            self.cpu_seconds += time.process_time()-started

    def summary(self, activity, wall):
        return dict(enabled=self.enabled and not bool(self.compatibility), goal=self.goal,
                    label=LABELS.get(self.goal, 'Seguindo os impulsos da rede'), until=self.until,
                    routine=self.habits.tendency(activity, wall) if self.learn_routine else None,
                    slots=len(self.habits.slots), episodes=len(self.memory.recent),
                    decisions=self.decisions, cpuSeconds=self.cpu_seconds, compatibility=self.compatibility)
