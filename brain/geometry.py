# SPDX-License-Identifier: GPL-3.0-only
"""Detecção por monitor usando apenas retângulos e estilo de janela."""
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
