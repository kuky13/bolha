# SPDX-License-Identifier: GPL-3.0-or-later
"""Painel de bateria da Bolha, ancorado na bandeja do Windows."""
import getpass
from html import escape

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)


from .windows_media import clean_label


def panel_position(area, monitor, anchor, size):
    """Posiciona dentro da área útil, acima ou ao lado da bandeja."""
    x, y = anchor.right() - size.width() + 1, anchor.top() - size.height() - 8
    if anchor.center().y() < area.top():
        y = area.top() + 8
    elif anchor.center().y() >= area.bottom():
        y = area.bottom() - size.height() - 7
    elif anchor.center().x() < area.left():
        x, y = area.left() + 8, anchor.center().y() - size.height()//2
    elif anchor.center().x() >= area.right():
        x, y = area.right() - size.width() - 7, anchor.center().y() - size.height()//2
    elif not monitor.contains(anchor.center()):
        x, y = area.right() - size.width() - 7, area.bottom() - size.height() - 7
    return QPoint(max(area.left(), min(x, area.right()-size.width()+1)),
                  max(area.top(), min(y, area.bottom()-size.height()+1)))


def ordered_devices(devices):
    return sorted(devices, key=lambda device: (device.asleep, device.name.casefold(), device.key))


def battery_icon():
    icon = QIcon()
    for size in (16, 24, 32):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(size / 24., size / 24.)
        painter.setPen(QPen(QColor('#22182d'), 3))
        painter.drawRoundedRect(QRectF(2.5, 6.5, 17., 11.), 3, 3)
        painter.setPen(QPen(QColor('#eee5fa'), 1.4))
        painter.drawRoundedRect(QRectF(2.5, 6.5, 17., 11.), 3, 3)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor('#e6cf89'))
        painter.drawRoundedRect(QRectF(5, 9, 10, 6), 1.1, 1.1)
        painter.setBrush(QColor('#eee5fa'))
        painter.drawRoundedRect(QRectF(20.5, 10, 1.5, 4), .6, .6)
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def device_icon(kind):
    size = 22
    pixmap = QPixmap(size*2, size*2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.scale(2, 2)
    painter.setPen(QPen(QColor('#e5d4ff'), 1.55, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    if kind == 'mouse':
        painter.drawRoundedRect(QRectF(5.1, 2.8, 11.8, 16.4), 5, 5)
        painter.drawLine(QPointF(11, 5.4), QPointF(11, 8.4))
    elif kind == 'headset':
        painter.drawArc(QRectF(3.1, 3.9, 15.8, 16), 0, 180*16)
        painter.drawRoundedRect(QRectF(2.4, 11.5, 4.1, 6), 1.35, 1.35)
        painter.drawRoundedRect(QRectF(15.5, 11.5, 4.1, 6), 1.35, 1.35)
    elif kind == 'keyboard':
        painter.drawRoundedRect(QRectF(2, 5.4, 18, 11.2), 2, 2)
        for y in (9, 12):
            for x in (5.5, 9, 12.5, 16):
                painter.drawPoint(QPointF(x, y))
        painter.drawLine(QPointF(8, 14.2), QPointF(14, 14.2))
    elif kind == 'gamepad':
        outline = QPainterPath(QPointF(6.8, 6.1))
        outline.cubicTo(3.4, 6.1, 2.6, 10, 2.1, 13.8)
        outline.cubicTo(1.8, 17.2, 5.6, 17.2, 8.2, 13.6)
        outline.lineTo(13.8, 13.6)
        outline.cubicTo(16.4, 17.2, 20.2, 17.2, 19.9, 13.8)
        outline.cubicTo(19.4, 10, 18.6, 6.1, 15.2, 6.1)
        outline.closeSubpath()
        painter.drawPath(outline)
        painter.drawLine(QPointF(6.4, 8.6), QPointF(6.4, 12))
        painter.drawLine(QPointF(4.7, 10.3), QPointF(8.1, 10.3))
        painter.drawPoint(QPointF(15.2, 9.3))
        painter.drawPoint(QPointF(17, 11))
    elif kind == 'phone':
        painter.drawRoundedRect(QRectF(5.5, 2.4, 11, 17.2), 2.2, 2.2)
        painter.drawLine(QPointF(9.4, 16.5), QPointF(12.6, 16.5))
    else:
        painter.drawRoundedRect(QRectF(4, 4, 14, 14), 3, 3)
        painter.drawEllipse(QPointF(11, 11), 2, 2)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return pixmap


def label(text='', name=''):
    widget = QLabel(text, objectName=name)
    widget.setTextFormat(Qt.PlainText)
    widget.setWordWrap(True)
    return widget


class BatteryPanel(QFrame):
    def __init__(self, monitor, tray):
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint)
        self.monitor = monitor
        self.tray = tray
        self._rendered = None
        try:
            self.local_user = clean_label(getpass.getuser(), 90)
        except (ImportError, KeyError, OSError):
            self.local_user = ''
        self.setObjectName('batteryPanel')
        self.setWindowTitle('Baterias da Bolha')
        self.setAccessibleName('Baterias dos periféricos')
        self.setFixedWidth(310)
        self.rows_height = 0
        self.setStyleSheet("""
            QFrame#batteryPanel { background: #211d2c; border: 1px solid #65557e; }
            QLabel { background: transparent; color: #f7f2ff; font-size: 13px; }
            QLabel#batteryTitle { font-size: 19px; font-weight: 650; }
            QLabel#batteryStatus, QLabel#batteryGroup { color: #ccc0db; font-size: 12px; }
            QFrame#batteryRow { background: #30293e; border-radius: 9px; }
            QFrame#batteryTile { background: #453857; border-radius: 8px; }
            QScrollArea { border: none; background: #211d2c; }
            QWidget#batteryRows { background: #211d2c; }
            QPushButton { background: #3e3354; color: #f7f2ff; padding: 6px 9px;
                          border: 1px solid #66547f; border-radius: 7px; }
            QPushButton:focus, QPushButton:hover { border-color: #e2ceff; }
            QProgressBar { background: #171321; border: none; border-radius: 3px; height: 6px; }
            QProgressBar::chunk { background: #cab6f7; border-radius: 3px; }
            QProgressBar[lowBattery=true]::chunk { background: #ffa3a8; }
            QProgressBar[charging=true]::chunk { background: #8de0ad; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(13,12,13,12)
        header = QHBoxLayout()
        header.addWidget(label('Baterias', 'batteryTitle'), 1)
        self.refresh = QPushButton('Atualizar')
        self.refresh.setAccessibleName('Atualizar leituras de bateria')
        self.refresh.clicked.connect(monitor.refresh)
        header.addWidget(self.refresh)
        layout.addLayout(header)
        self.status = label('', 'batteryStatus')
        layout.addWidget(self.status)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.scroll)
        monitor.changed.connect(self.sync)
        self.sync()

    def toggle(self):
        if self.isVisible():
            self.hide()
            return
        self.sync()
        self.show()
        self._place()
        self.raise_()
        if self.monitor.enabled:
            self.refresh.setFocus(Qt.OtherFocusReason)
            self.monitor.refresh()

    def _place(self):
        anchor = self.tray.geometry()
        screen = QGuiApplication.screenAt(anchor.center()) if anchor.isValid() else None
        screen = screen or QGuiApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            if not anchor.isValid():
                corner = screen.geometry().bottomRight()
                anchor = QRect(corner, corner)
            self.scroll.setFixedHeight(min(self.rows_height, 355, max(40, area.height() - 120)))
            self.layout().activate()
            self.adjustSize()
            self.move(panel_position(area, screen.geometry(), anchor, self.size()))

    def tray_text(self):
        active = sum(not device.asleep for device in self.monitor.devices)
        return f'Bolha · Baterias ({active} em uso)' if active else 'Bolha · Baterias'

    def sync(self):
        self.status.setText(self.monitor.status)
        self.refresh.setEnabled(self.monitor.enabled)
        devices = ordered_devices(self.monitor.devices)
        snapshot = (tuple(devices), self.monitor.threshold)
        # O sinal de progresso/erro pode mudar apenas a mensagem. Nesse caso,
        # conserva o viewport e os widgets de dispositivo já exibidos.
        if snapshot != self._rendered:
            self._rendered = snapshot
            rows = QWidget(objectName='batteryRows')
            column = QVBoxLayout(rows)
            column.setContentsMargins(0, 0, 0, 0)
            column.setSpacing(6)
            for asleep, title in ((False, 'Em uso'), (True, 'Em repouso')):
                group = [device for device in devices if device.asleep == asleep]
                if group:
                    column.addWidget(label(title, 'batteryGroup'))
                for device in group:
                    column.addWidget(self._row(device))
            self.scroll.setWidget(rows)
            rows.ensurePolished()
            column.activate()
            self.rows_height = rows.sizeHint().height() + 2
            self.scroll.setVisible(bool(devices))
            if devices:
                # QScrollArea ignora o sizeHint do filho. Dê ao viewport espaço
                # explícito, inclusive quando a primeira leitura chega oculto.
                rows.setMinimumHeight(self.rows_height - 2)
        self.tray.setToolTip(self.tray_text())
        if self.isVisible():
            self._place()

    def _row(self, device):
        row = QFrame(objectName='batteryRow')
        tooltip = f'<b>{escape(device.name)}</b>'
        if self.local_user:
            tooltip += f'<br>Usuário do Windows: {escape(self.local_user)}'
        row.setToolTip(tooltip)
        content = QHBoxLayout(row)
        content.setContentsMargins(9,8,10,8)
        content.setSpacing(9)
        tile = QFrame(objectName='batteryTile')
        tile.setFixedWidth(79)
        tile.setToolTip(tooltip)
        tile_layout = QVBoxLayout(tile)
        tile_layout.setContentsMargins(6, 4, 6, 5)
        tile_layout.setSpacing(3)
        top = QHBoxLayout()
        tile_layout.addLayout(top)
        icon = QLabel(objectName='batteryDeviceIcon')
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(22, 22)
        icon.setPixmap(device_icon(device.kind))
        icon.setToolTip(tooltip)
        top.addWidget(icon)
        percent = label(f'{device.percent}%' if device.percent is not None else '—')
        percent.setWordWrap(False)
        top.addWidget(percent, 0, Qt.AlignRight)
        content.addWidget(tile, 0, Qt.AlignVCenter)
        if device.percent is not None:
            meter = QProgressBar()
            meter.setAccessibleName(f'Carga de {device.name}')
            meter.setRange(0, 100)
            meter.setValue(device.percent)
            meter.setTextVisible(False)
            meter.setFixedHeight(5)
            meter.setProperty('lowBattery', device.percent <= self.monitor.threshold)
            meter.setProperty('charging', device.charging)
            tile_layout.addWidget(meter)
        details = QVBoxLayout()
        details.setSpacing(3)
        content.addLayout(details, 1)
        name = label(device.name)
        name.setToolTip(tooltip)
        details.addWidget(name)
        if device.percent is None:
            reason = 'Carga indisponível'
            if device.level:
                reason += ' · ' + device.level
            details.addWidget(label(reason, 'batteryStatus'))
        if device.charging:
            details.addWidget(label('Carregando', 'batteryStatus'))
        return row
