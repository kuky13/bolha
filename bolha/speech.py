# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Falas locais escolhidas pela política neural, sem ler conteúdo do desktop."""
import time
from collections import deque

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QTransform
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


def bubble_path(rect, thought=False, anchor=None, tail_top=False):
    """Silhueta comum a falas e bilhetes; a ponta permanece dentro da janela."""
    r = QRectF(rect).adjusted(2, 2, -2, -16)
    path = QPainterPath()
    path.addRoundedRect(r, 15, 15)
    x = max(r.left()+20, min(r.right()-20, anchor if anchor is not None else r.center().x()))
    if thought:
        path.addEllipse(QPointF(x, r.bottom()+5), 4, 3)
        path.addEllipse(QPointF(x-3, r.bottom()+11), 2, 2)
    else:
        tail = QPainterPath(QPointF(x-9, r.bottom()-1))
        tail.quadTo(x-5, r.bottom()+7, x-2, r.bottom()+13)
        tail.quadTo(x+3, r.bottom()+5, x+10, r.bottom()-1)
        tail.closeSubpath()
        path = path.united(tail)
    if tail_top:
        path = QTransform().translate(0, rect.top()+rect.bottom()).scale(1, -1).map(path)
    return path


def paint_bubble(painter, rect, text, thought=False, anchor=None, opacity=1., tail_top=False):
    painter.save()
    painter.setOpacity(painter.opacity()*max(0., min(1., opacity)))
    painter.setPen(QPen(QColor('#b4a0d8'), 1.3))
    painter.setBrush(QColor('#25212f'))
    painter.drawPath(bubble_path(rect, thought, anchor, tail_top))
    painter.setPen(QColor('#fff1c7'))
    font = QFont('Segoe UI', 10)
    painter.setFont(font)
    painter.drawText(QRectF(rect).adjusted(14, 24 if tail_top else 10, -14, -10 if tail_top else -24), Qt.AlignCenter | Qt.TextWordWrap, text)
    painter.restore()


class Dialogue:
    """A apresentação observa transições reais; a escolha usa a política do cérebro."""
    def __init__(self):
        self.recent = deque(maxlen=18)
        self.last_category = None
        self.next_reaction = 0.
        self.next_ambient = 0.
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
        if category != previous and category is not None and now >= self.next_reaction:
            self.next_reaction = now+9.
            self.next_ambient = now+game.prefs.get('mischiefInterval', 300)
        elif now >= self.next_ambient and game.prefs.get('mischiefEnabled', True) and not game.sleep.asleep:
            self.next_ambient = now+game.prefs.get('mischiefInterval', 300)
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
        self.until = self.started+max(4., min(7., 2.+len(self.text)/18.))
        self.setAccessibleDescription(self.text)

    def sync(self, now=None):
        now = time.monotonic() if now is None else now
        game = self.game
        if not game.pet_visible(now) or game.panel or now < game.quiet_until:
            self.until = 0.
            self.hide()
            self.dialogue.previous = None
            self.dialogue.next_ambient = now+game.prefs.get('mischiefInterval', 300)
            return
        result = self.dialogue.update(game, now)
        if result:
            self.present(*result, now=now)
        if not self.text or now >= self.until:
            self.hide()
            return
        left, top, right, bottom = game.bounds((game.body.x, game.body.y))
        width = max(80, min(270, int(right-left-16)))
        metrics = QFontMetrics(QFont('Segoe UI', 10))
        text_height = metrics.boundingRect(0, 0, width-28, 200, Qt.TextWordWrap, self.text).height()
        height = max(66, text_height+36)
        self.resize(width, height)
        self.anchor = max(22., min(width-22., game.body.x-max(left+8, min(right-width-8, game.body.x-width/2))))
        x = max(left+8, min(right-width-8, game.body.x-width/2))
        target_y = game.body.y-game.body.half_h-height-10
        self.tail_top = target_y < top+8
        if self.tail_top:
            target_y = game.body.y+game.body.half_h+10
        self.alpha = min(1., max(0., (now-self.started)/.22), max(0., (self.until-now)/.30))
        eased = 1.-(1.-self.alpha)**3
        y = max(top+8, min(bottom-height-8, target_y+(1.-eased)*6))
        self.move(round(x), round(y))
        self.show()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        paint_bubble(p, QRectF(self.rect()), self.text, self.thought, self.anchor, self.alpha, self.tail_top)
        p.end()
