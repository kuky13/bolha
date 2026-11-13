# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Falas locais escolhidas pela política neural, sem ler conteúdo do desktop."""
import math
import time
from collections import deque

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen, QTransform
from PySide6.QtWidgets import QWidget
from .pet import FLAGS

# Conteúdo próprio da Bolha. Nenhum nome de programa, arquivo ou janela é exposto.
LINES = {
    'carinho': (
        'Mais um pouquinho desse carinho?', 'Minhas orelhas aprovaram.',
        'Pronto, virei um pudim feliz.', 'Esse carinho valeu meu dia.',
        'Pode deixar, guardei esse momento.', 'Agora estou toda derretida.',
        'Tem carinho dos dois lados?', 'Minha bateria de afeto está carregando.'),
    'segurando': (
        'Ei, minhas orelhinhas!', 'O chão ficou tão longe…', 'Estou na sua mão, literalmente.',
        'Já deu de elevador?', 'Pode me colocar no chão com jeitinho?', 'Uma bolha também precisa de espaço.'),
    'bravo': (
        'Estou pequenininha, mas estou brava.', 'Minhas orelhas registraram uma reclamação.',
        'Preciso de um instante para desamassar o humor.', 'Não vale tirar meu brinquedo toda hora!',
        'Vou respirar… uma, duas, três bolhas.', 'Estou fazendo minha cara mais séria.'),
    'brincando': (
        'Agora é minha vez!', 'Essa eu quase peguei!', 'Mais uma rodada?', 'Estou de olho no brinquedo.',
        'Meu bote foi calculado. Quase.', 'Isso conta como exercício?', 'Pode mandar, estou pronta.',
        'Minha estratégia é correr e torcer.'),
    'trabalho': (
        'Estou trabalhando muito seriamente.', 'Uma tecla, uma ideia.', 'Supervisora de pixels a postos.',
        'Meu relatório tem três cochilos.', 'Só falta organizar meus pensamentos.',
        'Este notebook cabe direitinho nas minhas patinhas.'),
    'sono': (
        'Só vou fechar os olhos um pouquinho…', 'Meus pensamentos já estão de pijama.',
        'Hora de recarregar as orelhas.', 'O travesseiro imaginário está pronto.',
        'Se eu roncar, foi o computador.', 'Sonhando com um brinquedo que volta sozinho.'),
    'ambiente': (
        'Tem bastante chão para explorar por aqui.', 'Vou conferir aquele cantinho.',
        'O mundo parece diferente daqui de baixo.', 'Esta borda dá uma ótima vista.',
        'Será que cabe uma soneca ali?', 'Estou de guarda contra pixels entediados.',
        'Tudo tranquilo no meu pedacinho de tela.', 'Nenhum cantinho vai ficar sem uma visita.'),
    'casual': (
        'Oi. Só passei para ficar pertinho.', 'Minha agenda está livre para uma brincadeira.',
        'Hoje acordei redondinha.', 'Que bom dividir esse cantinho com você.',
        'Estou aqui se precisar de companhia.', 'Aceito carinho em horário comercial e fora dele.',
        'Minhas orelhas estão captando boas ideias.', 'Vou dar uma voltinha, já volto.'),
    'pensamento': (
        'Se eu sou redonda, onde começa meu abraço?', 'Será que o cursor também se cansa?',
        'Quantos cochilos cabem em um dia?', 'Uma bolha sonha com outras bolhas?',
        'E se eu guardar um pedacinho de silêncio?', 'Preciso inventar um bolso para meu brinquedo.',
        'Será que minhas orelhas parecem duas montanhas?', 'Acho que esqueci o que eu ia pensar.'),
    'curioso': (
        'O que será que tem por ali?', 'Minhas orelhas ouviram uma ideia.',
        'Vou olhar bem de pertinho.', 'Tem alguma brincadeira escondida aqui?',
        'Estou investigando um assunto muito redondo.', 'Já volto com uma descoberta.'),
    'triste': (
        'Posso ficar aqui do seu lado?', 'Hoje minhas orelhas estão quietinhas.',
        'Um carinho talvez ajude.', 'Vou juntar meus pedacinhos de coragem.',
        'Às vezes eu também preciso de uma pausa.', 'Sua companhia já deixa tudo mais leve.'),
}
THOUGHTS = frozenset(('pensamento', 'sono', 'curioso', 'triste', 'ambiente'))
SPEECH_INTERVAL = 45.
AMBIENT_MIN_INTERVAL = 300.
COMPACT_TEXT_PADDING = (11, 8, 12)
BUBBLE_TEXT_FLAGS = Qt.AlignCenter | Qt.TextWordWrap


def bubble_path(rect, thought=False, anchor=None, tail_top=False, *, compact=False):
    """Silhueta comum a falas e bilhetes; a ponta permanece dentro da janela."""
    tail_space = 12 if compact else 16
    r = QRectF(rect).adjusted(2, 2, -2, -tail_space)
    path = QPainterPath()
    radius = 10 if compact else 15
    path.addRoundedRect(r, radius, radius)
    anchor_margin = 14 if compact else 20
    x = max(r.left()+anchor_margin, min(r.right()-anchor_margin, anchor if anchor is not None else r.center().x()))
    scale = .7 if compact else 1.
    if thought:
        path.addEllipse(QPointF(x, r.bottom()+5*scale), 4*scale, 3*scale)
        path.addEllipse(QPointF(x-3*scale, r.bottom()+11*scale), 2*scale, 2*scale)
    else:
        tail = QPainterPath(QPointF(x-9*scale, r.bottom()-1))
        tail.quadTo(x-5*scale, r.bottom()+7*scale, x-2*scale, r.bottom()+13*scale)
        tail.quadTo(x+3*scale, r.bottom()+5*scale, x+10*scale, r.bottom()-1)
        tail.closeSubpath()
        path = path.united(tail)
    if tail_top:
        path = QTransform().translate(0, rect.top()+rect.bottom()).scale(1, -1).map(path)
    return path


def paint_bubble(painter, rect, text, thought=False, anchor=None, opacity=1., tail_top=False, *, compact=False):
    painter.save()
    painter.setOpacity(painter.opacity()*max(0., min(1., opacity)))
    painter.setPen(QPen(QColor('#9383af' if compact else '#b4a0d8'), 1. if compact else 1.3))
    painter.setBrush(QColor(37, 33, 47, 224 if compact else 255))
    painter.drawPath(bubble_path(rect, thought, anchor, tail_top, compact=compact))
    painter.setPen(QColor('#fff1c7'))
    font = QFont('Segoe UI', 10)
    painter.setFont(font)
    pad_x, pad_y, tail = COMPACT_TEXT_PADDING if compact else (14, 10, 14)
    text_rect = QRectF(rect).adjusted(pad_x, pad_y + (tail if tail_top else 0),
                                    -pad_x, -pad_y - (0 if tail_top else tail))
    painter.drawText(text_rect, BUBBLE_TEXT_FLAGS, text)
    painter.restore()


class Dialogue:
    """A apresentação observa transições reais; a escolha usa a política do cérebro."""
    def __init__(self):
        self.recent = deque(maxlen=18)
        self.last_category = None
        self.next_reaction = 0.
        self.next_ambient = None
        self.previous = None

    def choose(self, game, category):
        options = [line for line in LINES[category] if line not in self.recent]
        if not options:
            options = [line for line in LINES[category] if line != (self.recent[-1] if self.recent else None)]
        text = game.intelligence.choose('dialogue:'+category, options, rates=game.rates,
                                        emotion=game.state.emotion, energy=game.drives.energy,
                                        contact=game.drives.contact, source='local_dialogue_policy')
        if text not in options:
            return None
        self.recent.append(text)
        self.last_category = category
        return text

    def update(self, game, now):
        state = game.state
        category = ('segurando' if game.body.held else 'carinho' if state.caressing(now) else
                    'sono' if game.sleep.asleep else 'trabalho' if state.at_desk else
                    'brincando' if game.play_reaction.get('until', 0.) > now or game.pingpong is not None else
                    state.emotion if state.emotion in ('bravo', 'curioso', 'triste') else None)
        previous, self.previous = self.previous, category
        if not game.pet_visible(now) or game.panel or now < game.quiet_until:
            return None
        ambient_interval = max(AMBIENT_MIN_INTERVAL, game.prefs.get('mischiefInterval', 300))
        if self.next_ambient is None:
            self.next_ambient = now + ambient_interval
        if now < self.next_reaction:
            return None
        if category != previous and category is not None:
            self.next_ambient = now + ambient_interval
        elif now >= self.next_ambient and game.prefs.get('mischiefEnabled', True) and not game.sleep.asleep:
            self.next_ambient = now + ambient_interval
            # O cérebro pode preferir silêncio; nenhum sorteio independente decide agir.
            options = [key for key in ('ambiente', 'casual', 'pensamento') if key != self.last_category]
            category = game.intelligence.choose('dialogue_intent', options+['silencio'], rates=game.rates,
                                                emotion=state.emotion, energy=game.drives.energy,
                                                contact=game.drives.contact,
                                                weights={'silencio': max(0., .3-game.drives.energy)}, source='local_dialogue_policy')
            if category not in options:
                return None
        else:
            return None
        text = self.choose(game, category)
        if text:
            self.next_reaction = now + SPEECH_INTERVAL
        return (text, category in THOUGHTS) if text else None


class SpeechWindow(QWidget):
    def __init__(self, game):
        super().__init__(None, FLAGS | Qt.WindowTransparentForInput)
        self.game = game
        self.dialogue = Dialogue()
        self.text = ''
        self.thought = False
        self.started = self.until = 0.
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setWindowTitle('Bolha · pensamento')
        self.setAccessibleName('Fala da Bolha')

    def present(self, text, thought=False, now=None):
        self.text, self.thought = str(text), bool(thought)
        self.started = time.monotonic() if now is None else now
        self.until = self.started + max(2.6, min(5., 1.7 + len(self.text)/18.))
        self.setAccessibleDescription(self.text)

    def sync(self, now=None):
        now = time.monotonic() if now is None else now
        game = self.game
        if not game.pet_visible(now) or game.panel or now < game.quiet_until:
            self.until = 0.
            self.hide()
            self.dialogue.previous = None
            self.dialogue.next_ambient = None
            return
        result = self.dialogue.update(game, now)
        if result:
            self.present(*result, now=now)
        if not self.text or now >= self.until:
            self.hide()
            return
        left, top, right, bottom = game.bounds((game.body.x, game.body.y))
        metrics = QFontMetricsF(QFont('Segoe UI', 10), self)
        pad_x, pad_y, tail = COMPACT_TEXT_PADDING
        width = min(212, int(right-left-16), max(46, math.ceil(metrics.horizontalAdvance(self.text))+2*pad_x+2))
        if width < 46:
            self.hide()
            return
        text_bounds = metrics.boundingRect(QRectF(0., 0., width-2*pad_x, 0.), BUBBLE_TEXT_FLAGS, self.text)
        height = math.ceil(text_bounds.height()) + 2*pad_y + tail + 3
        if height > bottom-top-16:
            self.hide()
            return
        self.resize(width, height)
        x = max(left+8, min(right-width-8, game.body.x-width/2))
        self.anchor = game.body.x-x
        target_y = game.body.y-game.body.half_h-height-8
        toy = game.ball.body
        covers_toy = game.ball.isVisible() and (
            x-toy.half_w < toy.x < x+width+toy.half_w
            and target_y-toy.half_h < toy.y < target_y+height+toy.half_h)
        below_y = game.body.y+game.body.half_h+8
        self.tail_top = target_y < top+8 or (covers_toy and below_y+height <= bottom-8)
        if self.tail_top:
            target_y = below_y
        self.alpha = min(1., max(0., (now-self.started)/.22), max(0., (self.until-now)/.30))
        eased = 1.-(1.-self.alpha)**3
        y = max(top+8, min(bottom-height-8, target_y+(1.-eased)*6))
        self.move(round(x), round(y))
        self.show()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        paint_bubble(p, QRectF(self.rect()), self.text, self.thought, self.anchor, self.alpha, self.tail_top, compact=True)
        p.end()
