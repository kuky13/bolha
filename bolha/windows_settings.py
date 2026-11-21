# SPDX-License-Identifier: GPL-3.0-or-later
"""Controles da Central para as integrações locais do Windows."""
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QCheckBox, QLabel, QPushButton, QSpinBox


class ShortcutButton(QPushButton):
    changed = Signal()
    capturing = Signal(bool)

    def __init__(self, label):
        super().__init__()
        self.setAccessibleName(label)
        self.value = ''
        self.listening = False
        self.double = False
        self.clicked.connect(self.begin)

    def load(self, value):
        self.value = value
        self.setText(value.replace('&', '&&'))

    def begin(self):
        if not self.listening:
            self.listening = True
            self.capturing.emit(True)
            self.setText('Pressione a tecla desejada…')

    def finish(self, value=None):
        if self.listening:
            self.listening = False
            self.capturing.emit(False)
            self.load(value or self.value)
            self.changed.emit()

    def focusOutEvent(self, event):
        self.finish()
        super().focusOutEvent(event)

    def event(self, event):
        if not self.listening:
            return super().event(event)
        if event.type() == QEvent.ShortcutOverride:
            event.accept()
            return True
        if event.type() not in (QEvent.KeyPress, QEvent.KeyRelease):
            return super().event(event)
        if event.isAutoRepeat():
            return True
        key = event.key()
        modifiers = {Qt.Key_Alt: 'Alt esquerdo', Qt.Key_Control: 'Ctrl',
                     Qt.Key_Shift: 'Shift', Qt.Key_Meta: 'Meta', Qt.Key_AltGr: 'Alt direito'}
        if key == Qt.Key_Escape:
            self.finish()
        elif event.type() == QEvent.KeyRelease and key in modifiers and self.double:
            self.finish(modifiers[key])
        elif event.type() == QEvent.KeyPress and key not in modifiers:
            value = QKeySequence(event.keyCombination()).toString(QKeySequence.PortableText)
            if value:
                self.finish(value)
        return True


def plain_label(text=''):
    label = QLabel(text)
    label.setTextFormat(Qt.PlainText)
    label.setWordWrap(True)
    return label


class WindowsSettings:
    def __init__(self, layout, features, dirty):
        self.features = features
        self.finder = QCheckBox('Localizar o cursor')
        self.double = QCheckBox('Usar dois toques rápidos')
        self.finder_key = ShortcutButton('Tecla para localizar o cursor')
        self.media = QCheckBox('Pausar ou retomar a sessão atual de mídia')
        self.media_key = ShortcutButton('Atalho de mídia')
        self.spotify = QCheckBox('Dançar quando começar outra música no Spotify')
        self.battery = QCheckBox('Ler a bateria dos periféricos')
        self.alert = QCheckBox('Avisar quando a bateria baixar')
        self.threshold = QSpinBox(minimum=1, maximum=50, suffix='%', accessibleName='Limite de bateria fraca')
        self.battery_status = plain_label()
        self.shortcut_status = plain_label()
        self.media_status = plain_label()
        self.devices = plain_label()
        self.open_panel = QPushButton('Abrir painel da bandeja')
        self.open_panel.clicked.connect(features.battery_panel.toggle)
        self.refresh = QPushButton('Atualizar baterias agora')
        self.checks = {'finderEnabled': self.finder, 'finderDouble': self.double, 'mediaEnabled': self.media,
                       'spotifyEnabled': self.spotify, 'batteryEnabled': self.battery, 'batteryAlerts': self.alert}
        for widget in self.checks.values():
            widget.toggled.connect(dirty)
        for widget in (self.finder_key, self.media_key):
            widget.changed.connect(dirty)
            widget.capturing.connect(features.capture_shortcut)
        self.threshold.valueChanged.connect(dirty)
        self.double.toggled.connect(self._mode_changed)
        for widget in (self.finder, self.double, plain_label('Tecla do localizador'), self.finder_key,
                       plain_label('A Bolha segue o ponteiro e segura uma cópia dele na boca até o próximo clique. Esc cancela. O localizador também funciona com a leitura contínua do cursor desligada.'),
                       self.media, self.media_key, self.spotify,
                       plain_label('Funciona com o aplicativo Spotify para Windows. O localizador e a dança dependem de “Janelas abertas” para respeitar a tela cheia.'),
                       self.shortcut_status, self.media_status, self.battery, self.alert, plain_label('Limite de bateria fraca'),
                       self.threshold, self.open_panel, self.refresh, self.battery_status, self.devices):
            layout.addWidget(widget)
        self.refresh.clicked.connect(features.battery.refresh)
        features.battery.changed.connect(self.refresh_status)
        self.refresh_status()

    def _mode_changed(self, double):
        self.finder_key.double = double

    def load(self, prefs):
        for key, control in self.checks.items():
            control.setChecked(prefs[key])
        self.finder_key.load(prefs['finderKey'])
        self.media_key.load(prefs['mediaKey'])
        self.threshold.setValue(prefs['batteryThreshold'])
        self.refresh_status()

    def values(self):
        return dict({key: control.isChecked() for key, control in self.checks.items()},
                    finderKey=self.finder_key.value, mediaKey=self.media_key.value,
                    batteryThreshold=self.threshold.value())

    def finish_capture(self):
        self.finder_key.finish()
        self.media_key.finish()

    def refresh_status(self):
        battery = self.features.battery
        self.refresh.setEnabled(battery.enabled)
        self.open_panel.setEnabled(battery.enabled)
        self.battery_status.setText(battery.status)
        self.devices.setText('\n'.join(device.display for device in battery.devices))
        self.shortcut_status.setText(self.features.shortcut_status)
        self.media_status.setText(self.features.media.status)
