// SPDX-License-Identifier: GPL-3.0-only
import { app, type BrowserWindow, screen } from 'electron';
import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process';
import { join } from 'node:path';
import type { BrainSnapshot, DesktopLayout, Preferences } from '../shared/types';
import { log } from './diagnostics';

const EVENTS = new Set(['panic','hide','monitor','panel','hover','music','drag-start','drag','drag-end','poke','caress','spin','sleep','work','notebook','corner','ball','mischief','dismiss']);
export function validBrainEvent(value: unknown): value is Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const p = value as Record<string, unknown>;
  if (!EVENTS.has(String(p.type)) || Object.keys(p).some(k => !['type','x','y','vx','vy','value','id'].includes(k))) return false;
  for (const key of ['x','y','vx','vy'] as const) if (p[key] !== undefined && (typeof p[key] !== 'number' || !Number.isFinite(p[key]) || Math.abs(p[key]) > 100000)) return false;
  if (String(p.type).startsWith('drag') && (p.x === undefined || p.y === undefined)) return false;
  return (p.id === undefined || typeof p.id === 'string' && /^\d{1,8}$/.test(p.id)) && (p.value === undefined || typeof p.value === 'boolean' || typeof p.value === 'number' && Number.isFinite(p.value));
}

export function createBrain(win: BrowserWindow, initialDesktop: DesktopLayout, initialPreferences: Preferences, onReady: () => void) {
  let child: ChildProcessWithoutNullStreams | undefined, snapshot: BrainSnapshot | null = null, desktop = initialDesktop, preferences = initialPreferences;
  let stopping = false, buffer = '', cursorTimer: ReturnType<typeof setInterval> | undefined;
  const send = (value: unknown) => {
    if (child?.stdin.writable) child.stdin.write(JSON.stringify(value) + '\n');
  };
  const setDesktop = (value: DesktopLayout) => {
    desktop = value;
    let handle: number | undefined;
    if (process.platform === 'win32') handle = Number(win.getNativeWindowHandle().readBigUInt64LE());
    send({ type: 'desktop', value: { ...desktop, exclude: handle === undefined ? [] : [handle] } });
  };
  const start = () => {
    const root = app.isPackaged ? join(process.resourcesPath, 'brain') : join(__dirname, '../../brain');
    const command = app.isPackaged ? join(root, 'BolhaBrain.exe') : (process.env.BOLHA_PYTHON ?? (process.platform === 'win32' ? 'python' : 'python3.11'));
    const args = [...(app.isPackaged ? [] : [join(root, 'worker.py')]), '--data-dir', join(app.getPath('userData'), 'brain'), '--content-dir', join(app.isPackaged ? root : join(__dirname,'../../assets/drippy'), 'content')];
    child = spawn(command, args, { windowsHide: true, stdio: 'pipe', env: { ...process.env, OPENBLAS_NUM_THREADS: '1', OMP_NUM_THREADS: '1', PYTHONUTF8: '1', PYTHONDONTWRITEBYTECODE: '1' } });
    child.stdin.on('error', error => { if (!stopping) log('warn', `Canal do cérebro: ${error.message}`); });
    child.stderr.on('data', chunk => { log('warn', String(chunk).slice(0,2000)); });
    child.stdout.on('data', chunk => {
      buffer += String(chunk);
      if (buffer.length > 2_000_000) { child?.kill(); log('error','Resposta do cérebro excedeu o limite.'); return; }
      let end: number;
      while ((end = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0,end); buffer = buffer.slice(end+1);
        try {
          const next = JSON.parse(line) as BrainSnapshot;
          if (!next.ready || !Number.isFinite(next.x) || !Number.isFinite(next.y) || !Array.isArray(next.objects)) throw new Error('Estado inválido');
          const first = !snapshot;
          snapshot = next;
          if (!win.isDestroyed()) win.webContents.send('bolha:brain', snapshot);
          if (first) onReady();
        } catch (error) { log('error',`Resposta inválida do cérebro: ${String(error)}`); }
      }
    });
    child.on('error', error => { log('error',`Cérebro: ${error.message}`); });
    child.on('exit', code => {
      if (cursorTimer) clearInterval(cursorTimer);
      if (!stopping) {
        log('error', `O cérebro encerrou (${code}).`);
        if (!win.isDestroyed()) win.webContents.send('bolha:brain', { ...snapshot, ready: false, error: 'O cérebro foi interrompido. Feche e abra a Bolha para recuperar a memória salva.' });
      }
    });
    setDesktop(desktop);
    send({ type:'preferences', value: preferences });
    cursorTimer = setInterval(() => {
      if (preferences.senseCursor && !stopping && snapshot?.visible) send({ type:'cursor', ...screen.getCursorScreenPoint() });
    },100);
    cursorTimer.unref();
  };
  const stop = async () => {
    if (stopping || !child || child.exitCode !== null) return;
    stopping = true;
    if (cursorTimer) clearInterval(cursorTimer);
    send({ type: 'quit' });
    child.stdin.end();
    await new Promise<void>(resolve => {
      const timer = setTimeout(() => { child?.kill(); resolve(); }, 5000);
      child!.once('exit', () => { clearTimeout(timer); resolve(); });
    });
  };
  return {
    start, stop,
    getState: () => snapshot,
    event: (value: unknown) => { if (validBrainEvent(value)) send(value); },
    desktop: setDesktop,
    preferences: (value: Preferences) => { preferences = value; send({ type:'preferences', value }); },
  };
}
