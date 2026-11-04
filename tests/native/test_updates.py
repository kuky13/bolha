# SPDX-License-Identifier: GPL-3.0-only
import hashlib
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from unittest.mock import patch
import pytest
from bolha.migration import read_json
from bolha.updates import Transport, find_release, fetch_update, parse_checksums, validate_url, verify_file


@pytest.fixture
def feed():
    files={};data=b'NSIS test installer\0'*1000
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            entry=files.get(self.path)
            if entry is None:self.send_error(404);return
            status,headers,body=entry
            self.send_response(status)
            for key,value in headers.items():self.send_header(key,value)
            self.end_headers();self.wfile.write(body)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    base='http://127.0.0.1:'+str(server.server_port)+'/'
    name='Bolha-Setup-0.3.0-x64.exe'
    checksum=hashlib.sha256(data).hexdigest()
    sums=f'{checksum}  {name}\n'.encode()
    release=dict(tag_name='v0.3.0',draft=False,prerelease=False,assets=[
        dict(name=name,size=len(data),browser_download_url=base+name,digest='sha256:'+checksum),
        dict(name='SHA256SUMS.txt',size=len(sums),browser_download_url=base+'SHA256SUMS.txt')])
    files['/release.json']=(200,{},json.dumps(release).encode())
    files['/SHA256SUMS.txt']=(200,{},sums)
    files['/'+name]=(200,{'Content-Length':str(len(data))},data)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    yield base,files,data,release
    server.shutdown();thread.join();server.server_close()


def test_verified_download_and_cached_reverification(feed,tmp_path):
    base,files,data,_=feed
    result=fetch_update(Transport(base),'0.2.1',tmp_path/'data',tmp_path/'cache')
    path=Path(result['installer']); assert path.read_bytes()==data
    assert read_json(tmp_path/'data/pending-update.json')['sha256']==result['sha256']
    path.write_bytes(b'tampered')
    files['/Bolha-Setup-0.3.0-x64.exe']=(500,{},b'broken')
    with pytest.raises(Exception):fetch_update(Transport(base),'0.2.1',tmp_path/'data',tmp_path/'cache')
    assert not list((tmp_path/'cache').rglob('*.part'))
    with pytest.raises(ValueError):verify_file(path,result['size'],result['sha256'])


def test_bad_checksum_never_commits_download(feed,tmp_path):
    base,files,data,_=feed
    files['/Bolha-Setup-0.3.0-x64.exe']=(200,{},b'wrong'+data[5:])
    with pytest.raises(ValueError,match='integridade'):fetch_update(Transport(base),'0.2.1',tmp_path/'data',tmp_path/'cache')
    assert not list(tmp_path.rglob('*.exe'))
    assert not (tmp_path/'data/pending-update.json').exists()


def test_truncated_download_never_commits(feed,tmp_path):
    base,files,data,_=feed
    files['/Bolha-Setup-0.3.0-x64.exe']=(200,{},data[:25])
    with pytest.raises(ValueError,match='integridade'):fetch_update(Transport(base),'0.2.1',tmp_path/'data',tmp_path/'cache')
    assert not list(tmp_path.rglob('*.part'))


def test_redirect_is_validated_before_connection(feed):
    base,files,_,_=feed
    files['/redirect']=(302,{'Location':'https://example.com/steal'},b'')
    with pytest.raises(ValueError):Transport(base).read(base+'redirect',100)
    with pytest.raises(ValueError):validate_url('http://github.com/kuky13/bolha')
    with pytest.raises(ValueError):validate_url('https://github.com.evil.example/file')
    with pytest.raises(ValueError):validate_url('https://user:pass@github.com/file')
    assert validate_url('https://release-assets.githubusercontent.com/file')


def test_no_downgrade_or_prerelease_and_strict_manifest(feed):
    base,files,_,release=feed
    assert find_release(Transport(base),'0.3.0') is None
    release['prerelease']=True
    files['/release.json']=(200,{},json.dumps(release).encode())
    assert find_release(Transport(base),'0.2.1') is None
    with pytest.raises(ValueError):parse_checksums(('0'*64+'  ../escape.exe\n').encode())
    with pytest.raises(ValueError):parse_checksums(('0'*64+'  setup.exe\n') .encode()*2)


def test_api_digest_must_match_manifest(feed):
    base,files,_,release=feed
    release['assets'][0]['digest']='sha256:'+'f'*64
    files['/release.json']=(200,{},json.dumps(release).encode())
    with pytest.raises(ValueError,match='digest'):find_release(Transport(base),'0.2.1')


def test_download_never_follows_existing_temporary_symlink(feed,tmp_path):
    from bolha.updates import Release
    base,_,data,_=feed
    outside=tmp_path/'outside';outside.write_bytes(b'untouched')
    partial=tmp_path/'existing.part'
    try:partial.symlink_to(outside)
    except OSError:pytest.skip('symlinks indisponíveis')
    release=Release('0.3.0','setup.exe',base+'Bolha-Setup-0.3.0-x64.exe',len(data),hashlib.sha256(data).hexdigest())
    with pytest.raises(FileExistsError):Transport(base).download(release,partial)
    assert outside.read_bytes()==b'untouched' and partial.is_symlink()


def test_resume_offline_revalidates_native_pending_and_deferral(tmp_path,monkeypatch):
    from PySide6.QtWidgets import QApplication
    from bolha.updates import Updater
    from bolha.installation import record_update, DEFER_INTERVAL
    from bolha.migration import atomic_json
    import time
    app=QApplication.instance() or QApplication([])
    monkeypatch.setenv('BOLHA_TEST','1')
    monkeypatch.setenv('BOLHA_TEST_UPDATE_URL','http://127.0.0.1:1/')
    updater=Updater(tmp_path,'0.2.1',lambda:True,lambda:None)
    cache=updater.cache_root;cache.mkdir()
    setup=cache/'Bolha.exe';setup.write_bytes(b'verified pending')
    record_update(tmp_path,'0.3.0',setup,cache,size=setup.stat().st_size,sha256=hashlib.sha256(setup.read_bytes()).hexdigest())
    until=int(time.time()*1000)+DEFER_INTERVAL
    atomic_json(tmp_path/'update-deferred.json',dict(version='0.3.0',until=until))
    updater._deferred_version,updater._deferred_until='0.3.0',until
    with patch.object(updater.transport,'open',side_effect=AssertionError('não pode acessar rede')):
        pending=updater._resume()
        updater._apply(('resume',pending,None))
    assert updater.state['phase']=='ready' and updater.state['installAt']==until
    setup.write_bytes(b'tampered')
    with pytest.raises(ValueError):updater._resume()
    updater.stop()


def test_final_cache_write_failure_cleans_only_own_partial(feed,tmp_path):
    base,_,_,_=feed
    with patch('bolha.updates.os.replace',side_effect=PermissionError('arquivo bloqueado')):
        with pytest.raises(PermissionError):fetch_update(Transport(base),'0.2.1',tmp_path/'data',tmp_path/'cache')
    assert not list(tmp_path.rglob('*.part'))
    assert not (tmp_path/'data/pending-update.json').exists()
