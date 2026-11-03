// SPDX-License-Identifier: GPL-3.0-only
import type { DesktopLayout, DisplayArea, Point, Rect } from './types';


export function desktopLayout(areas: DisplayArea[]): DesktopLayout {
  if (!areas.length) areas = [{ id: 0, x: 0, y: 0, width: 800, height: 600, scaleFactor: 1 }];
  const x = Math.min(...areas.map(a => a.x)), y = Math.min(...areas.map(a => a.y));
  return { areas, bounds: { x, y, width: Math.max(...areas.map(a => a.x + a.width)) - x, height: Math.max(...areas.map(a => a.y + a.height)) - y } };
}

function inside(p: Point, area: Rect) { return p.x >= area.x && p.y >= area.y && p.x <= area.x + area.width && p.y <= area.y + area.height; }
export function areaAt(p: Point, areas: DisplayArea[]): DisplayArea {
  return areas.find(a => inside(p, a)) ?? areas.reduce((best, a) => {
    const d = (r: Rect) => Math.hypot(p.x - Math.max(r.x, Math.min(r.x + r.width, p.x)), p.y - Math.max(r.y, Math.min(r.y + r.height, p.y)));
    return d(a) < d(best) ? a : best;
  });
}
