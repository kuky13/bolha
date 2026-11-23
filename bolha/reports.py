# SPDX-License-Identifier: GPL-3.0-or-later
"""Envio explícito de relatos. A chave do BugPin fica no servidor."""
import json
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

REPORT_URL = 'https://api.kuky.solutions/bolha/v1/reports'
SUPPORT_URL = 'https://bolha.kuky.solutions/suporte/'
PRIVACY_URL = SUPPORT_URL + '#privacidade'
MIB = 1024 * 1024
ATTACHMENTS = {
    '.png': ('image/png', 5 * MIB), '.jpg': ('image/jpeg', 5 * MIB),
    '.jpeg': ('image/jpeg', 5 * MIB), '.gif': ('image/gif', 5 * MIB),
    '.webp': ('image/webp', 5 * MIB), '.mp4': ('video/mp4', 15 * MIB),
    '.webm': ('video/webm', 15 * MIB), '.mov': ('video/quicktime', 15 * MIB),
}
TOTAL_BYTES = 20 * MIB
RECEIPT_PATTERN = re.compile(r'[A-Za-z0-9_-]{8,96}')


def validate_attachments(paths):
    total = 0
    if len(paths) > 3:
        raise ValueError('Escolha até três anexos.')
    for path in paths:
        spec = ATTACHMENTS.get(path.suffix.lower())
        if not spec or not path.is_file():
            raise ValueError('Escolha uma imagem ou um vídeo compatível.')
        size = path.stat().st_size
        if not 0 < size <= spec[1]:
            raise ValueError('Uma imagem pode ter até 5 MB e um vídeo até 15 MB.')
        total += size
    if total > TOTAL_BYTES:
        raise ValueError('O total de anexos pode ter até 20 MB.')


def technical_summary(version, screen, enabled_modules):
    import platform
    import psutil
    return '\n'.join((
        f'Bolha {version}',
        f'Sistema: {platform.system()} {platform.release()} ({platform.machine()})',
        f'RAM total: {psutil.virtual_memory().total // MIB} MiB',
        f'RAM disponível: {psutil.virtual_memory().available // MIB} MiB',
        f'RAM da Bolha: {psutil.Process().memory_info().rss // MIB} MiB',
        f'Telas: {screen}',
        'Módulos ativos: ' + (', '.join(enabled_modules) or 'nenhum da lista'),
    ))


def error_summary(path, username=''):
    try:
        with Path(path).open('rb') as stream:
            end = stream.seek(0, 2)
            stream.seek(max(0, end - 16384))
            lines = stream.read(16384).decode('utf-8', 'replace').splitlines()
    except OSError:
        return ''
    # Só encaminha os tipos e áreas conhecidos. Mensagens arbitrárias de
    # exceções podem conter caminhos, nomes de programas e credenciais.
    events = []
    for line in lines:
        lower = line.casefold()
        if username and username.casefold() in lower:
            continue
        for key, label in (
            ('não foi possível gravar', 'Falha ao gravar dados locais'),
            ('atualização:', 'Falha na atualização'),
            ('falha na leitura de bateria', 'Falha na leitura de bateria'),
            ('confirmação local falhou', 'Falha na confirmação de abertura'),
            ('traceback', 'Exceção registrada'),
        ):
            if key in lower:
                events.append(label)
                break
    return '\n'.join(events[-12:])


def send_report(payload, paths, endpoint=REPORT_URL):
    validate_attachments(paths)
    boundary = uuid4().hex
    chunks = []
    total = 0
    for index, path in enumerate(paths, 1):
        suffix = path.suffix.lower()
        media_type, limit = ATTACHMENTS[suffix]
        with path.open('rb') as source:
            content = source.read(limit + 1)
        total += len(content)
        if not 0 < len(content) <= limit or total > TOTAL_BYTES:
            raise ValueError('Um anexo mudou ou excedeu o tamanho permitido.')
        chunks.extend((
            f'--{boundary}\r\nContent-Disposition: form-data; name="media"; filename="anexo-{index}{suffix}"\r\n'
            f'Content-Type: {media_type}\r\n\r\n'.encode(), content, b'\r\n',
        ))
    message = json.dumps(payload, ensure_ascii=False).encode()
    header = f'--{boundary}\r\nContent-Disposition: form-data; name="data"\r\n\r\n'.encode()
    request = Request(endpoint, data=b''.join((header, message, b'\r\n', *chunks,
                      f'--{boundary}--\r\n'.encode())),
                      headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}, method='POST')
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read(4097))
    except HTTPError as error:
        if error.code == 429:
            raise ValueError('Muitos envios em pouco tempo. Aguarde alguns minutos.') from error
        if error.code in (400, 413, 415, 422):
            raise ValueError('Confira o texto, o formato e o tamanho dos anexos.') from error
        raise OSError('O serviço de relatos está indisponível. Tente novamente mais tarde.') from error
    receipt = result.get('protocol') if isinstance(result, dict) else None
    if not isinstance(receipt, str) or not RECEIPT_PATTERN.fullmatch(receipt):
        raise OSError('Não recebi o protocolo. Você pode tentar novamente.')
    return receipt
