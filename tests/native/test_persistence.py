# SPDX-License-Identifier: GPL-3.0-only
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from bolha.migration import prepare_data, read_json
from bolha.preferences import PreferencesStore, SENSOR_KEYS
from bolha.installation import (cleanup_applied_update, cached_installer, compare_versions,
                               read_deferral, record_update, DEFER_INTERVAL)


def test_migration_preserves_memory_optouts_and_backup(tmp_path):
    memory = tmp_path/'brain/drippy'; memory.mkdir(parents=True)
    (memory/'seed.json').write_text('{"seed":1313}', encoding='utf-8')
    old = {'preferences':dict(senseCursor=False,senseWindows=False,avatarSize=150,musicControls=False)}
    (tmp_path/'config.json').write_text(json.dumps(old), encoding='utf-8')
    store = PreferencesStore(tmp_path)
    assert store.preferences['senseCursor'] is store.preferences['senseWindows'] is False
    assert store.preferences['avatarSize'] == 150
    assert 'musicControls' not in store.preferences
    marker = read_json(tmp_path/'native-migration.json')
    backup = Path(marker['backup'])
    assert read_json(backup/'config.json') == old
    assert (backup/'brain/drippy/seed.json').read_bytes() == (memory/'seed.json').read_bytes()
    assert not (tmp_path/'brain/bolha').exists()
    prepare_data(tmp_path)
    assert len(list((tmp_path/'backups').iterdir())) == 1


def test_both_memory_directories_are_preserved(tmp_path):
    for name in ('drippy','bolha'):
        (tmp_path/'brain'/name).mkdir(parents=True)
        (tmp_path/'brain'/name/'seed').write_text(name)
    prepare_data(tmp_path)
    for name in ('drippy','bolha'):
        assert (tmp_path/'brain'/name/'seed').read_text() == name


def test_backup_write_failure_never_migrates_source(tmp_path):
    old = tmp_path/'brain/drippy'; old.mkdir(parents=True)
    (old/'seed').write_text('1313')
    with patch('bolha.migration.shutil.copy2', side_effect=OSError('disk full')):
        with pytest.raises(OSError): prepare_data(tmp_path)
    assert (old/'seed').read_text() == '1313'
    assert not (tmp_path/'brain/bolha').exists()
    assert not (tmp_path/'native-migration.json').exists()


def test_corrupt_preferences_are_preserved_and_sensors_not_reenabled(tmp_path):
    content = b'{"preferences": {broken'
    (tmp_path/'config.json').write_bytes(content)
    store = PreferencesStore(tmp_path)
    assert store.error
    assert not any(store.preferences[k] for k in SENSOR_KEYS)
    assert (tmp_path/'config.json').read_bytes() == content
    assert list((tmp_path/'backups').glob('*/config.json'))[0].read_bytes() == content


def test_failed_save_keeps_runtime_and_disk_consistent(tmp_path):
    store = PreferencesStore(tmp_path)
    store.save({'senseApp': False, 'opacity': .4})
    saved = (tmp_path/'config.json').read_bytes()
    with patch('bolha.preferences.atomic_json', side_effect=OSError('read-only')):
        with pytest.raises(OSError): store.save({'senseApp': True})
    assert not store.preferences['senseApp']
    assert (tmp_path/'config.json').read_bytes() == saved
    store.reset_appearance()
    assert not store.preferences['senseApp'] and store.preferences['opacity'] == 1


def test_pending_cleanup_only_after_healthy_version_and_inside_cache(tmp_path):
    data = tmp_path/'data'; cache = tmp_path/'cache'
    target = cache/'pending/Bolha.exe'; target.parent.mkdir(parents=True)
    target.write_bytes(b'installer')
    part = target.with_suffix('.exe.part'); part.write_bytes(b'partial')
    other = target.parent/'user-document.txt'; other.write_text('keep')
    record_update(data, '0.3.0', target, cache)
    assert not cleanup_applied_update(data, '0.2.1', cache)
    assert target.exists()
    assert cleanup_applied_update(data, '0.3.0', cache)
    assert not target.exists() and not part.exists() and other.exists()
    assert not (data/'pending-update.json').exists()
    outside = tmp_path/'outside.exe'; outside.write_bytes(b'keep')
    with pytest.raises(ValueError): record_update(data,'0.3.0',outside,cache)
    (data/'pending-update.json').write_text(json.dumps(dict(version='0.3.0',installer=str(outside))))
    with pytest.raises(ValueError): cleanup_applied_update(data,'0.3.0',cache)
    assert outside.exists()


def test_symlink_cannot_escape_cache(tmp_path):
    cache=tmp_path/'cache';cache.mkdir()
    outside=tmp_path/'outside';outside.mkdir()
    try: (cache/'junction').symlink_to(outside, target_is_directory=True)
    except OSError: pytest.skip('symlinks indisponíveis')
    with pytest.raises(ValueError): cached_installer(cache,cache/'junction/setup.exe')


def test_deferral_is_epoch_ms_persistent_and_bounded(tmp_path):
    now=10000000000
    (tmp_path/'update-deferred.json').write_text(json.dumps(dict(version='0.3.0',until=now+DEFER_INTERVAL*4)))
    assert read_deferral(tmp_path,now)==('0.3.0',now+DEFER_INTERVAL)
    assert read_deferral(tmp_path,now+DEFER_INTERVAL*5)==('',0)
    assert compare_versions('0.3.0','0.2.1')==1
    with pytest.raises(ValueError):compare_versions('v0.3.0','0.2.1')


def test_recovery_cleanup_preserves_foreign_files_and_legacy_backup(tmp_path):
    import hashlib
    from bolha.installation import cleanup_recovery, APP_ID
    install=tmp_path/'Bolha';install.mkdir()
    backup=tmp_path/'Bolha.rollback-123';backup.mkdir()
    (backup/'Bolha.exe').write_bytes(b'old')
    (backup/'user.txt').write_text('keep')
    (backup/'bolha-native-installation.flag').write_text('bolha-native:solutions.kuky.bolha')
    (backup/'installed-files.json').write_text(json.dumps(dict(appId=APP_ID,files={'Bolha.exe':hashlib.sha256(b'old').hexdigest()})))
    transaction=tmp_path/'Bolha.transaction.ini'
    transaction.write_text(f'[recovery]\nbackup={backup}\nversion=0.3.0\nstate=committed\n',encoding='utf-16')
    cleanup_recovery(tmp_path/'data',install,'0.3.0')
    assert not (backup/'Bolha.exe').exists() and (backup/'user.txt').read_text()=='keep'
    assert not transaction.exists()
    assert str(backup) in read_json(tmp_path/'data/installation-recovery.json')['retained']


def test_recovery_rejects_outside_path_without_deleting_anything(tmp_path):
    from bolha.installation import cleanup_recovery
    outside=tmp_path/'documents';outside.mkdir();(outside/'keep').write_text('keep')
    transaction=tmp_path/'Bolha.transaction.ini'
    transaction.write_text(f'[recovery]\nbackup={outside}\nversion=0.3.0\nstate=committed\n',encoding='utf-16')
    with pytest.raises(ValueError):cleanup_recovery(tmp_path/'data',tmp_path/'Bolha','0.3.0')
    assert (outside/'keep').read_text()=='keep'


def test_health_before_installer_commit_never_removes_recovery(tmp_path):
    from bolha.installation import cleanup_recovery
    backup=tmp_path/'Bolha.rollback-123';backup.mkdir();(backup/'keep').write_text('old')
    transaction=tmp_path/'Bolha.transaction.ini'
    transaction.write_text(f'[recovery]\nbackup={backup}\nversion=0.3.0\nstate=active\n',encoding='utf-16')
    assert cleanup_recovery(tmp_path/'data',tmp_path/'Bolha','0.3.0') is False
    assert transaction.exists() and (backup/'keep').read_text()=='old'
    transaction.write_text(f'[recovery]\nbackup={backup}\nversion=0.3.0\nstate=committed\n',encoding='utf-16')
    assert cleanup_recovery(tmp_path/'data',tmp_path/'Bolha','0.3.0') is True
    assert (backup/'keep').exists() and not transaction.exists()


def test_failed_native_startup_preserves_legacy_path_and_retry_reads_new_learning(tmp_path):
    """A versão recuperada 0.1 pode continuar gravando antes de outra tentativa nativa."""
    import numpy as np
    from game import Game
    content=Path(__file__).resolve().parents[2]/'assets/bolha/content'
    brain=tmp_path/'brain'
    original=Game(brain,content)
    original.brain.learned[0,0]=.06
    original.save()
    legacy=brain/'drippy'
    (brain/'bolha').rename(legacy)  # Simula o perfil real 0.1; não é conversão do aplicativo.
    before={path.name:path.read_bytes() for path in legacy.iterdir() if path.is_file()}
    prepare_data(tmp_path)
    # Falha depois de ler a rede, antes de o aplicativo conseguir confirmar saúde.
    with patch('game.Drives',side_effect=RuntimeError('inicialização interrompida')):
        with pytest.raises(RuntimeError,match='inicialização interrompida'):Game(brain,content)
    assert legacy.is_dir() and not (brain/'bolha').exists()
    assert {path.name:path.read_bytes() for path in legacy.iterdir() if path.is_file()}==before
    # A versão antiga recuperada atualiza os mesmos pesos no caminho que sempre usou.
    original.brain.learned[0,0]=.07
    original.brain.save(legacy/'nervous.json')
    updated=(legacy/'nervous.json').read_bytes()
    prepare_data(tmp_path)  # Retry é idempotente e não restaura uma cópia de pesos obsoleta.
    resumed=Game(brain,content)
    assert resumed.pet_paths.base==legacy
    assert np.isclose(resumed.brain.learned[0,0],.07)
    assert (legacy/'nervous.json').read_bytes()==updated
    assert not (brain/'bolha').exists()
    backups=list((tmp_path/'backups').glob('*/brain/drippy/nervous.json'))
    assert len(backups)==1 and backups[0].read_bytes()==before['nervous.json']
