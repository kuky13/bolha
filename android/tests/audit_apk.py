# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail before emulator startup if shared modules, page alignment, or license/provenance assets are wrong."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import re
import struct
import sys
import zlib
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = ('mobile', 'game', 'bolha.__init__', 'bolha.motion',
            'bolha.facial_motion', 'bolha.dialogue', 'bolha.preferences', 'bolha.reactions')
REQUIRED_ASSETS = (
    'assets/LICENSE',
    'assets/NOTICE.md',
    'assets/PRIVACY.md',
    'assets/licenses/BOLHA-ASSETS.md',
    'assets/licenses/android/NOTICE.md',
)
ANDROID_LICENSE_FILES = {
    'Chaquopy-17.2.0.txt': ('Chaquopy 17.2.0', 'MIT', 'https://github.com/chaquo/chaquopy/tree/17.2.0'),
    'CPython-3.13.16.txt': ('CPython 3.13.16', 'PSF-2.0', 'https://github.com/python/cpython/tree/v3.13.16'),
    'OpenSSL-3.5.9.txt': ('OpenSSL 3.5.9', 'Apache-2.0', 'https://github.com/openssl/openssl/tree/openssl-3.5.9'),
    'NumPy-2.3.2.txt': ('NumPy 2.3.2', 'BSD-3-Clause', 'https://github.com/numpy/numpy/tree/v2.3.2'),
    'NumPy-Dragon4.txt': ('NumPy Dragon4', 'MIT', 'https://github.com/numpy/numpy/tree/v2.3.2'),
    'NumPy-LAPACK-Lite.txt': ('NumPy LAPACK Lite', 'BSD-3-Clause', 'https://github.com/numpy/numpy/tree/v2.3.2'),
    'NumPy-libdivide.txt': ('NumPy libdivide', 'Zlib', 'https://github.com/numpy/numpy/tree/v2.3.2'),
    'OpenBLAS.txt': ('OpenBLAS', 'BSD-3-Clause', 'https://github.com/chaquo/chaquopy/tree/17.2.0/server/pypi/packages'),
    'LLVM-libcxx.txt': ('LLVM libc++', 'Apache-2.0 WITH LLVM-exception', 'https://github.com/llvm/llvm-project'),
    'GCC-Runtime-Library-Exception-3.1.txt': ('GCC Runtime / libgfortran', 'GPL-3.0-or-later WITH GCC-exception-3.1', 'https://github.com/chaquo/chaquopy/tree/17.2.0/server/pypi/packages'),
    'XZ-5.4.6.txt': ('XZ Utils / liblzma 5.4.6', '0BSD', 'https://github.com/beeware/cpython-android-source-deps'),
    'bzip2-1.0.8.txt': ('bzip2 1.0.8', 'bzip2-1.0.6', 'https://github.com/beeware/cpython-android-source-deps'),
    'libffi-3.4.4.txt': ('libffi 3.4.4', 'MIT', 'https://github.com/beeware/cpython-android-source-deps'),
}
SO_PROVENANCE = (
    ('libpython', ('CPython 3.13.16', 'PSF-2.0', 'https://github.com/python/cpython/tree/v3.13.16')),
    ('libssl', ('OpenSSL 3.5.9', 'Apache-2.0', 'https://github.com/openssl/openssl/tree/openssl-3.5.9')),
    ('libcrypto', ('OpenSSL 3.5.9', 'Apache-2.0', 'https://github.com/openssl/openssl/tree/openssl-3.5.9')),
    ('libc++_shared', ('LLVM libc++', 'Apache-2.0 WITH LLVM-exception', 'https://github.com/llvm/llvm-project')),
    ('libchaquopy', ('Chaquopy 17.2.0', 'MIT', 'https://github.com/chaquo/chaquopy/tree/17.2.0')),
    ('libsqlite', ('SQLite', 'Public Domain', 'https://www.sqlite.org/copyright.html')),
    ('libbz2', ('bzip2 1.0.8', 'bzip2-1.0.6', 'https://github.com/beeware/cpython-android-source-deps')),
    ('libffi', ('libffi 3.4.4', 'MIT', 'https://github.com/beeware/cpython-android-source-deps')),
    ('liblzma', ('XZ Utils / liblzma 5.4.6', '0BSD', 'https://github.com/beeware/cpython-android-source-deps')),
    ('libopenblas', ('OpenBLAS', 'BSD-3-Clause', 'https://github.com/chaquo/chaquopy/tree/17.2.0/server/pypi/packages')),
    ('libgfortran', ('GNU libgfortran', 'GPL-3.0-or-later WITH GCC-exception-3.1', 'https://github.com/chaquo/chaquopy/tree/17.2.0/server/pypi/packages')),
    ('libquadmath', ('GCC libquadmath', 'GPL-3.0-or-later WITH GCC-exception-3.1', 'https://github.com/chaquo/chaquopy/tree/17.2.0/server/pypi/packages')),
    ('libgcc_s', ('GCC Runtime', 'GPL-3.0-or-later WITH GCC-exception-3.1', 'https://github.com/chaquo/chaquopy/tree/17.2.0/server/pypi/packages')),
    ('libz', ('zlib (Android / CPython deps)', 'Zlib', 'https://github.com/beeware/cpython-android-source-deps')),
)
MAX_ENTRY = 128 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MACHINES = {183: 'arm64-v8a', 62: 'x86_64'}


class AuditError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise AuditError(message)


def classify_so(name: str):
    base = Path(name).name.lower()
    for prefix, meta in SO_PROVENANCE:
        if base.startswith(prefix):
            return dict(component=meta[0], license=meta[1], source=meta[2])
    lower = name.lower()
    if 'requirements-' in lower and '/numpy/' in lower:
        return dict(component='NumPy 2.3.2', license='BSD-3-Clause',
                    source='https://chaquo.com/pypi-upstream/numpy/')
    if lower.startswith('assets/chaquopy/bootstrap-native/') and lower.endswith('/java/chaquopy.so'):
        return dict(component='Chaquopy 17.2.0', license='MIT',
                    source='https://github.com/chaquo/chaquopy/tree/17.2.0')
    if lower.startswith(('assets/chaquopy/stdlib-', 'assets/chaquopy/bootstrap-native/')) and '.cpython-313-' in base:
        return dict(component='CPython 3.13.16', license='PSF-2.0',
                    source='https://github.com/python/cpython/tree/v3.13.16')
    return None


def _parse_dist_info_metadata(raw: bytes) -> dict:
    meta = {}
    for line in raw.decode('utf-8', 'replace').splitlines():
        if not line:
            break
        if ':' in line:
            key, val = line.split(':', 1)
            meta.setdefault(key.strip().lower(), val.strip())
    return dict(
        name=meta.get('name', ''),
        version=meta.get('version', ''),
        license=meta.get('license-expression') or meta.get('license') or '',
        homePage=meta.get('home-page') or '',
    )


def _validate_android_notice_text(notice_text: str, label: str):
    lower = notice_text.lower()
    for token in ('chaquopy', 'cpython', 'openssl', 'numpy', 'openblas', 'libc++', 'libgfortran'):
        need(token in lower, f'{label}: componente obrigatório ausente ({token}).')


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
    entry = dict(path=name, abi=abi, minimumLoadAlignment=minimum, loadAlignments=alignments)
    provenance = classify_so(name)
    if provenance:
        entry['provenance'] = provenance
    return entry


def audit(apk):
    apk = Path(apk)
    report = dict(
        apk=str(apk),
        ok=False,
        requiredModules={},
        licenseAssets={},
        pythonPackages=[],
        archives=0,
        libraries=[],
        unmappedLibraries=[],
        architectures={},
        errors=[],
    )
    total = 0
    seen_entries = set()
    root_notice_text = None
    android_notice_text = None

    def walk(source, prefix='', depth=0):
        nonlocal total, root_notice_text, android_notice_text
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
                seen_entries.add(name)
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
                if name == 'assets/NOTICE.md':
                    root_notice_text = archive.read(item).decode('utf-8', 'replace')
                elif name == 'assets/licenses/android/NOTICE.md':
                    android_notice_text = archive.read(item).decode('utf-8', 'replace')
                elif name == 'assets/chaquopy/app.imy':
                    with ZipFile(BytesIO(archive.read(item))) as app:
                        names = set(app.namelist())
                        for module in REQUIRED:
                            base = module.replace('.', '/')
                            found = next((base + suffix for suffix in ('.py', '.pyc')
                                          if base + suffix in names), None)
                            if found:
                                report['requiredModules'][module] = found
                elif depth > 0 and item.filename.endswith('.dist-info/METADATA'):
                    report['pythonPackages'].append(_parse_dist_info_metadata(archive.read(item)))
                if item.is_dir() or not item.filename.endswith(('.imy', '.zip', '.so')):
                    continue
                with archive.open(item) as stream:
                    data = stream.read(MAX_ENTRY + 1)
                need(len(data) == item.file_size, f'{name}: tamanho ZIP expandido divergente.')
                if item.filename.endswith('.so'):
                    try:
                        lib_info = elf(data, name)
                        report['libraries'].append(lib_info)
                        if 'provenance' not in lib_info:
                            report['unmappedLibraries'].append(name)
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

        expected_assets = list(REQUIRED_ASSETS) + [
            f'assets/licenses/android/{fname}' for fname in ANDROID_LICENSE_FILES
        ]
        for asset in expected_assets:
            present = asset in seen_entries
            report['licenseAssets'][asset] = present
            if not present:
                report['errors'].append(f'Aviso/licença ausente no APK: {asset}')

        if root_notice_text is not None:
            if re.search(r'Bolha\s+0\.4\.4\b', root_notice_text):
                report['errors'].append('assets/NOTICE.md: referência desatualizada (Bolha 0.4.4).')
        if android_notice_text is not None:
            try:
                _validate_android_notice_text(android_notice_text, 'assets/licenses/android/NOTICE.md')
            except AuditError as error:
                report['errors'].append(str(error))

        if report['unmappedLibraries']:
            report['errors'].append(
                'Bibliotecas nativas sem procedência mapeada: ' + ', '.join(report['unmappedLibraries'])
            )

        for abi in MACHINES.values():
            libraries = [item for item in report['libraries'] if item['abi'] == abi]
            report['architectures'][abi] = dict(
                count=len(libraries),
                minimumLoadAlignment=min((item['minimumLoadAlignment'] for item in libraries), default=None),
            )
            if not libraries:
                report['errors'].append(f'{abi}: nenhuma biblioteca ELF64 válida encontrada.')
    except (AuditError, BadZipFile, OSError, RuntimeError, EOFError, struct.error, zlib.error) as error:
        report['errors'].append(str(error))
    report['ok'] = not report['errors']
    return report


def verify_repo(repo_root=ROOT, report_path=None):
    repo_root = Path(repo_root).resolve()
    errors = []
    gradle_path = repo_root / 'android/app/build.gradle'
    if not gradle_path.is_file():
        errors.append('android/app/build.gradle ausente.')
        gradle_text = ''
    else:
        gradle_text = gradle_path.read_text(encoding='utf-8')
        required_gradle_snippets = (
            "id 'com.android.application' version '8.10.1'",
            "id 'com.chaquo.python' version '17.2.0'",
            "version '3.13'",
            "install 'numpy==2.3.2'",
            'https://chaquo.com/pypi-upstream/',
            "abiFilters 'arm64-v8a', 'x86_64'",
            "include 'LICENSE', 'NOTICE.md'",
            "licenses/BOLHA-ASSETS.md",
            "into 'licenses/android'",
        )
        for snippet in required_gradle_snippets:
            if snippet not in gradle_text:
                errors.append(f'build.gradle sem configuração esperada: {snippet}')

    for rel in ('LICENSE', 'NOTICE.md', 'PRIVACY.md', 'licenses/BOLHA-ASSETS.md', 'android/licenses/NOTICE.md'):
        path = repo_root / rel
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f'Arquivo obrigatório ausente ou vazio: {rel}')

    android_notice = repo_root / 'android/licenses/NOTICE.md'
    if android_notice.is_file():
        try:
            _validate_android_notice_text(android_notice.read_text(encoding='utf-8'), 'android/licenses/NOTICE.md')
        except AuditError as error:
            errors.append(str(error))

    license_inventory = {}
    for fname, (component, lic_id, source_url) in ANDROID_LICENSE_FILES.items():
        path = repo_root / 'android/licenses' / fname
        present = path.is_file() and path.stat().st_size > 0
        license_inventory[fname] = dict(
            present=present,
            component=component,
            license=lic_id,
            source=source_url,
        )
        if not present:
            errors.append(f'Texto de licença Android ausente ou vazio: android/licenses/{fname}')

    report = dict(
        mode='repo',
        repoRoot=str(repo_root),
        ok=not errors,
        gradleConfigured=not any('build.gradle' in err for err in errors),
        licenseFiles=license_inventory,
        errors=errors,
    )
    if report_path:
        target = Path(report_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for error in errors:
        print('ERRO: ' + error, file=sys.stderr)
    print('Auditoria de procedência/licenças Android (repositório): ' + ('APROVADA' if report['ok'] else 'REPROVADA'))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', nargs='?', type=Path)
    parser.add_argument('--verify-repo', nargs='?', const=str(ROOT), metavar='REPO_DIR',
                        help='Valida build.gradle, licenças Android e procedência no repositório.')
    parser.add_argument('--report', type=Path, help='Gravar relatório JSON neste arquivo.')
    args = parser.parse_args()
    if args.verify_repo:
        report = verify_repo(args.verify_repo, args.report)
        return 0 if report['ok'] else 1
    if not args.apk:
        parser.error('Informe <apk> ou --verify-repo.')
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
