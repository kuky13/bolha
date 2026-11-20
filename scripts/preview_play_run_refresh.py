# SPDX-License-Identifier: GPL-3.0-or-later
"""Cenas dirigidas de corrida/brincadeira nas janelas Qt reais, sem perfil do usuário."""
import math
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'brain')]
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import QApplication
from bolha.pet import PetWindow
from bolha.scene import ObjectWindow
from game import Game


SCENES = (
    ('corrida-direita', 'Correndo para a direita'),
    ('corrida-esquerda', 'Correndo para a esquerda'),
    ('perseguindo', 'Perseguindo o brinquedo'),
    ('brincando', 'Esperar, perseguir, rebater e relaxar'),
    ('parando', 'Desacelerar e fechar o sorriso com calma'),
)


def render(output):
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    width, height, floor, fps, count = 820, 370, 310, 30, 90
    highlights = []
    for name, title in SCENES:
        frames = output/name
        frames.mkdir(exist_ok=True)
        with TemporaryDirectory() as profile, patch('time.monotonic', return_value=100.) as clock:
            game = Game(profile, ROOT/'assets/bolha/content')
            game.configure(dict(avatarSize=164, mischiefEnabled=False, onlineReactions=False,
                senseWindows=False, senseApp=False, senseIdle=False, senseCursor=False,
                roaming=False, adaptiveBehavior=False, notebookEnabled=False))
            game.desktop(dict(areas=[dict(x=0.,y=80.,width=width,height=floor-80.)]))
            body, toy = game.body, game.ball.body
            body.x, body.y = (650. if name=='corrida-esquerda' else 145.), floor-body.half_h
            body.angle = body.vx = body.vy = body.omega = 0.
            body.grounded = True
            body.surface = floor
            game.state.emotion = 'observando'
            game.state.tone.r['ANGRY'] = 0.
            game.choose_expression = lambda *args: None
            game.ball_stored = name in ('corrida-direita','corrida-esquerda','parando')
            game.ball.setVisible(not game.ball_stored)
            pet = PetWindow(game)
            toy_window = ObjectWindow(SimpleNamespace(game=game), game.ball)
            best = None
            try:
                for frame in range(count):
                    t = frame/fps
                    now = 100.+t
                    clock.return_value = now
                    body.vx = -170. if name=='corrida-esquerda' else 170.
                    game.play_reaction = {}
                    if name=='perseguindo':
                        game.play_reaction = dict(kind='brinquedo_perseguindo',started=now,until=now+.1,intensity=.9)
                    elif name=='brincando':
                        body.vx = 0.
                        if t < .4:
                            kind, started = 'brinquedo_esperando', 100.
                        elif t < 1.9:
                            kind, started = 'brinquedo_perseguindo', 100.4
                            body.vx = 240.
                        elif t < 2.32:
                            kind, started = 'brinquedo_rebatida', 101.9
                        else:
                            kind, started = 'brinquedo_esperando', 102.32
                        game.play_reaction = dict(kind=kind,started=started,until=now+.1,
                                                 intensity=.9,heading=-24.)
                    elif name=='parando':
                        body.vx = 220.*max(0.,min(1.,(1.65-t)/.65))
                    if frame:body.x += body.vx/fps
                    toy.x = body.x+136.
                    toy.y = floor-toy.half_h-max(0.,math.sin(t*6.))*85.
                    game.ball.roll_angle = t*140.
                    game.ball.place()
                    pet.sync()
                    toy_window.sync()
                    pose = pet.motion.pose
                    assert 0. <= pose['mouth_open'] < .8 and 0. <= pose['eye_open'] <= 1.3
                    image = QImage(width,height,QImage.Format_ARGB32_Premultiplied)
                    image.fill(QColor('#191722'))
                    painter = QPainter(image)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.fillRect(0,floor,width,height-floor,QColor('#292235'))
                    painter.setPen(QColor('#ffe1a1'))
                    painter.setFont(QFont('DejaVu Sans',16,QFont.DemiBold))
                    painter.drawText(QRectF(24,12,width-48,34),Qt.AlignVCenter,title)
                    painter.setFont(QFont('DejaVu Sans',10))
                    painter.setPen(QColor('#cbbdda'))
                    painter.drawText(24,65,'Prévia dirigida do aplicativo · desenho Qt real · sem alterar seu aprendizado')
                    painter.drawPixmap(pet.visual.pos(),pet.visual.grab())
                    if toy_window.isVisible():painter.drawPixmap(toy_window.pos(),toy_window.grab())
                    painter.end()
                    assert image.save(str(frames/f'{frame:03}.png'))
                    if best is None or pose['mouth_open'] > best[0]:
                        best = pose['mouth_open'], image.copy()
                    if name=='parando' and frame==70:best = 1.,image.copy()
                assert best is not None and not best[1].isNull()
                assert best[1].save(str(output/f'{name}.png'))
                highlights.append(best[1])
            finally:
                toy_window.close()
                pet.close()
            subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(fps),
                '-i',str(frames/'%03d.png'),'-filter_complex_threads','1','-vf',
                'split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3',
                '-loop','0',str(output/f'{name}.gif')],check=True)
    sheet = QImage(width*2,height*3,QImage.Format_ARGB32_Premultiplied)
    sheet.fill(QColor('#191722'))
    painter = QPainter(sheet)
    for index, image in enumerate(highlights):
        painter.drawImage(index%2*width,index//2*height,image)
    painter.end()
    assert sheet.save(str(output/'prancha-corrida-brincadeira.png'))


if __name__ == '__main__':
    render(Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/bolha-native-previews/play-run'))
