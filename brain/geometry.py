# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Detecção por monitor usando apenas retângulos e estilo de janela."""
import math
def fullscreen_monitors(windows, displays):
    blocked = set()
    for index, display in enumerate(displays):
        scale = display.get('scaleFactor', 1)
        nx, ny = display.get('nativeX', display['x']), display.get('nativeY', display['y'])
        mx, my = display.get('monitorX', display['x']), display.get('monitorY', display['y'])
        full = (nx, ny, nx + display.get('monitorWidth', display['width'])*scale,
                ny + display.get('monitorHeight', display['height'])*scale)
        work = (nx + (display['x']-mx)*scale, ny + (display['y']-my)*scale,
                nx + (display['x']-mx+display['width'])*scale,
                ny + (display['y']-my+display['height'])*scale)
        def covers(rect, target):
            return rect[0] <= target[0]+1 and rect[1] <= target[1]+1 and rect[2] >= target[2]-1 and rect[3] >= target[3]-1
        for rect, maximized, framed in windows:
            if maximized and framed and covers(rect, work):
                break  # A normal maximized app in front hides a fullscreen app behind it.
            if covers(rect, full) and not (maximized and framed):
                blocked.add(index)
                break
    return blocked


def visible_window_platforms(windows, displays):
    """Bordas superiores visíveis, de pixels Win32 para cada monitor Qt.

    ``windows`` vem em ordem frontal: ``(hwnd, (l,t,r,b), maximizada)``.
    Cada ID identifica uma janela, monitor e trecho visível. O limite direito
    devolvido inclui CLOSE_BUTTONS porque Body/Behavior já o descontam; o
    recorte real dos botões é feito uma única vez na borda direita da janela.
    """
    from pestinha.core.physics import CLOSE_BUTTONS

    mappings = []
    for index, display in enumerate(displays):
        scale = display.get('scaleFactor', 1)
        if scale <= 0:
            continue
        mx, my = display.get('monitorX', display['x']), display.get('monitorY', display['y'])
        nx, ny = display.get('nativeX', display['x']), display.get('nativeY', display['y'])
        nr = nx + display.get('nativeWidth', display.get('monitorWidth', display['width']) * scale)
        nb = ny + display.get('nativeHeight', display.get('monitorHeight', display['height']) * scale)
        work = (max(nx, nx + (display['x'] - mx) * scale),
                max(ny, ny + (display['y'] - my) * scale),
                min(nr, nx + (display['x'] - mx + display['width']) * scale),
                min(nb, ny + (display['y'] - my + display['height']) * scale))
        mappings.append((str(display.get('id', index)), scale, mx, my, nx, ny, nr, nb, work))

    platforms, foreground = [], []
    for hwnd, rect, maximized in windows:
        left, top, right, bottom = rect
        if right <= left or bottom <= top:
            continue
        if not maximized:
            # O canto inferior pode pertencer a outra tela: só o topo determina
            # a conversão. Os botões físicos usam a escala da sua própria tela.
            right_scale = next((m[1] for m in mappings if m[4] < right <= m[6] and m[5] <= top < m[7]), 1.)
            usable_right = right - CLOSE_BUTTONS * right_scale
            for monitor_id, scale, mx, my, nx, ny, _nr, _nb, work in mappings:
                if not work[1] <= top < work[3]:
                    continue
                lo, hi = max(left + 10 * scale, work[0]), min(usable_right, work[2])
                segments = [(lo, hi)] if lo < hi else []
                for front_left, front_top, front_right, front_bottom in foreground:
                    if not front_top <= top < front_bottom:
                        continue
                    visible = []
                    for start, end in segments:
                        if front_right <= start or front_left >= end:
                            visible.append((start, end))
                        else:
                            if start < front_left:
                                # A borda coberta não deve aceitar um centro de
                                # corpo por causa do <= usado na física.
                                visible.append((start, math.nextafter(front_left, -math.inf)))
                            if front_right < end:
                                visible.append((front_right, end))
                    segments = visible
                for piece, (start, end) in enumerate(segments):
                    if start >= end:
                        continue
                    platforms.append(((hwnd, monitor_id, piece),
                                      mx + (start - nx) / scale,
                                      math.nextafter(mx + (end - nx) / scale + CLOSE_BUTTONS, -math.inf),
                                      my + (top - ny) / scale))
        # Maximizadas também escondem as barras das janelas que estão atrás.
        foreground.append(rect)
    return platforms
