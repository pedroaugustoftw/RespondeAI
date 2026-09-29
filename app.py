import os
import sys
from html import escape
from pathlib import Path

import keyring
from PySide6.QtCore import Qt, QRect, QPoint, QBuffer, QIODevice, QThread, Signal, QTimer, QSize, QStandardPaths
from PySide6.QtGui import QColor, QPainter, QPen, QShortcut, QKeySequence, QFont, QIcon
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QCheckBox, QDialogButtonBox, QMessageBox, QComboBox,
    QStackedWidget, QListWidget, QScrollArea, QListWidgetItem)

from core import Store, solve, DEFAULT_MODEL, DEFAULT_VISION_MODEL, DEFAULT_GEMINI_MODEL
from ui import Panel, PanelDialog, TitleBar, Spinner, icon, icon_button

STYLE = '''
QWidget { background:transparent; color:#eef1ff; font-family:"Segoe UI"; font-size:13px; }
QLabel#brand { font-size:18px; font-weight:600; }
QLabel#logo { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #5279ff,stop:1 #4837fa); border-radius:9px; }
QLabel#muted { color:#a6b4d0; font-size:12px; }
QPushButton { background:#19222d; border:1px solid #364355; border-radius:10px; padding:8px 12px; }
QPushButton:hover { background:#293952; }
QPushButton#primary { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #507cff,stop:1 #2c53ff); border:1px solid #5b7aff; font-weight:600; font-size:17px; border-radius:13px; }
QPushButton#primary:hover { background:#5078ff; }
QPushButton:disabled { background:#26334a; color:#8290a8; }
QPushButton#iconButton { padding:0; }
QPushButton#windowButton,QPushButton#closeButton { border:0; background:transparent; padding:0; border-radius:6px; }
QPushButton#windowButton:hover { background:#293952; }
QPushButton#closeButton:hover { background:#873644; }
QTextEdit,QLineEdit,QSpinBox,QComboBox { background:#19222f; border:1px solid #303b4c; border-radius:8px; padding:8px; selection-background-color:#345cc4; }
QTextEdit#answer { font-size:17px; border-radius:13px; padding:14px; }
QProgressBar { background:#3d4964; border:0; border-radius:4px; min-height:7px; max-height:7px; }
QProgressBar::chunk { background:#4bd58b; border-radius:4px; }
QWidget#divider { background:#263140; }
QLabel#success { color:#65de99; font-weight:600; font-size:15px; }
QWidget#historyCard { background:#19222d; border:1px solid #273343; border-radius:12px; }
QPushButton#historyAnswer { background:transparent; border:0; text-align:left; padding:0; color:#b4c3e0; }
QListWidget { background:transparent; border:0; padding:10px; outline:0; }
QListWidget::item { padding:13px 10px; border-radius:9px; margin-bottom:4px; }
QListWidget::item:selected { background:#1e304e; color:#65a1ff; }
QScrollArea { border:0; }
QScrollBar:vertical { background:transparent; width:6px; margin:3px; }
QScrollBar::handle:vertical { background:#43516a; border-radius:3px; min-height:20px; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0; }
QMessageBox { background:#141e2b; }
QComboBox QAbstractItemView { background:#19222f; selection-background-color:#2e4770; }
'''


class Selection(QWidget):
    selected = Signal(bytes)
    cancelled = Signal()

    def __init__(self, screen):
        super().__init__()
        self.snapshot = screen.grabWindow(0)
        self.origin = None
        self.current = QPoint()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setGeometry(screen.geometry())
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)
        toolbar = QWidget(self)
        toolbar.setStyleSheet('background:#111923; border:1px solid #354052; border-radius:12px;')
        toolbar.setGeometry(max(0, (self.width()-350)//2), 30, 350, 48)
        row = QHBoxLayout(toolbar)
        row.setContentsMargins(14, 4, 8, 4)
        label = QLabel('Selecione a área da tela')
        label.setStyleSheet('border:0; font-size:14px;')
        row.addWidget(label)
        cancel = icon_button('close', 'Cancelar captura (Esc)', 30)
        cancel.clicked.connect(self.cancel)
        row.addWidget(cancel)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.snapshot)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 115))
        if self.origin is not None:
            area = QRect(self.origin, self.current).normalized().intersected(self.rect())
            painter.save()
            painter.setClipRect(area)
            painter.drawPixmap(self.rect(), self.snapshot)
            painter.restore()
            painter.setPen(QPen(QColor('#82a4ff'), 2, Qt.DashLine))
            painter.drawRect(area)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.position().toPoint()
            self.current = self.origin
            self.update()

    def mouseMoveEvent(self, event):
        self.current = event.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or self.origin is None:
            return
        area = QRect(self.origin, event.position().toPoint()).normalized().intersected(self.rect())
        if area.width() < 15 or area.height() < 15:
            self.origin = None
            self.update()
            return
        ratio = self.snapshot.devicePixelRatio()
        crop = self.snapshot.copy(QRect(round(area.x()*ratio), round(area.y()*ratio),
                                       round(area.width()*ratio), round(area.height()*ratio)))
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        crop.save(buffer, 'PNG')
        self.hide()
        self.selected.emit(bytes(buffer.data()))
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel()

    def cancel(self):
        self.close()
        self.cancelled.emit()


class Worker(QThread):
    result = Signal(str, bool)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(self, store, png, key, model, provider=None):
        super().__init__()
        self.args = store, png, key, model
        self.provider = provider or store.get('provider', 'groq')

    def run(self):
        try:
            self.result.emit(*solve(*self.args, progress=self.progress.emit,
                                     cancelled=self.isInterruptionRequested, provider=self.provider))
        except Exception as exc:
            self.failed.emit(str(exc))


class Window(Panel):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.worker = None
        self.selector = None
        self.setWindowTitle('RespondeAI')
        self.setFixedSize(340, 232)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(TitleBar(self))
        self.header_line = QWidget()
        self.header_line.setObjectName('divider')
        self.header_line.setFixedHeight(1)
        self.header_line.hide()
        layout.addWidget(self.header_line)
        self.pages = QStackedWidget()
        layout.addWidget(self.pages)
        home = QWidget()
        home_layout = QVBoxLayout(home)
        home_layout.setContentsMargins(20, 10, 20, 18)
        home_layout.setSpacing(16)
        self.start = QPushButton('  Iniciar')
        self.start.setIcon(icon('scan', '#ffffff', 26))
        self.start.setIconSize(QSize(26, 26))
        self.start.setObjectName('primary')
        self.start.setFixedHeight(64)
        self.start.clicked.connect(self.capture)
        home_layout.addWidget(self.start)
        row = QHBoxLayout()
        self.settings_button = icon_button('settings', 'Configurações', 46)
        self.settings_button.clicked.connect(self.settings)
        row.addWidget(self.settings_button)
        row.addStretch()
        meter, self.counter, self.progress = self.make_meter()
        row.addWidget(meter)
        row.addStretch()
        history = icon_button('history', 'Histórico', 46)
        history.clicked.connect(self.history)
        row.addWidget(history)
        home_layout.addLayout(row)
        self.pages.addWidget(home)
        result = QWidget()
        result_layout = QVBoxLayout(result)
        result_layout.setContentsMargins(20, 10, 20, 18)
        result_layout.setSpacing(12)
        summary = QHBoxLayout()
        self.result_label = QLabel('Resposta')
        self.result_label.setObjectName('success')
        self.result_check = QLabel()
        self.result_check.setPixmap(icon('check', '#0f2921', 20).pixmap(QSize(20, 20)))
        self.result_check.setAlignment(Qt.AlignCenter)
        self.result_check.setFixedSize(30, 30)
        self.result_check.setStyleSheet('background:#59d98b; border-radius:15px;')
        summary.addWidget(self.result_check)
        summary.addWidget(self.result_label)
        summary.addStretch()
        meter, self.result_counter, self.result_progress = self.make_meter()
        summary.addWidget(meter)
        result_layout.addLayout(summary)
        self.status = QLabel()
        self.status.setObjectName('muted')
        self.status.setWordWrap(True)
        self.status.hide()
        result_layout.addWidget(self.status)
        self.answer = QTextEdit()
        self.answer.setObjectName('answer')
        self.answer.setReadOnly(True)
        self.answer.setMinimumHeight(70)
        self.answer.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        result_layout.addWidget(self.answer, 1)
        self.busy = QWidget()
        busy_layout = QVBoxLayout(self.busy)
        busy_layout.setContentsMargins(8, 0, 8, 0)
        busy_layout.setSpacing(8)
        busy_layout.addStretch()
        self.spinner = Spinner()
        busy_layout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        self.busy_label = QLabel('Preparando sua resposta…')
        self.busy_label.setAlignment(Qt.AlignCenter)
        self.busy_label.setWordWrap(True)
        self.busy_label.setStyleSheet('font-size:15px; color:#d0dcf3;')
        busy_layout.addWidget(self.busy_label)
        busy_layout.addStretch()
        self.busy.hide()
        result_layout.addWidget(self.busy, 1)
        actions = QHBoxLayout()
        self.copy = icon_button('copy', 'Copiar resposta', 44, primary=True)
        self.copy.clicked.connect(lambda: QApplication.clipboard().setText(self.answer.toPlainText()))
        actions.addWidget(self.copy)
        self.new = QPushButton('  Novo')
        self.new.setIcon(icon('refresh'))
        self.new.setFixedHeight(44)
        self.new.clicked.connect(self.new_or_cancel)
        actions.addWidget(self.new, 1)
        self.result_settings = icon_button('settings', 'Configurações', 44)
        self.result_settings.clicked.connect(self.settings)
        actions.addWidget(self.result_settings)
        result_layout.addLayout(actions)
        self.pages.addWidget(result)
        self.shortcut = QShortcut(QKeySequence('Ctrl+Shift+X'), self)
        self.shortcut.activated.connect(self.capture)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.refresh()

    def make_meter(self):
        meter = QWidget()
        meter.setFixedWidth(112)
        layout = QVBoxLayout(meter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        counter = QLabel()
        counter.setAlignment(Qt.AlignCenter)
        counter.setStyleSheet('color:#c7d3f1; font-size:12px;')
        progress = QProgressBar()
        progress.setTextVisible(False)
        layout.addWidget(counter)
        layout.addWidget(progress)
        return meter, counter, progress

    def new_or_cancel(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.result_label.setText('Cancelando…')
            self.new.setEnabled(False)
        else:
            self.capture()

    def result_page(self, title, success=False):
        self.header_line.show()
        self.pages.setCurrentIndex(1)
        self.setFixedSize(400, 300)
        self.result_label.setText(title)
        self.result_check.setVisible(success)
        self.status.hide()
        self.busy.hide()
        self.answer.show()
        self.keep_on_screen()

    def show_progress(self, message):
        if self.worker and self.worker.isInterruptionRequested():
            return
        self.result_label.setText('Processando')
        self.busy_label.setText(message)

    def keep_on_screen(self):
        area = self.screen().availableGeometry()
        self.move(max(area.left(), min(self.x(), area.right()-self.width()+1)),
                  max(area.top(), min(self.y(), area.bottom()-self.height()+1)))

    def refresh(self):
        used, limit = self.store.used(), self.store.get('daily_limit', 30)
        self.counter.setText(f'{used} / {limit}')
        self.progress.setRange(0, limit)
        self.progress.setValue(min(used, limit))
        self.result_counter.setText(self.counter.text())
        self.result_progress.setRange(0, limit)
        self.result_progress.setValue(min(used, limit))

    def api_key(self):
        provider = self.store.get('provider', 'groq')
        saved = (keyring.get_password('RespondeAI', provider) or '').strip()
        variable = 'GEMINI_API_KEY' if provider == 'gemini' else 'GROQ_API_KEY'
        return saved or os.getenv(variable, '').strip()

    def settings(self):
        dialog = PanelDialog(self, 'Configurações • RespondeAI', 600, 430)
        body = QHBoxLayout()
        body.setSpacing(0)
        nav = QListWidget()
        nav.setFixedWidth(172)
        for title, symbol in [('Geral', 'settings'), ('Limite de uso', 'scan'),
                              ('API', 'scan'), ('Histórico', 'history')]:
            nav.addItem(QListWidgetItem(icon(symbol), title))
        pages = QStackedWidget()
        body.addWidget(nav)
        body.addWidget(pages, 1)
        dialog.root.addLayout(body, 1)
        forms = []
        for title in ['Geral', 'Limite de uso', 'API', 'Histórico']:
            page = QWidget()
            form = QFormLayout(page)
            form.setContentsMargins(18, 15, 20, 15)
            form.setSpacing(14)
            heading = QLabel(title)
            heading.setStyleSheet('font-size:18px; font-weight:600;')
            form.addRow(heading)
            scroll_page = QScrollArea()
            scroll_page.setWidgetResizable(True)
            scroll_page.setWidget(page)
            pages.addWidget(scroll_page)
            forms.append(form)
        nav.currentRowChanged.connect(pages.setCurrentIndex)
        nav.setCurrentRow(0)
        general, usage, api, history_form = forms
        api.setSpacing(8)
        platform = QComboBox()
        platform.setObjectName('apiProvider')
        platform.addItem('Groq', 'groq')
        platform.addItem('Gemini', 'gemini')
        platform.setCurrentIndex(max(0, platform.findData(self.store.get('provider', 'groq'))))
        api.addRow('Plataforma', platform)
        key = QLineEdit()
        key.setObjectName('apiKey')
        key.setEchoMode(QLineEdit.Password)
        try:
            saved_keys = {p: (keyring.get_password('RespondeAI', p) or '').strip()
                          for p in ('groq', 'gemini')}
        except Exception:
            QMessageBox.warning(self, 'Chave API', 'Não foi possível acessar o cofre de credenciais do sistema.')
            return
        environment_keys = {p: os.getenv(p.upper() + '_API_KEY', '').strip() for p in saved_keys}
        profiles = {
            'groq': {'key': saved_keys['groq'] or environment_keys['groq'],
                     'model': self.store.get('groq_model', DEFAULT_MODEL),
                     'vision': self.store.get('vision_model', DEFAULT_VISION_MODEL)},
            'gemini': {'key': saved_keys['gemini'] or environment_keys['gemini'],
                       'model': self.store.get('gemini_model', DEFAULT_GEMINI_MODEL),
                       'vision': self.store.get('gemini_vision_model', DEFAULT_GEMINI_MODEL)}}
        api.addRow('Chave API', key)
        reveal = QCheckBox('Mostrar chave')
        reveal.setObjectName('showApiKey')
        reveal.toggled.connect(lambda checked: key.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password))
        api.addRow(reveal)
        source = QLabel()
        source.setObjectName('keySource')
        source.setWordWrap(True)
        source.setStyleSheet('color:#a6b4d0; font-size:12px;')
        api.addRow(source)
        model = QLineEdit()
        model.setObjectName('textModel')
        api.addRow('Só texto', model)
        vision = QLineEdit()
        vision.setObjectName('visionModel')
        api.addRow('Com imagem', vision)
        current = [platform.currentData()]
        def save_draft():
            profiles[current[0]] = {'key': key.text().strip(), 'model': model.text().strip(),
                                    'vision': vision.text().strip()}
        def load_profile():
            current[0] = platform.currentData()
            profile = profiles[current[0]]
            key.setText(profile['key'])
            key.setPlaceholderText('Cole sua chave ' + platform.currentText())
            model.setText(profile['model'])
            vision.setText(profile['vision'])
            reveal.setChecked(False)
            key.setEchoMode(QLineEdit.Password)
            source.setText('Chave salva neste app.' if saved_keys[current[0]] else
                           'Chave da variável ' + current[0].upper() + '_API_KEY.' if environment_keys[current[0]] else
                           'Nenhuma chave configurada.')
        def change_platform():
            save_draft()
            load_profile()
        load_profile()
        platform.currentIndexChanged.connect(change_platform)
        limit = QSpinBox()
        limit.setRange(1, 10000)
        limit.setValue(self.store.get('daily_limit', 30))
        usage.addRow('Teto diário local', limit)
        screen = QComboBox()
        for i, monitor in enumerate(QApplication.screens()):
            screen.addItem(f'{i+1}: {monitor.name()}', i)
        screen.setCurrentIndex(min(self.store.get('screen', 0), screen.count()-1))
        general.addRow('Monitor', screen)
        capture_mode = QComboBox()
        capture_mode.addItem('Detectar figuras automaticamente', 'auto')
        capture_mode.addItem('Somente texto (não enviar imagem)', 'text')
        capture_mode.addItem('A questão contém figura ou gráfico', 'figure')
        capture_mode.setCurrentIndex(max(0, capture_mode.findData(self.store.get('capture_mode', 'auto'))))
        general.addRow('Captura', capture_mode)
        auto = QCheckBox('Copiar resposta automaticamente')
        auto.setChecked(self.store.get('auto_copy', False))
        general.addRow(auto)
        shortcut_note = QLabel('Atalho: Ctrl + Shift + X\nDisponível com o aplicativo em foco.')
        shortcut_note.setObjectName('muted')
        general.addRow(shortcut_note)
        note = QLabel('Cada questão usa 1 chamada. Com figura, o modelo recebe a imagem e responde diretamente. O OCR é local. Reenvios também contam.\n\nLimites de segundos/minutos aguardam e reenviam. Limite diário interrompe a consulta.')
        note.setWordWrap(True)
        note.setObjectName('muted')
        usage.addRow(note)
        history_note = QLabel('Suas respostas ficam salvas neste computador.')
        history_note.setWordWrap(True)
        history_form.addRow(history_note)
        history_open = QPushButton('Abrir histórico')
        history_open.clicked.connect(self.history)
        history_form.addRow(history_open)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText('Salvar')
        buttons.button(QDialogButtonBox.Cancel).setText('Cancelar')
        buttons.rejected.connect(dialog.reject)
        footer = QHBoxLayout()
        footer.setContentsMargins(18, 5, 18, 16)
        footer.addWidget(buttons)
        dialog.root.addLayout(footer)
        def save_settings():
            save_draft()
            if any(not profile['model'] or not profile['vision'] for profile in profiles.values()):
                QMessageBox.warning(dialog, 'Modelo', 'Informe os modelos de resposta e leitura da imagem.')
                return
            if any(not profile['key'] and (saved_keys[p] or environment_keys[p]) for p, profile in profiles.items()):
                QMessageBox.warning(dialog, 'Chave API', 'Informe a chave que deseja usar. Cancelar mantém a atual.')
                return
            try:
                for p, profile in profiles.items():
                    candidate = profile['key']
                    if candidate and candidate != saved_keys[p]:
                        keyring.set_password('RespondeAI', p, candidate)
                        if keyring.get_password('RespondeAI', p) != candidate:
                            raise RuntimeError('Falha ao confirmar a gravação da chave')
                for name, value in [('provider', platform.currentData()),
                                    ('groq_model', profiles['groq']['model']), ('vision_model', profiles['groq']['vision']),
                                    ('gemini_model', profiles['gemini']['model']), ('gemini_vision_model', profiles['gemini']['vision']),
                                    ('daily_limit', limit.value()),
                                    ('screen', screen.currentIndex()), ('auto_copy', auto.isChecked()),
                                    ('capture_mode', capture_mode.currentData())]:
                    self.store.set(name, value)
                self.refresh()
                dialog.accept()
            except Exception:
                QMessageBox.warning(dialog, 'Configuração', 'Não foi possível salvar as configurações ou a chave no cofre do sistema.')
        buttons.accepted.connect(save_settings)
        dialog.exec()
        key.clear()

    def capture(self):
        if (self.worker and self.worker.isRunning()) or (self.selector and self.selector.isVisible()):
            return
        try:
            self.capture_provider = self.store.get('provider', 'groq')
            self.key = self.api_key()
        except Exception:
            self.show_error('Não foi possível acessar a chave no cofre do sistema.')
            return
        if not self.key:
            self.settings()
            return
        self.start.setEnabled(False)
        self.new.setEnabled(False)
        self.showMinimized()
        QTimer.singleShot(350, self.select_area)

    def select_area(self):
        screens = QApplication.screens()
        screen = screens[min(self.store.get('screen', 0), len(screens)-1)]
        self.selector = Selection(screen)
        self.selector.selected.connect(self.submit)
        self.selector.cancelled.connect(self.restore)
        self.selector.show()
        self.selector.activateWindow()
        self.selector.setFocus()

    def restore(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.start.setEnabled(True)
        self.new.setEnabled(True)

    def submit(self, png):
        self.restore()
        if len(png) > 14 * 1024 * 1024:
            self.show_error('Área muito grande. Selecione uma região menor.')
            return
        self.start.setEnabled(False)
        self.new.setEnabled(False)
        self.settings_button.setEnabled(False)
        self.result_settings.setEnabled(False)
        self.answer.clear()
        self.result_page('Lendo a captura…')
        self.result_label.setText('Processando')
        self.answer.hide()
        self.busy_label.setText('Preparando sua resposta…')
        self.busy.show()
        self.copy.setEnabled(False)
        self.worker = Worker(self.store, png, self.key, self.store.get('groq_model', DEFAULT_MODEL), self.capture_provider)
        self.worker.result.connect(self.show_answer)
        self.worker.failed.connect(self.show_error)
        self.worker.progress.connect(self.show_progress)
        self.worker.finished.connect(self.finished)
        self.new.setText('  Cancelar')
        self.new.setIcon(icon('close'))
        self.new.setEnabled(True)
        self.worker.start()

    def finished(self):
        self.start.setEnabled(True)
        self.new.setEnabled(True)
        self.new.setText('  Novo')
        self.new.setIcon(icon('refresh'))
        self.settings_button.setEnabled(True)
        self.result_settings.setEnabled(True)
        self.refresh()

    def show_error(self, message):
        self.result_page('Não foi possível responder')
        self.answer.setPlainText(message)
        self.copy.setEnabled(False)

    def show_answer(self, answer, cached=False):
        self.result_page('Resposta', success=True)
        if answer.startswith('Alternativa:'):
            lines = answer.split('\n', 1)
            self.answer.setHtml('<div style="font-size:18px; font-weight:600;">'
                                + escape(lines[0]) + '</div>'
                                + ('<div style="margin-top:5px;">' + escape(lines[1]).replace('\n', '<br>') + '</div>' if len(lines) > 1 else ''))
        else:
            self.answer.setPlainText(answer)
        self.copy.setEnabled(True)
        self.result_label.setToolTip('Resposta reutilizada do histórico' if cached else 'Resposta recebida')
        if self.store.get('auto_copy', False):
            QApplication.clipboard().setText(answer)

    def history(self):
        dialog = PanelDialog(self, 'Histórico • RespondeAI', 560, 400)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 18)
        dialog.root.addWidget(content)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cards = QWidget()
        card_layout = QVBoxLayout(cards)
        card_layout.setContentsMargins(0, 0, 5, 0)
        card_layout.setSpacing(7)
        records = self.store.history()
        if not records:
            card_layout.addWidget(QLabel('Nenhuma resposta ainda.'))
        for created, answer in records:
            card = QWidget()
            card.setObjectName('historyCard')
            row = QHBoxLayout(card)
            row.setContentsMargins(12, 12, 12, 12)
            image_label = QLabel()
            image_label.setPixmap(icon('image', '#c1cce2', 22).pixmap(QSize(22, 22)))
            row.addWidget(image_label)
            column = QVBoxLayout()
            title = QLabel('Questão de múltipla escolha' if answer.startswith('Alternativa:') else 'Resposta em texto')
            column.addWidget(title)
            preview = QPushButton(answer.splitlines()[0][:52])
            preview.setObjectName('historyAnswer')
            preview.setToolTip('Abrir resposta completa')
            def open_answer(checked=False, value=answer):
                self.show_answer(value, cached=True)
                dialog.accept()
            preview.clicked.connect(open_answer)
            column.addWidget(preview)
            row.addLayout(column, 1)
            timestamp = QLabel(created.replace('T', '\n'))
            timestamp.setObjectName('muted')
            timestamp.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(timestamp)
            card_layout.addWidget(card)
        card_layout.addStretch()
        scroll.setWidget(cards)
        layout.addWidget(scroll)
        clear = QPushButton('Apagar histórico e cache')
        def erase():
            if QMessageBox.question(dialog, 'Apagar histórico', 'Apagar todas as respostas salvas? O contador será mantido.') == QMessageBox.Yes:
                self.store.clear_history()
                dialog.accept()
        clear.clicked.connect(erase)
        layout.addWidget(clear)
        dialog.exec()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.status.setText('Aguarde a consulta terminar antes de fechar.')
            self.status.show()
            event.ignore()
        else:
            event.accept()


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--diagnostico':
        from diagnostics import run
        sys.exit(run(sys.argv[2]))
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('RespondeAI.Desktop')
    app = QApplication(sys.argv)
    app.setFont(QFont('Segoe UI', 10))
    app.setApplicationName('RespondeAI')
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / 'assets' / 'respondeai.ico')))
    app.setStyleSheet(STYLE)
    folder = (Path(os.environ['LOCALAPPDATA']) / 'RespondeAI' if sys.platform == 'win32'
              else Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)))
    folder.mkdir(parents=True, exist_ok=True)
    window = Window(Store(folder / 'respondeai.db'))
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
