// SPDX-License-Identifier: GPL-3.0-only
const EVENTS = new Set(['panic','hide','monitor','panel','hover','music','drag-start','drag','drag-end','poke','caress','spin','sleep','work','notebook','corner','ball','mischief','dismiss','quiet','reset-memory']);
export function validBrainEvent(value: unknown): value is Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const p = value as Record<string, unknown>;
  if (!EVENTS.has(String(p.type)) || Object.keys(p).some(k => !['type','x','y','vx','vy','value','id'].includes(k))) return false;
  for (const key of ['x','y','vx','vy'] as const) if (p[key] !== undefined && (typeof p[key] !== 'number' || !Number.isFinite(p[key]) || Math.abs(p[key]) > 100000)) return false;
  if (String(p.type).startsWith('drag') && (p.x === undefined || p.y === undefined)) return false;
  return (p.id === undefined || typeof p.id === 'string' && /^\d{1,8}$/.test(p.id)) && (p.value === undefined || typeof p.value === 'boolean' || typeof p.value === 'number' && Number.isFinite(p.value));
}

