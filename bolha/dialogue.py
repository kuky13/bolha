# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Política de falas compartilhada entre interfaces nativas."""
from collections import deque

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


