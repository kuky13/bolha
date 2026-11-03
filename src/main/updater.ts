// SPDX-License-Identifier: GPL-3.0-only
import { app, type BrowserWindow } from 'electron';
import { autoUpdater } from 'electron-updater';
import { join } from 'node:path';
import { readFileSync, writeFileSync, rmSync } from 'node:fs';
import { COUNTDOWN, CHECK_INTERVAL, DEFER_INTERVAL, compareVersions, installationDeadline } from '../shared/updatePolicy';
import { cleanupAppliedUpdate, recordUpdate } from './updateCleanup';
import type { UpdateState } from '../shared/types';
import { log } from './diagnostics';

export function createUpdater(win: BrowserWindow, beforeInstall: () => Promise<void>, recoverBrain: () => void) {
  let state: UpdateState = { phase: 'idle' }, checking = false, installing = false;
  let checkTimer: ReturnType<typeof setInterval> | undefined, installTimer: ReturnType<typeof setTimeout> | undefined;
  const marker = join(app.getPath('userData'), 'pending-update.json');
  const deferFile = join(app.getPath('userData'), 'update-deferred.json');
  let deferredVersion = '', deferredUntil = 0;
  try {
    const saved = JSON.parse(readFileSync(deferFile, 'utf8'));
    if (typeof saved.version === 'string' && Number.isFinite(saved.until) && saved.until > Date.now()) {
      compareVersions(saved.version, saved.version);
      deferredVersion = saved.version;
      deferredUntil = Math.min(saved.until, Date.now() + DEFER_INTERVAL);
    }
  } catch { /* No deferred update. */ }
  const cacheRoot = join(process.env.LOCALAPPDATA ?? join(app.getPath('appData'), '..', 'Local'), 'bolha-updater');
  const send = (next: UpdateState) => {
    state = next;
    if (!win.isDestroyed()) win.webContents.send('bolha:update', state);
  };
  const useTestFeed = process.env.BOLHA_TEST_UPDATE_URL;
  if (useTestFeed && process.env.BOLHA_TEST === '1') {
    const url = new URL(useTestFeed);
    if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1') throw new Error('Feed de teste precisa ser local.');
    autoUpdater.setFeedURL({ provider: 'generic', url: url.href });
  }
  autoUpdater.autoDownload = true;
  autoUpdater.autoInstallOnAppQuit = false;
  autoUpdater.allowPrerelease = false;
  autoUpdater.allowDowngrade = false;
  autoUpdater.logger = { info: (...a: unknown[]) => log('info', a.join(' ')), warn: (...a: unknown[]) => log('warn', a.join(' ')), error: (...a: unknown[]) => log('error', a.join(' ')), debug: () => {} };
  const enabled = app.isPackaged && process.platform === 'win32' && (process.env.BOLHA_TEST !== '1' || !!useTestFeed);

  const install = async () => {
    if (state.phase !== 'ready' || installing) return;
    installing = true;
    if (installTimer) clearTimeout(installTimer);
    send({ ...state, phase: 'installing', message: 'Instalando. A Bolha vai reabrir em instantes.' });
    try { await beforeInstall(); autoUpdater.quitAndInstall(true, true); }
    catch (error) { installing = false; recoverBrain(); send({ phase: 'error', message: String(error) }); }
  };
  const schedule = (deferred: boolean) => {
    if (state.phase !== 'ready') return;
    if (installTimer) clearTimeout(installTimer);
    const installAt = Math.max(installationDeadline(Date.now(), deferred), state.version === deferredVersion ? deferredUntil : 0);
    if (deferred) {
      deferredVersion = state.version ?? '';
      deferredUntil = installAt;
      try { writeFileSync(deferFile, JSON.stringify({ version: deferredVersion, until: deferredUntil })); }
      catch (error) { log('warn', `Não consegui guardar o adiamento: ${String(error)}`); }
    }
    send({ ...state, installAt });
    installTimer = setTimeout(install, installAt - Date.now());
  };
  autoUpdater.on('checking-for-update', () => send({ phase: 'checking' }));
  autoUpdater.on('update-not-available', () => send({ phase: 'idle', message: 'Você está na versão mais recente.' }));
  autoUpdater.on('download-progress', progress => send({ phase: 'downloading', version: state.version, percent: progress.percent }));
  autoUpdater.on('update-available', info => send({ phase: 'downloading', version: info.version, percent: 0 }));
  autoUpdater.on('update-downloaded', info => {
    void (async () => {
      try {
        await recordUpdate(marker, { version: info.version, installer: info.downloadedFile }, cacheRoot);
        state = { phase: 'ready', version: info.version };
        schedule(false);
      } catch (error) { send({ phase: 'error', message: `Não consegui preparar a atualização: ${String(error)}` }); }
    })();
  });
  autoUpdater.on('error', error => {
    const wasInstalling = installing;
    installing = false;
    if (wasInstalling) recoverBrain();
    if (installTimer) clearTimeout(installTimer);
    send({ phase: 'error', message: 'Não foi possível atualizar agora. Você pode continuar usando a bolha.' });
    log('error', `Atualização: ${error.message}`);
  });

  const check = async () => {
    if (!enabled) { send({ phase: 'idle', message: 'Atualizações automáticas ficam disponíveis na versão instalada para Windows.' }); return; }
    if (checking || ['ready', 'installing', 'downloading'].includes(state.phase)) return;
    checking = true;
    try { await autoUpdater.checkForUpdates(); }
    catch (error) { log('warn', `Consulta de atualização: ${String(error)}`); }
    finally { checking = false; }
  };
  const healthy = async () => {
    try {
      const cleaned = await cleanupAppliedUpdate(marker, app.getVersion(), cacheRoot);
      if (!cleaned) return;
      if (deferredVersion && compareVersions(app.getVersion(), deferredVersion) >= 0) rmSync(deferFile, { force: true });
    } catch (error) {
      log('warn', `Limpeza será tentada novamente: ${String(error)}`);
      const retry = setTimeout(() => { void healthy(); }, COUNTDOWN);
      retry.unref();
    }
  };
  return {
    getState: () => ({ ...state }),
    check,
    defer: () => schedule(true),
    install,
    healthy,
    start: () => { if (enabled) { void check(); checkTimer = setInterval(() => { void check(); }, CHECK_INTERVAL); checkTimer.unref(); } },
    stop: () => { if (checkTimer) clearInterval(checkTimer); if (installTimer) clearTimeout(installTimer); },
  };
}
