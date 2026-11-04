# SPDX-License-Identifier: GPL-3.0-only
"""Objetos do modelo: uma única física compartilhada pelas janelas Qt."""
import math
import time
from pathlib import Path
from .core.physics import Body, GRAVITY

_current = None


def set_scene(app):
    global _current
    _current = app


class Signal:
    def __init__(self, *_types):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in tuple(self.callbacks):
            callback(*args)


class Geometry:
    def __init__(self, x, y, w, h):
        self._x, self._y, self._w, self._h = x, y, w, h

    def x(self): return self._x
    def y(self): return self._y
    def width(self): return self._w
    def height(self): return self._h
    def center(self): return Geometry(self._x + self._w / 2, self._y + self._h / 2, 0, 0)


class Item:
    def __init__(self, kind, width, height, text=""):
        self.app = _current
        self.id = str(self.app.next_id)
        self.app.next_id += 1
        self.kind, self._w, self._h, self.text = kind, width, height, text
        self._cx = self._cy = 0.0
        self.visible = False
        self.closed = False
        self.clicked = Signal()
        self.born = time.monotonic()
        self.carried = False
        self.resting = True
        self.tilt = 0.0
        self.vy = 0.0
        self.valida = True
        self.working = False
        self.image = None
        self.app.objects[self.id] = self

    def width(self): return self._w
    def height(self): return self._h
    def place(self, x=None, y=None):
        if x is None and hasattr(self, 'body'):
            self._cx, self._cy = self.body.x, self.body.y
        elif x is not None:
            self._cx, self._cy = float(x), float(y)
    def geometry(self): return Geometry(self._cx - self._w / 2, self._cy - self._h / 2, self._w, self._h)
    def isVisible(self): return self.visible and not self.closed
    def setVisible(self, value): self.visible = bool(value) and not self.closed
    def show(self): self.setVisible(True)
    def hide(self): self.setVisible(False)
    def close(self): self.visible = False; self.closed = True
    def deleteLater(self): self.close(); self.app.objects.pop(self.id, None)
    def update(self): pass
    def raise_(self): pass
    def set_working(self, value): self.working = value
    def move(self, x, y): self.place(x + self._w / 2, y + self._h / 2)
    def fall(self, dt, floor):
        if self.carried or self.resting: return
        self.vy += GRAVITY * dt
        y = self._cy + self.vy * dt
        if y + self._h / 2 >= floor:
            y = floor - self._h / 2
            self.vy = -self.vy * 0.25 if self.vy > 300 else 0
            self.resting = self.vy == 0
        self.place(self._cx, y)
    def snapshot(self):
        return dict(id=self.id, kind=self.kind, x=self._cx, y=self._cy, width=self._w, height=self._h,
                    text=self.text, image=self.image, angle=self.tilt, working=self.working, carried=self.carried)


class ObjectThing(Item):
    @property
    def x(self): return self._cx
    @property
    def y(self): return self._cy


class FloatingThing(Item):
    def x(self): return self._cx - self._w / 2
    def y(self): return self._cy - self._h / 2


class ImageThing(ObjectThing):
    def __init__(self, path, max_side):
        super().__init__('meme', min(240, max_side), min(240, max_side))
        self.valida = bool(path and Path(path).is_file())
        self.image = Path(path).stem if path else None
        self.emotion=Path(path).parent.name if path else 'observando'
        self.title='';self.subtitle=''
        if self.valida and Path(path).suffix.lower()=='.svg':
            import xml.etree.ElementTree as ET
            try:
                root=ET.fromstring(Path(path).read_text(encoding='utf-8'))
                texts=[''.join(node.itertext()) for node in root if node.tag.endswith('text')]
                self.title=texts[0] if texts else ''
                self.subtitle=texts[1] if len(texts)>1 else ''
            except (OSError,ET.ParseError):self.valida=False


class NoteThing(ObjectThing):
    def __init__(self, text, small=False):
        super().__init__('note', 150 if small else 190, 120 if small else 145, text)


class SignThing(ObjectThing):
    def __init__(self, text, style='small', scale=1.0):
        super().__init__('sign', min(340, 190 * scale), min(210, 94 * scale), text)
        self.style = style


class FlagThing(SignThing):
    pass


def criar_cartaz(data):
    cls = FlagThing if data.get('bandeira') else SignThing
    return cls(data['texto'], data.get('estilo'), data.get('escala', 1.0))


class PlaquinhaCanto(FloatingThing):
    def __init__(self, app):
        super().__init__('corner', 190, 150, 'CANTINHO DO CASTIGO')
        left, _top, _right, bottom = app.bounds()
        self.move(left + 12, bottom - 154)


class Notebook(FloatingThing):
    def __init__(self, app):
        super().__init__('notebook', 190, 115)
        left, _top, right, bottom = app.bounds()
        self.move((left + right) / 2 - 95, bottom - 120)


class Fireworks(Item):
    def __init__(self, app):
        super().__init__('fireworks', 300, 250)
        self.until = 0.0
    def launch(self, x, y):
        self.place(x, y); self.until = time.monotonic() + 3.2; self.show()
    def snapshot(self):
        if time.monotonic() > self.until: self.hide()
        return super().snapshot()


class Ball(Item):
    def __init__(self, x, y, kind='ball', sprite=None):
        super().__init__('paper' if kind == 'papel' else 'ball', 34, 34)
        self.body = Body(x, y, 17, 17)
        self.dragging = False
        self.last_handled = -1e9
        self.place()
    def kick(self, vx, vy): self.body.jump(vx, vy)
    def handled_by_user(self, now): return self.dragging or now - self.last_handled < 1
    def step(self, dt, bounds, areas=None, monitors=None, displays=None):
        if not self.dragging: self.body.step(dt, bounds, [], areas, monitors, displays)
        self.place()
