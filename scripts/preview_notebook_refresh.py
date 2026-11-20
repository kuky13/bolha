# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""PNG e GIF do renderer Qt real; somente prévias, sem iniciar o aplicativo."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'brain')]
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import QApplication
from bolha.objects import paint_notebook


def sheet(paint, title, phase=.05):
    image = QImage(900, 450, QImage.Format_ARGB32_Premultiplied)
    image.fill(QColor('#191722'))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor('#fff1c7'))
    painter.setFont(QFont('DejaVu Sans', 18, QFont.DemiBold))
    painter.drawText(30, 36, title)
    painter.setFont(QFont('DejaVu Sans', 10))
    painter.setPen(QColor('#cbbdda'))
    painter.drawText(30, 59, 'Desenho Qt do aplicativo · ampliado para conferir os detalhes')
    for index, working in enumerate((False, True)):
        left = index*450
        painter.drawText(QRectF(left, 70, 450, 24), Qt.AlignCenter,
                         'Trabalhando' if working else 'Repouso')
        paint(painter, QRectF(left+93, 98, 264, 192), working, phase)
        paint(painter, QRectF(left+73, 318, 132, 96), working, phase)
        paint(painter, QRectF(left+278, 335, 86, 62), working, phase)
        painter.drawText(QRectF(left+52, 417, 174, 24), Qt.AlignCenter, 'Tamanho 100%')
        painter.drawText(QRectF(left+250, 417, 144, 24), Qt.AlignCenter, 'Tamanho 65%')
    painter.end()
    return image


def save(image, path):
    if not image.save(str(path)):
        raise OSError(f'Não foi possível salvar {path}.')


def render(output, before_ref=None):
    app = QApplication.instance() or QApplication([])
    output.mkdir(parents=True, exist_ok=True)
    if before_ref:
        source = subprocess.run(['git', 'show', f'{before_ref}:bolha/objects.py'],
                                cwd=ROOT, check=True, capture_output=True, text=True).stdout
        before = ModuleType('bolha.notebook_before')
        before.__package__ = 'bolha'
        exec(compile(source, f'{before_ref}:bolha/objects.py', 'exec'), before.__dict__)
        save(sheet(before.paint_notebook, 'Antes · notebook'), output/'before.png')
    save(sheet(paint_notebook, 'Notebook · desenho atual'), output/'after.png')
    for name, working in (('idle', False), ('working', True)):
        for scale, width, height in (('100', 132, 96), ('65', 86, 62)):
            image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
            image.fill(Qt.transparent)
            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)
            paint_notebook(painter, QRectF(0, 0, width, height), working, .05)
            painter.end()
            save(image, output/f'after-{name}-{scale}.png')
    frames = output/'frames'
    frames.mkdir(exist_ok=True)
    for frame in range(72):
        save(sheet(paint_notebook, 'Notebook · ciclo de trabalho', frame/20),
             frames/f'{frame:03}.png')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                    '-framerate', '20', '-i', str(frames/'%03d.png'),
                    '-filter_complex',
                    '[0:v]split[a][b];[a]palettegen[p];[b][p]paletteuse=dither=none',
                    '-loop', '0', str(output/'notebook-working.gif')], check=True)
    if before_ref:print(output/'before.png')
    print(output/'after.png')
    print(output/'notebook-working.gif')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, nargs='?',
                        default=Path('/tmp/bolha-native-previews/notebook'))
    parser.add_argument('--before-ref', help='Commit ou tag para comparação opcional; requer Git.')
    args = parser.parse_args()
    render(args.output, args.before_ref)
