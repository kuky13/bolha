# SPDX-License-Identifier: GPL-3.0-only
"""Empacota o cérebro original sem exigir Python na máquina do usuário."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir',
           '--name', 'BolhaBrain', '--distpath', str(root / 'brain-dist'),
           '--workpath', str(root / 'brain-build/work'), '--specpath', str(root / 'brain-build'),
           '--paths', str(root / 'brain'), '--collect-all', 'numpy']
if sys.platform == 'win32':
    command.extend(['--hidden-import', 'win32timezone'])
command.append(str(root / 'brain/worker.py'))
subprocess.run(command, cwd=root, check=True)
