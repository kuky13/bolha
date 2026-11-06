# SPDX-License-Identifier: GPL-3.0-only
"""Rejeita artefatos web/worker e dependências Qt fora do runtime Core/Gui/Widgets."""
import argparse
import json
from pathlib import Path

FORBIDDEN=('electron','app.asar','chrome_','chromium','ffmpeg','node.exe','node_modules',
           'qtuiotouchplugin','qtwebengine','qt6webengine','qt6qml','qt6quick','qt6network','brain.exe','worker.py')
REQUIRED=('bolha-version.json','THIRD-PARTY-NOTICES.txt','licenses/LICENSE','licenses/PYTHON-LICENSE.txt',
          'PySide6/plugins/imageformats/qgif.dll')


def audit(root, output_json=None):
    root=Path(root)
    if not (root/'Bolha.exe').is_file():raise ValueError('Bolha.exe ausente.')
    for item in root.rglob('*'):
        if item.is_symlink():raise ValueError('Atalho inesperado: '+str(item))
        if any(token in item.name.lower() for token in FORBIDDEN):
            raise ValueError('Componente removido ainda presente: '+str(item))
        if item.is_file() and item.suffix.lower() in ('.js','.jsx','.ts','.tsx','.html','.css'):
            raise ValueError('Camada web inesperada: '+str(item))
    internal=root/'_internal'
    for required in REQUIRED:
        if not (internal/required).is_file():raise ValueError('Recurso obrigatório ausente: '+required)
    report=dict(root=str(root),executable='Bolha.exe',gifDecoder='PySide6/plugins/imageformats/qgif.dll',gifDecoderPresent=True)
    if output_json:
        target=Path(output_json);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Pacote nativo auditado:',json.dumps(report,ensure_ascii=False))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--output-json')
    args=parser.parse_args();audit(args.directory,args.output_json)
