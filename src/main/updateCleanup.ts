// SPDX-License-Identifier: GPL-3.0-only
import { readFile, writeFile, mkdir, rm, readdir } from 'node:fs/promises';
import { dirname, join, resolve, relative, isAbsolute } from 'node:path';
import { compareVersions } from '../shared/updatePolicy';

export interface PendingUpdate { version: string; installer: string }
function inside(root: string, path: string): boolean {
  const rel = relative(resolve(root), resolve(path));
  return !!rel && rel !== '..' && !rel.startsWith('..' + (process.platform === 'win32' ? '\\' : '/')) && !isAbsolute(rel);
}
export async function recordUpdate(file: string, update: PendingUpdate, cacheRoot: string): Promise<void> {
  if (!inside(cacheRoot, update.installer) || !update.installer.toLowerCase().endsWith('.exe')) throw new Error('Instalador fora do cache da Bolha.');
  await mkdir(dirname(file), { recursive: true });
  await writeFile(file, JSON.stringify(update), { mode: 0o600 });
}

/** Only a healthy, newer app can remove its own downloaded update cache. */
export async function cleanupAppliedUpdate(file: string, current: string, cacheRoot: string): Promise<boolean> {
  let pending: PendingUpdate;
  try { pending = JSON.parse(await readFile(file, 'utf8')) as PendingUpdate; }
  catch (error) { if ((error as NodeJS.ErrnoException).code === 'ENOENT') return true; throw error; }
  if (typeof pending.version !== 'string' || typeof pending.installer !== 'string') throw new Error('Registro de atualização inválido.');
  if (compareVersions(current, pending.version) < 0) return false;
  if (!inside(cacheRoot, pending.installer) || !pending.installer.toLowerCase().endsWith('.exe')) throw new Error('Cache de atualização inválido.');
  await rm(pending.installer, { force: true });
  const pendingDir = dirname(pending.installer);
  for (const name of await readdir(pendingDir).catch(() => [] as string[])) {
    if (/\.(?:part|blockmap)$/i.test(name) || name === 'update-info.json') await rm(join(pendingDir, name), { force: true });
  }
  await rm(file, { force: true });
  return true;
}
