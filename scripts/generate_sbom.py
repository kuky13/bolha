# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
"""Gera e valida SBOM CycloneDX 1.5 JSON para os artefatos Windows e Android."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.package_batteryhub import BINARIES as BATTERYHUB_BINARIES
from scripts.package_batteryhub import PORTABLE as BATTERYHUB_PORTABLE
from scripts.package_batteryhub import PORTABLE_SHA as BATTERYHUB_PORTABLE_SHA
from scripts.package_batteryhub import SOURCES as BATTERYHUB_SOURCES

SBOM_NAMESPACE = uuid.UUID('7f4a21b8-62b1-4a7a-9b86-1435bb317001')

PYPI_METADATA = {
    'PySide6-Essentials': {
        'license': 'GPL-3.0-only',
        'url': 'https://code.qt.io/cgit/pyside/pyside-setup.git/tag/?h=v6.11.3',
        'publisher': 'The Qt Company Ltd.',
    },
    'shiboken6': {
        'license': 'GPL-3.0-only',
        'url': 'https://code.qt.io/cgit/pyside/pyside-setup.git/tag/?h=v6.11.3',
        'publisher': 'The Qt Company Ltd.',
    },
    'numpy': {
        'license': 'BSD-3-Clause',
        'url': 'https://github.com/numpy/numpy',
        'publisher': 'NumPy Developers',
    },
    'psutil': {
        'license': 'BSD-3-Clause',
        'url': 'https://github.com/giampaolo/psutil',
        'publisher': 'Giampaolo Rodola',
    },
    'pywin32': {
        'license': 'NOASSERTION',
        'url': 'https://github.com/mhammond/pywin32',
        'publisher': 'Mark Hammond',
    },
    'winrt-runtime': {
        'license': 'MIT',
        'url': 'https://github.com/pywinrt/pywinrt/tree/v3.2.1',
        'publisher': 'Microsoft Corporation / David Lechner',
    },
    'winrt-Windows.Foundation': {
        'license': 'MIT',
        'url': 'https://github.com/pywinrt/pywinrt/tree/v3.2.1',
        'publisher': 'Microsoft Corporation / David Lechner',
    },
    'winrt-Windows.Foundation.Collections': {
        'license': 'MIT',
        'url': 'https://github.com/pywinrt/pywinrt/tree/v3.2.1',
        'publisher': 'Microsoft Corporation / David Lechner',
    },
    'winrt-Windows.Storage.Streams': {
        'license': 'MIT',
        'url': 'https://github.com/pywinrt/pywinrt/tree/v3.2.1',
        'publisher': 'Microsoft Corporation / David Lechner',
    },
    'winrt-Windows.Media.Control': {
        'license': 'MIT',
        'url': 'https://github.com/pywinrt/pywinrt/tree/v3.2.1',
        'publisher': 'Microsoft Corporation / David Lechner',
    },
    'pyinstaller': {
        'license': 'GPL-2.0-or-later',
        'url': 'https://github.com/pyinstaller/pyinstaller',
        'publisher': 'PyInstaller Development Team',
    },
    'pytest': {
        'license': 'MIT',
        'url': 'https://github.com/pytest-dev/pytest',
        'publisher': 'pytest-dev',
    },
}


AUDITED_PYTHON_VERSIONS = {
    'PySide6-Essentials': {'6.11.3'},
    'shiboken6': {'6.11.3'},
    'numpy': {'2.3.2', '2.4.6'},
    'psutil': {'7.2.2'},
    'pywin32': {'311'},
    'winrt-runtime': {'3.2.1'},
    'winrt-Windows.Foundation': {'3.2.1'},
    'winrt-Windows.Foundation.Collections': {'3.2.1'},
    'winrt-Windows.Storage.Streams': {'3.2.1'},
    'winrt-Windows.Media.Control': {'3.2.1'},
    'pyinstaller': {'6.22.3'},
    'pytest': {'8.4.2'},
}


def audited_python(name: str, version: str) -> dict:
    if version not in AUDITED_PYTHON_VERSIONS.get(name, ()):
        raise ValueError(f'Dependência Python sem auditoria para esta versão: {name}=={version}.')
    return PYPI_METADATA[name]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _license_entry(expr: str) -> list:
    if any(op in expr for op in (' AND ', ' OR ', ' WITH ')):
        return [{'expression': expr}]
    if expr in ('Public Domain', 'NOASSERTION'):
        return [{'license': {'name': expr}}]
    return [{'license': {'id': expr}}]


def _component(
    *,
    bom_ref: str,
    comp_type: str,
    name: str,
    version: str,
    license_expr: str,
    purl: str | None = None,
    publisher: str | None = None,
    description: str | None = None,
    scope: str = 'required',
    vcs_url: str | None = None,
    dist_url: str | None = None,
    hashes: list | None = None,
    properties: list | None = None,
) -> dict:
    item = {
        'bom-ref': bom_ref,
        'type': comp_type,
        'name': name,
        'version': version,
        'scope': scope,
        'licenses': _license_entry(license_expr),
    }
    if publisher:
        item['publisher'] = publisher
    if description:
        item['description'] = description
    if purl:
        item['purl'] = purl
    ext_refs = []
    if vcs_url:
        ext_refs.append({'type': 'vcs', 'url': vcs_url})
    if dist_url:
        ext_refs.append({'type': 'distribution', 'url': dist_url})
    if ext_refs:
        item['externalReferences'] = ext_refs
    if hashes:
        item['hashes'] = hashes
    if properties:
        item['properties'] = properties
    return item


def _parse_requirements(path: Path, seen=None) -> list:
    if seen is None:
        seen = set()
    path = path.resolve()
    if path in seen:
        return []
    seen.add(path)
    entries = []
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('-r '):
            entries.extend(_parse_requirements(path.parent / line[3:].strip(), seen))
            continue
        req_part, _, marker = line.partition(';')
        match = re.match(r'^([A-Za-z0-9_.-]+)==([^\s;]+)$', req_part.strip())
        if not match:
            raise ValueError(f'Requisito não pinado em {path.name}: {line}')
        entries.append((match.group(1), match.group(2), marker.strip()))
    return entries


def _load_qt_attributions(repo_root: Path) -> list:
    base = repo_root / 'licenses/third-party/QtBase-6.11.3'
    results = []
    for attr in sorted(base.rglob('qt_attribution.json')):
        raw = json.loads(attr.read_text(encoding='utf-8'), strict=False)
        items = raw if isinstance(raw, list) else [raw]
        for item in items:
            results.append({
                'name': item.get('Name') or item.get('Id'),
                'version': item.get('Version') or 'unspecified',
                'license': item.get('LicenseId') or item.get('License') or 'Unknown',
            })
    return results


def _build_windows_sbom(repo_root: Path, bundle_dir: Path | None = None,
                        installer: Path | None = None) -> dict:
    pyproject = tomllib.loads((repo_root / 'pyproject.toml').read_text(encoding='utf-8'))
    project = pyproject['project']
    version = project['version']
    root_ref = f'pkg:github/kuky13/bolha@{version}#windows'

    components = []
    runtime_refs = []

    # 1. Python dependencies from requirements.txt
    for pkg_name, pkg_ver, marker in _parse_requirements(repo_root / 'requirements.txt'):
        meta = audited_python(pkg_name, pkg_ver)
        bom_ref = f'pkg:pypi/{pkg_name.lower()}@{pkg_ver}'
        props = [{'name': 'bolha:environmentMarker', 'value': marker}] if marker else None
        components.append(_component(
            bom_ref=bom_ref,
            comp_type='library',
            name=pkg_name,
            version=pkg_ver,
            license_expr=meta['license'],
            purl=bom_ref,
            publisher=meta.get('publisher'),
            scope='required',
            vcs_url=meta.get('url'),
            properties=props,
            description='Licenças por módulo. win32/License.txt na tag b311 declara BSD-3-Clause.' if pkg_name == 'pywin32' else None,
        ))
        runtime_refs.append(bom_ref)
        if pkg_name == 'PySide6-Essentials':
            shib_meta = audited_python('shiboken6', pkg_ver)
            shib_ref = f'pkg:pypi/shiboken6@{pkg_ver}'
            components.append(_component(
                bom_ref=shib_ref,
                comp_type='library',
                name='shiboken6',
                version=pkg_ver,
                license_expr=shib_meta['license'],
                purl=shib_ref,
                publisher=shib_meta['publisher'],
                scope='required',
                vcs_url=shib_meta['url'],
            ))
            runtime_refs.append(shib_ref)

    # 2. Build dependencies (excluded from runtime)
    for pkg_name, pkg_ver, _ in _parse_requirements(repo_root / 'requirements-build.txt'):
        if any(c['name'] == pkg_name for c in components):
            continue
        meta = audited_python(pkg_name, pkg_ver)
        bom_ref = f'pkg:pypi/{pkg_name.lower()}@{pkg_ver}'
        components.append(_component(
            bom_ref=bom_ref,
            comp_type='application',
            name=pkg_name,
            version=pkg_ver,
            license_expr=meta['license'],
            purl=bom_ref,
            publisher=meta.get('publisher'),
            scope='excluded',
            vcs_url=meta.get('url'),
        ))

    # 3. Verified native / vendored Windows components
    bh_dir = repo_root / 'third_party/batteryhub'
    bh_src_sha = _sha256_file(bh_dir / 'BatteryHub-1.1.0-source.tar.gz')
    hc_src_sha = _sha256_file(bh_dir / 'headsetcontrol-4.3.0.tar.gz')
    bh_zip_sha = _sha256_file(bh_dir / BATTERYHUB_PORTABLE)
    if bh_zip_sha != BATTERYHUB_PORTABLE_SHA:
        raise ValueError('SHA-256 de BatteryHub-1.1.0-portable.zip não confere.')

    qt_attrs = _load_qt_attributions(repo_root)
    native_components = [
        _component(
            bom_ref='pkg:generic/pestinha@0bb768a',
            comp_type='library',
            name='Pestinha (base upstream)',
            version='0bb768a2be024221ee1da62cc335362279d912d6',
            license_expr='GPL-3.0-or-later',
            publisher='mille-okws and contributors',
            vcs_url='https://github.com/mille-okws/pestinha',
        ),
        _component(
            bom_ref='pkg:generic/cpython@3.11',
            comp_type='library',
            name='CPython',
            version='3.11',
            license_expr='PSF-2.0',
            publisher='Python Software Foundation',
            vcs_url='https://github.com/python/cpython',
        ),
        _component(
            bom_ref='pkg:generic/qtbase@6.11.3',
            comp_type='framework',
            name='Qt6 Base (Core/Gui/Widgets/OpenGL)',
            version='6.11.3',
            license_expr='GPL-3.0-only',
            publisher='The Qt Company Ltd.',
            vcs_url='https://code.qt.io/cgit/qt/qtbase.git/tag/?h=v6.11.3',
            properties=[{'name': 'qt:thirdPartyAttributionCount', 'value': str(len(qt_attrs))}],
        ),
        _component(
            bom_ref='pkg:generic/qtsvg@6.11.3',
            comp_type='library',
            name='QtSvg (Qt6Svg.dll)',
            version='6.11.3',
            license_expr='GPL-3.0-only',
            publisher='The Qt Company Ltd.',
            vcs_url='https://code.qt.io/cgit/qt/qtsvg.git/tag/?h=v6.11.3',
        ),
        _component(
            bom_ref='pkg:generic/qt-plugins@6.11.3',
            comp_type='library',
            name='Plugins Qt (platforms, styles, imageformats, iconengines)',
            version='6.11.3',
            license_expr='GPL-3.0-only',
            publisher='The Qt Company Ltd.',
            vcs_url='https://code.qt.io/cgit/qt/qtimageformats.git/tag/?h=v6.11.3',
            description='Inclui qwindows.dll, qmodernwindowsstyle.dll, qgif.dll, qico.dll, qjpeg.dll, qsvg.dll, qwebp.dll, qsvgicon.dll; qtuiotouchplugin.dll e Qt6Network.dll excluídos.',
        ),
        _component(
            bom_ref='pkg:generic/openssl@3.0.13',
            comp_type='library',
            name='OpenSSL (libssl-3.dll / libcrypto-3.dll)',
            version='3.0.13',
            license_expr='Apache-2.0',
            publisher='The OpenSSL Project Authors',
            vcs_url='https://github.com/openssl/openssl/tree/openssl-3.0.13',
        ),
        _component(
            bom_ref='pkg:generic/mesa-llvm-opengl32sw@llvmpipe',
            comp_type='library',
            name='Mesa / LLVM (opengl32sw.dll)',
            version='llvmpipe',
            license_expr='MIT AND NCSA',
            description='Referências a Mesa 11.2.2 e LLVM 3.6.2 no DLL publicado. A lista exata de terceiros do build Qt segue em revisão.',
            publisher='Mesa / LLVM Contributors (Qt prebuilt)',
            dist_url='https://download.qt.io/development_releases/prebuilt/llvmpipe/windows/',
            vcs_url='https://gitlab.freedesktop.org/mesa/mesa',
        ),
        _component(
            bom_ref='pkg:github/krisgfx9/Wireless-Device-Battery-Monitor@1.1.0',
            comp_type='application',
            name='BatteryHub',
            version='1.1.0',
            license_expr='GPL-3.0-only',
            publisher='krisgfx9 and contributors',
            vcs_url='https://github.com/krisgfx9/Wireless-Device-Battery-Monitor/releases/tag/v1.1.0',
            hashes=[
                {'alg': 'SHA-256', 'content': BATTERYHUB_BINARIES['BatteryHub.exe']},
            ],
            properties=[
                {'name': 'bolha:sourceTarballSha256', 'value': bh_src_sha},
                {'name': 'bolha:portableArchiveSha256', 'value': bh_zip_sha},
            ],
        ),
        _component(
            bom_ref='pkg:github/Sapd/HeadsetControl@4.3.0',
            comp_type='application',
            name='headsetcontrol',
            version='4.3.0',
            license_expr='GPL-3.0-only',
            publisher='Sapd and contributors',
            vcs_url='https://github.com/Sapd/HeadsetControl/releases/tag/4.3.0',
            hashes=[
                {'alg': 'SHA-256', 'content': BATTERYHUB_BINARIES['headsetcontrol.exe']},
            ],
            properties=[
                {'name': 'bolha:sourceTarballSha256', 'value': hc_src_sha},
            ],
        ),
        _component(
            bom_ref='pkg:generic/nsis@3.11',
            comp_type='application',
            name='NSIS',
            version='3.11',
            license_expr='Zlib',
            scope='excluded',
            publisher='NSIS Contributors',
            dist_url='https://nsis.sourceforge.io/',
        ),
    ]

    if bundle_dir is not None:
        from scripts.audit_native import audit as audit_bundle
        bundle_report = audit_bundle(bundle_dir, strict=True)
        detected = bundle_report['detectedComponents']
        internal = Path(bundle_dir) / '_internal'
        verified_files = []
        for rel in (
            *detected.get('qtLibraries', []),
            *detected.get('qtPlugins', []),
            *detected.get('openSslDlls', []),
        ):
            p = internal / rel
            if p.is_file():
                verified_files.append(f'{rel}:{_sha256_file(p)}')
        if (internal / 'PySide6/opengl32sw.dll').is_file():
            verified_files.append(f'PySide6/opengl32sw.dll:{_sha256_file(internal / "PySide6/opengl32sw.dll")}')
        for comp in native_components:
            if comp['name'].startswith('Qt6 Base') and verified_files:
                comp.setdefault('properties', []).append(
                    {'name': 'bolha:verifiedBundleFiles', 'value': ', '.join(verified_files)}
                )

    for comp in native_components:
        components.append(comp)
        if comp['scope'] == 'required':
            runtime_refs.append(comp['bom-ref'])

    bom = {
        'bomFormat': 'CycloneDX',
        'specVersion': '1.5',
        'serialNumber': f'urn:uuid:{uuid.uuid5(SBOM_NAMESPACE, f"windows:{version}")}',
        'version': 1,
        'metadata': {
            'component': {
                'bom-ref': root_ref,
                'type': 'application',
                'name': 'Bolha (Windows x64)',
                'version': version,
                'publisher': 'André Ribeiro Lima (KukySolutions)',
                'purl': root_ref,
                'licenses': _license_entry(project['license']),
            },
            'tools': {
                'components': [
                    {
                        'type': 'application',
                        'name': 'scripts/generate_sbom.py',
                        'version': '1.0.0',
                    }
                ]
            },
        },
        'components': components,
        'dependencies': [
            {'ref': root_ref, 'dependsOn': runtime_refs},
        ],
    }
    if installer:
        bom['metadata']['component']['hashes'] = [
            {'alg': 'SHA-256', 'content': _sha256_file(installer)}
        ]
    return bom


def _parse_gradle_pins(gradle_path: Path) -> dict:
    text = gradle_path.read_text(encoding='utf-8')
    agp = re.search(r"id 'com\.android\.application' version '([^']+)'", text)
    chaquopy = re.search(r"id 'com\.chaquo\.python' version '([^']+)'", text)
    py_ver = re.search(r"version '(\d+\.\d+)'", text)
    pip_pkgs = re.findall(r"install '([^']+)'", text)
    if not all((agp, chaquopy, py_ver)):
        raise ValueError('Gradle sem versões explícitas para AGP, Chaquopy ou Python.')
    versions = (agp.group(1), chaquopy.group(1), py_ver.group(1))
    if versions != ('8.10.1', '17.2.0', '3.13') or pip_pkgs != ['numpy==2.3.2']:
        raise ValueError(f'Atualize o inventário Android para estas versões: {versions}, {pip_pkgs}.')
    return {'agp': versions[0], 'chaquopy': versions[1], 'pip': pip_pkgs}


def _build_android_sbom(repo_root: Path, apk_path: Path | None = None) -> dict:
    pyproject = tomllib.loads((repo_root / 'pyproject.toml').read_text(encoding='utf-8'))
    project = pyproject['project']
    version = project['version']
    root_ref = f'pkg:github/kuky13/bolha@{version}#android'

    gradle_info = _parse_gradle_pins(repo_root / 'android/app/build.gradle')
    components = [
        _component(
            bom_ref='pkg:generic/pestinha@0bb768a',
            comp_type='library',
            name='Pestinha (base upstream)',
            version='0bb768a2be024221ee1da62cc335362279d912d6',
            license_expr='GPL-3.0-or-later',
            publisher='mille-okws and contributors',
            vcs_url='https://github.com/mille-okws/pestinha',
        ),
        _component(
            bom_ref=f'pkg:maven/com.android.tools.build/gradle@{gradle_info["agp"]}',
            comp_type='library',
            name='Android Gradle Plugin',
            version=gradle_info['agp'],
            license_expr='Apache-2.0',
            scope='excluded',
            vcs_url='https://android.googlesource.com/platform/tools/base',
        ),
        _component(
            bom_ref=f'pkg:maven/com.chaquo.python/gradle@{gradle_info["chaquopy"]}',
            comp_type='framework',
            name='Chaquopy',
            version=gradle_info['chaquopy'],
            license_expr='MIT',
            publisher='Chaquo Ltd',
            vcs_url='https://github.com/chaquo/chaquopy/tree/17.2.0',
        ),
        _component(
            bom_ref='pkg:generic/cpython-android@3.13.16',
            comp_type='library',
            name='CPython (Android)',
            version='3.13.16',
            license_expr='PSF-2.0',
            publisher='Python Software Foundation',
            vcs_url='https://github.com/python/cpython/tree/v3.13.16',
        ),
        _component(
            bom_ref='pkg:generic/openssl-android@3.5.9',
            comp_type='library',
            name='OpenSSL (Android)',
            version='3.5.9',
            license_expr='Apache-2.0',
            publisher='The OpenSSL Project Authors',
            vcs_url='https://github.com/openssl/openssl/tree/openssl-3.5.9',
        ),
        _component(
            bom_ref='pkg:generic/sqlite-android@3',
            comp_type='library',
            name='SQLite',
            version='3',
            license_expr='Public Domain',
            publisher='SQLite Consortium',
            dist_url='https://www.sqlite.org/copyright.html',
        ),
        _component(
            bom_ref='pkg:generic/bzip2@1.0.8',
            comp_type='library',
            name='bzip2',
            version='1.0.8',
            license_expr='bzip2-1.0.6',
            publisher='Julian Seward',
            vcs_url='https://github.com/beeware/cpython-android-source-deps',
        ),
        _component(
            bom_ref='pkg:generic/libffi@3.4.4',
            comp_type='library',
            name='libffi',
            version='3.4.4',
            license_expr='MIT',
            publisher='libffi contributors',
            vcs_url='https://github.com/beeware/cpython-android-source-deps',
        ),
        _component(
            bom_ref='pkg:generic/xz-liblzma@5.4.6',
            comp_type='library',
            name='XZ Utils / liblzma',
            version='5.4.6',
            license_expr='0BSD',
            publisher='XZ Utils contributors',
            vcs_url='https://github.com/beeware/cpython-android-source-deps',
        ),
        _component(
            bom_ref='pkg:generic/openblas-android@chaquopy',
            comp_type='library',
            name='OpenBLAS (wheels NumPy Android)',
            version='0.3',
            license_expr='BSD-3-Clause',
            publisher='The OpenBLAS Project',
            vcs_url='https://github.com/chaquo/chaquopy/tree/17.2.0/server/pypi/packages',
        ),
        _component(
            bom_ref='pkg:generic/llvm-libcxx@ndk',
            comp_type='library',
            name='LLVM libc++ (libc++_shared.so)',
            version='ndk',
            license_expr='Apache-2.0 WITH LLVM-exception',
            publisher='LLVM Project',
            vcs_url='https://github.com/llvm/llvm-project',
        ),
        _component(
            bom_ref='pkg:generic/gcc-libgfortran@ndk',
            comp_type='library',
            name='GNU libgfortran (wheels NumPy Android)',
            version='gcc',
            license_expr='GPL-3.0-or-later WITH GCC-exception-3.1',
            publisher='Free Software Foundation, Inc.',
            vcs_url='https://github.com/chaquo/chaquopy/tree/17.2.0/server/pypi/packages',
        ),
    ]

    for spec in gradle_info['pip']:
        pkg_name, pkg_ver = spec.split('==', 1)
        meta = audited_python(pkg_name, pkg_ver)
        bom_ref = f'pkg:pypi/{pkg_name.lower()}@{pkg_ver}?repository_url=https://chaquo.com/pypi-upstream/'
        components.append(_component(
            bom_ref=bom_ref,
            comp_type='library',
            name=pkg_name,
            version=pkg_ver,
            license_expr=meta['license'],
            purl=bom_ref,
            publisher=meta.get('publisher', 'NumPy Developers'),
            vcs_url=meta['url'],
            dist_url='https://chaquo.com/pypi-upstream/',
        ))

    apk_hashes = None
    if apk_path is not None:
        from android.tests.audit_apk import audit as audit_apk
        apk_report = audit_apk(apk_path)
        if not apk_report['ok']:
            raise ValueError('Auditoria do APK falhou: ' + '; '.join(apk_report['errors']))
        apk_hashes = [{'alg': 'SHA-256', 'content': _sha256_file(Path(apk_path))}]
        abi_summary = ', '.join(
            f'{abi}:{info["count"]}' for abi, info in apk_report['architectures'].items()
        )
        components[2].setdefault('properties', []).append(
            {'name': 'bolha:verifiedApkElfLibraries', 'value': abi_summary}
        )

    runtime_refs = [c['bom-ref'] for c in components if c['scope'] == 'required']
    root_comp = {
        'bom-ref': root_ref,
        'type': 'application',
        'name': 'Bolha (Android APK)',
        'version': version,
        'publisher': 'André Ribeiro Lima (KukySolutions)',
        'purl': root_ref,
        'licenses': _license_entry(project['license']),
    }
    if apk_hashes:
        root_comp['hashes'] = apk_hashes

    return {
        'bomFormat': 'CycloneDX',
        'specVersion': '1.5',
        'serialNumber': f'urn:uuid:{uuid.uuid5(SBOM_NAMESPACE, f"android:{version}")}',
        'version': 1,
        'metadata': {
            'component': root_comp,
            'tools': {
                'components': [
                    {
                        'type': 'application',
                        'name': 'scripts/generate_sbom.py',
                        'version': '1.0.0',
                    }
                ]
            },
        },
        'components': components,
        'dependencies': [
            {'ref': root_ref, 'dependsOn': runtime_refs},
        ],
    }


def validate_sbom(bom: dict, target: str) -> None:
    if bom.get('bomFormat') != 'CycloneDX':
        raise ValueError(f'{target}: bomFormat deve ser CycloneDX.')
    if bom.get('specVersion') != '1.5':
        raise ValueError(f'{target}: specVersion deve ser 1.5.')
    if not str(bom.get('serialNumber', '')).startswith('urn:uuid:'):
        raise ValueError(f'{target}: serialNumber inválido.')
    meta_comp = bom.get('metadata', {}).get('component', {})
    if not meta_comp.get('name') or not meta_comp.get('version') or not meta_comp.get('licenses'):
        raise ValueError(f'{target}: metadata.component incompleto.')

    refs = {meta_comp['bom-ref']}
    names_lower = set()
    for comp in bom.get('components', []):
        for field in ('bom-ref', 'type', 'name', 'version', 'licenses'):
            if not comp.get(field):
                raise ValueError(f'{target}: componente sem campo obrigatório {field}: {comp}')
        if not (comp.get('externalReferences') or comp.get('purl') or comp.get('hashes')):
            raise ValueError(f'{target}: componente sem origem/procedência: {comp["name"]}')
        refs.add(comp['bom-ref'])
        names_lower.add(comp['name'].lower())

    for dep in bom.get('dependencies', []):
        if dep.get('ref') not in refs:
            raise ValueError(f'{target}: dependência ref desconhecida: {dep.get("ref")}')
        for sub in dep.get('dependsOn', []):
            if sub not in refs:
                raise ValueError(f'{target}: dependsOn desconhecido: {sub}')

    expected = (
        ('pyside6-essentials', 'qtsvg', 'plugins qt', 'openssl', 'mesa / llvm', 'batteryhub', 'headsetcontrol', 'winrt-runtime')
        if target == 'windows'
        else ('chaquopy', 'cpython (android)', 'numpy', 'openssl (android)', 'openblas', 'llvm libc++', 'gnu libgfortran', 'bzip2', 'libffi', 'xz utils')
    )
    for token in expected:
        if not any(token in name for name in names_lower):
            raise ValueError(f'{target}: componente esperado ausente do SBOM: {token}')


def generate(repo_root=ROOT, target='all', output_dir=None, windows_bundle=None, android_apk=None, check=False, windows_installer=None):
    repo_root = Path(repo_root).resolve()
    version = tomllib.loads((repo_root / 'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    targets = ('windows', 'android') if target == 'all' else (target,)
    results = {}

    for kind in targets:
        bom = (
            _build_windows_sbom(repo_root, Path(windows_bundle) if windows_bundle else None,
                               Path(windows_installer) if windows_installer else None)
            if kind == 'windows'
            else _build_android_sbom(repo_root, Path(android_apk) if android_apk else None)
        )
        validate_sbom(bom, kind)
        results[kind] = bom
        if output_dir:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f'bolha-{version}-{kind}.cdx.json'
            out_path.write_text(json.dumps(bom, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(f'SBOM CycloneDX 1.5 ({kind}) gravado em {out_path} ({len(bom["components"])} componentes).')
        elif check:
            print(f'SBOM CycloneDX 1.5 ({kind}) validado ({len(bom["components"])} componentes).')

    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', default=str(ROOT), help='Raiz do repositório Bolha.')
    parser.add_argument('--target', choices=('windows', 'android', 'all'), default='all')
    parser.add_argument('--output-dir', help='Diretório para gravar os arquivos *.cdx.json.')
    parser.add_argument('--windows-bundle', help='Bundle Windows descompactado para anexar hashes verificados.')
    parser.add_argument('--windows-installer', help='Instalador Windows para anexar a SHA-256.')
    parser.add_argument('--android-apk', help='APK Android para anexar hashes e bibliotecas verificadas.')
    parser.add_argument('--check', action='store_true', help='Valida estrutura CycloneDX 1.5, licenças e procedência.')
    args = parser.parse_args()
    generate(
        repo_root=args.repo_root,
        target=args.target,
        output_dir=args.output_dir,
        windows_bundle=args.windows_bundle,
        windows_installer=args.windows_installer,
        android_apk=args.android_apk,
        check=args.check,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
