# SPDX-License-Identifier: GPL-3.0-or-later
"""Recebe relatos da Bolha e encaminha para uma instância privada do BugPin."""
import asyncio
from collections import OrderedDict, deque
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import time

from fastapi import FastAPI, HTTPException, Request
import httpx
from starlette.datastructures import UploadFile

from bolha.reports import ATTACHMENTS, MIB, RECEIPT_PATTERN, TOTAL_BYTES

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
windows = OrderedDict()
active = asyncio.Semaphore(4)
ID = re.compile(r'[a-zA-Z0-9_-]{8,64}')


def text_field(data, key, limit, minimum=0):
    value = data.get(key, '')
    if (not isinstance(value, str) or not minimum <= len(value.strip()) <= limit
            or '\x00' in value):
        raise HTTPException(400, 'Campo inválido.')
    return value.strip()


def compatible(suffix, head):
    if suffix == '.png':
        return head.startswith(b'\x89PNG\r\n\x1a\n')
    if suffix in ('.jpg', '.jpeg'):
        return head.startswith(b'\xff\xd8\xff')
    if suffix == '.gif':
        return head[:6] in (b'GIF87a', b'GIF89a')
    if suffix == '.webp':
        return head[:4] == b'RIFF' and head[8:12] == b'WEBP'
    if suffix == '.webm':
        return head[:4] == b'\x1a\x45\xdf\xa3' and b'webm' in head
    return head[4:8] == b'ftyp' and len(head) >= 16


def rate_limit(address):
    now = time.monotonic()
    while windows and (len(windows) > 2048 or now - next(iter(windows.values()))[-1] > 600):
        windows.popitem(last=False)
    entries = windows.setdefault(address, deque())
    while entries and now - entries[0] >= 600:
        entries.popleft()
    windows.move_to_end(address)
    if len(entries) >= 5:
        raise HTTPException(429, 'Limite de envios.', headers={'Retry-After': '600'})
    entries.append(now)


@app.post('/v1/reports', status_code=201)
async def submit(request: Request):
    rate_limit(request.client.host if request.client else 'local')
    if active.locked():
        raise HTTPException(503, 'Aguarde e tente novamente.')
    length = request.headers.get('content-length', '')
    if not length.isascii() or not length.isdecimal() or len(length) > 10:
        raise HTTPException(411, 'Tamanho obrigatório.')
    if not 0 < int(length) <= TOTAL_BYTES + 128 * 1024:
        raise HTTPException(413, 'Envio grande demais.')
    key = os.environ.get('BUGPIN_PROJECT_KEY')
    target = os.environ.get('BUGPIN_URL', '').rstrip('/')
    storage = Path(os.environ.get('BUGPIN_STORAGE', '/bugpin-data'))
    if not key or not target or not storage.is_dir() or shutil.disk_usage(storage).free < 512 * MIB:
        raise HTTPException(503, 'Serviço de relatos indisponível.')
    async with active:
        async with request.form(max_files=3, max_fields=1, max_part_size=64 * 1024) as form:
            try:
                data = json.loads(form.get('data', ''))
            except (ValueError, TypeError):
                raise HTTPException(400, 'Relato inválido.')
            if not isinstance(data, dict) or data.get('consent') is not True:
                raise HTTPException(400, 'Confirmação de envio obrigatória.')
            ident = text_field(data, 'submissionId', 64, 8)
            if not ID.fullmatch(ident):
                raise HTTPException(400, 'Identificador inválido.')
            platform = text_field(data, 'platform', 30)
            if platform not in ('Windows', 'Android', 'Linux'):
                raise HTTPException(400, 'Plataforma inválida.')
            version = text_field(data, 'version', 32)
            title = text_field(data, 'title', 180, 4)
            description = text_field(data, 'description', 4000, 8)
            steps = text_field(data, 'steps', 4000)
            technical = text_field(data, 'technical', 4000)
            errors = text_field(data, 'errors', 4000)
            public_fields = [description, f'Bolha {version} · {platform}']
            for heading, value in (('Como reproduzir', steps), ('Diagnóstico selecionado', technical),
                                   ('Erros selecionados', errors)):
                if value:
                    public_fields.append(f'{heading}\n{value}')
            payload = {
                'title': title, 'description': '\n\n'.join(public_fields), 'locale': 'pt-BR',
                'submissionId': ident,
                'metadata': {
                    'url': 'https://bolha.kuky.solutions/suporte/',
                    'browser': {'name': 'Bolha', 'version': version, 'userAgent': 'Bolha'},
                    'device': {'type': 'mobile' if platform == 'Android' else 'desktop', 'os': platform},
                    'viewport': {'width': 0, 'height': 0, 'devicePixelRatio': 1},
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                },
            }
            files = []
            total = 0
            for index, (field, upload) in enumerate(form.multi_items()):
                if field == 'data':
                    continue
                if field != 'media' or not isinstance(upload, UploadFile):
                    raise HTTPException(400, 'Anexo inválido.')
                suffix = Path(upload.filename or '').suffix.lower()
                spec = ATTACHMENTS.get(suffix)
                if not spec:
                    raise HTTPException(415, 'Formato inválido.')
                size = upload.size or 0
                total += size
                if not 0 < size <= spec[1] or total > TOTAL_BYTES:
                    raise HTTPException(413, 'Anexo grande demais.')
                if not compatible(suffix, await upload.read(512)):
                    raise HTTPException(415, 'O conteúdo não corresponde ao formato.')
                await upload.seek(0)
                files.append(('media', (f'anexo-{index}{suffix}', upload.file, spec[0])))
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    kwargs = {'data': {'data': json.dumps(payload)}, 'files': files} if files else {'json': payload}
                    response = await client.post(target + '/api/widget/submit', headers={'X-Api-Key': key}, **kwargs)
                result = response.json()
                receipt = result.get('reportId', '')
            except (httpx.HTTPError, ValueError, AttributeError):
                raise HTTPException(502, 'Não recebi o protocolo.')
            if response.status_code in (400, 413, 415, 422):
                raise HTTPException(response.status_code, 'O relato ou o anexo foi recusado.')
            if response.status_code == 429:
                raise HTTPException(429, 'Limite de envios.', headers={'Retry-After': '600'})
            if (response.status_code not in (200, 201) or result.get('success') is not True
                    or not isinstance(receipt, str) or not RECEIPT_PATTERN.fullmatch(receipt)):
                raise HTTPException(502, 'Não recebi o protocolo.')
            return {'protocol': receipt}
