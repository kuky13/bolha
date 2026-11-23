# SPDX-License-Identifier: GPL-3.0-or-later
"""Testes do contrato HTTP com uma interface BugPin simulada."""
import json

from fastapi.testclient import TestClient
import httpx
import pytest

from service import report_gateway as gateway


@pytest.fixture
def client(monkeypatch, tmp_path):
    gateway.windows.clear()
    monkeypatch.setenv('BUGPIN_PROJECT_KEY', 'staging')
    monkeypatch.setenv('BUGPIN_URL', 'http://private')
    monkeypatch.setenv('BUGPIN_STORAGE', str(tmp_path))
    upstream = []
    seen = set()

    class FakeBugPin:
        def __init__(self, timeout): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, headers, **kwargs):
            data = kwargs.get('json') or json.loads(kwargs['data']['data'])
            ident = data['submissionId']
            status = 200 if ident in seen else 201
            seen.add(ident)
            upstream.append((url, data, kwargs.get('files')))
            return httpx.Response(status, json={'success': True, 'reportId': 'rpt_stage123'})

    monkeypatch.setattr(gateway.httpx, 'AsyncClient', FakeBugPin)

    with TestClient(gateway.app) as value:
        yield value, upstream


def payload(**patch):
    return dict(dict(title='Teste de relato', description='Descrição sintética com passos.',
                       steps='Abra e feche a Central', version='0.5.9.4', platform='Windows',
                       submissionId='staging-123456', consent=True), **patch)


def submit(client, data, attachments=None):
    return client.post('/v1/reports', files=[
        ('data', (None, json.dumps(data))), *(attachments or ()),
    ])


def test_consent_is_required_and_unknown_fields_are_omitted(client):
    http, upstream = client
    assert submit(http, payload(consent=False)).status_code == 400
    result = submit(http, payload(secret='USER-TOKEN', path='C:/Users/Private'))
    assert result.status_code == 201 and result.json() == {'protocol': 'rpt_stage123'}
    assert 'USER-TOKEN' not in repr(upstream) and 'Private' not in repr(upstream)
    assert upstream[0][0].endswith('/api/widget/submit')


def test_unsupported_files_and_retries(client):
    http, upstream = client
    png = [('media', ('nome.png', b'\x89PNG\r\n\x1a\nfixture', 'image/png'))]
    fake = [('media', ('nome.png', b'arquivo-invalido', 'image/png'))]
    assert submit(http, payload(), fake).status_code == 415
    assert submit(http, payload(), png).json() == {'protocol': 'rpt_stage123'}
    assert submit(http, payload(), png).json() == {'protocol': 'rpt_stage123'}
    assert upstream[0][2][0][1][0].startswith('anexo-')
    assert upstream[0][1]['submissionId'] == upstream[1][1]['submissionId']
