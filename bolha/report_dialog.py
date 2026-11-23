# SPDX-License-Identifier: GPL-3.0-or-later
import platform
from pathlib import Path
from threading import Thread
from uuid import uuid4

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QFileDialog, QHBoxLayout, QLineEdit,
    QListWidget, QPlainTextEdit, QScrollArea, QVBoxLayout, QWidget,
)

from . import VERSION
from .dialogs import _button, _fit, _label
from .reports import PRIVACY_URL, error_summary, send_report, technical_summary, validate_attachments


class ReportDialog(QDialog):
    completed = Signal(str, bool)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.paths = []
        self.submission_key = uuid4().hex
        self.sending = False
        self.setWindowTitle('Relatar problema')
        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        scroll.setWidget(body)
        outer.addWidget(scroll)
        layout = QVBoxLayout(body)
        layout.addWidget(_label('O relato inclui a versão da Bolha e a plataforma. Você escolhe os demais dados.'))
        self.subject = QLineEdit(placeholderText='Título do problema', maxLength=180)
        self.subject.setAccessibleName('Título do problema')
        layout.addWidget(self.subject)
        self.description = self._text('O que aconteceu?')
        self.steps = self._text('Como reproduzir')
        layout.addWidget(self.description)
        layout.addWidget(self.steps)
        self.technical = QCheckBox('Incluir informações técnicas')
        self.errors = QCheckBox('Incluir erros da Bolha')
        for check in (self.technical, self.errors):
            layout.addWidget(check)
        self.tech_preview = self._text('Prévia editável das informações técnicas')
        self.errors_preview = self._text('Prévia editável dos erros')
        for widget in (self.tech_preview, self.errors_preview):
            widget.hide()
            layout.addWidget(widget)
        self.technical.toggled.connect(self._technical)
        self.errors.toggled.connect(self._errors)
        self.attachments = QListWidget(accessibleName='Anexos selecionados para enviar')
        self.attachments.setMaximumHeight(68)
        self.attachments.hide()
        self.attachments.itemDoubleClicked.connect(lambda *_: self._preview_attachment())
        layout.addWidget(self.attachments)
        buttons = QHBoxLayout()
        buttons.addWidget(_button('Escolher imagens ou vídeos', self._attach))
        self.remove = _button('Remover anexo', self._remove)
        self.remove.setEnabled(False)
        self.attachments.itemSelectionChanged.connect(
            lambda: self.remove.setEnabled(self.attachments.currentRow() >= 0))
        buttons.addWidget(self.remove)
        layout.addLayout(buttons)
        privacy = _label()
        privacy.setTextFormat(Qt.RichText)
        privacy.setOpenExternalLinks(True)
        privacy.setText(f'O relato será recebido em um painel privado. <a href="{PRIVACY_URL}">Política de privacidade</a>')
        layout.addWidget(privacy)
        self.consent = QCheckBox('Revisei o relato e autorizo o envio dos dados selecionados')
        layout.addWidget(self.consent)
        self.status = _label()
        self.status.setAccessibleName('Estado do envio')
        layout.addWidget(self.status)
        self.send = _button('Enviar relato', self._send)
        self.send.setEnabled(False)
        self.consent.toggled.connect(self.send.setEnabled)
        layout.addWidget(self.send)
        self.completed.connect(self._finished)
        _fit(self, 580, 590)

    def _text(self, caption):
        edit = QPlainTextEdit(placeholderText=caption)
        edit.setAccessibleName(caption)
        edit.setMaximumHeight(80)
        return edit

    def _technical(self, enabled):
        self.tech_preview.setVisible(enabled)
        if enabled:
            screens = ', '.join(f'{screen.size().width()}×{screen.size().height()} a {screen.devicePixelRatio():g}×'
                                for screen in QApplication.screens())
            prefs = self.controller.store.preferences
            modules = [name for flag, name in (('batteryEnabled', 'baterias'), ('roaming', 'passeio'),
                       ('adaptiveBehavior', 'comportamento'), ('onlineReactions', 'GIFs')) if prefs.get(flag)]
            self.tech_preview.setPlainText(technical_summary(VERSION, screens, modules))

    def _errors(self, enabled):
        self.errors_preview.setVisible(enabled)
        if enabled:
            path = self.controller.data_dir / 'logs' / 'main.log'
            self.errors_preview.setPlainText(error_summary(path))

    def _attach(self):
        selection, _ = QFileDialog.getOpenFileNames(
            self, 'Escolher anexos', '', 'Imagens e vídeos (*.png *.jpg *.jpeg *.gif *.webp *.mp4 *.webm *.mov)')
        merged = list(dict.fromkeys([*self.paths, *map(Path, selection)]))
        try:
            validate_attachments(merged)
        except (OSError, ValueError) as error:
            self.status.setText(str(error))
            return
        self.paths = merged
        self._render_attachments()

    def _remove(self):
        row = self.attachments.currentRow()
        if row >= 0:
            self.paths.pop(row)
            self._render_attachments()

    def _preview_attachment(self):
        row = self.attachments.currentRow()
        if 0 <= row < len(self.paths):
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.paths[row])))

    def _render_attachments(self):
        self.attachments.clear()
        self.attachments.addItems([path.name for path in self.paths])
        self.attachments.setVisible(bool(self.paths))
        self.remove.setEnabled(False)

    def _send(self):
        if self.sending or not self.consent.isChecked():
            return
        data = dict(title=self.subject.text().strip(), description=self.description.toPlainText().strip(),
                    steps=self.steps.toPlainText().strip(), consent=True, version=VERSION,
                    platform='Windows' if platform.system() == 'Windows' else 'Linux',
                    technical=self.tech_preview.toPlainText().strip() if self.technical.isChecked() else '',
                    errors=self.errors_preview.toPlainText().strip() if self.errors.isChecked() else '',
                    submissionId=self.submission_key)
        if len(data['title']) < 4 or len(data['description']) < 8:
            self.status.setText('Preencha o título e descreva o que aconteceu.')
            return
        if any(len(data[key]) > 4000 for key in ('description', 'steps', 'technical', 'errors')):
            self.status.setText('Cada campo pode ter até 4.000 caracteres.')
            return
        paths = tuple(self.paths)
        self.sending = True
        self.setEnabled(False)
        self.status.setText('Enviando relato…')

        def upload():
            try:
                self.completed.emit(send_report(data, paths), True)
            except (OSError, ValueError, TimeoutError):
                self.completed.emit('Não foi possível enviar. Confira os anexos ou tente novamente mais tarde.', False)

        Thread(target=upload, name='bolha-relato', daemon=True).start()

    def _finished(self, message, succeeded):
        self.sending = False
        self.setEnabled(True)
        if succeeded:
            self.status.setText('Relato recebido. Protocolo ' + message)
            self.status.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            self.consent.setChecked(False)
            self.send.setEnabled(False)
            self.consent.setEnabled(False)
        else:
            self.status.setText(message)
            self.send.setEnabled(self.consent.isChecked())

    def reject(self):
        if not self.sending:
            super().reject()
