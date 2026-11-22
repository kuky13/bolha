# SPDX-License-Identifier: GPL-3.0-or-later
"""Empacota a cópia arquivada do BatteryHub e suas fontes, fixadas por SHA-256."""
import hashlib
from pathlib import Path
import shutil
from zipfile import ZipFile

ARCHIVES = Path(__file__).resolve().parents[1] / 'third_party' / 'batteryhub'
PORTABLE = 'BatteryHub-1.1.0-portable.zip'
PORTABLE_SHA = '7a97a1ff0aefa895386077093b23a714df549a08fad3b1b9c37ccf2100a27026'
SOURCES = {
    'BatteryHub-1.1.0-source.tar.gz': '2737323731e53ab8d936b2fa5c95ab84f2cb7c6abb3d05d3bf150af8c637f108',
    'headsetcontrol-4.3.0.tar.gz': '918dcacf8aef347744b36b2d259d76880fa64b3869f0f8ef26b6576b873d28a7',
}
BINARIES = {
    'BatteryHub.exe': 'c0c4d87299b6a97f610aedcf6916870b1226d59d9cf586484ff9fe63f4b8a924',
    'headsetcontrol.exe': 'e371da043710ddb8fc70af77f2ccad1cd03f8c6f49ba423e08764ad7a94a3c40',
}
NOTICES = ('LICENSE.txt', 'THIRD_PARTY_NOTICES.txt')


def verify_checksum(path, checksum):
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
        raise ValueError('SHA-256 não confere: ' + path.name)


def verify(folder):
    for name, checksum in BINARIES.items():
        verify_checksum(folder/name, checksum)
    for name in NOTICES:
        if not (folder/name).is_file():
            raise ValueError('Aviso de licença ausente: ' + name)


def prepare(folder, release):
    for name, checksum in SOURCES.items():
        path = ARCHIVES / name
        verify_checksum(path, checksum)
        shutil.copy2(path, release/name)
    if folder is None:
        return
    archive = ARCHIVES / PORTABLE
    verify_checksum(archive, PORTABLE_SHA)
    folder.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive) as package:
        for name in (*BINARIES, *NOTICES):
            (folder/name).write_bytes(package.read(name))
    verify(folder)
