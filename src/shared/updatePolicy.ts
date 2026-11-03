// SPDX-License-Identifier: GPL-3.0-only
export const CHECK_INTERVAL = 6 * 60 * 60 * 1000;
export const COUNTDOWN = 30_000;
export const DEFER_INTERVAL = 60 * 60 * 1000;

export function compareVersions(left: string, right: string): number {
  const parse = (value: string) => /^\d+\.\d+\.\d+$/.test(value) ? value.split('.').map(Number) : null;
  const a = parse(left), b = parse(right);
  if (!a || !b) throw new Error('Versão inválida.');
  for (let i = 0; i < 3; i++) if (a[i] !== b[i]) return a[i] > b[i] ? 1 : -1;
  return 0;
}

export function installationDeadline(now: number, deferred: boolean): number {
  return now + (deferred ? DEFER_INTERVAL : COUNTDOWN);
}
