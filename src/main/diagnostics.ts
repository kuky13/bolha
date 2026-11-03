// SPDX-License-Identifier: GPL-3.0-only
import { app } from 'electron';
import { appendFileSync, mkdirSync, statSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import type { LogEntry } from '../shared/types';

const entries: LogEntry[] = [];
export function log(level: LogEntry['level'], message: string): void {
  const entry = { time: new Date().toISOString(), level, message: message.slice(0, 2000) };
  entries.push(entry);
  if (entries.length > 300) entries.shift();
  try {
    const dir = join(app.getPath('userData'), 'logs');
    mkdirSync(dir, { recursive: true });
    const file = join(dir,'session.log');
    try { if (statSync(file).size > 256000) writeFileSync(file,readFileSync(file).subarray(-128000)); } catch { /* First entry. */ }
    appendFileSync(file, JSON.stringify(entry) + '\n');
  } catch { /* A read-only disk must not prevent the companion from starting. */ }
}
export function getLogs(): LogEntry[] { return entries.map(e => ({ ...e })); }
export function report(): string {
  return `Bolha ${app.getVersion()}\n${process.platform} ${process.arch}\nElectron ${process.versions.electron}\n\n${entries.map(e => `${e.time} [${e.level}] ${e.message}`).join('\n')}`;
}
