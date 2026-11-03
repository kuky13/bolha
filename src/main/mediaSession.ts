// SPDX-License-Identifier: GPL-3.0-only
import { spawn } from 'node:child_process';
import { writeFile, mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

export interface MediaState {
  title: string;
  artist: string;
  isPlaying: boolean;
  
  albumArt: string | null;
}

const PS_SCRIPT = String.raw`
param([string]$Action = "state")

# Sem isso, título/artista com acento (ç, ã, õ...) podem sair corrompidos:
# quando o stdout do PowerShell é redirecionado (não é um console de
# verdade), ele pode cair pro codepage OEM do Windows pra codificar a saída, # o Node do outro lado decodifica como UTF-8, e os bytes não batem. Força
# UTF-8 nos dois lados (aqui + .toString('utf-8') no runPowerShell abaixo).
# Em try/catch porque [Console]::OutputEncoding pode lançar "handle inválido"
# quando não existe um console de verdade por trás do pipe, se isso falhar,
# segue com o encoding padrão em vez de derrubar o script inteiro.
try {
  $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
  [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
} catch {}

Add-Type -AssemblyName System.Runtime.WindowsRuntime
# Seleciona o overload genérico AsTask(TResult) de IAsyncOperation(TResult) por
# ARIDADE genérica (1 parâmetro de tipo), não pelo nome mangled do tipo, # comparar aquela string exigiria um caractere de crase literal no script, que
# é frágil de embutir vindo de um template string do JS (que também usa crase
# como delimitador de string).
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetGenericArguments().Count -eq 1
})[0]

function Await-WinRT($WinRtTask, $ResultType) {
  $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
  $netTask = $asTask.Invoke($null, @($WinRtTask))
  $netTask.Wait(-1) | Out-Null
  return $netTask.Result
}

[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager,Windows.Media.Control,ContentType=WindowsRuntime] | Out-Null

$manager = Await-WinRT ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])
$session = $manager.GetCurrentSession()

if (-not $session) {
  Write-Output "{}"
  exit 0
}

switch ($Action) {
  "playpause" { $session.TryTogglePlayPauseAsync() | Out-Null; Start-Sleep -Milliseconds 150 }
  "next"      { $session.TrySkipNextAsync() | Out-Null; Start-Sleep -Milliseconds 150 }
  "previous"  { $session.TrySkipPreviousAsync() | Out-Null; Start-Sleep -Milliseconds 150 }
  default     {}
}

$props = Await-WinRT ($session.TryGetMediaPropertiesAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
$playback = $session.GetPlaybackInfo()
$isPlaying = $playback.PlaybackStatus -eq [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionPlaybackStatus]::Playing

# Capa do álbum: o SMTC entrega como IRandomAccessStreamReference, então tem
# que abrir o stream e ler os bytes na mão. Tudo dentro de try/catch próprio, # thumbnail é um extra, nunca pode derrubar a leitura de titulo/artista.
$albumArt = ""
try {
  if ($props.Thumbnail) {
    [Windows.Storage.Streams.DataReader,Windows.Storage.Streams,ContentType=WindowsRuntime] | Out-Null
    $streamRef = $props.Thumbnail
    $stream = Await-WinRT ($streamRef.OpenReadAsync()) ([Windows.Storage.Streams.IRandomAccessStreamWithContentType])
    if ($stream -and $stream.Size -gt 0) {
      $size = [uint32]$stream.Size
      $reader = New-Object Windows.Storage.Streams.DataReader($stream.GetInputStreamAt(0))
      Await-WinRT ($reader.LoadAsync($size)) ([uint32]) | Out-Null
      $bytes = New-Object byte[] $size
      $reader.ReadBytes($bytes)
      $reader.Dispose()
      $stream.Dispose()
      $albumArt = [Convert]::ToBase64String($bytes)
    }
  }
} catch {
  $albumArt = ""
}

$result = [PSCustomObject]@{
  title     = $props.Title
  artist    = $props.Artist
  isPlaying = $isPlaying
  albumArt  = $albumArt
}
$result | ConvertTo-Json -Compress
`;

async function runPowerShell(action: 'state' | 'playpause' | 'next' | 'previous'): Promise<MediaState | null> {
  const dir = await mkdtemp(join(tmpdir(), 'bolha-media-'));
  const scriptPath = join(dir, 'media.ps1');
  await writeFile(scriptPath, PS_SCRIPT, 'utf-8');

  try {
    const output = await new Promise<string>((resolve, reject) => {
      const child = spawn('powershell.exe', [
        '-NoProfile',
        '-NonInteractive',
        '-ExecutionPolicy', 'Bypass',
        '-File', scriptPath,
        '-Action', action,
      ], { windowsHide: true });
      const timeout = setTimeout(() => { child.kill(); reject(new Error('O player não respondeu.')); }, 8000);
      child.once('close', () => clearTimeout(timeout));
      child.once('error', () => clearTimeout(timeout));
      let stdout = '';
      let stderr = '';
      child.stdout.on('data', (d) => { stdout += d.toString(); if (stdout.length > 4000000) { child.kill(); reject(new Error('Resposta de mídia inválida.')); } });
      child.stderr.on('data', (d) => { stderr += d.toString(); });
      child.on('error', reject);
      child.on('close', (code) => {
        if (code !== 0) reject(new Error(`powershell saiu com código ${code}: ${stderr}`));
        else resolve(stdout);
      });
    });

    const trimmed = output.trim();
    if (!trimmed || trimmed === '{}') return null;
    const parsed = JSON.parse(trimmed);
    const rawArt = typeof parsed.albumArt === 'string' ? parsed.albumArt : '';
    return {
      title: parsed.title ?? '',
      artist: parsed.artist ?? '',
      isPlaying: Boolean(parsed.isPlaying),
      albumArt: rawArt ? `data:image/jpeg;base64,${rawArt}` : null,
    };
  } catch (err) {
    console.error('[Bolha] mediaSession falhou:', err);
    return null;
  } finally {
    await rm(dir, { recursive: true, force: true }).catch(() => {});
  }
}

export function getMediaState(): Promise<MediaState | null> {
  return runPowerShell('state');
}

export function mediaPlayPause(): Promise<MediaState | null> {
  return runPowerShell('playpause');
}

export function mediaNext(): Promise<MediaState | null> {
  return runPowerShell('next');
}

export function mediaPrevious(): Promise<MediaState | null> {
  return runPowerShell('previous');
}
