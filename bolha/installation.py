# SPDX-License-Identifier: GPL-3.0-only
"""Contratos de instalação, inicialização e limpeza compatíveis com a Bolha 0.1/0.2."""
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from .migration import atomic_json, read_json

APP_ID = 'solutions.kuky.bolha'
INSTALLER_GUID = 'efdda9e4-adbf-5481-bf79-1ee5a33cbceb'
COUNTDOWN = 30_000
CHECK_INTERVAL = 6 * 60 * 60 * 1000
DEFER_INTERVAL = 60 * 60 * 1000


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{1,6}\.\d{1,6}\.\d{1,6}', value):
        raise ValueError('Versão inválida.')
    return tuple(map(int, value.split('.')))


def compare_versions(left, right):
    a, b = version_tuple(left), version_tuple(right)
    return (a > b) - (a < b)


def test_mode():
    return os.environ.get('BOLHA_TEST') == '1'


def data_directory():
    override = os.environ.get('BOLHA_TEST_USER_DATA') if test_mode() else None
    if override:
        return Path(override)
    if sys.platform == 'win32':
        return Path(os.environ['APPDATA']) / 'bolha'
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'bolha'


def cache_directory(data_dir):
    # Os testes nunca compartilham o cache real nem as chaves de inicialização.
    if test_mode():
        legacy = os.environ.get('BOLHA_TEST_LEGACY_CACHE')
        return Path(legacy) if legacy else Path(data_dir) / 'update-cache'
    local = os.environ.get('LOCALAPPDATA')
    return (Path(local) if local else Path(data_dir).parent / 'Local') / 'bolha-updater'


def cached_installer(cache_root, installer):
    """Resolve links/junctions antes da comparação; só descendentes .exe são aceitos."""
    root = Path(cache_root).resolve()
    candidate = Path(installer).resolve()
    if candidate == root or not candidate.is_relative_to(root) or candidate.suffix.lower() != '.exe':
        raise ValueError('Instalador fora do cache da Bolha.')
    return candidate


def record_update(data_dir, version, installer, cache_root, **verified):
    version_tuple(version)
    path = cached_installer(cache_root, installer)
    atomic_json(Path(data_dir) / 'pending-update.json',
                dict(version=version, installer=str(path), **verified))


def cleanup_applied_update(data_dir, current_version, cache_root):
    """Chamado somente após desenho+cérebro saudáveis; suporta o marcador Electron."""
    marker = Path(data_dir) / 'pending-update.json'
    try:
        pending = read_json(marker)
    except FileNotFoundError:
        pending = None
    if pending is not None:
        if not isinstance(pending, dict):
            raise ValueError('Registro de atualização inválido.')
        if compare_versions(current_version, pending.get('version')) < 0:
            return False
        installer = cached_installer(cache_root, pending.get('installer', ''))
        installer.unlink(missing_ok=True)
        if installer.parent.exists():
            for item in installer.parent.iterdir():
                if item.is_file() and not item.is_symlink() and (
                        item.suffix.lower() in ('.part', '.blockmap') or item.name == 'update-info.json'):
                    item.unlink()
        marker.unlink(missing_ok=True)
    deferred = Path(data_dir) / 'update-deferred.json'
    try:
        saved = read_json(deferred)
        if isinstance(saved, dict) and compare_versions(current_version, saved.get('version')) >= 0:
            deferred.unlink(missing_ok=True)
    except FileNotFoundError:
        pass
    return True


def read_deferral(data_dir, now=None):
    now = int(time.time() * 1000) if now is None else now
    try:
        saved = read_json(Path(data_dir) / 'update-deferred.json')
        version_tuple(saved['version'])
        until = saved['until']
        if type(until) not in (int, float) or not now < until < float('inf'):
            return '', 0
        return saved['version'], min(int(until), now + DEFER_INTERVAL)
    except (OSError, ValueError, TypeError, KeyError):
        return '', 0


def startup_enabled():
    if sys.platform != 'win32' or test_mode():
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
            command = winreg.QueryValueEx(key, 'Bolha')[0]
            return isinstance(command, str) and bool(command)
    except FileNotFoundError:
        return False


def set_startup(enabled):
    if type(enabled) is not bool:
        raise ValueError('Inicialização deve ser verdadeira ou falsa.')
    if sys.platform != 'win32' or test_mode():
        return False
    import winreg
    if enabled and not getattr(sys, 'frozen', False):
        raise ValueError('Inicialização automática exige o aplicativo instalado.')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
        if enabled:
            winreg.SetValueEx(key, 'Bolha', 0, winreg.REG_SZ, '"' + sys.executable + '"')
        else:
            try: winreg.DeleteValue(key, 'Bolha')
            except FileNotFoundError: pass
    return enabled


def launch_installer(installer, cache_root):
    if sys.platform != 'win32':
        raise OSError('O instalador é exclusivo do Windows.')
    path = cached_installer(cache_root, installer)
    args = [str(path), '/S', '--updated', '--force-run']
    if test_mode():
        args.append('/TEST')
    return subprocess.Popen(args, close_fds=True, creationflags=subprocess.DETACHED_PROCESS)


def cleanup_recovery(data_dir, install_dir, current_version):
    """Remove sóarquivos nativos inventariados; instalações Electron/dados extras ficam guardados."""
    import configparser
    import hashlib
    from pathlib import PurePosixPath
    install = Path(install_dir).resolve()
    transaction = install.with_name(install.name + '.transaction.ini')
    try: content = transaction.read_bytes()
    except FileNotFoundError: return True
    text = content.decode('utf-16' if content.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')
    record = configparser.ConfigParser(interpolation=None)
    record.read_string(text)
    version = record.get('recovery','version')
    if compare_versions(current_version,version)<0: return False
    if record.get('recovery','state',fallback='active')!='committed': return False
    raw = Path(record.get('recovery','backup'))
    backup = raw.resolve()
    if (raw.is_symlink() or backup.parent!=install.parent
            or not backup.name.startswith(install.name+'.rollback-') or backup==install):
        raise ValueError('Diretório de recuperação fora da instalação.')
    retained = []
    if backup.exists():
        marker=backup/'bolha-native-installation.flag'
        manifest=backup/'installed-files.json'
        if marker.is_file() and not marker.is_symlink() and marker.read_text(encoding='utf-8')=='bolha-native:solutions.kuky.bolha' and manifest.is_file():
            saved=read_json(manifest)
            if not isinstance(saved,dict) or saved.get('appId')!=APP_ID or not isinstance(saved.get('files'),dict):
                raise ValueError('Inventário da instalação anterior inválido.')
            targets=[]
            for relative, expected in saved['files'].items():
                part=PurePosixPath(relative.replace('\\','/'))
                if part.is_absolute() or ':' in relative or '..' in part.parts or not part.parts:
                    raise ValueError('Caminho inválido no inventário de recuperação.')
                target=backup.joinpath(*part.parts)
                if target.is_symlink() or not target.resolve().is_relative_to(backup):
                    raise ValueError('Atalho no inventário de recuperação.')
                if target.exists():
                    with target.open('rb') as source: actual=hashlib.file_digest(source,'sha256').hexdigest()
                    # Se foi modificado depois, pode conter trabalho do usuário: preserva.
                    if actual==expected:targets.append(target)
            for target in targets: target.unlink(missing_ok=True)
            for name in ('installed-files.json','bolha-native-installation.flag','bolha-test-install.flag','Uninstall Bolha.exe'):
                target=backup/name
                if target.is_file() and not target.is_symlink(): target.unlink()
            for directory in sorted((p for p in backup.rglob('*') if p.is_dir() and not p.is_symlink()), key=lambda p:len(p.parts),reverse=True):
                try:directory.rmdir()
                except OSError:pass
            try:backup.rmdir()
            except OSError:retained.append(str(backup))
        else:
            retained.append(str(backup))
    if retained:
        atomic_json(Path(data_dir)/'installation-recovery.json',dict(version=current_version,retained=retained,
                    message='Backup anterior preservado: contém arquivos legados, modificados ou desconhecidos.'))
    transaction.unlink(missing_ok=True)
    return True
