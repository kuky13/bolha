# SPDX-License-Identifier: GPL-3.0-only
"""SHA-256 nativo e latest.yml SHA-512 compatível com electron-updater 6.8.11."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re


def generate(directory, version):
    if not re.fullmatch(r'\d+\.\d+\.\d+', version): raise ValueError('Versão inválida.')
    directory = Path(directory)
    name = f'Bolha-Setup-{version}-x64.exe'
    installer = directory / name
    with installer.open('rb') as source:
        sha512 = base64.b64encode(hashlib.file_digest(source, 'sha512').digest()).decode('ascii')
    size = installer.stat().st_size
    # URL relativa, path/sha512 legados e files[] para atualização Electron->Qt sem blockmap.
    (directory/'latest.yml').write_text(
        f'version: {version}\nfiles:\n  - url: {name}\n    sha512: {sha512}\n    size: {size}\n'
        f'path: {name}\nsha512: {sha512}\nreleaseDate: "{datetime.now(timezone.utc).isoformat()}"\n',encoding='utf-8')
    files = [installer, directory/'latest.yml']
    notice = directory/'THIRD-PARTY-NOTICES.txt'
    if notice.exists(): files.append(notice)
    lines = []
    for path in files:
        with path.open('rb') as source: digest=hashlib.file_digest(source,'sha256').hexdigest()
        lines.append(f'{digest}  {path.name}\n')
    (directory/'SHA256SUMS.txt').write_text(''.join(lines),encoding='utf-8')
    return files


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('version')
    args=parser.parse_args();generate(args.directory,args.version)
