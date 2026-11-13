# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail before emulator startup if shared modules or native page alignment are wrong."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import struct
import sys
import zlib
from zipfile import BadZipFile, ZipFile

REQUIRED = ('mobile', 'game', 'bolha.__init__', 'bolha.motion',
            'bolha.facial_motion', 'bolha.dialogue', 'bolha.preferences', 'bolha.reactions')
MAX_ENTRY = 128 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MACHINES = {183: 'arm64-v8a', 62: 'x86_64'}


class AuditError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise AuditError(message)


def elf(data, name):
    need(len(data) >= 64 and data[:6] == b'\x7fELF\x02\x01',
         f'{name}: biblioteca precisa ser ELF64 little-endian.')
    machine = struct.unpack_from('<H', data, 18)[0]
    need(machine in MACHINES, f'{name}: arquitetura ELF inesperada ({machine}).')
    offset = struct.unpack_from('<Q', data, 32)[0]
    entry_size, count = struct.unpack_from('<HH', data, 54)
    need(entry_size >= 56 and 0 < count <= 4096 and offset >= 64
         and offset + entry_size * count <= len(data),
         f'{name}: tabela de segmentos ELF fora dos limites.')
    alignments = []
    for index in range(count):
        kind, _, start, virtual, _, size, memory, alignment = struct.unpack_from(
            '<IIQQQQQQ', data, offset + index * entry_size)
        if kind != 1:  # PT_LOAD
            continue
        need(start + size <= len(data) and memory >= size,
             f'{name}: segmento LOAD fora dos limites.')
        need(alignment > 0 and alignment & (alignment - 1) == 0
             and start % alignment == virtual % alignment,
             f'{name}: alinhamento LOAD inválido ({alignment}).')
        alignments.append(alignment)
    need(alignments, f'{name}: nenhum segmento LOAD.')
    abi = MACHINES[machine]
    need(not any(other in name for other in MACHINES.values() if other != abi),
         f'{name}: arquitetura ELF diverge do diretório ABI.')
    minimum = min(alignments)
    need(abi != 'arm64-v8a' or minimum >= 16384,
         f'{name}: LOAD ARM64 alinhado em {minimum} bytes; mínimo exigido: 16384.')
    return dict(path=name, abi=abi, minimumLoadAlignment=minimum,
                loadAlignments=alignments)


def audit(apk):
    report = dict(apk=str(apk), ok=False, requiredModules={}, archives=0,
                  libraries=[], architectures={}, errors=[])
    total = 0

    def walk(source, prefix='', depth=0):
        nonlocal total
        need(depth <= 3, f'{prefix}: profundidade ZIP excedida.')
        source.seek(0, 2)
        archive_size = source.tell()
        source.seek(0)
        with ZipFile(source) as archive:
            entries = archive.infolist()
            report['archives'] += 1
            need(len(entries) <= 20000 and len({item.filename for item in entries}) == len(entries),
                 f'{prefix or apk}: ZIP tem entradas demais ou nomes duplicados.')
            for item in entries:
                name = prefix + item.filename
                need(not item.flag_bits & 1, f'{name}: ZIP criptografado não é auditável.')
                need(0 <= item.file_size <= MAX_ENTRY and item.compress_size >= 0
                     and 0 <= item.header_offset <= archive_size - 30,
                     f'{name}: tamanho ou posição ZIP inválido.')
                total += item.file_size
                need(total <= MAX_TOTAL, 'Conteúdo ZIP excede o limite de auditoria de 512 MiB.')
                source.seek(item.header_offset)
                header = source.read(30)
                need(header[:4] == b'PK\x03\x04', f'{name}: cabeçalho ZIP local inválido.')
                filename_size, extra_size = struct.unpack_from('<HH', header, 26)
                end = item.header_offset + 30 + filename_size + extra_size + item.compress_size
                need(end <= archive_size, f'{name}: conteúdo ZIP fora dos limites.')
                if name == 'assets/chaquopy/app.imy':
                    with ZipFile(BytesIO(archive.read(item))) as app:
                        names = set(app.namelist())
                        for module in REQUIRED:
                            base = module.replace('.', '/')
                            found = next((base + suffix for suffix in ('.py', '.pyc')
                                          if base + suffix in names), None)
                            if found:
                                report['requiredModules'][module] = found
                if item.is_dir() or not item.filename.endswith(('.imy', '.zip', '.so')):
                    continue
                with archive.open(item) as stream:
                    data = stream.read(MAX_ENTRY + 1)
                need(len(data) == item.file_size, f'{name}: tamanho ZIP expandido divergente.')
                if item.filename.endswith('.so'):
                    try:
                        report['libraries'].append(elf(data, name))
                    except AuditError as error:
                        report['errors'].append(str(error))
                else:
                    walk(BytesIO(data), name + '!/', depth + 1)

    try:
        with apk.open('rb') as source:
            walk(source)
        missing = [name for name in REQUIRED if name not in report['requiredModules']]
        if missing:
            report['errors'].append('assets/chaquopy/app.imy: módulos ausentes: ' + ', '.join(missing))
        for abi in MACHINES.values():
            libraries = [item for item in report['libraries'] if item['abi'] == abi]
            report['architectures'][abi] = dict(count=len(libraries),
                minimumLoadAlignment=min((item['minimumLoadAlignment'] for item in libraries), default=None))
            if not libraries:
                report['errors'].append(f'{abi}: nenhuma biblioteca ELF64 válida encontrada.')
    except (AuditError, BadZipFile, OSError, RuntimeError, EOFError, struct.error, zlib.error) as error:
        report['errors'].append(str(error))
    report['ok'] = not report['errors']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('--report', type=Path, help='Gravar relatório JSON neste arquivo.')
    args = parser.parse_args()
    report = audit(args.apk)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for abi, summary in report['architectures'].items():
        print(f'{abi}: {summary["count"]} bibliotecas; LOAD mínimo {summary["minimumLoadAlignment"]} bytes.')
    for error in report['errors']:
        print('ERRO: ' + error, file=sys.stderr)
    print('Auditoria estática do APK: ' + ('APROVADA' if report['ok'] else 'REPROVADA'))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
