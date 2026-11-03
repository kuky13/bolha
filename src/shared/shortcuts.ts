// SPDX-License-Identifier: GPL-3.0-only
const SPECIAL_KEYS: Record<string, string> = {
  ' ': 'Space',
  ArrowUp: 'Up',
  ArrowDown: 'Down',
  ArrowLeft: 'Left',
  ArrowRight: 'Right',
  Escape: 'Esc',
};

export function formatAccelerator(e: { ctrlKey: boolean; metaKey: boolean; altKey: boolean; shiftKey: boolean; key: string }): string | null {
  const parts: string[] = [];
  if (e.ctrlKey || e.metaKey) parts.push('CommandOrControl');
  if (e.altKey) parts.push('Alt');
  if (e.shiftKey) parts.push('Shift');

  const key = e.key;
  if (['Control', 'Meta', 'Alt', 'Shift'].includes(key)) return null; // só modificador, ainda não é um atalho válido

  const mainKey = SPECIAL_KEYS[key] ?? (key.length === 1 ? key.toUpperCase() : key);
  parts.push(mainKey);
  return parts.join('+');
}
const RESERVED_ACCELERATORS = new Set([
  'Alt+Tab',
  'Alt+F4',
  'Alt+Esc',
  'Alt+Space',
  'CommandOrControl+Alt+Delete',
  'CommandOrControl+Shift+Esc',
  'CommandOrControl+Esc',
  'CommandOrControl+Alt+Esc',
  'Esc',
  'PrintScreen',
]);

export function isReservedAccelerator(accel: string): boolean {
  return RESERVED_ACCELERATORS.has(accel);
}
