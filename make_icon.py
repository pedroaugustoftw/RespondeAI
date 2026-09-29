"""Renderiza o logo vetorial existente em PNG e ICO para Windows."""
from pathlib import Path
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication.instance() or QApplication([])
    folder = Path(__file__).resolve().parent / 'assets'
    image = QImage(256, 256, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    QSvgRenderer(str(folder / 'respondeai.svg')).render(painter)
    painter.end()
    image.save(str(folder / 'respondeai.png'))
    with Image.open(folder / 'respondeai.png') as source:
        source.save(folder / 'respondeai.ico', sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])


if __name__ == '__main__':
    main()
