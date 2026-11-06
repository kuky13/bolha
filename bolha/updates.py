# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Atualização GitHub em segundo plano, sem credenciais e sem bloquear o desenho Qt."""
from concurrent.futures import Future
from dataclasses import dataclass
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import threading
import time
import uuid
from urllib.error import HTTPError
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from PySide6.QtCore import QObject, QCoreApplication, QTimer, Signal
from .installation import (CHECK_INTERVAL, COUNTDOWN, DEFER_INTERVAL, cache_directory,
                           cached_installer, cleanup_applied_update, cleanup_recovery, compare_versions,
                           launch_installer, read_deferral, record_update, test_mode, version_tuple)
from .migration import atomic_json, read_json

REPOSITORY = 'kuky13/bolha'
RELEASE_URL = 'https://api.github.com/repos/' + REPOSITORY + '/releases/latest'
MAX_INSTALLER = 1024 * 1024 * 1024
ALLOWED_HOSTS = frozenset(('github.com', 'api.github.com', 'release-assets.githubusercontent.com',
                           'objects.githubusercontent.com'))
LOG = logging.getLogger(__name__)


class LocalUpdateLog(logging.Handler):
    def emit(self, record):
        try:
            from pestinha.log import log
            log('[atualização]', record.getMessage())
        except (ImportError, OSError, ValueError):
            pass


LOG.addHandler(LocalUpdateLog())
LOG.propagate = False


class UpdateCancelled(Exception):
    pass


@dataclass(frozen=True)
class Release:
    version: str
    name: str
    url: str
    size: int
    sha256: str


def validate_url(url, test_base=None):
    parsed = urlsplit(url)
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError('Endereço de atualização inválido.')
    if test_base:
        origin = urlsplit(test_base)
        if (origin.scheme != 'http' or origin.hostname != '127.0.0.1'
                or parsed.scheme != 'http' or parsed.hostname != '127.0.0.1'
                or parsed.port != origin.port):
            raise ValueError('O feed de teste precisa continuar no mesmo servidor local.')
    elif parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.port not in (None, 443):
        raise ValueError('Endereço de atualização fora do GitHub.')
    return url


class SafeRedirect(HTTPRedirectHandler):
    def __init__(self, test_base=None):
        self.test_base = test_base

    def redirect_request(self, request, response, code, message, headers, newurl):
        validate_url(newurl, self.test_base)
        return super().redirect_request(request, response, code, message, headers, newurl)


class Transport:
    def __init__(self, test_base=None, cancelled=None):
        self.test_base = test_base
        self.cancelled = cancelled or threading.Event()
        self.opener = build_opener(SafeRedirect(test_base))

    def open(self, url):
        validate_url(url, self.test_base)
        if self.cancelled.is_set():
            raise UpdateCancelled()
        response = self.opener.open(Request(url, headers={'User-Agent': 'Bolha-native-updater',
                                                         'Accept': 'application/vnd.github+json'}), timeout=15)
        validate_url(response.geturl(), self.test_base)
        return response

    def read(self, url, limit):
        with self.open(url) as response:
            content = response.read(limit + 1)
        if len(content) > limit:
            raise ValueError('Metadados da atualização excedem o limite.')
        return content

    def download(self, release, output, progress=None):
        digest = hashlib.sha256()
        size = 0
        created = False
        try:
            descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
            created = True
            with os.fdopen(descriptor, 'wb') as target, self.open(release.url) as response:
                declared = response.headers.get('Content-Length')
                if declared is not None and int(declared) != release.size:
                    raise ValueError('Tamanho informado pelo servidor não confere.')
                while True:
                    if self.cancelled.is_set():
                        raise UpdateCancelled()
                    chunk = response.read(128 * 1024)
                    if not chunk: break
                    size += len(chunk)
                    if size > release.size:
                        raise ValueError('Download maior que o instalador publicado.')
                    target.write(chunk); digest.update(chunk)
                    if progress: progress(size / release.size * 100)
                target.flush(); os.fsync(target.fileno())
            if size != release.size or digest.hexdigest() != release.sha256:
                raise ValueError('A integridade do instalador não confere.')
        except BaseException:
            if created: Path(output).unlink(missing_ok=True)
            raise


def parse_checksums(content):
    checksums = {}
    for line in content.decode('utf-8-sig').splitlines():
        if not line.strip(): continue
        match = re.fullmatch(r'([0-9a-fA-F]{64}) [ *]([A-Za-z0-9_.-]+)', line)
        if not match or match[2] in checksums or match[2] in ('.', '..'):
            raise ValueError('Manifesto SHA-256 inválido.')
        checksums[match[2]] = match[1].lower()
    return checksums


def release_asset(data, name, version, transport):
    assets = [item for item in data.get('assets', []) if isinstance(item, dict) and item.get('name') == name]
    if len(assets) != 1:
        raise ValueError('Arquivo obrigatório ausente ou duplicado: ' + name)
    asset = assets[0]
    size = asset.get('size')
    if type(size) is not int or not 0 < size <= MAX_INSTALLER:
        raise ValueError('Tamanho de arquivo inválido.')
    url = asset.get('browser_download_url', '')
    validate_url(url, transport.test_base)
    if not transport.test_base:
        expected = f'https://github.com/{REPOSITORY}/releases/download/v{version}/{quote(name)}'
        if url != expected:
            raise ValueError('Arquivo não pertence à versão publicada da Bolha.')
    return asset


def find_release(transport, current_version):
    url = urljoin(transport.test_base.rstrip('/') + '/', 'release.json') if transport.test_base else RELEASE_URL
    try:
        data = json.loads(transport.read(url, 2 * 1024 * 1024))
    except HTTPError as error:
        if error.code == 404: return None
        raise
    if not isinstance(data, dict):
        raise ValueError('Resposta de versão inválida.')
    if data.get('draft') or data.get('prerelease'): return None
    tag = data.get('tag_name', '')
    if not isinstance(tag, str) or not tag.startswith('v'):
        raise ValueError('Tag de versão inválida.')
    version = tag[1:]
    if compare_versions(version, current_version) <= 0: return None
    name = f'Bolha-Setup-{version}-x64.exe'
    installer = release_asset(data, name, version, transport)
    manifest = release_asset(data, 'SHA256SUMS.txt', version, transport)
    if manifest['size'] > 1024 * 1024:
        raise ValueError('Manifesto muito grande.')
    content = transport.read(manifest['browser_download_url'], 1024 * 1024)
    if len(content) != manifest['size']:
        raise ValueError('Tamanho do manifesto não confere.')
    checksum = parse_checksums(content).get(name)
    if not checksum:
        raise ValueError('Checksum do instalador ausente.')
    # O GitHub também informa SHA-256 em releases recentes. Se presente, ambos devem concordar.
    digest = installer.get('digest')
    if digest and digest != 'sha256:' + checksum:
        raise ValueError('Manifesto diverge do digest publicado pelo GitHub.')
    return Release(version, name, installer['browser_download_url'], installer['size'], checksum)


def verify_file(path, size, checksum):
    path = Path(path)
    if type(size) is not int or not 0 < size <= MAX_INSTALLER or not re.fullmatch('[0-9a-f]{64}', str(checksum)):
        raise ValueError('Registro de integridade inválido.')
    if path.stat().st_size != size:
        raise ValueError('O tamanho do instalador mudou.')
    with path.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != checksum:
            raise ValueError('O instalador foi alterado depois do download.')
    return path


def fetch_update(transport, current_version, data_dir, cache_root, progress=None):
    release = find_release(transport, current_version)
    if release is None: return None
    directory = Path(cache_root) / release.version
    directory.mkdir(parents=True, exist_ok=True)
    installer = cached_installer(cache_root, directory / release.name)
    # Um download de outra execução só é usado depois de verificar novamente tamanho e hash.
    try:
        verify_file(installer, release.size, release.sha256)
    except (OSError, ValueError):
        part = installer.with_name(installer.name + '.' + uuid.uuid4().hex + '.part')
        try:
            transport.download(release, part, progress)
            os.replace(part, installer)
        finally:
            part.unlink(missing_ok=True)
    record_update(data_dir, release.version, installer, cache_root, size=release.size, sha256=release.sha256)
    return dict(version=release.version, installer=str(installer), size=release.size, sha256=release.sha256)


class Updater(QObject):
    changed = Signal(dict)
    _completed = Signal(object)
    _progress = Signal(dict)

    def __init__(self, data_dir, version, before_install, on_recover, parent=None):
        super().__init__(parent)
        version_tuple(version)
        self.data_dir, self.version = Path(data_dir), version
        self.before_install, self.on_recover = before_install, on_recover
        self.cache_root = cache_directory(self.data_dir)
        self.state = {'phase': 'idle'}
        self._stopped, self._checking = False, False
        self._cancelled = threading.Event()
        test_feed = os.environ.get('BOLHA_TEST_UPDATE_URL') if test_mode() else None
        if test_feed: validate_url(test_feed, test_feed)
        self.transport = Transport(test_feed, self._cancelled)
        self.enabled = (os.name == 'nt' and (getattr(__import__('sys'), 'frozen', False) or test_mode())
                        and (not test_mode() or bool(test_feed)))
        self._deferred_version, self._deferred_until = read_deferral(self.data_dir)
        self._completed.connect(self._apply)
        self._progress.connect(self._send)
        self._check_timer = QTimer(self); self._check_timer.setInterval(CHECK_INTERVAL)
        self._check_timer.timeout.connect(self.check)
        self._install_timer = QTimer(self); self._install_timer.setSingleShot(True)
        self._install_timer.timeout.connect(self.install)
        self._cleanup_timer = QTimer(self); self._cleanup_timer.setSingleShot(True)
        self._cleanup_timer.setInterval(COUNTDOWN); self._cleanup_timer.timeout.connect(self.healthy)
        self._pending = None

    def _send(self, state):
        if not self._stopped:
            self.state = dict(state); self.changed.emit(dict(state))
            if test_mode() and os.environ.get('BOLHA_TEST_STATUS') == '1':
                try: atomic_json(self.data_dir / 'update-state.json', state)
                except OSError: pass

    def _background(self, kind, operation):
        def run():
            try: result = (kind, operation(), None)
            except Exception as error: result = (kind, None, error)
            if not self._stopped: self._completed.emit(result)
        threading.Thread(target=run, name='Bolha-update-' + kind, daemon=True).start()

    def start(self):
        if self.enabled and not self._stopped:
            self._checking = True
            self._background('resume', self._resume)
            self._check_timer.start()

    def _resume(self):
        try: pending = read_json(self.data_dir / 'pending-update.json')
        except FileNotFoundError: return None
        if not isinstance(pending, dict): raise ValueError('Registro pendente inválido.')
        if compare_versions(pending.get('version'), self.version) <= 0: return None
        # Marcadores Electron não têm SHA-256: precisam ser conferidos no feed antes de executar.
        if not all(key in pending for key in ('size', 'sha256')): return None
        verify_file(cached_installer(self.cache_root, pending['installer']), pending['size'], pending['sha256'])
        return pending

    def check(self):
        if not self.enabled:
            self._send({'phase': 'idle', 'message': 'Atualizações disponíveis no aplicativo instalado para Windows.'})
            return
        if self._stopped or self._checking or self.state['phase'] in ('downloading', 'ready', 'installing', 'verifying'):
            return
        self._checking = True
        self._send({'phase': 'checking'})
        last_progress = [0.]
        def progress(percent):
            now = time.monotonic()
            if percent >= 100 or now - last_progress[0] >= .15:
                last_progress[0] = now
                self._progress.emit({'phase': 'downloading', 'percent': percent})
        self._background('check', lambda: fetch_update(self.transport, self.version, self.data_dir,
                                                       self.cache_root, progress))

    def _schedule(self, deferred=False):
        if self.state['phase'] != 'ready': return
        now = int(time.time() * 1000)
        deadline = now + (DEFER_INTERVAL if deferred else COUNTDOWN)
        if self.state['version'] == self._deferred_version:
            deadline = max(deadline, self._deferred_until)
        if deferred:
            try:
                atomic_json(self.data_dir / 'update-deferred.json', dict(version=self.state['version'], until=deadline))
            except OSError as error:
                LOG.warning('Falha ao guardar adiamento: %s', error)
                self._install_timer.stop()
                self._send(dict(self.state, installAt=None, message='Não consegui guardar o adiamento. Atualização pausada.'))
                return
            self._deferred_version, self._deferred_until = self.state['version'], deadline
        self._send(dict(self.state, installAt=deadline))
        self._install_timer.start(max(0, deadline - now))

    def snapshot(self):
        return dict(self.state)

    def defer(self):
        self._schedule(True)

    postpone = defer

    def install(self):
        if self.state['phase'] != 'ready' or not self._pending: return
        self._install_timer.stop()
        self._send(dict(self.state, phase='verifying', message='Conferindo o instalador…'))
        pending = dict(self._pending)
        self._background('install', lambda: verify_file(cached_installer(self.cache_root, pending['installer']),
                                                       pending['size'], pending['sha256']))

    def _apply(self, event):
        if self._stopped: return
        kind, value, error = event
        if kind == 'cleanup':
            if error or value is False:
                if error: LOG.warning('Limpeza da atualização adiada: %s', error)
                self._cleanup_timer.start()
            return
        if kind in ('check', 'resume'): self._checking = False
        if error:
            if isinstance(error, UpdateCancelled): return
            LOG.warning('Atualização: %s', error)
            if kind == 'flushed': self.on_recover()
            self._send({'phase': 'error', 'message': 'Não foi possível atualizar agora. Você pode continuar usando a Bolha.'})
            return
        if kind in ('check', 'resume'):
            if value is None:
                if kind == 'resume': self.check()
                else: self._send({'phase': 'idle', 'message': 'Você está na versão mais recente.'})
            else:
                self._pending = value
                self._send({'phase': 'ready', 'version': value['version']}); self._schedule()
        elif kind in ('install', 'flushed'):
            try:
                if kind == 'install':
                    prepared = self.before_install()
                    if isinstance(prepared, Future):
                        self._send(dict(self.state, message='Salvando o aprendizado…'))
                        def await_flush():
                            if prepared.result(timeout=15) is False:
                                raise OSError('Não foi possível salvar o aprendizado.')
                            return value
                        self._background('flushed', await_flush)
                        return
                    if prepared is False:
                        raise OSError('Não foi possível salvar o aprendizado antes da instalação.')
                launch_installer(value, self.cache_root)
                self._send(dict(self.state, phase='installing', message='Instalando. A Bolha vai reabrir em instantes.'))
                QCoreApplication.instance().quit()
            except Exception as install_error:
                LOG.warning('Instalação: %s', install_error)
                self.on_recover()
                self._send({'phase': 'error', 'message': 'Instalação adiada. Seu aplicativo continua disponível.'})

    def healthy(self):
        # O chamador já confirmou o primeiro desenho e um ciclo saudável do cérebro.
        def cleanup():
            cleaned = cleanup_applied_update(self.data_dir, self.version, self.cache_root)
            import sys
            if cleaned and getattr(sys, 'frozen', False):
                return cleanup_recovery(self.data_dir, Path(sys.executable).parent, self.version)
            return cleaned
        self._background('cleanup', cleanup)

    def stop(self):
        self._stopped = True; self._cancelled.set()
        for timer in (self._check_timer, self._install_timer, self._cleanup_timer): timer.stop()
