"""Diagnóstico offline de interface, persistência e OCR dos pacotes distribuídos."""
import json
import platform
import tempfile
import traceback
from pathlib import Path


def run(destination):
    report = {'ok': False, 'system': platform.system(), 'architecture': platform.machine()}
    try:
        import requests
        import cv2
        import numpy as np
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QIcon
        from app import Window
        from core import Store
        from local_ocr import read_capture
        def offline(*args, **kwargs):
            raise RuntimeError('O OCR tentou acessar a rede.')
        requests.sessions.Session.request = offline
        app = QApplication.instance() or QApplication([])
        icon = QIcon(str(Path(__file__).resolve().parent / 'assets' / 'respondeai.ico'))
        assert not icon.isNull(), 'Icone ausente'
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder) / 'diagnostic.db')
            window = Window(store)
            window.show()
            app.processEvents()
            assert window.width() == 340
            window.close()
            canvas = np.full((180, 800, 3), 255, dtype=np.uint8)
            cv2.putText(canvas, 'Alternativa A: 4', (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
            success, png = cv2.imencode('.png', canvas)
            assert success
            capture = read_capture(png.tobytes(), 'text')
            assert '4' in capture.text and 'Alternativa' in capture.text, capture.text
            report['ocr_offline'] = True
            report['interface'] = True
        report['ok'] = True
    except Exception:
        report['error'] = traceback.format_exc()
    Path(destination).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['ok'] else 1
