"""Gera imagens da interface com dados fictícios e sem acessar APIs ou credenciais."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QListWidget
from app import Window, PanelDialog, STYLE
from core import Store


def main():
    app = QApplication([])
    app.setStyleSheet(STYLE)
    output = ROOT / 'docs' / 'images'
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        store = Store(Path(folder) / 'demo.db')
        window = Window(store)
        window.show()
        app.processEvents()
        window.grab().save(str(output / 'inicio.png'))
        window.show_answer('Alternativa: A\n4')
        app.processEvents()
        window.grab().save(str(output / 'resposta.png'))
        window.result_page('Processando')
        window.answer.hide()
        window.busy_label.setText('Otimizando uso de tokens…')
        window.busy.show()
        window.copy.setEnabled(False)
        window.new.setText('  Cancelar')
        app.processEvents()
        window.grab().save(str(output / 'carregamento.png'))
        def capture_dialog(dialog):
            nav = dialog.findChild(QListWidget)
            dialog.show()
            for index, filename in ((0, 'configuracoes.png'), (2, 'api.png')):
                nav.setCurrentRow(index)
                app.processEvents()
                dialog.grab().save(str(output / filename))
            dialog.reject()
            return 0
        with patch('app.keyring.get_password', return_value=None), \
             patch('app.os.getenv', return_value=''), \
             patch.object(PanelDialog, 'exec', capture_dialog):
            window.settings()
        window.close()


if __name__ == '__main__':
    main()
