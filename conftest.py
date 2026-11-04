# SPDX-License-Identifier: GPL-3.0-only
"""Uma QApplication por sessão para toda a suíte (widgets e atualizador)."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope='session', autouse=True)
def qt_application():
    app=QApplication.instance() or QApplication([])
    yield app


@pytest.fixture(autouse=True)
def _block_live_reaction_network(monkeypatch):
    """Impede chamadas reais de rede para ReactionGIFs/Nekos.best na suíte de testes."""
    try:
        from bolha.reactions import ReactionTransport
    except ImportError:
        return
    def _blocked(*_args, **_kwargs):
        raise OSError('Rede bloqueada nos testes automatizados por padrão.')
    monkeypatch.setattr(ReactionTransport, 'get_bytes', _blocked)
