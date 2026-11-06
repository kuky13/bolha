# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Ponto de entrada usado pelo PyInstaller; execução pelo código: python -m bolha."""
from bolha.__main__ import main

if __name__=='__main__':
    raise SystemExit(main())
