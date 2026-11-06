# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""NSIS portable oficial, fixado por SHA-256; não instala nada no sistema."""
import argparse
import hashlib
from pathlib import Path
import tempfile
from urllib.request import urlopen
import zipfile

VERSION='3.11'
URL='https://downloads.sourceforge.net/project/nsis/NSIS%203/3.11/nsis-3.11.zip'
# Publicado pelo projeto em https://sourceforge.net/projects/nsis/files/NSIS%203/3.11/nsis-3.11.zip/download
SHA256='c7d27f780ddb6cffb4730138cd1591e841f4b7edb155856901cdf5f214394fa1'


def fetch(destination):
    destination=Path(destination).resolve();destination.mkdir(parents=True,exist_ok=True)
    executable=destination/f'nsis-{VERSION}'/'makensis.exe'
    if executable.exists():return executable
    with tempfile.TemporaryFile() as archive:
        with urlopen(URL,timeout=60) as response:
            size=0
            while chunk:=response.read(128*1024):
                size+=len(chunk)
                if size>10*1024*1024:raise ValueError('Arquivo NSIS maior que o esperado.')
                archive.write(chunk)
        archive.seek(0)
        if hashlib.file_digest(archive,'sha256').hexdigest()!=SHA256:raise ValueError('SHA-256 do NSIS inválido.')
        archive.seek(0)
        with zipfile.ZipFile(archive) as source:
            for entry in source.infolist():
                target=(destination/entry.filename).resolve()
                if not target.is_relative_to(destination):raise ValueError('Caminho inválido no NSIS.')
            source.extractall(destination)
    if not executable.exists():raise ValueError('Compilador NSIS ausente.')
    return executable


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('destination',nargs='?',default='build/tools')
    print(fetch(parser.parse_args().destination))
