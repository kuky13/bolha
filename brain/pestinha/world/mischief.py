"""
MISCHIEF - memes, fotos e bilhetes que o pet espalha pela tela.

Regras fixas (não dependem do cérebro):
    - só com permissão, fora de tela cheia e abaixo do limite de objetos
    - um clique em qualquer lugar do objeto fecha ele (sempre)
    - nada nasce em cima do cursor
O cérebro só decide QUANDO e com que emoção; aqui se decide a FORMA.
"""

import math
import time

from ..scene import Signal

from .. import config
from .objetos import ImageThing, NoteThing
from ..ajustes import TAMANHO_MEME as MEME_MAX, TAMANHO_MEME_CANTO as CORNER_MAX

CORNER_MARGIN = 18


class MischiefEngine:
    """Guarda os objetos na tela e decide a próxima travessura."""

    # Signal instances belong to each engine.     # (objeto, segundos que ficou na tela)

    def __init__(self, conteudo):
        """Guarda os objetos na tela (memes, bilhetes, fotos) e o conteúdo do pet para sorteá-los."""
        self.dismissed = Signal(object, float)
        self.things = []
        self.last_act = -1e9
        self.interval = 300.0
        self.max_objects = 3
        self.online_reactions = True
        self.paths = conteudo                                 # ConteudoPaths: só o conteúdo deste pet e o comum
        self.notes = config.Notes(conteudo.notes)
        self.notes_sad = config.Notes(conteudo.notes_sad)       # bilhetes de quando ele está triste
        self.policy = None
        self.rates = {}
        self.energy = self.contact = 1.

    def _choose(self, action, candidates, emotion='observando', weights=None):
        """Escolhe uma alternativa real pela política central; sem política, aguarda."""
        if not candidates or self.policy is None:return None
        keys=[str(index) for index in range(len(candidates))]
        policy_weights={key:float((weights or {}).get(key,0.)) for key in keys}
        selected=self.policy.choose(action,keys,rates=self.rates,emotion=emotion,
                                    energy=self.energy,contact=self.contact,duration=0.,
                                    source='mischief_world',weights=policy_weights)
        try:index=int(selected)
        except (TypeError,ValueError):return None
        return candidates[index] if 0<=index<len(candidates) else None

    def _meme_paths(self, emotion, working=False):
        root=self.paths.memes_trabalho if working else self.paths.memes
        own=config.list_images(root/'trabalho') if working else config.list_images(root/emotion)
        if own:return own
        return [path for label in config.EMOTIONS for path in config.list_images(root/label)]

    # ---------------- agenda ----------------

    def allowed(self, perms, prof, fullscreen):
        """Diz se uma travessura pode acontecer agora (permissões, tela cheia e limite de objetos)."""
        if not perms["ativo"] or not perms["travessuras"]:
            return False
        if fullscreen and not perms["tela_cheia"]:
            return False
        if not (perms["memes"] or perms["fotos"] or perms["bilhetes"]):
            return False
        return len(self.things) < self.max_objects and time.monotonic() - self.last_act >= self.interval

    def available(self, emotion, perms, working=False):
        """Ações que as regras permitem agora (a memória escolhe entre elas)."""
        if emotion == "dormindo":
            return []                                   # dormindo, nem pensar
        if emotion == "triste":                         # triste só cola bilhetes tristes
            return ["bilhete_triste", "nada"] if perms["bilhetes"] and self.notes_sad.has_lines() else []
        online = perms.get("online_reactions", self.online_reactions)
        if working:                                     # programando sem estar sentado: meme de trabalho
            trabalho = perms["memes"] and online
            return ["meme_trabalho", "nada"] if trabalho else []
        memes = perms["memes"] and online
        notes = perms["bilhetes"] and self.notes.has_lines()
        if emotion == "bravo":
            options = ((["meme_canto", "meme"] if memes else []) + (["bilhete_canto"] if notes else []))
            return options + ["nada"] if options else []
        photos = perms["fotos"] and bool(config.list_images(self.paths.fotos))
        options = (["meme"] if memes else []) + (["foto"] if photos else []) + (["bilhete"] if notes else [])
        return options + ["atravessar", "nada"] if options else []

    def plan(self, action, emotion):
        """
        Transforma a ação escolhida em algo concreto:
            ("corner", thing)    coisinha de revolta num canto
            ("deliver", thing)   arrasta um meme/foto/bilhete pela tela
            ("cross", None)      atravessa a tela e não faz nada
            None                 nada
        """
        if action in ("meme_canto", "bilhete_canto"):
            thing = self._make(action.split("_")[0], emotion, small=True)
            return ("corner", thing) if thing else None
        if action in ("meme", "meme_trabalho", "foto", "bilhete", "bilhete_triste"):
            thing = self._make(action, emotion, small=False)
            return ("deliver", thing) if thing else None
        if action == "atravessar":
            return ("cross", None)
        return None

    def _make(self, kind, emotion, small):
        """Monta o objeto da travessura: imagem, bilhete ou foto, conforme o tipo e a emoção."""
        if kind in ("meme", "meme_trabalho") and not self.online_reactions:
            return None
        if kind == "meme":
            paths=self._meme_paths(emotion)
            candidates=list(paths)+(['online'] if self.online_reactions else [])
            selected=self._choose('mischief_content',candidates,emotion)
            if selected is None:return None
            path=None if selected=='online' else selected
            thing = ImageThing(path, CORNER_MAX if small else MEME_MAX, emotion=emotion,
                               reaction_kind='online' if path is None else kind)
        elif kind == "meme_trabalho":
            paths=self._meme_paths(emotion,working=True) or self._meme_paths(emotion)
            candidates=list(paths)+(['online'] if self.online_reactions else [])
            selected=self._choose('mischief_content',candidates,emotion)
            if selected is None:return None
            path=None if selected=='online' else selected
            thing = ImageThing(path, MEME_MAX, emotion=emotion,
                               reaction_kind='online' if path is None else kind)
        elif kind == "foto":
            options=config.list_images(self.paths.fotos)
            path=self._choose('mischief_content',options,emotion)
            thing = ImageThing(path, MEME_MAX, emotion=emotion, reaction_kind=kind) if path else None
        else:
            notes = self.notes_sad if kind == "bilhete_triste" else self.notes
            notes.has_lines()
            options=[line for line in notes.lines if line!=notes.last] or list(notes.lines)
            text=self._choose('mischief_note',options,emotion)
            if text is not None:notes.last=text
            thing = NoteThing(text, small=small) if text else None
        if thing is not None and not getattr(thing, "valida", True):
            thing.deleteLater()                      # imagem ilegível: nada de objeto invisível na tela
            return None
        if thing is not None:
            thing.clicked.connect(self._on_click)
        return thing

    def create_online_reaction(self, emotion='observando'):
        """Cria uma reação online sem depender de arquivo ou catálogo local."""
        if not self.online_reactions or len(self.things) >= self.max_objects:
            return None
        thing = ImageThing(None, MEME_MAX, emotion=emotion, reaction_kind='online')
        thing.valida = True
        thing.clicked.connect(self._on_click)
        self._add(thing)
        return thing

    # ---------------- colocação ----------------

    def show_in_corner(self, thing, bounds, cursor):
        """Põe o objeto num canto da tela (travessura 'de revolta')."""
        left, top, right, bottom = bounds
        hw, hh = thing.width() / 2, thing.height() / 2
        corners = [
            (left + hw + CORNER_MARGIN, top + hh + CORNER_MARGIN),
            (right - hw - CORNER_MARGIN, top + hh + CORNER_MARGIN),
            (left + hw + CORNER_MARGIN, bottom - hh - CORNER_MARGIN),
            (right - hw - CORNER_MARGIN, bottom - hh - CORNER_MARGIN),
        ]
        free = [
            c for c in corners
            if all(math.hypot(c[0] - t.x, c[1] - t.y) > 80 for t in self.things)
            and math.hypot(c[0] - cursor[0], c[1] - cursor[1]) > 250
        ]
        if not free:
            thing.deleteLater()
            return False
        weights={str(index):math.dist(point,cursor) for index,point in enumerate(free)}
        selected=self._choose('mischief_location',free,getattr(thing,'emotion','observando'),weights)
        if selected is None:
            thing.deleteLater();return False
        thing.place(*selected)
        self._add(thing)
        return True

    def attach(self, thing, x, y):
        """Você pegou o objeto: ele segue o mouse até você soltar."""
        thing.carried = True
        thing.resting = False
        thing.place(x, y)
        self._add(thing)

    def release(self, thing):
        """Você soltou o objeto: ele volta a cair."""
        thing.carried = False
        thing.vy = 0.0
        # post-it cola onde foi largado; meme e foto caem como objetos
        thing.resting = isinstance(thing, NoteThing)

    def follow(self, thing, anchor_x, anchor_y, dt):
        """Objeto arrastado segue o pet com atraso (mola), parecendo ter peso."""
        k = 1.0 - math.exp(-dt / 0.12)
        thing.place(thing.x + (anchor_x - thing.x) * k, thing.y + (anchor_y - thing.y) * k)

    def _add(self, thing):
        """Põe um objeto na lista e o mostra."""
        self.last_act = time.monotonic()
        self.things.append(thing)
        thing.show()

    # ---------------- ciclo ----------------

    def tick(self, dt, floor):
        """Um passo de física: os objetos caem até o chão."""
        for thing in self.things:
            thing.fall(dt, floor)

    def set_visible(self, visible):
        """Mostra ou esconde todos os objetos de uma vez."""
        for thing in self.things:
            thing.setVisible(visible)

    def _on_click(self, thing):
        """Clicaram no objeto: ele some e o tempo até o clique é registrado."""
        elapsed = time.monotonic() - thing.born
        self._remove(thing)
        self.dismissed.emit(thing, elapsed)

    def _remove(self, thing):
        """Tira um objeto da tela e da lista."""
        if thing in self.things:
            self.things.remove(thing)
        thing.close()
        thing.deleteLater()

    def clear(self):
        """Tira todos os objetos da tela."""
        for thing in list(self.things):
            self._remove(thing)

    def clear_memes(self):
        """Remove apenas reações online de meme quando o recurso é desligado."""
        for thing in list(self.things):
            if getattr(thing, "kind", None) == "meme":
                self._remove(thing)
