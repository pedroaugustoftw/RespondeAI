"""Confere os arquivos antes de anexar ao rascunho de uma Release."""
import hashlib
from pathlib import Path
import tarfile
import zipfile

folder = Path('release-assets')
checksums = list(folder.glob('*.sha256'))
assert checksums, 'Nenhum pacote encontrado'
for checksum in checksums:
    digest, name = checksum.read_text().split()
    assert Path(name).name == name
    binary = folder / name
    with binary.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest, name
    arm = '-arm64' in name
    if binary.suffix == '.exe':
        with binary.open('rb') as stream:
            stream.seek(60)
            offset = int.from_bytes(stream.read(4), 'little')
            stream.seek(offset + 4)
            machine = int.from_bytes(stream.read(2), 'little')
        assert machine == (0xaa64 if arm else 0x8664), name
    elif name.endswith('.tar.gz'):
        with tarfile.open(binary, 'r:gz') as archive:
            header = archive.extractfile('RespondeAI').read(20)
        assert header[:4] == b'\x7fELF'
        assert int.from_bytes(header[18:20], 'little') == (183 if arm else 62), name
    else:
        with zipfile.ZipFile(binary) as archive:
            with archive.open('RespondeAI.app/Contents/MacOS/RespondeAI') as stream:
                header = stream.read(8)
        assert header[:4] == b'\xcf\xfa\xed\xfe', name
        assert int.from_bytes(header[4:8], 'little') == (0x100000c if arm else 0x1000007), name
    print('Integridade e arquitetura confirmadas:', name)
