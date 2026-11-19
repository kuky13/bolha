# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Ensaios no jogo real, com cópia descartável do perfil e nenhuma gravação real."""
import copy
from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile
import time


@dataclass(frozen=True)
class ActivityTest:
    key: str
    title: str
    steps: tuple
    preferences: tuple = ()
    sensors: tuple = ()


ACTIVITY_TESTS = (
    ActivityTest('caress', 'Carinho', ('Passe o mouse devagar sobre a Bolha ou faça carinho pelo menu.', 'Observe os corações e o relaxamento do rosto.')),
    ActivityTest('hold', 'Segurar e soltar', ('Clique e mantenha pressionado sobre a Bolha por alguns segundos.', 'Continue segurando: a irritação deve crescer gradualmente.', 'Solte o botão. A expressão deve acompanhar a queda sem mudar de repente.')),
    ActivityTest('throw', 'Arremesso e recuperação', ('Pegue a Bolha, mova o mouse e solte em movimento.', 'Veja o quique e a irritação após o pouso.', 'Faça carinho e veja a recuperação gradual.')),
    ActivityTest('sleep', 'Sono e despertar', ('Observe os olhos fechando, a respiração e os zzz.', 'A Bolha acorda sem deixar efeitos do sono.')),
    ActivityTest('toy', 'Brinquedo e ponteiro', ('Aproxime o mouse do brinquedo e empurre-o.', 'Pegue e solte o brinquedo em movimento; veja os quiques nas bordas.'), sensors=('senseCursor',)),
    ActivityTest('chase', 'Correr atrás do brinquedo', ('O brinquedo está perto. Mova-o e veja a Bolha decidir como brincar.', 'Leve o brinquedo para o outro lado e confira a direção da corrida.'), ('chaseEnabled', 'roaming'), ('senseCursor',)),
    ActivityTest('juggle', 'Embaixadinhas', ('O pedido de embaixadinhas foi enviado ao cérebro.', 'Veja o fim da contagem e a volta à brincadeira.'), ('juggleEnabled',)),
    ActivityTest('pingpong', 'Pingue-pongue', ('Mova o mouse para controlar a raquete na área de trabalho.', 'A partida termina e os objetos voltam ao lugar.'), ('pingpongEnabled',), ('senseCursor',)),
    ActivityTest('notebook', 'Notebook', ('Veja o notebook perto da Bolha.', 'O cérebro recebeu um pedido para trabalhar; a resposta depende do humor.', 'O notebook é guardado.'), ('notebookEnabled',)),
    ActivityTest('protest', 'Protesto e perdão', ('A cópia da Bolha recebeu um estímulo de irritação; observe o protesto.', 'Faça carinho para ajudar o cérebro a recuperar a calma.'), ('protestsEnabled',)),
    ActivityTest('sign', 'Cartaz', ('Veja a placa junto do corpo, inclusive ao girar ou arrastar a Bolha.', 'O cartaz é retirado sem deixar objetos na tela.'), ('protestsEnabled', 'signsEnabled')),
    ActivityTest('revolution', 'Revolução das Bolhas', ('Observe a placa e os lançamentos decididos pelo cérebro. Há no máximo seis brinquedos.', 'O brinquedo da cópia foi trocado; observe os próximos lançamentos usarem o tipo oposto.', 'A revolução termina e os projéteis são limpos.'), ('protestsEnabled', 'revolutionEnabled')),
    ActivityTest('fireworks', 'Comemoração e fogos', ('O cérebro recebeu um pedido para comemorar.', 'Observe os fogos terminando sem novos disparos em sequência.'), ('fireworksEnabled',)),
    ActivityTest('speech', 'Falas e pensamentos', ('Faça carinho para provocar uma fala; confira se todo o texto cabe no balão.', 'Leve a Bolha para um canto e repita a interação.'), ('speechEnabled',)),
    ActivityTest('note', 'Bilhete com prazo', ('Veja o bilhete próximo da Bolha, sem cortar o texto.', 'Espere alguns segundos: o bilhete deve desaparecer sozinho.'), ('mischiefEnabled', 'notesEnabled')),
    ActivityTest('gif', 'Meme ou GIF online', ('A consulta usa somente o humor. Aguarde a resposta da rede.', 'Veja o GIF sumir; clique com o botão direito para consultar sua origem.'), ('mischiefEnabled', 'onlineReactions')),
    ActivityTest('pop', 'Estouro e volta pelo canto', ('A cópia atingiu o limite de arremessos. Observe o estouro.', 'Espere 30 segundos para ver a volta tímida pelo canto.', 'Faça carinho para ajudar a Bolha a se soltar.'), ('popEnabled',)),
    ActivityTest('cursor', 'Mastigar e devolver o ponteiro', ('Deixe o mouse próximo da Bolha. O cérebro recebeu um estímulo de irritação.', 'Quando o ponteiro for pego, confira as duas mastigadas e a devolução. Mover ou clicar deve devolver imediatamente.'), ('cursorPrankEnabled', 'adaptiveBehavior'), ('senseCursor',)),
)
TESTS_BY_KEY = {item.key: item for item in ACTIVITY_TESTS}


class ActivityTestSession:
    """O controlador pausa o jogo original e liga suas janelas a ``game`` até stop()."""
    def __init__(self, live_game):
        from game import Game
        from pestinha import scene, store
        if getattr(scene._current, 'is_activity_test', False):
            raise RuntimeError('Já há um teste em andamento. Pare-o antes de iniciar outro.')
        self.live_game = live_game
        self.game = None
        self.current = None
        self.step = -1
        self.closed = False
        self._dispatcher = store._dispatcher
        self._temporary = tempfile.TemporaryDirectory(prefix='bolha-funcao-')
        self.root = Path(self._temporary.name)
        try:
            # Não seguir atalhos de pasta: o ensaio só precisa dos dados deste perfil.
            if any(path.is_symlink() for path in live_game.data_dir.rglob('*')):
                raise OSError('O perfil contém um vínculo de arquivo. O teste foi cancelado para preservá-lo.')
            shutil.copytree(live_game.data_dir, self.root/'brain', dirs_exist_ok=True)
            store.set_dispatcher(self._discard_test_write)
            self.game = Game(self.root/'brain', live_game.conteudo.proprio)
            self.game.is_activity_test = True
            self.game.configure(copy.deepcopy(live_game.prefs))
            for name in ('areas', 'monitors', 'displays', 'blocked'):
                setattr(self.game, name, copy.deepcopy(getattr(live_game, name)))
            self.game.body.x, self.game.body.y = live_game.body.x, live_game.body.y
            self.game.cursor = tuple(live_game.cursor)
            self.game.fit(self.game.body)
            self.game.hidden = self.game.panicked = self.game.panel = False
            self.game.quiet_until = 0.
        except Exception:
            store.set_dispatcher(self._dispatcher)
            scene.set_scene(live_game)
            self._temporary.cleanup()
            raise

    def _discard_test_write(self, path, text, append=False):
        # A cópia aprende em RAM. Nada entra na fila assíncrona do perfil real.
        if not Path(path).resolve().is_relative_to(self.root.resolve()):
            raise OSError('Gravação fora do perfil de teste recusada.')

    @property
    def instruction(self):
        if self.closed:
            return 'Teste encerrado. A memória original foi preservada.'
        if self.current is None:
            return 'Execute uma função por vez.'
        return self.current.steps[self.step]

    @property
    def has_next(self):
        return self.current is not None and self.step+1 < len(self.current.steps)

    def reason(self, key):
        test = TESTS_BY_KEY[key]
        if not self.live_game.visible():
            return 'Mostre a Bolha e saia da pausa de emergência para testar.'
        from .preferences import ACTIVITY_SWITCHES
        names = {key: title for _, key, title in ACTIVITY_SWITCHES}
        names.update(mischiefEnabled='Memes e bilhetes', onlineReactions='GIFs online',
                     cursorPrankEnabled='Brincar de comer o ponteiro', adaptiveBehavior='Aprendizado adaptativo',
                     popEnabled='Estouro', roaming='Passear pela tela')
        for preference in test.preferences:
            if not self.game.prefs.get(preference, True):
                return 'Função desligada: '+names.get(preference, preference)+'. Ative-a antes do teste.'
        for sensor in test.sensors:
            if not self.game.prefs.get(sensor, True):
                return 'Este teste precisa da leitura do ponteiro, que está desligada.'
        return ''

    def run(self, key, now=None):
        if self.closed:
            raise RuntimeError('O teste já foi encerrado.')
        if self.current is not None:
            raise RuntimeError('Pare este teste antes de escolher outra função.')
        reason = self.reason(key)
        if reason:
            return reason
        self.current = TESTS_BY_KEY[key]
        self.step = 0
        self._perform(time.monotonic() if now is None else now)
        return self.instruction

    def next_step(self, now=None):
        if self.closed:
            raise RuntimeError('O teste já foi encerrado.')
        if not self.has_next:
            return self.instruction
        self.step += 1
        self._perform(time.monotonic() if now is None else now)
        return self.instruction

    def _perform(self, now):
        game, key, step = self.game, self.current.key, self.step
        def interact(kind, **data):
            return game.interact(dict(type=kind, **data), now=now)
        if key == 'sleep':
            interact('sleep' if step == 0 else 'wake')
        elif key == 'caress' and step == 0:
            interact('caress')
        elif key in ('toy', 'chase', 'juggle') and step == 0:
            if game.ball_stored:
                interact('ball')
            game.sleep.wake(startled=False)
            game.drives.energy = .85
            game.body.angle = 0.
            floor = game.bounds()[3]
            game.body.y = floor-game.body.half_h
            game.body.grounded = True
            game.body.surface = floor
            reach = game.body.half_w+game.ball.body.half_w+8.
            game.ball.body.x = game.body.x-reach if game.body.x > sum(game.bounds()[::2])/2 else game.body.x+reach
            game.ball.body.y = floor-game.ball.body.half_h
            game.ball.body.grounded = True
            game.ball.body.vx = game.ball.body.vy = 0.
            game.fit(game.ball.body)
            game.ball.place()
            if key != 'toy':
                interact('play', trick='juggle' if key == 'juggle' else 'kick')
        elif key == 'pingpong':
            interact('pingpong')
        elif key == 'notebook':
            if step == 0:
                if game.mesa.escondido:
                    interact('notebook')
                game.mesa.caderno.show()
            else:
                interact('work' if step == 1 else 'notebook')
        elif key in ('protest', 'sign', 'revolution'):
            if step == 0:
                game.protest.stage = 4 if key == 'revolution' else 2
                game.protest.grievance = game.prof.get('stage_up', [1, 2, 3, 4])[game.protest.stage-1]+.2
                game.protest.stage_since = now
                game.protest.respawn_at = now
                game.state.protest_stage = game.protest.stage
                game.state.emotion = 'bravo'
                game.senses.kick('TOY_TAKEN', 1.)
            elif key == 'revolution' and step == 1:
                game.configure({'toyAppearance': 'ball' if game.prefs.get('toyAppearance') == 'peanut' else 'peanut'})
            elif step == len(self.current.steps)-1:
                if key != 'protest':
                    game.protest.stage = game.protest.grievance = 0
                    if game.protest.sign:
                        game.protest.sign.deleteLater()
                        game.protest.sign = None
                    game.revolucao.fechar()
                interact('caress')
        elif key == 'fireworks' and step == 0:
            game.state.emotion = 'feliz'
            game.drives.energy = .85
            interact('celebrate')
        elif key == 'speech' and step == 0:
            interact('caress')
        elif key == 'note' and step == 0:
            note = game.mischief._make('bilhete', 'contente', False)
            if note:
                game.mischief.show_note(note, game.body, game.bounds(), game.cursor, now)
        elif key == 'gif' and step == 0:
            interact('reaction-now')
        elif key == 'pop':
            if step == 0:
                limit = game.prefs.get('popThrowLimit', 12)
                for _ in range(limit):
                    game._record_strong_throw(now)
            elif step == 2:
                interact('caress')
        elif key == 'cursor' and step == 0:
            game.state.emotion = 'bravo'
            game.state.tone.r['ANGRY'] = .95
            game.senses.kick('TOY_TAKEN', 1.)

    def stop(self):
        if self.closed:
            return
        from pestinha import scene, store
        self.closed = True
        try:
            if self.game:
                self.game.cursor_prank.cancel(self.game, time.monotonic())
                self.game._cancel_holds(time.monotonic())
                self.game.stop_pingpong()
                self.game.revolucao.fechar()
                for item in list(self.game.objects.values()):
                    item.deleteLater()
        finally:
            store.set_dispatcher(self._dispatcher)
            scene.set_scene(self.live_game)
            store.clear_protection_after_backup(self.root)
            self._temporary.cleanup()
