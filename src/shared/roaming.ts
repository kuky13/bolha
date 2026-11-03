// SPDX-License-Identifier: GPL-3.0-only
import type { DesktopLayout, DisplayArea, Point, Rect } from './types';

export interface RoamingState extends Point { vx: number; vy: number; phase: number; pause: number; distance: number }
const MARGIN = 12;

export function desktopLayout(areas: DisplayArea[]): DesktopLayout {
  if (!areas.length) areas = [{ id: 0, x: 0, y: 0, width: 800, height: 600, scaleFactor: 1 }];
  const x = Math.min(...areas.map(a => a.x)), y = Math.min(...areas.map(a => a.y));
  return { areas, bounds: { x, y, width: Math.max(...areas.map(a => a.x + a.width)) - x, height: Math.max(...areas.map(a => a.y + a.height)) - y } };
}

function centerBounds(area: Rect, size: number): Rect {
  const half = size / 2 + MARGIN;
  return { x: area.x + Math.min(half, area.width / 2), y: area.y + Math.min(half, area.height / 2), width: Math.max(0, area.width - half * 2), height: Math.max(0, area.height - half * 2) };
}
function inside(p: Point, area: Rect) { return p.x >= area.x && p.y >= area.y && p.x <= area.x + area.width && p.y <= area.y + area.height; }
export function areaAt(p: Point, areas: DisplayArea[]): DisplayArea {
  return areas.find(a => inside(p, a)) ?? areas.reduce((best, a) => {
    const d = (r: Rect) => Math.hypot(p.x - Math.max(r.x, Math.min(r.x + r.width, p.x)), p.y - Math.max(r.y, Math.min(r.y + r.height, p.y)));
    return d(a) < d(best) ? a : best;
  });
}
export function clampPoint(p: Point, areas: DisplayArea[], size: number): Point {
  const b = centerBounds(areaAt(p, areas), size);
  return { x: Math.max(b.x, Math.min(b.x + b.width, p.x)), y: Math.max(b.y, Math.min(b.y + b.height, p.y)) };
}
export function initialRoaming(point: Point | null, areas: DisplayArea[], size: number): RoamingState {
  const a = areas[0];
  const p = clampPoint(point ?? { x: a.x + a.width * 0.75, y: a.y + a.height * 0.65 }, areas, size);
  return { ...p, vx: 62, vy: 31, phase: 0, pause: 0, distance: 0 };
}

/** Pure simulation in screen DIP. No browser/OS I/O and no wall-clock dependency. */
export function stepRoaming(state: RoamingState, dt: number, areas: DisplayArea[], size: number, paused: boolean, random = Math.random): RoamingState {
  const safe = clampPoint(state, areas, size);
  const s = { ...state, ...safe };
  dt = Math.max(0, Math.min(0.05, dt));
  if (paused || !dt) return s;
  if (s.pause > 0) return { ...s, pause: Math.max(0, s.pause - dt) };
  const candidate = { x: s.x + s.vx * dt, y: s.y + s.vy * dt };
  const current = areaAt(s, areas), target = areas.find(a => inside(candidate, a));
  const b = centerBounds(current, size);
  // Neighbouring screens can be crossed before the centre reaches the seam.
  const near = areas.filter(a => a.id !== current.id).find(a => {
    const towardX = s.vx > 0 ? a.x >= current.x + current.width - 2 && candidate.x >= b.x + b.width : a.x + a.width <= current.x + 2 && candidate.x <= b.x;
    const towardY = s.vy > 0 ? a.y >= current.y + current.height - 2 && candidate.y >= b.y + b.height : a.y + a.height <= current.y + 2 && candidate.y <= b.y;
    return (towardX && candidate.y >= a.y && candidate.y <= a.y + a.height) || (towardY && candidate.x >= a.x && candidate.x <= a.x + a.width);
  });
  if (near || (target && target.id !== current.id)) {
    const next = near ?? target!;
    const clamped = clampPoint(candidate, [next], size);
    return { ...s, ...clamped, phase: s.phase + dt * 3.2, distance: s.distance + Math.hypot(s.vx, s.vy) * dt };
  }
  if (candidate.x < b.x || candidate.x > b.x + b.width) s.vx *= -1;
  if (candidate.y < b.y || candidate.y > b.y + b.height) s.vy *= -1;
  const next = clampPoint({ x: s.x + s.vx * dt, y: s.y + s.vy * dt }, [current], size);
  s.distance += Math.hypot(s.vx, s.vy) * dt;
  if (s.distance > 700) {
    s.distance = 0;
    s.pause = 0.8 + random() * 1.6;
    s.vy = (random() < 0.5 ? -1 : 1) * (24 + random() * 24);
    // Also reach displays separated by a gap in the OS arrangement.
    if (areas.length > 1 && !near) {
      const other = areas[(areas.indexOf(current) + 1) % areas.length];
      Object.assign(next, clampPoint({ x: other.x + other.width / 2, y: other.y + other.height / 2 }, [other], size));
    }
  }
  return { ...s, ...next, phase: s.phase + dt * 3.2 };
}

export function jumpOffset(state: RoamingState, paused: boolean): number {
  return paused || state.pause > 0 ? 0 : -Math.abs(Math.sin(state.phase * Math.PI)) * 18;
}
