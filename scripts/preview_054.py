# SPDX-License-Identifier: GPL-3.0-or-later
"""Cenas dirigidas das janelas Qt reais; não substituem testes no Windows."""
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'brain')]
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import QApplication
from bolha.pet import PetWindow
from bolha.scene import NativeScene
from game import Game


def render(output):
    output.mkdir(parents=True, exist_ok=True)
    frames = output/'frames'
    frames.mkdir(exist_ok=True)
    app = QApplication.instance() or QApplication([])
    images = []
    width, height, floor = 720, 430, 382
    for index, scenario in enumerate(('texto', 'revolucao', 'segurar', 'mastigar')):
        with TemporaryDirectory() as profile, patch('time.monotonic', return_value=100.) as clock:
            game = Game(profile, ROOT/'assets/bolha/content')
            game.configure(dict(avatarSize=64 if scenario=='texto' else 110,
                mischiefEnabled=False, onlineReactions=False, senseWindows=False,
                senseApp=False, senseIdle=False, senseCursor=True, roaming=False,
                cursorPrankEnabled=True, notebookEnabled=False))
            game.desktop(dict(areas=[dict(x=0., y=72., width=width, height=floor-72)]))
            game.body.x, game.body.y = 360., floor-game.body.half_h
            game.body.grounded = True
            game.body.surface = floor
            game.ball_stored = True
            game.ball.hide()
            game.last_think = game.last_save = game.last_native = 1000.
            game.cursor = (560., 280.)
            if scenario in ('texto', 'revolucao'):
                game.protest.stage = 4 if scenario=='revolucao' else 2
                game.protest.grievance = 1.25
                game.protest.respawn_at = 100.
                game.protest_ctl.carry(100., False)
                if scenario=='texto':
                    game.body.x, game.body.y = width-43., floor-game.body.half_h
                    game.protest.sign.text = 'OLHA A BOLINHA QUE ACHEI'
                game.state.emotion = 'bravo' if scenario=='revolucao' else 'contente'
                game.state.tone.r['ANGRY'] = .85 if scenario=='revolucao' else .05
                game.revolucao.policy.event = lambda *args, **kwargs: True
            elif scenario=='segurar':
                game.interact(dict(type='hold-start'), now=100.)
                game.body.y = 230.
            else:
                game.cursor_prank.angry_attempt = True
                game.cursor_prank.phase = 'chew'
                game.cursor_prank.started = 100.
                game.cursor_prank.anchor = game.cursor
                game.state.tone.r['ANGRY'] = .7
            pet = PetWindow(game)
            scene = NativeScene(game)
            try:
                for frame in range(150):
                    now = 100.+frame/30.
                    clock.return_value = now
                    if scenario=='segurar' and frame==110:
                        game.interact(dict(type='drag-end', x=360., y=230., vx=280., vy=-100.), now=now)
                    if scenario=='segurar':
                        # A cena mantém o mesmo estímulo para observar só a continuidade visual.
                        game.state.tone.r['ANGRY'] = min(.9, max(0., (frame-20)/95.))
                    if scenario=='mastigar' and frame==100:
                        game.cursor_prank.phase = 'chew'
                        game.cursor_prank.started = now
                    game.tick(1/30., now)
                    pet.sync()
                    scene.sync()
                    image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
                    image.fill(QColor('#191722'))
                    painter = QPainter(image)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.fillRect(0, floor, width, height-floor, QColor('#292235'))
                    painter.setPen(QColor('#ffe1a1'))
                    painter.setFont(QFont('DejaVu Sans', 15, QFont.DemiBold))
                    title = {'texto': 'Texto inteiro com a Bolha pequena no canto',
                             'revolucao': 'Revolução: placa e até 6 projéteis',
                             'segurar': 'Irritação gradual ao segurar e soltar',
                             'mastigar': 'Duas mastigadas leves e devolução do ponteiro'}[scenario]
                    painter.drawText(QRectF(20, 12, width-40, 35), Qt.AlignVCenter, title)
                    painter.setFont(QFont('DejaVu Sans', 10))
                    painter.setPen(QColor('#cbbdda'))
                    painter.drawText(20, 63, 'Cena dirigida com o renderizador Qt do aplicativo · GPL')
                    painter.drawPixmap(pet.visual.pos(), pet.visual.grab())
                    for window in scene.windows.values():
                        if window.isVisible():
                            painter.drawPixmap(window.pos(), window.grab())
                    if scene.speech.isVisible():
                        painter.drawPixmap(scene.speech.pos(), scene.speech.grab())
                    painter.end()
                    image.save(str(frames/f'{index*150+frame:04}.png'))
                    if frame == (109 if scenario=='segurar' else 18 if scenario=='mastigar' else 100):
                        image.save(str(output/f'{scenario}.png'))
                        images.append(image)
            finally:
                scene.close()
                pet.close()
    sheet = QImage(width*2, height*2, QImage.Format_ARGB32_Premultiplied)
    painter = QPainter(sheet)
    for index, image in enumerate(images):
        painter.drawImage((index % 2)*width, (index//2)*height, image)
    painter.end()
    sheet.save(str(output/'previas.png'))


if __name__ == '__main__':
    render(Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/bolha-054-previas'))
