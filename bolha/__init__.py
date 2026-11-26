# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Bolha nativa: versão do código e versão do pacote instalado."""
import json
from pathlib import Path
import sys
from .versioning import version_tuple

VERSION = '0.5.9.5'
if getattr(sys, 'frozen', False):
    value = json.loads((Path(sys._MEIPASS) / 'bolha-version.json').read_text(encoding='utf-8'))
    try:
        VERSION = value['version']
        version_tuple(VERSION)
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError('Versão do pacote Bolha inválida.') from error
