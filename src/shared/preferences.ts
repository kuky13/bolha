// SPDX-License-Identifier: GPL-3.0-only
import type { Preferences, Shortcuts } from './types';
import { isReservedAccelerator } from './shortcuts';

export function defaults(): Preferences {
  return { avatarSize: 136, opacity: 1, roaming: true, mediaEnabled: false, showMedia: true, position: null,
    shortcuts: { playPause: 'MediaPlayPause', next: 'MediaNextTrack', previous: 'MediaPreviousTrack' },
    mischiefEnabled: true, mischiefInterval: 300, maxObjects: 3, burstLimit: 12,
    senseApp: true, senseIdle: true, senseCursor: true, senseWindows: true };
}

export function validShortcut(value: unknown): value is string {
  return typeof value === 'string' && value.length <= 80 &&
    /^(?:(?:CommandOrControl|Ctrl|Alt|Shift|Super)\+)*(?:[A-Z0-9]|F(?:[1-9]|1[0-9]|2[0-4])|Space|Up|Down|Left|Right|MediaPlayPause|MediaNextTrack|MediaPreviousTrack)$/.test(value) && !isReservedAccelerator(value);
}

/** The renderer can only change the known local preferences. */
export function sanitizePreferences(patch: unknown, previous: Preferences = defaults()): Preferences {
  const next: Preferences = { ...previous, shortcuts: { ...previous.shortcuts }, position: previous.position && { ...previous.position } };
  if (!patch || typeof patch !== 'object' || Array.isArray(patch)) return next;
  const p = patch as Record<string, unknown>;
  if (typeof p.avatarSize === 'number' && Number.isFinite(p.avatarSize)) next.avatarSize = Math.round(Math.min(200, Math.max(80, p.avatarSize)));
  if (typeof p.opacity === 'number' && Number.isFinite(p.opacity)) next.opacity = Math.min(1, Math.max(0.2, p.opacity));
  for (const key of ['roaming', 'mediaEnabled', 'showMedia', 'mischiefEnabled', 'senseApp', 'senseIdle', 'senseCursor', 'senseWindows'] as const) if (typeof p[key] === 'boolean') next[key] = p[key];
  for (const [key, low, high] of [['mischiefInterval',60,1800],['maxObjects',1,5],['burstLimit',6,30]] as const) {
    if (typeof p[key] === 'number' && Number.isFinite(p[key])) next[key] = Math.round(Math.min(high, Math.max(low, p[key])));
  }
  if (p.position === null) next.position = null;
  else if (p.position && typeof p.position === 'object') {
    const point = p.position as Record<string, unknown>;
    if (typeof point.x === 'number' && typeof point.y === 'number' && Number.isFinite(point.x) && Number.isFinite(point.y)) next.position = { x: point.x, y: point.y };
  }
  if (p.shortcuts && typeof p.shortcuts === 'object') {
    for (const key of ['playPause', 'next', 'previous'] as const) {
      const value = (p.shortcuts as Partial<Shortcuts>)[key];
      if (validShortcut(value)) next.shortcuts[key] = value;
    }
  }
  return next;
}
