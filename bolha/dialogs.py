# SPDX-License-Identifier: GPL-3.0-only
"""Diálogos locais, abertos pelo controlador somente quando solicitados.

Controller: store.preferences; save_preferences(patch)/reset_appearance() -> dict;
startup_enabled()/set_startup(bool)/reset_learning() -> bool; diagnostics_text()
-> str; show_neural(); game; updater.state/changed/check()/defer(). Gravações que
falham lançam OSError/ValueError e preservam os dados anteriores. False retornado
por set_startup(False) significa sucesso, não erro. Os diálogos não alteram a
física nem game.panel: o controlador acompanha QDialog.finished.
reset_learning() True confirma a solicitação de backup/reinício, cuja conclusão
é assíncrona; falhas posteriores ficam no diagnóstico do controlador.
"""
import math
import time

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPalette
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QScrollArea, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QVBoxLayout, QWidget,
)
from . import VERSION
from .preferences import DEFAULTS


def _label(text=''):
    label = QLabel(text)
    label.setTextFormat(Qt.PlainText)
    label.setWordWrap(True)
    return label


def _number(value, default=0.):
    try:
        value = float(value)
        return value if math.isfinite(value) else default
    except (ValueError, TypeError, OverflowError):
        return default


def _fit(dialog, width, height):
    area = QApplication.primaryScreen().availableGeometry()
    dialog.setMinimumSize(min(430, area.width()-24), min(380, area.height()-48))
    dialog.resize(min(width, area.width()-24), min(height, area.height()-48))


def _button(text, callback):
    button = QPushButton(text)
    button.setAutoDefault(False)
    button.clicked.connect(callback)
    return button


class SettingsDialog(QDialog):
    """Aplicar salva somente campos editados, preservando sensores e precisão."""
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle('Configurações da Bolha')
        self.setAccessibleName('Configurações da Bolha')
        self._loading = True
        self.checks = {}
        self.baseline = {}
        self.startup = False
        self.tabs = QTabWidget()
        self.tabs.setAccessibleName('Categorias de configurações')
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs, 1)
        self._appearance_tab()
        self._behavior_tab()
        self._privacy_tab()
        self._app_tab()
        self.status = _label()
        self.status.setMinimumHeight(32)
        self.status.setAccessibleName('Resultado das configurações')
        layout.addWidget(self.status)
        buttons = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Close)
        self.apply_button = buttons.button(QDialogButtonBox.Apply)
        self.apply_button.setText('&Aplicar')
        self.apply_button.clicked.connect(self.apply_changes)
        buttons.button(QDialogButtonBox.Close).setText('&Fechar')
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._load(controller.store.preferences)
        try:
            self.startup = bool(controller.startup_enabled())
        except (OSError, ValueError):
            self.autostart.setEnabled(False)
            self._status('Não consegui consultar a inicialização com o Windows.', True)
        self.autostart.setChecked(self.startup)
        self._loading = False
        self._dirty()
        if getattr(controller.store, 'error', ''):
            self._status(controller.store.error, True)
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self.refresh_update)
        controller.updater.changed.connect(self.refresh_update)
        _fit(self, 590, 570)

    def _tab(self, title):
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setSpacing(12)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidget(body)
        self.tabs.addTab(scroll, title)
        return layout

    def _check(self, key, text, layout, description=''):
        control = QCheckBox(text)
        control.setObjectName(key)
        control.setAccessibleName(text)
        control.setToolTip(description)
        control.toggled.connect(self._dirty)
        self.checks[key] = control
        layout.addWidget(control)
        return control

    def _spin(self, low, high, suffix, name):
        control = QSpinBox()
        control.setRange(low, high)
        control.setSuffix(suffix)
        control.setAccessibleName(name)
        control.valueChanged.connect(self._dirty)
        return control

    def _appearance_tab(self):
        layout = self._tab('Aparência')
        layout.addWidget(_label('Ajuste o tamanho e a transparência da Bolha.'))
        form = QFormLayout()
        self.avatar_size = self._spin(80, 200, ' px', 'Tamanho da Bolha')
        self.opacity = self._spin(20, 100, ' %', 'Opacidade da Bolha')
        form.addRow('&Tamanho:', self.avatar_size)
        form.addRow('&Opacidade:', self.opacity)
        layout.addLayout(form)
        self._check('roaming', 'Passear pela tela', layout,
                    'O passeio pausa durante o arrasto, o carinho e o uso dos painéis.')
        layout.addWidget(_button('Restaurar aparência', self.reset_appearance))
        layout.addWidget(_label('Use Aplicar para salvar as alterações. Restaurar aparência altera somente tamanho e opacidade.'))
        layout.addStretch()

    def _behavior_tab(self):
        layout = self._tab('Comportamento')
        self._check('mischiefEnabled', 'Trazer memes e bilhetes', layout)
        form = QFormLayout()
        self.interval = self._spin(1, 30, ' min', 'Intervalo mínimo entre travessuras')
        self.object_limit = self._spin(1, 5, '', 'Máximo de objetos na tela')
        form.addRow('Intervalo &mínimo:', self.interval)
        form.addRow('Máximo de &objetos:', self.object_limit)
        layout.addLayout(form)
        self.checks['mischiefEnabled'].toggled.connect(self.interval.setEnabled)
        self.checks['mischiefEnabled'].toggled.connect(self.object_limit.setEnabled)
        self._check('adaptiveBehavior', 'Usar objetivos e aprendizado adaptativo', layout)
        self._check('learnRoutine', 'Aprender hábitos por horário', layout)
        layout.addWidget(_label('O aprendizado permanece neste computador. Desativar uma função preserva o que já foi aprendido.'))
        layout.addWidget(_button('Abrir painel neural', self.controller.show_neural))
        layout.addStretch()

    def _privacy_tab(self):
        layout = self._tab('Privacidade')
        layout.addWidget(_label('Escolha quais sinais locais a Bolha pode usar para entender o contexto. Cada leitura pode ser desligada separadamente.'))
        for key, text, description in (
            ('senseApp', 'Programa ativo', 'Lê o nome do processo, sem ler o título ou o conteúdo da janela.'),
            ('senseIdle', 'Tempo sem interação', 'Usa o tempo ocioso informado pelo sistema, sem registrar teclas.'),
            ('senseCursor', 'Posição do ponteiro', 'Usa a posição do ponteiro para reagir à sua presença.'),
            ('senseWindows', 'Posição e tamanho das janelas', 'Usa a geometria para pousar e evitar telas cheias, sem capturar imagens.'),
        ):
            self._check(key, text, layout, description)
            layout.addWidget(_label(description))
        layout.addStretch()

    def _app_tab(self):
        layout = self._tab('App')
        layout.addWidget(_label(f'Bolha {VERSION}'))
        self.autostart = QCheckBox('Iniciar com o Windows')
        self.autostart.setAccessibleName('Iniciar com o Windows')
        self.autostart.toggled.connect(self._dirty)
        layout.addWidget(self.autostart)
        layout.addWidget(_label('Instalações novas começam com essa opção desligada.'))
        self.update_label = _label()
        self.update_label.setAccessibleName('Estado da atualização')
        layout.addWidget(self.update_label)
        row = QHBoxLayout()
        self.check_update = _button('Verificar atualizações', self._check_update)
        self.defer_update = _button('Adiar por 1 hora', self._defer_update)
        row.addWidget(self.check_update)
        row.addWidget(self.defer_update)
        layout.addLayout(row)
        layout.addWidget(_label('Atualizações pelo GitHub Releases. A consulta acontece ao abrir e a cada seis horas.'))
        layout.addWidget(_button('Copiar diagnóstico local', self.copy_diagnostics))
        layout.addWidget(_label('O relatório fica local. Você escolhe se quer compartilhar o texto copiado.'))
        layout.addWidget(_button('Apagar aprendizado…', self.reset_learning))
        layout.addStretch()

    def _values(self):
        return dict({key: control.isChecked() for key, control in self.checks.items()},
                    avatarSize=self.avatar_size.value(), opacity=self.opacity.value()/100,
                    mischiefInterval=self.interval.value()*60, maxObjects=self.object_limit.value())

    def _load(self, preferences, appearance_only=False):
        loading = self._loading
        self._loading = True
        values = dict(DEFAULTS, **preferences)
        self.avatar_size.setValue(int(values['avatarSize']))
        self.opacity.setValue(round(values['opacity']*100))
        if not appearance_only:
            self.interval.setValue(max(1, round(values['mischiefInterval']/60)))
            self.object_limit.setValue(int(values['maxObjects']))
            for key, control in self.checks.items():
                control.setChecked(values[key])
            self.interval.setEnabled(values['mischiefEnabled'])
            self.object_limit.setEnabled(values['mischiefEnabled'])
        rendered = self._values()
        for key in ('avatarSize', 'opacity') if appearance_only else rendered:
            self.baseline[key] = rendered[key]
        self._loading = loading

    def _dirty(self, *_):
        if not self._loading:
            self.apply_button.setEnabled(self._values() != self.baseline or self.autostart.isChecked() != self.startup)

    def _status(self, text, error=False):
        self.status.setText(text)
        palette = self.palette()
        if error:
            palette.setColor(QPalette.WindowText, QColor('#9d202d' if palette.color(QPalette.Window).lightness() > 128 else '#f2b4bd'))
        self.status.setPalette(palette)

    def apply_changes(self):
        patch = {key: value for key, value in self._values().items() if self.baseline.get(key) != value}
        try:
            if patch:
                self._load(self.controller.save_preferences(patch))
            requested = self.autostart.isChecked()
            if requested != self.startup:
                actual = self.controller.set_startup(requested)
                if actual is not requested:
                    raise OSError('O Windows não confirmou a alteração.')
                self.startup = actual
        except (OSError, ValueError) as error:
            self._status(f'Não consegui concluir as alterações: {error}. Os dados já salvos foram preservados.', True)
            self._dirty()
            return
        self._dirty()
        self._status('Preferências salvas neste computador.')

    def reset_appearance(self):
        try:
            self._load(self.controller.reset_appearance(), appearance_only=True)
        except (OSError, ValueError) as error:
            self._status(f'Não consegui restaurar a aparência: {error}. Os dados anteriores foram preservados.', True)
            return
        self._dirty()
        self._status('Tamanho e opacidade restaurados. As outras preferências foram mantidas.')

    def copy_diagnostics(self):
        try:
            QApplication.clipboard().setText(self.controller.diagnostics_text())
        except (OSError, ValueError) as error:
            self._status(f'Não consegui preparar o diagnóstico: {error}.', True)
            return
        self._status('Diagnóstico copiado. Você escolhe onde compartilhar.')

    def reset_learning(self):
        question = QMessageBox(self)
        question.setWindowTitle('Apagar aprendizado da Bolha')
        question.setText('Reiniciar a memória, os hábitos e as associações aprendidas?')
        question.setInformativeText('As preferências serão mantidas. Essa ação só acontece após a confirmação.')
        erase = question.addButton('Apagar aprendizado', QMessageBox.DestructiveRole)
        cancel = question.addButton('Cancelar', QMessageBox.RejectRole)
        question.setDefaultButton(cancel)
        question.exec()
        if question.clickedButton() is not erase:
            return
        try:
            if not self.controller.reset_learning():
                raise OSError('Não foi possível concluir a gravação.')
        except (OSError, ValueError) as error:
            self._status(f'Não consegui reiniciar o aprendizado: {error}. Confira o diagnóstico local.', True)
            return
        self._status('Reinício solicitado. A Bolha guarda o backup antes de reiniciar; qualquer falha aparecerá no diagnóstico.')

    def _check_update(self):
        self.controller.updater.check()
        self.refresh_update()

    def _defer_update(self):
        self.controller.updater.defer()
        self.refresh_update()

    def refresh_update(self, *_):
        if not self.isVisible():
            return
        state = self.controller.updater.state
        phase = state.get('phase', 'idle')
        message = state.get('message')
        descriptions = dict(idle='Nenhuma atualização pendente.', checking='Consultando o GitHub…',
                            downloading=f"Baixando atualização: {max(0, min(100, _number(state.get('percent')))):.0f}%.",
                            ready=f"Versão {state.get('version', '')} pronta para instalar.",
                            verifying='Conferindo o instalador…', installing='Instalando. A Bolha será reaberta.',
                            error='A atualização falhou. Você pode continuar usando esta versão.')
        text = str(message or descriptions.get(phase, 'Aguardando atualização.'))
        deadline = _number(state.get('installAt'))
        if phase == 'ready' and deadline:
            seconds = max(0, math.ceil((deadline-time.time()*1000)/1000))
            text += f' Instalação em {seconds} s.' if seconds <= 60 else f' Instalação em {math.ceil(seconds/60)} min.'
        self.update_label.setText(text)
        self.check_update.setEnabled(phase in ('idle', 'error'))
        self.defer_update.setVisible(phase == 'ready')
        self.defer_update.setEnabled(phase == 'ready')

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_update()
        self.update_timer.start()

    def hideEvent(self, event):
        self.update_timer.stop()
        super().hideEvent(event)


class NeuralCanvas(QWidget):
    """Pontos reais da rede; brilho representa o rastro, sem conexões inventadas."""
    COLORS = ('#f0c96c', '#9bcaef', '#cda9ec', '#9ed5b3')

    def __init__(self):
        super().__init__()
        self.points = []
        self.setMinimumSize(280, 180)
        self.setAccessibleName('Atividade dos neurônios da Bolha')

    def set_network(self, positions, trace, kind):
        points = []
        for position, activity, category in zip(positions, trace, kind):
            if len(position) < 2:
                continue
            x, y = _number(position[0], .5), _number(position[1], .5)
            points.append((max(0., min(1., x)), max(0., min(1., y)),
                           max(0., min(1., _number(activity))), int(_number(category)) % 4))
        self.points = points
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.palette().base())
        painter.setPen(Qt.NoPen)
        bounds = QRectF(self.rect()).adjusted(14, 14, -14, -14)
        for x, y, activity, category in self.points:
            color = QColor(self.COLORS[category])
            color.setAlphaF(.25 + .75*activity)
            painter.setBrush(color)
            radius = 1.8 + activity*1.8
            painter.drawEllipse(QPointF(bounds.left()+x*bounds.width(), bounds.top()+y*bounds.height()), radius, radius)
        painter.end()


class NeuralDialog(QDialog):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._notice_until = 0.
        self.setWindowTitle('Cérebro da Bolha')
        self.setAccessibleName('Painel neural da Bolha')
        layout = QVBoxLayout(self)
        self.emotion = _label('Aguardando o estado da Bolha…')
        self.emotion.setAccessibleName('Emoção atual')
        layout.addWidget(self.emotion)
        row = QHBoxLayout()
        self.drives = {}
        for key, title in (('energy', 'Energia'), ('contact', 'Carência'), ('stimulation', 'Estímulo')):
            column = QVBoxLayout()
            column.addWidget(_label(title))
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setAccessibleName(title)
            column.addWidget(bar)
            row.addLayout(column)
            self.drives[key] = bar
        layout.addLayout(row)
        self.tabs = QTabWidget()
        self.tabs.setAccessibleName('Informações do cérebro')
        layout.addWidget(self.tabs, 1)
        activity = QWidget()
        activity_layout = QVBoxLayout(activity)
        self.network_title = _label()
        activity_layout.addWidget(self.network_title)
        self.canvas = NeuralCanvas()
        activity_layout.addWidget(self.canvas, 1)
        activity_layout.addWidget(_label('Cada ponto é um neurônio. O brilho mostra seu rastro de atividade.'))
        activity_layout.addWidget(_label('Amarelo: sensores · Azul: excitação · Roxo: inibição · Verde: ação'))
        self.rates = _label()
        activity_layout.addWidget(self.rates)
        self.tabs.addTab(activity, 'Atividade')
        groups = QWidget()
        groups_layout = QVBoxLayout(groups)
        groups_layout.addWidget(_label('Grupos neurais com maior atividade, em disparos por segundo.'))
        self.pools = QTableWidget(0, 2)
        self.pools.setAccessibleName('Atividade dos grupos neurais')
        self.pools.setHorizontalHeaderLabels(['Grupo', 'Atividade (Hz)'])
        self.pools.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pools.verticalHeader().hide()
        self.pools.setEditTriggers(QAbstractItemView.NoEditTriggers)
        groups_layout.addWidget(self.pools)
        self.tabs.addTab(groups, 'Grupos')
        self.learning = QPlainTextEdit()
        self.learning.setReadOnly(True)
        self.learning.setAccessibleName('Objetivos, hábitos e associações aprendidas')
        self.tabs.addTab(self.learning, 'Aprendizado')
        diagnostics = QWidget()
        diagnostics_layout = QVBoxLayout(diagnostics)
        self.metrics = _label()
        diagnostics_layout.addWidget(self.metrics)
        diagnostics_layout.addWidget(_label('RSS mede este aplicativo inteiro. A estimativa dos arrays inclui seus buffers NumPy, sem objetos e bibliotecas. Os arrays já fazem parte do RSS: não some essas medidas.'))
        diagnostics_layout.addWidget(_button('Copiar diagnóstico local', self.copy_diagnostics))
        diagnostics_layout.addStretch()
        self.tabs.addTab(diagnostics, 'Diagnóstico')
        self.status = _label()
        self.status.setAccessibleName('Estado do painel neural')
        layout.addWidget(self.status)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText('&Fechar')
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.refresh)
        _fit(self, 700, 590)

    @staticmethod
    def _rates(values, limit=8):
        return sorted(((str(key), max(0., _number(value))) for key, value in values.items()),
                      key=lambda pair: pair[1], reverse=True)[:limit]

    def refresh(self):
        if not self.isVisible() or self.isMinimized():
            return
        try:
            game = self.controller.game
            brain = game.brain
            self.canvas.set_network(brain.pos, brain.trace, brain.kind)
            emotion = dict(curioso='Curiosa', bravo='Brava', assustado='Assustada',
                           dramatico='Dramática', dormindo='Dormindo', sonolento='Sonolenta',
                           timido='Tímida', atento='Atenta', entediado='Entediada',
                           travesso='Travessa').get(game.state.emotion, str(game.state.emotion).capitalize())
            activity = dict(IDLE='Em pausa', AWAY='Ausente', PROGRAMMING='Programação',
                            DESIGNING='Criação', GAMING='Jogo', BROWSING='Navegação',
                            SOCIAL='Conversa', MUSIC='Mídia').get(game.activity, 'Outro contexto')
            self.emotion.setText(f'Emoção: {emotion} · Contexto: {activity}')
            self.network_title.setText(f'Rede local · {brain.N} neurônios')
            for key, bar in self.drives.items():
                bar.setValue(round(max(0., min(1., _number(getattr(game.drives, key))))*100))
            self.rates.setText('Impulsos: ' + ' · '.join(f'{key}: {value:.1f} Hz' for key, value in self._rates(game.rates, 3)))
            rates = self._rates(brain.pool_rates())
            self.pools.setRowCount(len(rates))
            for row, (name, value) in enumerate(rates):
                for col, text in enumerate((name, f'{value:.1f}')):
                    item = self.pools.item(row, col)
                    if item is None:
                        self.pools.setItem(row, col, QTableWidgetItem(text))
                    elif item.text() != text:
                        item.setText(text)
            summary = game.intelligence.summary(game.activity, time.time())
            lines = [f"Objetivo: {summary.get('label', 'Seguindo os impulsos da rede')}",
                     'Objetivos adaptativos: ' + ('ativos' if summary.get('enabled') else 'pausados'),
                     f"Hábitos por horário: {summary.get('slots', 0)} registros",
                     f"Memórias de interações: {summary.get('episodes', 0)}",
                     f"Decisões adaptativas: {summary.get('decisions', 0)}", '', 'Associações aprendidas (pesos):']
            learned = brain.learned_summary(8)
            lines.extend(f'{source} → {target}: {_number(weight):+.4f}' for source, target, weight in learned)
            if not learned:
                lines.append('Ainda não há associações para mostrar.')
            if summary.get('compatibility'):
                lines.extend(('', str(summary['compatibility'])))
            text = '\n'.join(lines)
            if self.learning.toPlainText() != text:
                self.learning.setPlainText(text)
            rss, arrays = _number(game.app_rss_mib), _number(game.brain_array_mib)
            self.metrics.setText(f'Aplicativo inteiro (RSS): {f"{rss:.1f} MiB" if rss > 0 else "aguardando medição"}\n'
                                 f'Arrays da rede (estimativa): {f"{arrays:.2f} MiB" if arrays > 0 else "aguardando medição"}')
            if time.monotonic() >= self._notice_until:
                self.status.clear()
        except (AttributeError, TypeError, ValueError, OSError) as error:
            self.status.setText(f'Este quadro não pôde ser atualizado: {error}. O aplicativo pode continuar aberto.')

    def copy_diagnostics(self):
        try:
            QApplication.clipboard().setText(self.controller.diagnostics_text())
        except (OSError, ValueError) as error:
            self.status.setText(f'Não consegui preparar o diagnóstico: {error}.')
            return
        self.status.setText('Diagnóstico copiado. Nenhum envio automático.')
        self._notice_until = time.monotonic()+5

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
        self.timer.start()

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def changeEvent(self, event):
        super().changeEvent(event)
        if self.isMinimized():
            self.timer.stop()
        elif self.isVisible():
            self.timer.start()
