// SPDX-License-Identifier: GPL-3.0-only
import { app, BrowserWindow, clipboard, globalShortcut, ipcMain, Menu, nativeImage, screen, Tray } from 'electron';
import Store from 'electron-store';
import { join } from 'node:path';
import { mkdirSync, writeFileSync } from 'node:fs';
import { defaults, sanitizePreferences } from '../shared/preferences';
import { desktopLayout } from '../shared/roaming';
import type { DesktopLayout, Preferences, Shortcuts, MediaState } from '../shared/types';
import { getMediaState, mediaNext, mediaPlayPause, mediaPrevious } from './mediaSession';
import { getLogs, log, report } from './diagnostics';
import { createUpdater } from './updater';
import { createBrain, validBrainEvent } from './brain';

app.setName('Bolha');
app.setAppUserModelId('solutions.kuky.bolha');
const testData = process.env.BOLHA_TEST === '1' ? process.env.BOLHA_TEST_USER_DATA : undefined;
app.setPath('userData', testData ?? join(app.getPath('appData'), 'bolha'));
if (!app.requestSingleInstanceLock()) app.quit();
else {
  let win: BrowserWindow | undefined, tray: Tray | undefined;
  let store: Store<{ preferences: Preferences }>, preferences: Preferences;
  let desktop: DesktopLayout;
  let shortcuts: Record<keyof Shortcuts, boolean> = { playPause: false, next: false, previous: false };
  let updater: ReturnType<typeof createUpdater> | undefined;
  let brain: ReturnType<typeof createBrain> | undefined;
  let rendererReady = false, healthWritten = false, quitting = false;
  const healthy = async () => {
    if (!rendererReady || !brain?.getState()?.ready || healthWritten) return;
    healthWritten = true;
    await updater!.healthy();
    try {
      mkdirSync(app.getPath('userData'), { recursive: true });
      writeFileSync(join(app.getPath('userData'), 'health.json'), JSON.stringify({ version: app.getVersion(), ready: true, neurons: brain.getState()!.neurons, pid:process.pid }));
    } catch (error) { log('warn', `Não consegui gravar o diagnóstico de abertura: ${String(error)}`); }
    updater!.start();
    if (process.env.BOLHA_TEST === '1' && process.env.BOLHA_TEST_EXIT_VERSION === app.getVersion()) setTimeout(() => app.quit(), 45000);
  };
  let mediaPending: Promise<MediaState | null> | null = null;
  const mediaCall = (action: 'state' | 'playpause' | 'next' | 'previous') => {
    if (!preferences.mediaEnabled || process.platform !== 'win32') return Promise.resolve(null);
    if (action === 'state' && mediaPending) return mediaPending;
    const task = action === 'playpause' ? mediaPlayPause() : action === 'next' ? mediaNext() : action === 'previous' ? mediaPrevious() : getMediaState();
    if (action === 'state') {
      mediaPending = task;
      void task.finally(() => { mediaPending = null; });
    }
    return task;
  };
  const readDesktop = () => desktopLayout(screen.getAllDisplays().map(d => {
    const center = { x: Math.round(d.bounds.x + d.bounds.width/2), y: Math.round(d.bounds.y + d.bounds.height/2) };
    const native = process.platform === 'win32' ? screen.dipToScreenPoint(center) : center;
    return { id: d.id, ...d.workArea, scaleFactor: d.scaleFactor, monitorX:d.bounds.x, monitorY:d.bounds.y, monitorWidth:d.bounds.width, monitorHeight:d.bounds.height,
      nativeX: native.x - d.bounds.width*d.scaleFactor/2, nativeY: native.y - d.bounds.height*d.scaleFactor/2 };
  }));
  const startup = () => process.platform === 'win32' && app.isPackaged && app.getLoginItemSettings().openAtLogin;
  const syncShortcuts = () => {
    globalShortcut.unregisterAll();
    shortcuts = { playPause: false, next: false, previous: false };
    try { globalShortcut.register('CommandOrControl+Alt+Shift+B', () => brain?.event({type:'panic'})); } catch { log('warn','Atalho de pausa indisponível.'); }
    if (!preferences.mediaEnabled || process.platform !== 'win32') return;
    for (const [key, action] of [['playPause', 'playpause'], ['next', 'next'], ['previous', 'previous']] as const) {
      try { shortcuts[key] = globalShortcut.register(preferences.shortcuts[key], () => { void mediaCall(action); }); }
      catch { shortcuts[key] = false; }
    }
  };
  const show = () => { brain?.event({type:'hide',value:false}); win?.showInactive(); };
  const hide = () => { brain?.event({type:'hide',value:true}); win?.hide(); };
  const save = (patch: unknown) => {
    preferences = sanitizePreferences(patch, preferences);
    store.set('preferences', preferences);
    syncShortcuts();
    brain?.preferences(preferences);
    win?.webContents.send('bolha:preferences', preferences);
    refreshTray();
    return preferences;
  };
  const refreshTray = () => {
    tray?.setContextMenu(Menu.buildFromTemplate([
      { label: 'Mostrar a Drippy', click: show },
      { label: 'Esconder a Drippy', click: hide },
      { type: 'separator' },
      { label: 'Pausar / retomar a Drippy', click: () => brain?.event({type:'panic'}) },
      { label: 'Passear pela tela', type: 'checkbox', checked: preferences.roaming, click: () => save({ roaming: !preferences.roaming }) },
      { label: 'Configurações', click: () => { show(); win?.webContents.send('bolha:open-settings'); } },
      { label: 'Verificar atualização', click: () => { void updater?.check(); } },
      { type: 'separator' },
      { label: 'Sair da Bolha', click: () => app.quit() },
    ]));
  };
  app.on('second-instance', show);
  app.whenReady().then(() => {
    store = new Store({ defaults: { preferences: defaults() } });
    preferences = sanitizePreferences(store.get('preferences'));
    desktop = readDesktop();
    win = new BrowserWindow({
      ...desktop.bounds, frame: false, transparent: true, hasShadow: false, alwaysOnTop: true,
      skipTaskbar: true, focusable: false, resizable: false, movable: false, show: false,
      webPreferences: { preload: join(__dirname, '../preload/index.js'), contextIsolation: true, nodeIntegration: false, sandbox: true, backgroundThrottling: false },
    });
    win.setIgnoreMouseEvents(true, { forward: true });
    win.setAlwaysOnTop(true, 'screen-saver');
    win.webContents.session.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
    win.webContents.session.setPermissionCheckHandler(() => false);
    win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    win.webContents.on('will-navigate', event => { event.preventDefault(); });
    win.webContents.on('render-process-gone', (_event, details) => log('error', `Renderizador: ${details.reason}`));
    updater = createUpdater(win, async () => { await brain?.stop(); }, () => { if (!quitting) brain?.start(); });
    brain = createBrain(win, desktop, preferences, () => { void healthy(); });

    const trusted = (event: Electron.IpcMainEvent | Electron.IpcMainInvokeEvent) => !!win && event.sender === win.webContents && event.senderFrame === win.webContents.mainFrame;
    const handle = (name: string, fn: (value: unknown) => unknown) => {
      ipcMain.handle(name, (event, value: unknown) => { if (!trusted(event)) throw new Error('Origem não permitida.'); return fn(value); });
    };
    handle('bolha:bootstrap', () => ({ preferences, desktop, version: app.getVersion(), update: updater!.getState(), startup: startup(), shortcutStatus: shortcuts, brain: brain!.getState() }));
    ipcMain.on('bolha:brain-event', (event, value: unknown) => {
      if (trusted(event) && validBrainEvent(value)) {
        if (value.type === 'panel' && typeof value.value === 'boolean') { win?.setFocusable(value.value); if (value.value) win?.focus(); }
        brain?.event(value);
      }
    });
    handle('bolha:preferences', save);
    ipcMain.on('bolha:click-through', (event, ignore: unknown) => {
      if (trusted(event) && typeof ignore === 'boolean') win?.setIgnoreMouseEvents(ignore, { forward: true });
    });
    handle('bolha:media', action => {
      if (!['state', 'playpause', 'next', 'previous'].includes(String(action))) throw new Error('Ação de mídia inválida.');
      return mediaCall(action as 'state' | 'playpause' | 'next' | 'previous');
    });
    handle('bolha:startup', enabled => {
      if (typeof enabled !== 'boolean') throw new Error('Opção inválida.');
      if (process.platform === 'win32' && app.isPackaged) app.setLoginItemSettings({ openAtLogin: enabled });
      return startup();
    });
    handle('bolha:logs', getLogs);
    handle('bolha:copy-diagnostics', () => { clipboard.writeText(report()); });
    handle('bolha:reset', () => save(defaults()));
    handle('bolha:check-updates', () => updater!.check());
    handle('bolha:defer-update', () => updater!.defer());
    handle('bolha:install-update', () => updater!.install());
    handle('bolha:hide', hide);
    handle('bolha:quit', () => app.quit());
    let started = false;
    handle('bolha:ready', async () => {
      if (started) return;
      started = true;
      log('info', `Bolha ${app.getVersion()} pronta.`);
      rendererReady = true;
      await healthy();
    });
    const iconPath = app.isPackaged ? join(process.resourcesPath, 'tray.png') : join(__dirname, '../../assets/drippy/tray.png');
    const icon = nativeImage.createFromPath(iconPath);
    if (icon.isEmpty()) log('warn', 'Ícone da bandeja indisponível.');
    tray = new Tray(icon.isEmpty() ? icon : icon.resize({ width: 20, height: 20 }));
    tray.setToolTip('Bolha · Drippy');
    tray.on('click', () => { if (win?.isVisible()) hide(); else show(); });
    syncShortcuts();
    refreshTray();
    const displayChanged = () => {
      desktop = readDesktop();
      win?.setBounds(desktop.bounds);
      win?.webContents.send('bolha:desktop', desktop);
      brain?.desktop(desktop);
    };
    screen.on('display-added', displayChanged);
    screen.on('display-removed', displayChanged);
    screen.on('display-metrics-changed', displayChanged);
    win.once('ready-to-show', show);
    brain.start();
    const devUrl = process.env.ELECTRON_RENDERER_URL;
    if (!app.isPackaged && devUrl) void win.loadURL(devUrl);
    else void win.loadFile(join(__dirname, '../renderer/index.html'));
  }).catch(error => { console.error(error); app.exit(1); });
  app.on('before-quit', event => {
    globalShortcut.unregisterAll(); updater?.stop();
    if (!quitting) { event.preventDefault(); quitting = true; void brain?.stop().finally(() => app.quit()); }
    else tray?.destroy();
  });
  app.on('window-all-closed', () => app.quit());
}
