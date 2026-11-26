# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Rejeita artefatos web/worker/Qt fora do runtime e audita licenças, fontes e procedência."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.package_batteryhub import BINARIES as BATTERYHUB_BINARIES
from scripts.package_batteryhub import NOTICES as BATTERYHUB_NOTICES
from scripts.package_batteryhub import PORTABLE as BATTERYHUB_PORTABLE
from scripts.package_batteryhub import PORTABLE_SHA as BATTERYHUB_PORTABLE_SHA
from scripts.package_batteryhub import SOURCES as BATTERYHUB_SOURCES

FORBIDDEN = (
    'electron', 'app.asar', 'chrome_', 'chromium', 'ffmpeg', 'node.exe', 'node_modules',
    'qtuiotouchplugin', 'qtwebengine', 'qt6webengine', 'qt6qml', 'qt6quick', 'qt6network',
    'brain.exe', 'worker.py',
)
REQUIRED = (
    'bolha-version.json', 'THIRD-PARTY-NOTICES.txt', 'licenses/LICENSE',
    'licenses/PYTHON-LICENSE.txt', 'PySide6/plugins/imageformats/qgif.dll',
)
STRICT_REQUIRED_LICENSES = (
    'licenses/NOTICE.md',
    'licenses/PRIVACY.md',
    'licenses/BOLHA-ASSETS.md',
    'licenses/PYWINRT-MIT.txt',
    'licenses/third-party/QtBase-6.11.3/ORIGIN.txt',
)
NOTICE_COVERAGE_RULES = {
    'pyside6_qt6': ('pyside6', 'qt6', 'qtbase.git'),
    'qtsvg': ('qtsvg', 'qtsvg.git'),
    'qt_plugins': ('plugins qt', 'imageformats'),
    'openssl_windows': ('openssl', '3.0.13', 'openssl-3.0.13'),
    'mesa_llvm': ('mesa', 'llvm', 'opengl32sw'),
    'batteryhub': ('batteryhub', '1.1.0', 'batteryhub-1.1.0-source.tar.gz'),
    'headsetcontrol': ('headsetcontrol', '4.3.0', 'headsetcontrol-4.3.0.tar.gz'),
    'pywinrt': ('pywinrt', 'pywinrt-mit.txt'),
}
EXPECTED_WIN_PINS = (
    'PySide6-Essentials==6.11.3',
    'numpy==2.4.6',
    'psutil==7.2.2',
    'pywin32==311',
    'winrt-runtime==3.2.1',
    'winrt-Windows.Media.Control==3.2.1',
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()


def validate_notices_text(text: str, label: str = 'THIRD-PARTY-NOTICES.txt') -> dict:
    if re.search(r'Bolha\s+0\.4\.4\b', text):
        raise ValueError(f'{label}: cabeçalho desatualizado (Bolha 0.4.4).')
    lower = text.lower()
    coverage = {}
    missing = []
    for key, tokens in NOTICE_COVERAGE_RULES.items():
        ok = all(token in lower for token in tokens)
        coverage[key] = ok
        if not ok:
            missing.append(key)
    if missing:
        raise ValueError(f'{label}: cobertura ausente para {", ".join(missing)}.')
    if 'https://' not in lower:
        raise ValueError(f'{label}: URLs de origem/fonte ausentes.')
    return coverage


def _detect_bundle_components(internal: Path) -> dict:
    return {
        'qtLibraries': sorted(
            p.relative_to(internal).as_posix()
            for p in (internal / 'PySide6').glob('Qt6*.dll')
        ) if (internal / 'PySide6').is_dir() else [],
        'qtPlugins': sorted(
            p.relative_to(internal).as_posix()
            for p in (internal / 'PySide6/plugins').rglob('*.dll')
        ) if (internal / 'PySide6/plugins').is_dir() else [],
        'qtSvgPresent': (internal / 'PySide6/Qt6Svg.dll').is_file()
        or (internal / 'PySide6/plugins/imageformats/qsvg.dll').is_file()
        or (internal / 'PySide6/plugins/iconengines/qsvgicon.dll').is_file(),
        'mesaLlvmPresent': (internal / 'PySide6/opengl32sw.dll').is_file(),
        'openSslDlls': sorted(
            p.relative_to(internal).as_posix()
            for p in internal.rglob('*.dll')
            if p.name.lower().startswith(('libssl', 'libcrypto'))
        ),
        'batteryHubPresent': (internal / 'third_party/batteryhub/BatteryHub.exe').is_file(),
        'headsetControlPresent': (internal / 'third_party/batteryhub/headsetcontrol.exe').is_file(),
    }


def _verify_batteryhub_dir(folder: Path) -> dict:
    verified = {}
    for name, expected in BATTERYHUB_BINARIES.items():
        target = folder / name
        if not target.is_file():
            raise ValueError(f'Binário BatteryHub ausente: {target}')
        digest = _sha256_file(target)
        if digest != expected:
            raise ValueError(f'SHA-256 divergente em {name}: esperado {expected}, obtido {digest}.')
        verified[name] = digest
    for notice in BATTERYHUB_NOTICES:
        if not (folder / notice).is_file():
            raise ValueError(f'Aviso BatteryHub ausente: {folder / notice}')
    return verified


def audit(root, output_json=None, *, strict=False):
    root = Path(root)
    if not (root / 'Bolha.exe').is_file():
        raise ValueError('Bolha.exe ausente.')
    for item in root.rglob('*'):
        if item.is_symlink():
            raise ValueError('Atalho inesperado: ' + str(item))
        if any(token in item.name.lower() for token in FORBIDDEN):
            raise ValueError('Componente removido ainda presente: ' + str(item))
        if item.is_file() and item.suffix.lower() in ('.js', '.jsx', '.ts', '.tsx', '.html', '.css'):
            raise ValueError('Camada web inesperada: ' + str(item))
    internal = root / '_internal'
    for required in REQUIRED:
        if not (internal / required).is_file():
            raise ValueError('Recurso obrigatório ausente: ' + required)

    notices_text = (internal / 'THIRD-PARTY-NOTICES.txt').read_text(encoding='utf-8')
    is_rich_notices = strict or len(notices_text) > 120 or 'componentes redistribu' in notices_text.lower()
    notices_coverage = validate_notices_text(notices_text) if is_rich_notices else None

    version_raw = (internal / 'bolha-version.json').read_text(encoding='utf-8').strip()
    package_version = None
    if version_raw.startswith('{'):
        try:
            package_version = json.loads(version_raw).get('version')
        except json.JSONDecodeError as exc:
            raise ValueError('bolha-version.json inválido.') from exc

    detected = _detect_bundle_components(internal)
    battery_dir = internal / 'third_party/batteryhub'
    battery_verified = {}
    if strict or battery_dir.is_dir():
        battery_verified = _verify_batteryhub_dir(battery_dir)

    licenses_present = {
        rel: (internal / rel).is_file()
        for rel in (*STRICT_REQUIRED_LICENSES, 'licenses/LICENSE', 'licenses/PYTHON-LICENSE.txt')
    }
    if strict:
        missing_lic = [rel for rel, ok in licenses_present.items() if not ok]
        if missing_lic:
            raise ValueError('Licenças obrigatórias ausentes no pacote: ' + ', '.join(missing_lic))
        qt_licenses_dir = internal / 'licenses/third-party/QtBase-6.11.3/LICENSES'
        if not qt_licenses_dir.is_dir() or not any(qt_licenses_dir.glob('*.txt')):
            raise ValueError('Licenças QtBase-6.11.3 ausentes no pacote.')

    report = dict(
        root=str(root),
        executable='Bolha.exe',
        version=package_version,
        gifDecoder='PySide6/plugins/imageformats/qgif.dll',
        gifDecoderPresent=True,
        noticesValidated=bool(is_rich_notices),
        noticesCoverage=notices_coverage,
        detectedComponents=detected,
        batteryhubVerified=battery_verified,
        licensesPresent=licenses_present,
    )
    if output_json:
        target = Path(output_json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Pacote nativo auditado:', json.dumps(report, ensure_ascii=False))
    return report


def _validate_reuse(repo_root: Path) -> dict:
    reuse_path = repo_root / 'REUSE.toml'
    licenses_dir = repo_root / 'LICENSES'
    if not reuse_path.is_file():
        raise ValueError('REUSE.toml ausente na raiz do repositório.')
    if not licenses_dir.is_dir():
        raise ValueError('Diretório LICENSES/ ausente na raiz do repositório.')
    data = tomllib.loads(reuse_path.read_text(encoding='utf-8'))
    if data.get('version') != 1 or not data.get('annotations'):
        raise ValueError('REUSE.toml deve definir version = 1 e [[annotations]].')
    available = {p.stem for p in licenses_dir.glob('*.txt')}
    referenced = set()
    for entry in data['annotations']:
        expr = entry.get('SPDX-License-Identifier', '').strip()
        if not expr:
            raise ValueError(f'Anotação REUSE sem SPDX-License-Identifier: {entry}')
        if not entry.get('SPDX-FileCopyrightText'):
            raise ValueError(f'Anotação REUSE sem SPDX-FileCopyrightText: {entry}')
        for token in re.split(r'\s+(?:AND|OR|WITH)\s+', expr):
            token = token.strip('() ')
            if token:
                referenced.add(token)
    missing_texts = sorted(referenced - available)
    if missing_texts:
        raise ValueError('LICENSES/*.txt ausente para: ' + ', '.join(missing_texts))
    unused_texts = sorted(available - referenced)
    if unused_texts:
        raise ValueError('LICENSES/*.txt não referenciado em REUSE.toml: ' + ', '.join(unused_texts))
    return dict(annotations=len(data['annotations']), licenses=sorted(referenced))


def verify_repo(repo_root=ROOT, output_json=None):
    repo_root = Path(repo_root).resolve()
    pyproject = tomllib.loads((repo_root / 'pyproject.toml').read_text(encoding='utf-8'))
    project = pyproject.get('project', {})
    version = project.get('version')
    if not version:
        raise ValueError('Versão ausente em pyproject.toml.')
    if project.get('license') != 'GPL-3.0-or-later':
        raise ValueError('Licença em pyproject.toml deve ser GPL-3.0-or-later.')

    reqs = (repo_root / 'requirements.txt').read_text(encoding='utf-8')
    reqs_build = (repo_root / 'requirements-build.txt').read_text(encoding='utf-8')
    combined_reqs = reqs + '\n' + reqs_build
    for pin in EXPECTED_WIN_PINS:
        if pin not in combined_reqs:
            raise ValueError(f'Dependência esperada ausente ou sem pinagem exata: {pin}')
    if 'pyinstaller==6.22.3' not in reqs_build:
        raise ValueError('pyinstaller==6.22.3 ausente em requirements-build.txt.')

    notice_md = (repo_root / 'NOTICE.md').read_text(encoding='utf-8')
    notice_links = ('packaging/THIRD-PARTY-NOTICES.txt', 'android/licenses/NOTICE.md')
    if any(ref not in notice_md for ref in notice_links):
        raise ValueError('NOTICE.md deve apontar para os avisos Windows e Android.')
    third_party_txt = (repo_root / 'packaging/THIRD-PARTY-NOTICES.txt').read_text(encoding='utf-8')
    notice_coverage_txt = validate_notices_text(third_party_txt, 'packaging/THIRD-PARTY-NOTICES.txt')

    required_files = (
        'LICENSE',
        'NOTICE.md',
        'PRIVACY.md',
        'packaging/THIRD-PARTY-NOTICES.txt',
        'licenses/BOLHA-ASSETS.md',
        'licenses/PYWINRT-MIT.txt',
        'licenses/third-party/QtBase-6.11.3/ORIGIN.txt',
    )
    for rel in required_files:
        path = repo_root / rel
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f'Arquivo de licença/aviso obrigatório ausente ou vazio: {rel}')
    qt_lic_dir = repo_root / 'licenses/third-party/QtBase-6.11.3/LICENSES'
    qt_lic_count = len(list(qt_lic_dir.glob('*.txt')))
    if qt_lic_count == 0:
        raise ValueError('licenses/third-party/QtBase-6.11.3/LICENSES está vazio.')

    bh_dir = repo_root / 'third_party/batteryhub'
    archives = {}
    for name, expected in {BATTERYHUB_PORTABLE: BATTERYHUB_PORTABLE_SHA, **BATTERYHUB_SOURCES}.items():
        path = bh_dir / name
        if not path.is_file():
            raise ValueError(f'Arquivo third_party/batteryhub ausente: {name}')
        digest = _sha256_file(path)
        if digest != expected:
            raise ValueError(f'SHA-256 divergente para {name}: esperado {expected}, obtido {digest}.')
        archives[name] = digest

    zip_binaries = {}
    with ZipFile(bh_dir / BATTERYHUB_PORTABLE) as zf:
        names = set(zf.namelist())
        for notice in BATTERYHUB_NOTICES:
            if notice not in names:
                raise ValueError(f'{notice} ausente em {BATTERYHUB_PORTABLE}.')
        for binary, expected in BATTERYHUB_BINARIES.items():
            if binary not in names:
                raise ValueError(f'{binary} ausente em {BATTERYHUB_PORTABLE}.')
            digest = _sha256_bytes(zf.read(binary))
            if digest != expected:
                raise ValueError(f'SHA-256 divergente para {binary} em {BATTERYHUB_PORTABLE}.')
            zip_binaries[binary] = digest

    reuse_info = _validate_reuse(repo_root)
    report = dict(
        mode='repo',
        repoRoot=str(repo_root),
        version=version,
        license=project.get('license'),
        reuse=reuse_info,
        noticeLinks=notice_links,
        thirdPartyNoticesCoverage=notice_coverage_txt,
        qtBaseLicenseTexts=qt_lic_count,
        batteryhubArchives=archives,
        batteryhubPortableBinaries=zip_binaries,
        ok=True,
    )
    if output_json:
        target = Path(output_json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Repositório nativo auditado:', json.dumps(report, ensure_ascii=False))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', help='Diretório do bundle Windows (ex.: build/<ver>/dist/Bolha).')
    parser.add_argument('--verify-repo', nargs='?', const=str(ROOT), metavar='REPO_DIR',
                        help='Valida manifestos, licenças, avisos e fontes arquivadas no repositório.')
    parser.add_argument('--strict', action='store_true',
                        help='Exige todos os avisos completos e licenças terceiras no bundle.')
    parser.add_argument('--output-json', help='Grava o relatório JSON neste caminho.')
    args = parser.parse_args()
    if args.verify_repo:
        verify_repo(args.verify_repo, args.output_json)
    elif args.directory:
        audit(args.directory, args.output_json, strict=args.strict)
    else:
        parser.error('Informe <directory> do bundle ou --verify-repo.')
