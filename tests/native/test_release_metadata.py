# SPDX-License-Identifier: GPL-3.0-or-later
# Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
import base64
import hashlib
import pytest
from scripts.release_metadata import generate
from bolha.updates import parse_checksums
from scripts.audit_native import audit


def test_metadata_preserves_electron_and_native_integrity_contracts(tmp_path):
    content=b'NSIS installer binary fixture'
    name='Bolha-Setup-0.3.0-x64.exe'
    (tmp_path/name).write_bytes(content)
    generate(tmp_path,'0.3.0')
    latest=(tmp_path/'latest.yml').read_text()
    checksum=base64.b64encode(hashlib.sha512(content).digest()).decode()
    assert latest.count('sha512: '+checksum)==2
    assert 'version: 0.3.0\n' in latest
    assert 'path: '+name in latest and 'size: '+str(len(content)) in latest
    manifest=parse_checksums((tmp_path/'SHA256SUMS.txt').read_bytes())
    assert manifest[name]==hashlib.sha256(content).hexdigest()
    assert manifest['latest.yml']==hashlib.sha256((tmp_path/'latest.yml').read_bytes()).hexdigest()


def test_package_audit_rejects_removed_runtime(tmp_path):
    (tmp_path/'Bolha.exe').write_bytes(b'app')
    internal=tmp_path/'_internal';internal.mkdir()
    for name in ('bolha-version.json','THIRD-PARTY-NOTICES.txt','licenses/LICENSE','licenses/PYTHON-LICENSE.txt',
                 'PySide6/plugins/imageformats/qgif.dll'):
        path=internal/name;path.parent.mkdir(exist_ok=True,parents=True);path.write_text('fixture')
    audit_json=tmp_path/'audit.json'
    report=audit(tmp_path,audit_json)
    assert report['gifDecoder']=='PySide6/plugins/imageformats/qgif.dll' and report['gifDecoderPresent'] is True
    assert '"gifDecoderPresent": true' in audit_json.read_text(encoding='utf-8')
    (internal/'PySide6/plugins/imageformats/qgif.dll').unlink()
    with pytest.raises(ValueError,match='qgif.dll'):audit(tmp_path)
    (internal/'PySide6/plugins/imageformats/qgif.dll').write_text('fixture')
    (internal/'Qt6WebEngineCore.dll').write_bytes(b'bad')
    with pytest.raises(ValueError,match='Componente removido'):audit(tmp_path)
