# SPDX-License-Identifier: GPL-3.0-only
"""Servidor e limites do driver podem ser testados sem executar .exe."""
import hashlib
import json
from pathlib import Path
import shutil
from urllib.error import HTTPError
from http.client import IncompleteRead
from urllib.request import urlopen

import pytest
from scripts.test_windows_native import (Feed, NativeValidation, installer_version,
    legacy_allowed, read_json, test_environment as environment, validate_metrics, write_json)
import scripts.test_windows_native as driver


def test_legacy_never_runs_on_notebook_and_needs_hosted_runner():
    hosted = dict(GITHUB_ACTIONS='true', RUNNER_ENVIRONMENT='github-hosted', RUNNER_OS='Windows')
    assert legacy_allowed(hosted, 'github-runner')
    assert not legacy_allowed(hosted, 'KUKYBOOK26')
    assert not legacy_allowed(dict(hosted, RUNNER_ENVIRONMENT='self-hosted'), 'other')
    assert not legacy_allowed({}, 'other')


def test_environment_always_isolates_install_data_and_drops_inherited_test_flags(tmp_path, monkeypatch):
    monkeypatch.setenv('BOLHA_TEST_FAIL_START', '0.3.1')
    monkeypatch.setenv('BOLHA_TEST_LEGACY_CACHE', 'real-cache')
    env = environment(tmp_path/'data', tmp_path/'app', tmp_path/'report.json', 'http://127.0.0.1:12345/')
    assert env['BOLHA_TEST'] == env['BOLHA_TEST_ALLOW_STOP'] == '1'
    assert Path(env['BOLHA_TEST_USER_DATA']) == tmp_path/'data'
    assert Path(env['BOLHA_TEST_INSTALL_DIR']) == tmp_path/'app'
    assert 'BOLHA_TEST_FAIL_START' not in env and 'BOLHA_TEST_LEGACY_CACHE' not in env


def test_feed_exact_metadata_checksum_interruption_and_no_path_escape(tmp_path):
    installer = tmp_path/'Bolha-Setup-0.3.1-x64.exe'
    content = b'MZ'+b'fixture'*20000
    installer.write_bytes(content)
    with Feed(installer) as feed:
        release = json.load(urlopen(feed.url+'release.json'))
        assert release['tag_name'] == 'v0.3.1'
        asset = release['assets'][0]
        assert asset['size'] == len(content)
        assert asset['browser_download_url'] == feed.url+installer.name
        assert urlopen(asset['browser_download_url']).read() == content
        assert hashlib.sha256(content).hexdigest().encode() in urlopen(feed.url+'SHA256SUMS.txt').read()
        assert b'sha512:' in urlopen(feed.url+'latest.yml').read()
        with pytest.raises(HTTPError): urlopen(feed.url+'../outside.txt')
        feed.mode = 'checksum'
        assert b'0'*64 in urlopen(feed.url+'SHA256SUMS.txt').read()
        feed.mode = 'interrupted'
        with pytest.raises(IncompleteRead): urlopen(feed.url+installer.name).read()
        assert feed.interrupted
        feed.mode = 'offline'
        with pytest.raises(HTTPError) as failure: urlopen(feed.url+'release.json')
        assert failure.value.code == 503


def test_names_and_atomic_report(tmp_path):
    assert installer_version('Bolha-Setup-0.3.1-x64.exe') == '0.3.1'
    with pytest.raises(ValueError): installer_version('setup.exe')
    with pytest.raises(ValueError): installer_version('Bolha-Setup-../1-x64.exe')
    path = tmp_path/'nested/report.json'
    write_json(path, {'local':'memória ♡'})
    assert read_json(path) == {'local':'memória ♡'}
    assert not path.with_name(path.name+'.tmp').exists()


def test_stale_or_base_metrics_never_validate_new_target_health():
    health = dict(version='0.3.1', pid=222, ready=True, neurons=470)
    current = dict(version='0.3.1', pid=222, healthy=True, neurons=470, frameCount=10, thinkCount=3)
    assert validate_metrics(current, health) is current
    for invalid in ({}, dict(current, version='0.3.0'), dict(current, pid=111),
                    dict(current, healthy=False), dict(current, frameCount=0)):
        with pytest.raises(AssertionError):
            validate_metrics(invalid, health)


def test_reused_output_removes_previous_runtime_report_before_launch(tmp_path):
    base = tmp_path/'Bolha-Setup-0.3.0-x64.exe'
    target = tmp_path/'Bolha-Setup-0.3.1-x64.exe'
    base.write_bytes(b'MZbase')
    target.write_bytes(b'MZtarget')
    output = tmp_path/'reused-output'
    write_json(output/'automatic-update-runtime.json', dict(version='0.3.1', pid=111, healthy=True))
    validation = NativeValidation(base, target, output)
    try:
        env = validation.environment('automatic-update')
        assert not Path(env['BOLHA_TEST_REPORT']).exists()
        assert read_json(env['BOLHA_TEST_REPORT']) is None
        with pytest.raises(AssertionError):
            validate_metrics(read_json(env['BOLHA_TEST_REPORT']) or {}, dict(version='0.3.1',pid=222,ready=True,neurons=470))
    finally:
        shutil.rmtree(validation.root)


def test_stop_rejects_base_report_when_target_never_wrote_metrics(tmp_path, monkeypatch):
    validation = object.__new__(NativeValidation)
    validation.data, validation.exe = tmp_path/'data', tmp_path/'app/Bolha.exe'
    validation.current_report = tmp_path/'automatic-update-runtime.json'
    validation.processes = []
    monkeypatch.setattr(driver, 'process_alive', lambda *_: False)
    write_json(validation.current_report, dict(version='0.3.0', pid=111, healthy=True,
               neurons=470, frameCount=90, thinkCount=20))
    target_health = dict(version='0.3.1', pid=222, ready=True, neurons=470)
    with pytest.raises(AssertionError, match='outra versão'):
        validation.stop(target_health)
    validation.current_report.unlink()
    with pytest.raises(AssertionError):
        validation.stop(target_health)
