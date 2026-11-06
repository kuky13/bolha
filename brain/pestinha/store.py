# SPDX-License-Identifier: GPL-3.0-or-later
# Adapted from Pestinha by @mille-okws and contributors; see NOTICE.md.
"""
STORE - a única forma de gravar e ler arquivos de estado.

Escrita atômica (arquivo temporário + troca), leitura tolerante (arquivo
ausente ou corrompido vira o valor padrão, sem derrubar o app) e uma linha
por registro para os históricos. Todos os módulos usam isto.
"""

import json
import os
import shutil
import sys
import time
from pathlib import Path


_dispatcher = None
_read_errors = []
_protected = set()


def set_dispatcher(dispatcher):
    """O runtime pode enfileirar texto imutável; testes puros gravam diretamente."""
    global _dispatcher
    _dispatcher = dispatcher


def read_errors():
    return list(_read_errors)


def clear_protection_after_backup(base):
    """Só chamar após mover o diretório original inteiro para backup confirmado."""
    base=Path(base)
    _protected.difference_update(p for p in tuple(_protected) if p.is_relative_to(base))
    _read_errors[:]=[item for item in _read_errors if not Path(item[0]).is_relative_to(base)]


def write_text(path, text, append=False):
    path = Path(path)
    if path in _protected:
        raise OSError(f'Arquivo protegido após falha de leitura/backup: {path.name}')
    if _dispatcher is not None:
        _dispatcher(path, text, append)
    else:
        atomic_write_text(path, text, append)


def atomic_write_text(path, text, append=False):
    """Executa I/O de um snapshot já serializado; não lê objetos mutáveis do jogo."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path if append else path.with_name(path.name + '.tmp')
    with open(tmp, 'a' if append else 'w', encoding='utf-8', newline='') as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    if not append:
        os.replace(tmp, path)


def write_json(path, data, indent=None):
    """Grava um JSON de forma atômica (arquivo temporário e troca), recusando NaN e infinito."""
    path = Path(path)
    texto = json.dumps(data, ensure_ascii=False, indent=indent, allow_nan=False)   # erro antes de tocar no arquivo
    write_text(path, texto)


def _sem_nan(valor):
    """Recusa NaN e infinito ao gravar ou ler JSON."""
    raise ValueError(f"constante não permitida no JSON: {valor}")


def preserve_invalid(path,reason):
    """Preserva memória semanticamente inválida e impede sobrescrita silenciosa."""
    path=Path(path)
    backup=path.with_name(path.name+'.corrompido.'+str(time.time_ns()))
    try:shutil.copy2(path,backup)
    except OSError:pass
    _protected.add(path);_read_errors.append((str(path),str(reason)))


def read_json(path, default=None):
    """Lê um JSON; se o arquivo não existir ou estiver corrompido, devolve `default` (e guarda o arquivo ruim como .corrompido)."""
    path = Path(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.loads(f.read(), parse_constant=_sem_nan)
    except FileNotFoundError:
        return default
    except OSError as error:
        _protected.add(path)
        _read_errors.append((str(path),str(error)))
        return default
    except ValueError as error:
        backup = path.with_name(path.name + '.corrompido')
        if backup.exists(): backup = path.with_name(path.name + '.corrompido.' + str(time.time_ns()))
        try:
            shutil.copy2(path, backup)
        except OSError:
            _protected.add(path)
        _read_errors.append((str(path),str(error)))
        return default


def apagar_pasta(path):
    """Apaga uma pasta inteira; devolve os caminhos que não deu para apagar (lista vazia = tudo certo).

    Python 3.12+ usa `onexc` (o `onerror` está obsoleto lá); o 3.11 só conhece `onerror`.
    As duas recebem (função, caminho, erro), então o mesmo callback serve.
    """
    falhas = []
    chave = "onexc" if sys.version_info >= (3, 12) else "onerror"
    shutil.rmtree(path, **{chave: lambda _f, caminho, _e: falhas.append(str(caminho))})
    return falhas


def pasta_gravavel(pasta):
    """Diz se dá para criar e gravar arquivos na pasta (criando-a, se preciso)."""
    teste = Path(pasta) / ".teste_de_gravacao"
    try:
        teste.parent.mkdir(parents=True, exist_ok=True)
        teste.write_bytes(b"")
        teste.unlink()
    except OSError:
        return False
    return True


def append_line(path, line):
    """Acrescenta uma linha no fim de um arquivo de texto (cria a pasta se preciso)."""
    write_text(path, line.rstrip('\n') + '\n', append=True)


def read_lines(path):
    """Lê as linhas de um arquivo de texto (tolerante a caracteres ruins); vazio se não existir."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return []


def write_lines(path, lines):
    """Grava uma lista de linhas em um arquivo de texto."""
    write_text(path, ''.join(line.rstrip('\n') + '\n' for line in lines))
