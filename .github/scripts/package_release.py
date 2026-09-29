import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile


def main():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from rapidocr import RapidOCR, LangRec, OCRVersion, ModelType
    RapidOCR(params={'Rec.lang_type': LangRec.LATIN, 'Rec.ocr_version': OCRVersion.PPOCRV5,
                     'Rec.model_type': ModelType.MOBILE, 'Global.log_level': 'warning'})
    subprocess.run([sys.executable, 'make_icon.py'], check=True)
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', 'RespondeAI.spec'], check=True)
    system = platform.system()
    arch = 'arm64' if platform.machine().lower() in ('arm64', 'aarch64') else 'x64'
    assert arch == os.environ['EXPECTED_ARCH'], (arch, os.environ['EXPECTED_ARCH'])
    output = Path('release-assets')
    output.mkdir(exist_ok=True)
    label = 'macOS' if system == 'Darwin' else system
    name = f'RespondeAI-{label}-{arch}'
    executable = Path('dist/RespondeAI.exe' if system == 'Windows' else
                      'dist/RespondeAI.app/Contents/MacOS/RespondeAI' if system == 'Darwin' else 'dist/RespondeAI').resolve()
    report = Path('build/diagnostic.json').resolve()
    completed = subprocess.run([str(executable), '--diagnostico', str(report)], timeout=240)
    if report.exists():
        print(report.read_text(encoding='utf-8'), flush=True)
    completed.check_returncode()
    assert json.loads(report.read_text(encoding='utf-8'))['ok']
    if system == 'Windows':
        artifact = output / (name + '.exe')
        shutil.copy2(executable, artifact)
    elif system == 'Darwin':
        artifact = output / (name + '.zip')
        subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', 'dist/RespondeAI.app', str(artifact)], check=True)
    else:
        artifact = output / (name + '.tar.gz')
        with tarfile.open(artifact, 'w:gz') as archive:
            archive.add(executable, arcname='RespondeAI')
    digest = hashlib.file_digest(artifact.open('rb'), 'sha256').hexdigest()
    (output / (name + '.sha256')).write_text(digest + '  ' + artifact.name + '\n', encoding='ascii')


if __name__ == '__main__':
    main()
