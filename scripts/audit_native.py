# SPDX-License-Identifier: GPL-3.0-only
"""Rejeita artefatos web/worker e dependências Qt fora do runtime Core/Gui/Widgets."""
import argparse
from pathlib import Path

FORBIDDEN=('electron','app.asar','chrome_','chromium','ffmpeg','node.exe','node_modules',
           'qtuiotouchplugin','qtwebengine','qt6webengine','qt6qml','qt6quick','qt6network','brain.exe','worker.py')


def audit(root):
    root=Path(root)
    if not (root/'Bolha.exe').is_file():raise ValueError('Bolha.exe ausente.')
    for item in root.rglob('*'):
        if item.is_symlink():raise ValueError('Atalho inesperado: '+str(item))
        if any(token in item.name.lower() for token in FORBIDDEN):
            raise ValueError('Componente removido ainda presente: '+str(item))
        if item.is_file() and item.suffix.lower() in ('.js','.jsx','.ts','.tsx','.html','.css'):
            raise ValueError('Camada web inesperada: '+str(item))
    internal=root/'_internal'
    for required in ('bolha-version.json','THIRD-PARTY-NOTICES.txt','licenses/LICENSE','licenses/PYTHON-LICENSE.txt'):
        if not (internal/required).is_file():raise ValueError('Recurso obrigatório ausente: '+required)
    print('Pacote nativo auditado:',root)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');audit(parser.parse_args().directory)
