// SPDX-License-Identifier: GPL-3.0-only
import { contextBridge, ipcRenderer } from 'electron';
import type { BolhaAPI } from '../shared/types';

function subscribe<T>(channel: string, callback: (value: T) => void): () => void {
  const listener = (_: Electron.IpcRendererEvent, value: T) => callback(value);
  ipcRenderer.on(channel, listener);
  return () => { ipcRenderer.removeListener(channel, listener); };
}
const api: BolhaAPI & { ready(): Promise<void> } = {
  bootstrap: () => ipcRenderer.invoke('bolha:bootstrap'),
  savePreferences: patch => ipcRenderer.invoke('bolha:preferences', patch),
  setClickThrough: ignore => { ipcRenderer.send('bolha:click-through', ignore); },
  setStartup: enabled => ipcRenderer.invoke('bolha:startup', enabled),
  media: action => ipcRenderer.invoke('bolha:media', action),
  logs: () => ipcRenderer.invoke('bolha:logs'),
  copyDiagnostics: () => ipcRenderer.invoke('bolha:copy-diagnostics'),
  resetPreferences: () => ipcRenderer.invoke('bolha:reset'),
  checkUpdates: () => ipcRenderer.invoke('bolha:check-updates'),
  deferUpdate: () => ipcRenderer.invoke('bolha:defer-update'),
  installUpdate: () => ipcRenderer.invoke('bolha:install-update'),
  hide: () => ipcRenderer.invoke('bolha:hide'),
  quit: () => ipcRenderer.invoke('bolha:quit'),
  ready: () => ipcRenderer.invoke('bolha:ready'),
  onDesktop: callback => subscribe('bolha:desktop', callback),
  onUpdate: callback => subscribe('bolha:update', callback),
  onPreferences: callback => subscribe('bolha:preferences', callback),
  onOpenSettings: callback => subscribe('bolha:open-settings', callback),
  brainEvent: event => { ipcRenderer.send('bolha:brain-event', event); },
  onBrain: callback => subscribe('bolha:brain', callback),
};
contextBridge.exposeInMainWorld('bolha', Object.freeze(api));
