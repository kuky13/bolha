# SPDX-License-Identifier: GPL-3.0-or-later
"""Novidades locais, vinculadas à versão instalada."""
import configparser
from pathlib import Path
import sys

from .migration import atomic_json, read_json
from .versioning import compare_versions, version_tuple


def read_local(path):
    try:
        value = read_json(path)
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def current_notes(version):
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    notes = read_local(root / 'assets' / 'bolha' / 'content' / 'novidades.json')
    highlights = notes.get('highlights')
    if isinstance(highlights, list) and notes.get('version') == version:
        return [text for text in highlights if isinstance(text, str)][:4]
    return []


class WelcomeState:
    def __init__(self, directory, version, install_directory=None):
        self.directory = Path(directory)
        self.file = self.directory / 'welcome.json'
        self.state = read_local(self.file)
        self.version = version
        self.previous = read_local(self.directory / 'health.json').get('version')
        self.install_directory = install_directory

    def _replaced(self):
        if self.install_directory is None:
            return False
        transaction = self.install_directory.with_name(self.install_directory.name + '.transaction.ini')
        try:
            reader = configparser.ConfigParser(interpolation=None)
            reader.read(transaction, encoding='utf-16')
            return (reader.get('recovery', 'version') == self.version and
                    compare_versions(self.version, reader.get('recovery', 'previousVersion')) > 0 and
                    reader.get('recovery', 'state') in ('active', 'installed', 'committed'))
        except (OSError, UnicodeError, ValueError, configparser.Error):
            return False

    def needs_notes(self):
        if self.state.get('notesSeen') == self.version:
            return False
        if self.state.get('notesPending') == self.version:
            return True
        for previous in (self.state.get('openedVersion'), self.previous):
            try:
                version_tuple(previous)
                if compare_versions(self.version, previous) > 0:
                    return True
            except (ValueError, TypeError):
                pass
        pending = read_local(self.directory / 'pending-update.json')
        return pending.get('version') == self.version or self._replaced()

    def record(self, **values):
        next_state = dict(self.state, **values)
        atomic_json(self.file, next_state)
        self.state = next_state
