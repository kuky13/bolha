# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Relógio visual compartilhado pela expressão e pelo notebook."""
from bisect import bisect_right
import math

TYPING_SECONDS = 3.6

KEYS = (0, 2, 4, 6, 11, 13, 15, 17)

def typing_frame(now):
    """Oito teclas em dois grupos, com uma pausa para conferir a tela."""
    part = (now % TYPING_SECONDS) * 10
    beat = int(part)
    progress = bisect_right(KEYS, beat)
    if beat not in KEYS:
        return -1, 0., progress
    return progress - 1, math.sin(math.pi * (part - beat)), progress
