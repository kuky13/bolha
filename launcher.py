# SPDX-License-Identifier: GPL-3.0-only
"""Ponto de entrada usado pelo PyInstaller; execução pelo código: python -m bolha."""
from bolha.__main__ import main

if __name__=='__main__':
    raise SystemExit(main())
