# SPDX-License-Identifier: GPL-3.0-or-later
"""Sessões locais do Windows. Metadados voláteis, sem API do Spotify."""
import asyncio
import queue
import threading

SPOTIFY_APPS = frozenset({
    'spotify.exe', 'spotify', 'spotifyab.spotifymusic_zpdnekdrzrea0!spotify',
})


def clean_label(value, limit=64):
    return ' '.join(''.join(c if c.isprintable() else ' ' for c in value).split())[:limit]


async def session_operation(manager_class, status, action):
    manager = await manager_class.request_async()
    if action == 'toggle':
        session = manager.get_current_session()
        if session is None:
            return False
        playback = session.get_playback_info()
        if playback is None:
            return False
        if playback.playback_status == status.PLAYING and playback.controls.is_pause_enabled:
            return await session.try_pause_async()
        if playback.playback_status in (status.PAUSED, status.STOPPED, status.OPENED) and playback.controls.is_play_enabled:
            return await session.try_play_async()
        return False

    for session in manager.get_sessions():
        if session.source_app_user_model_id.casefold() not in SPOTIFY_APPS:
            continue
        playback = session.get_playback_info()
        if playback is None or playback.playback_status != status.PLAYING:
            continue
        properties = await session.try_get_media_properties_async()
        if properties is not None:
            track = clean_label(properties.title), clean_label(properties.artist)
            if any(track):
                return track
    return None


def _operation(action):
    import winrt.windows.foundation  # Registra as projeções de IAsyncOperation.
    import winrt.windows.foundation.collections
    import winrt.windows.storage.streams
    from winrt.runtime import ApartmentType, init_apartment, uninit_apartment
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as Manager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as Status,
    )
    init_apartment(ApartmentType.MULTI_THREADED)
    try:
        return asyncio.run(asyncio.wait_for(session_operation(Manager, Status, action), 4))
    finally:
        uninit_apartment()


class Media:
    def __init__(self):
        self.results = queue.SimpleQueue()
        self.busy = False
        self.toggle_pending = False
        self.next_poll = 0.
        self.status = 'Aguardando sessão de mídia do Windows.'

    def request(self, action):
        if self.busy:
            if action == 'toggle':
                self.toggle_pending = True
            return
        self.busy = True
        threading.Thread(target=self._run, args=(action,), daemon=True, name='bolha-media').start()

    def _run(self, action):
        try:
            result = _operation(action)
        except (TimeoutError, OSError, RuntimeError, ImportError, TypeError, AttributeError):
            self.results.put((action, False, None))
        else:
            self.results.put((action, True, result))

    def poll(self, now, read_spotify):
        track = None
        try:
            action, success, result = self.results.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            if not success:
                self.status = 'Sessões de mídia indisponíveis no Windows.'
            elif action == 'toggle':
                self.status = ('Controle enviado à sessão de mídia atual.' if result else
                               'Nenhuma sessão atual aceita o comando de reprodução.')
            else:
                self.status = 'Spotify em reprodução.' if result else 'Spotify em repouso ou fechado.'
                if read_spotify:
                    track = result
        if self.toggle_pending and not self.busy:
            self.toggle_pending = False
            self.request('toggle')
        if read_spotify and now >= self.next_poll and not self.busy:
            self.next_poll = now + 2.
            self.request('spotify')
        return track


class SpotifyReaction:
    def __init__(self):
        self.last_track = None
        self.next_reaction = 0.

    def observe(self, track, now, can_react):
        if not track:
            return None
        track_id = tuple(value.casefold() for value in track)
        if track_id == self.last_track:
            return None
        self.last_track = track_id
        if not can_react or now < self.next_reaction:
            return None
        self.next_reaction = now + 300
        title, artist = track
        if artist and title:
            return f'“{title}” de {artist}? Minhas orelhas já entraram na dança.'
        if artist:
            return f'{artist} tocando! Minhas orelhas aprovaram.'
        return f'“{title}” tocando! Vou dar uma dançadinha.'
