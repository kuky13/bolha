
from bolha.migration import atomic_json
from bolha.preferences import PreferencesStore
from bolha.reports import error_summary
from bolha.welcome import WelcomeState, current_notes


def test_new_defaults_are_safe_and_existing_profile_keeps_values(tmp_path):
    fresh = PreferencesStore(tmp_path)
    assert fresh.preferences['avatarSize'] == 90
    assert fresh.preferences['objectScales']['notebook'] == 1.2
    assert fresh.preferences['cursorPrankEnabled'] is False
    fresh.save({'avatarSize': 147, 'cursorPrankEnabled': True, 'senseCursor': False})
    old = PreferencesStore(tmp_path)
    assert old.preferences['avatarSize'] == 147
    assert old.preferences['cursorPrankEnabled'] is True
    assert old.preferences['senseCursor'] is False


def test_release_notes_are_once_per_version_even_if_cleanup_runs_before_view(tmp_path):
    version = '0.5.9.4'
    state = WelcomeState(tmp_path, version)
    assert current_notes(version)
    assert not state.needs_notes()
    atomic_json(tmp_path / 'pending-update.json', {'version': version})
    assert state.needs_notes()
    state.record(openedVersion=version, notesPending=version)
    (tmp_path / 'pending-update.json').unlink()
    assert WelcomeState(tmp_path, version).needs_notes()
    state.record(notesSeen=version)
    assert not WelcomeState(tmp_path, version).needs_notes()


def test_report_log_summary_uses_known_labels_only(tmp_path):
    log = tmp_path / 'main.log'
    log.write_text('Traceback token=SECRET C:\\Users\\Victim\\arquivo.docx\n'
                   'Atualização: https://host.invalid/?token=SECRET\n'
                   'Conversa pessoal que nunca sai\n', encoding='utf-8')
    result = error_summary(log)
    assert result.splitlines() == ['Exceção registrada', 'Falha na atualização']
    assert not any(term in result for term in ('SECRET', 'Victim', 'pessoal'))
