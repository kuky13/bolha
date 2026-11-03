// SPDX-License-Identifier: GPL-3.0-only
export interface Point { x: number; y: number }
export interface Rect extends Point { width: number; height: number }
export interface DisplayArea extends Rect { id: number; scaleFactor: number; nativeX?: number; nativeY?: number; monitorX?: number; monitorY?: number; monitorWidth?: number; monitorHeight?: number }
export interface DesktopLayout { bounds: Rect; areas: DisplayArea[] }
export interface MediaState { title: string; artist: string; isPlaying: boolean; albumArt: string | null }
export type MediaAction = 'playpause' | 'next' | 'previous';
export interface Shortcuts { playPause: string; next: string; previous: string }
export interface Preferences {
  avatarSize: number;
  opacity: number;
  roaming: boolean;
  mediaEnabled: boolean;
  showMedia: boolean;
  shortcuts: Shortcuts;
  position: Point | null;
  mischiefEnabled: boolean;
  mischiefInterval: number;
  maxObjects: number;
  burstLimit: number;
  senseApp: boolean;
  senseIdle: boolean;
  senseCursor: boolean;
  senseWindows: boolean;
  adaptiveBehavior: boolean;
  learnRoutine: boolean;
}
export interface SceneObject { id: string; kind: 'ball' | 'paper' | 'notebook' | 'meme' | 'note' | 'corner' | 'sign' | 'fireworks'; x: number; y: number; width: number; height: number; text: string; image?: string; angle: number; working: boolean; carried: boolean }
export interface BrainSnapshot {
  pose: 'idle' | 'held' | 'airborne' | 'lying' | 'sleeping' | 'working'; grounded: boolean; surface: number; vx: number; vy: number; landing: number;
  ready: boolean; panicked: boolean; blocked: number[]; shyness: number; x: number; y: number; angle: number; emotion: string; phase: 'normal' | 'burst' | 'away' | 'shy'; visible: boolean; held: boolean; caressing: boolean; gaze: number[]; speech: string;
  objects: SceneObject[]; energy: number; stimulation: number; lonely: number; protest: number; castigo: boolean; escapes: number; activity: string; motors: Record<string, number>; learned: Array<[string,string,number]>; neurons: number; error?: string | null;
  neural?: { positions: number[][]; trace: number[]; kind: number[]; pools: Record<string, number> };
  intelligence?: { enabled: boolean; goal: string | null; label: string; slots: number; episodes: number; decisions: number; cpuSeconds: number; compatibility: string; brainRssMiB: number; routine: { attention:number; rest:number; familiarity:number } | null };
}
export interface BrainEvent { type: 'panic' | 'hide' | 'monitor' | 'panel' | 'hover' | 'music' | 'drag-start' | 'drag' | 'drag-end' | 'poke' | 'caress' | 'spin' | 'sleep' | 'rest' | 'work' | 'notebook' | 'corner' | 'ball' | 'mischief' | 'dismiss' | 'quiet' | 'reset-memory'; id?: string; x?: number; y?: number; vx?: number; vy?: number; value?: boolean | number }
export type UpdatePhase = 'idle' | 'checking' | 'downloading' | 'ready' | 'installing' | 'error';
export interface UpdateState { phase: UpdatePhase; version?: string; percent?: number; installAt?: number; message?: string }
export interface LogEntry { time: string; level: 'info' | 'warn' | 'error'; message: string }
export interface Bootstrap { preferences: Preferences; desktop: DesktopLayout; version: string; update: UpdateState; startup: boolean; shortcutStatus: Record<keyof Shortcuts, boolean>; brain: BrainSnapshot | null }
export interface BolhaAPI {
  bootstrap(): Promise<Bootstrap>;
  savePreferences(patch: Partial<Preferences>): Promise<Preferences>;
  setClickThrough(ignore: boolean): void;
  setStartup(enabled: boolean): Promise<boolean>;
  media(action: MediaAction | 'state'): Promise<MediaState | null>;
  logs(): Promise<LogEntry[]>;
  copyDiagnostics(): Promise<void>;
  resetPreferences(): Promise<Preferences>;
  checkUpdates(): Promise<void>;
  deferUpdate(): Promise<void>;
  installUpdate(): Promise<void>;
  hide(): Promise<void>;
  quit(): Promise<void>;
  onDesktop(callback: (layout: DesktopLayout) => void): () => void;
  onUpdate(callback: (state: UpdateState) => void): () => void;
  onPreferences(callback: (preferences: Preferences) => void): () => void;
  onOpenSettings(callback: () => void): () => void;
  brainEvent(event: BrainEvent): void;
  onBrain(callback: (state: BrainSnapshot) => void): () => void;
}
