# SPDX-License-Identifier: GPL-3.0-or-later
"""Leitura local via BatteryHub --json. Origem e licença em NOTICE.md."""
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from .windows_media import clean_label

# Receptores MCHOSE V9 Pro e V9 Pro 2 identificados pelo HeadsetControl e pelo BatteryHub.
USB_HEADSET_RECEIVERS = frozenset({'hsc:291d:385d', 'hsc:3837:6011', 'mchose:v9pro2'})


@dataclass(frozen=True)
class DeviceBattery:
    key: str
    name: str
    percent: int | None
    level: str
    charging: bool
    asleep: bool
    kind: str = 'other'
    connected: bool = True
    connection: str = ''

    @property
    def display(self):
        level = f'{self.percent}%' if self.percent is not None else self.level or 'Indisponível'
        state = ' · carregando' if self.charging else ' · em repouso' if self.asleep else ''
        return f'{self.name} · {level}{state}'

    def tray_tooltip(self, stale=False):
        charge = f'{self.percent}%' if self.percent is not None else 'Carga indisponível'
        detail = f'\n{charge}'
        if self.is_charging(stale):
            detail += ' · Carregando'
        elif stale:
            detail += ' · Última leitura'
        # A dica nativa reserva uma posição UTF-16 para o terminador.
        budget = 254 - len(detail.encode('utf-16-le'))
        name = self.name.encode('utf-16-le')
        if len(name) > budget:
            return name[:budget - 2].decode('utf-16-le', errors='ignore').rstrip() + '…' + detail
        return self.name + detail

    def is_charging(self, stale=False):
        return self.charging and self.connected and not self.asleep and not stale


def device_kind(kind, name, key=''):
    if key in USB_HEADSET_RECEIVERS:
        return 'headset'
    if kind == 'headset':
        if re.search(r'\b(?:earbuds?|buds|airpods(?!\s+max\b)|tws)\b', name, re.IGNORECASE):
            return 'earbuds'
        if re.fullmatch(r'hsc:[0-9a-f]{4}:[0-9a-f]{4}', key) or re.search(r'\bheadset\b', name, re.IGNORECASE):
            return 'headset'
        return 'headphones'
    if kind in ('mouse', 'headphones', 'earbuds', 'keyboard', 'gamepad', 'phone'):
        return kind
    return 'other'


def device_connection(key, via):
    if key in USB_HEADSET_RECEIVERS or via in ('2.4 ghz receiver', '2.4 ghz dongle'):
        return 'Receptor USB (2,4 GHz)'
    if via in ('usb', 'usb cable'):
        return 'Cabo USB'
    if via == 'usb dongle':
        return 'Receptor USB'
    if via.startswith('bluetooth'):
        return 'Bluetooth'
    if via == 'phone link':
        return 'Vincular ao Celular'
    return ''


def parse_devices(raw):
    if len(raw) > 256*1024:
        raise ValueError('Resposta de bateria grande demais')
    data = json.loads(raw.decode('utf-8'))
    if not isinstance(data, list):
        raise ValueError('Resposta de bateria inválida')
    devices = {}
    valid = 0
    for item in data:
        if not isinstance(item, dict):
            continue
        key, name, percent = (item.get(field) for field in ('key', 'name', 'percent'))
        if not isinstance(key, str) or not key or not isinstance(name, str):
            continue
        valid += 1
        if item.get('connected') is False and item.get('asleep') is not True:
            continue
        level = item.get('level')
        hardware_key = key.casefold()
        via = item.get('via')
        via = via.strip().casefold() if isinstance(via, str) else ''
        name = clean_label(name, 512) or 'Dispositivo sem nome'
        devices[key] = DeviceBattery(
            key, name,
            percent if type(percent) is int and 0 <= percent <= 100 else None,
            clean_label(level, 40) if isinstance(level, str) else '',
            item.get('charging') is True, item.get('asleep') is True,
            device_kind(item.get('kind'), name, hardware_key), item.get('connected') is not False,
            device_connection(hardware_key, via),
        )
    if data and not valid:
        raise ValueError('Nenhum dispositivo válido na resposta de bateria')
    return list(devices.values())


class BatteryAlerts:
    def __init__(self):
        self.above = {}

    def observe(self, devices, threshold, enabled):
        changed = []
        for device in devices:
            if device.percent is None or device.asleep:
                continue
            above = device.percent > threshold
            if self.above.get(device.key, False) and not above and not device.charging and enabled:
                changed.append(device)
            self.above[device.key] = above
        return changed


class BatteryMonitor(QObject):
    changed = Signal()

    def __init__(self, notify, folder=None):
        super().__init__()
        root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
        self.folder = folder or root / 'third_party' / 'batteryhub'
        self.notify = notify
        self.devices = []
        self.alerts = BatteryAlerts()
        self.enabled = False
        self.threshold = 15
        self.warn_low = True
        self.status = 'Leitura desativada.'
        self.success = False
        self.stale = False
        self.timed_out = False
        self.cancelled_read = False
        self.process = QProcess(self)
        self.process.finished.connect(self._finish)
        self.process.errorOccurred.connect(self._process_error)
        self.process.setStandardErrorFile(QProcess.nullDevice())
        self.period = QTimer(self, interval=60000)
        self.period.timeout.connect(self.refresh)
        self.deadline = QTimer(self, interval=15000, singleShot=True)
        self.deadline.timeout.connect(self._timeout)

    def configure(self, enabled, threshold, warn_low):
        threshold_changed = threshold != self.threshold
        self.threshold, self.warn_low = threshold, warn_low
        if threshold_changed:
            self.alerts = BatteryAlerts()
            self.alerts.observe(self.devices, self.threshold, False)
        if enabled == self.enabled:
            if threshold_changed:
                self.changed.emit()
            return
        self.enabled = enabled
        if enabled:
            self.period.start()
            self.refresh()
        else:
            self.period.stop()
            self.deadline.stop()
            self.cancelled_read = True
            self.process.kill()
            self.devices = []
            self.success = False
            self.stale = False
            self.alerts = BatteryAlerts()
            self._status('Leitura desativada.')

    def _status(self, text):
        self.status = text
        self.changed.emit()

    def refresh(self):
        if not self.enabled or self.process.state() != QProcess.NotRunning:
            return
        executable = self.folder / 'BatteryHub.exe'
        if not executable.is_file() or not (self.folder/'headsetcontrol.exe').is_file():
            self.stale = self.success
            self._status('BatteryHub ausente neste pacote.')
            return
        self.timed_out = False
        self.cancelled_read = False
        self.process.setWorkingDirectory(str(self.folder))
        self._status('Consultando periféricos…')
        self.deadline.start()
        self.process.start(str(executable), ['--json'], QProcess.ReadOnly)

    def _timeout(self):
        self.timed_out = True
        self.process.kill()

    def _failed(self):
        self.deadline.stop()
        if self.enabled:
            self.stale = self.success
            text = 'Tempo de leitura esgotado.' if self.timed_out else 'Falha na leitura de bateria.'
            if self.success:
                text += ' Exibindo a última leitura.'
            self._status(text)

    def _process_error(self, error):
        if error == QProcess.FailedToStart:
            self._failed()

    def _finish(self, code, exit_status):
        self.deadline.stop()
        raw = bytes(self.process.readAllStandardOutput())
        if not self.enabled:
            return
        if self.cancelled_read:
            self.refresh()
            return
        if code or exit_status != QProcess.NormalExit or self.timed_out:
            self._failed()
            return
        try:
            self.devices = parse_devices(raw)
        except ValueError:
            self._failed()
            return
        self.success = True
        self.stale = False
        changes = self.alerts.observe(self.devices, self.threshold, self.warn_low)
        self._status('Leitura atualizada.' if self.devices else 'Nenhum periférico compatível encontrado.')
        if changes:
            self.notify(changes)

    def stop(self):
        self.configure(False, self.threshold, self.warn_low)
        if self.process.state() != QProcess.NotRunning:
            self.process.waitForFinished(1000)
