# SPDX-License-Identifier: GPL-3.0-only
"""Conversão local com backup verificável antes de alterar arquivos existentes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import uuid

SCHEMA = 1
MARKER = 'native-migration.json'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def atomic_json(path, value):
    path = Path(path)
    text = json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + '\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix=path.name+'.', suffix='.tmp', delete=False) as stream:
            name = Path(stream.name)
            stream.write(text);stream.flush();os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if name is not None: name.unlink(missing_ok=True)


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare_data(data_dir):
    """Migração idempotente; qualquer falha anterior à confirmação preserva a origem."""
    root = Path(data_dir)
    root.mkdir(parents=True, exist_ok=True)
    marker = root / MARKER
    try:
        saved = read_json(marker)
        if isinstance(saved, dict) and saved.get('schemaVersion') == SCHEMA:
            return root / 'brain'
    except (FileNotFoundError, ValueError):
        pass
    files = []
    for name in ('config.json','pending-update.json','update-deferred.json'):
        source = root / name
        if source.is_symlink(): raise ValueError('Arquivo de dados não pode ser um atalho: '+name)
        if source.is_file(): files.append(source)
    brain = root / 'brain'
    if brain.is_symlink(): raise ValueError('A pasta de memória não pode ser um atalho.')
    if brain.exists():
        for source in brain.rglob('*'):
            if source.is_symlink(): raise ValueError('Atalho dentro da memória: '+source.name)
            if source.is_file(): files.append(source)
    backup = None
    manifest = {}
    if files:
        backup = root / 'backups' / ('native-0.3.0-'+str(time.time_ns())+'-'+uuid.uuid4().hex[:8])
        backup.mkdir(parents=True)
        for source in files:
            relative = source.relative_to(root)
            target = backup / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = sha256(source)
            shutil.copy2(source, target)
            if sha256(target) != digest or sha256(source) != digest:
                raise OSError('A validação do backup falhou: '+str(relative))
            manifest[str(relative)] = digest
        atomic_json(backup / 'manifest.json', manifest)
    # Compatibilidade com instalações anteriores ao nome Bolha, sem sobrescrever memória nova.
    legacy = brain / 'drippy'
    if legacy.is_dir() and not (brain / 'bolha').exists():
        legacy.rename(brain / 'bolha')
    brain.mkdir(exist_ok=True)
    atomic_json(marker, {'schemaVersion':SCHEMA,'backup':str(backup) if backup else None,
                         'files':manifest,'completedAt':time.time()})
    return brain
