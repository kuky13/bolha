# SPDX-License-Identifier: GPL-3.0-or-later
"""Obtém os binários e as fontes correspondentes, fixados por SHA-256."""
import hashlib
from pathlib import Path
import shutil
from urllib.request import urlopen
from zipfile import ZipFile

UPSTREAM = 'https://github.com/krisgfx9/Wireless-Device-Battery-Monitor'
RELEASE = UPSTREAM + '/releases/download/v1.1.0/'
COMMIT = '7cc44f2b2c63341e2b478463c7467759837a74a9'
PORTABLE = 'BatteryHub-1.1.0-portable.zip'
PORTABLE_SHA = '7a97a1ff0aefa895386077093b23a714df549a08fad3b1b9c37ccf2100a27026'
SOURCES = {
    'BatteryHub-1.1.0-source.tar.gz': (
        'https://codeload.github.com/krisgfx9/Wireless-Device-Battery-Monitor/tar.gz/' + COMMIT,
        '2737323731e53ab8d936b2fa5c95ab84f2cb7c6abb3d05d3bf150af8c637f108',
    ),
    'headsetcontrol-4.3.0.tar.gz': (
        RELEASE + 'headsetcontrol-4.3.0.tar.gz',
        '918dcacf8aef347744b36b2d259d76880fa64b3869f0f8ef26b6576b873d28a7',
    ),
}
BINARIES = {
    'BatteryHub.exe': 'c0c4d87299b6a97f610aedcf6916870b1226d59d9cf586484ff9fe63f4b8a924',
    'headsetcontrol.exe': 'e371da043710ddb8fc70af77f2ccad1cd03f8c6f49ba423e08764ad7a94a3c40',
}
NOTICES = ('LICENSE.txt', 'THIRD_PARTY_NOTICES.txt')


def download(path, url, checksum):
    if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == checksum:
        return path
    with urlopen(url, timeout=30) as response:
        raw = response.read(24*1024*1024 + 1)
    if len(raw) > 24*1024*1024 or hashlib.sha256(raw).hexdigest() != checksum:
        raise ValueError('SHA-256 não confere: ' + path.name)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(raw)
    temporary.replace(path)
    return path


def verify(folder):
    for name, checksum in BINARIES.items():
        target = folder / name
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != checksum:
            raise ValueError('Binário de bateria não confere: ' + name)
    for name in NOTICES:
        if not (folder/name).is_file():
            raise ValueError('Aviso de licença ausente: ' + name)


def prepare(cache, folder, release):
    cache.mkdir(parents=True, exist_ok=True)
    for name, (url, checksum) in SOURCES.items():
        path = download(cache/name, url, checksum)
        shutil.copy2(path, release/name)
    if folder is None:
        return
    archive = download(cache/PORTABLE, RELEASE+PORTABLE, PORTABLE_SHA)
    folder.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive) as package:
        entries = {Path(item.filename).name: item for item in package.infolist() if not item.is_dir()}
        for name in (*BINARIES, *NOTICES):
            (folder/name).write_bytes(package.read(entries[name]))
    verify(folder)
