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
