"""Componentes visuais do RespondeAI, desenhados em Qt/SVG."""
from PySide6.QtCore import Qt, QRectF, QSize, QByteArray, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QLinearGradient, QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget, QDialog, QLabel, QPushButton, QHBoxLayout, QVBoxLayout

PATHS = {
    'scan': '<path d="M8 3H4a1 1 0 0 0-1 1v4m13-5h4a1 1 0 0 1 1 1v4M3 16v4a1 1 0 0 0 1 1h4m8 0h4a1 1 0 0 0 1-1v-4M9 12h6"/>',
    'copy': '<rect x="8" y="5" width="12" height="16" rx="2"/><path d="M16 5V3H4v14h4"/>',
    'close': '<path d="m6 6 12 12M6 18 18 6"/>',
    'minus': '<path d="M5 12h14"/>',
    'refresh': '<path d="M20 8a8 8 0 0 0-14-2L3 9m0-5v5h5m-4 7a8 8 0 0 0 14 2l3-3m0 5v-5h-5"/>',
    'history': '<path d="M3 10a9 9 0 1 1 1 7M3 4v6h6m3-4v6l4 2"/>',
    'check': '<path d="m5 12 4 4L19 6"/>',
    'settings': '<polygon points="19.39,8.94 21.76,9.82 21.76,14.18 19.39,15.06 19.39,15.06 20.44,17.36 17.36,20.44 15.06,19.39 15.06,19.39 14.18,21.76 9.82,21.76 8.94,19.39 8.94,19.39 6.64,20.44 3.56,17.36 4.61,15.06 4.61,15.06 2.24,14.18 2.24,9.82 4.61,8.94 4.61,8.94 3.56,6.64 6.64,3.56 8.94,4.61 8.94,4.61 9.82,2.24 14.18,2.24 15.06,4.61 15.06,4.61 17.36,3.56 20.44,6.64 19.39,8.94"/><circle cx="12" cy="12" r="3.5"/>',
    'image': '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1"/><path d="m3 17 5-5 4 4 4-6 5 7"/>',
}


class Spinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.setInterval(35)
        self.timer.timeout.connect(self.tick)

    def tick(self):
        self.angle = (self.angle + 12) % 360
        self.update()

    def showEvent(self, event):
        self.timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bounds = QRectF(self.rect()).adjusted(5, 5, -5, -5)
        painter.setPen(QPen(QColor('#26364d'), 3))
        painter.drawEllipse(bounds)
        pen = QPen(QColor('#628bff'), 3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(bounds, -self.angle*16, 105*16)


def icon(name, color='#bfcae8', size=24):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{PATHS[name]}</svg>'
    pix = QPixmap(size * 2, size * 2)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    QSvgRenderer(QByteArray(svg.encode())).render(painter)
    painter.end()
    pix.setDevicePixelRatio(2)
    return QIcon(pix)


def icon_button(name, tooltip, size=42, primary=False):
    button = QPushButton()
    button.setIcon(icon(name, '#ffffff' if primary else '#b8c7ea'))
    button.setIconSize(QSize(21, 21))
    button.setFixedSize(size, size)
    button.setToolTip(tooltip)
    button.setAccessibleName(tooltip)
    button.setCursor(Qt.PointingHandCursor)
    button.setObjectName('primary' if primary else 'iconButton')
    return button


def paint_panel(widget):
    painter = QPainter(widget)
    painter.setRenderHint(QPainter.Antialiasing)
    bounds = QRectF(widget.rect()).adjusted(1, 1, -1, -1)
    gradient = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
    gradient.setColorAt(0, QColor('#121c29'))
    gradient.setColorAt(1, QColor('#0e151e'))
    painter.setBrush(gradient)
    painter.setPen(QPen(QColor('#36404e'), 1))
    painter.drawRoundedRect(bounds, 18, 18)


class TitleBar(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setFixedHeight(62)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 12, 10)
        layout.setSpacing(10)
        logo = QLabel()
        logo.setObjectName('logo')
        logo.setFixedSize(34, 34)
        logo.setAlignment(Qt.AlignCenter)
        logo.setPixmap(icon('scan', '#ffffff', 22).pixmap(QSize(22, 22)))
        layout.addWidget(logo)
        name = QLabel('RespondeAI')
        name.setObjectName('brand')
        layout.addWidget(name)
        layout.addStretch()
        minimize = icon_button('minus', 'Minimizar', 32)
        minimize.setObjectName('windowButton')
        minimize.clicked.connect(window.showMinimized)
        layout.addWidget(minimize)
        close = icon_button('close', 'Fechar', 32)
        close.setObjectName('closeButton')
        close.clicked.connect(window.close)
        layout.addWidget(close)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.window.windowHandle():
            self.window.windowHandle().startSystemMove()


class Panel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint
                            | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        paint_panel(self)


class PanelDialog(QDialog):
    def __init__(self, parent, title, width=590, height=405):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(width, height)
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(1, 1, 1, 1)
        self.root.setSpacing(0)
        self.root.addWidget(TitleBar(self))
        line = QWidget()
        line.setObjectName('divider')
        line.setFixedHeight(1)
        self.root.addWidget(line)

    def paintEvent(self, event):
        paint_panel(self)
