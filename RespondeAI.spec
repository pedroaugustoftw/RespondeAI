from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

datas = collect_data_files('rapidocr') + [('assets/respondeai.ico', 'assets')]
binaries = collect_dynamic_libs('onnxruntime')
hiddenimports = collect_submodules('rapidocr') + collect_submodules('win32ctypes') + ['keyring.backends.Windows']

a = Analysis(['app.py'], pathex=[], binaries=binaries, datas=datas,
             hiddenimports=hiddenimports, hookspath=[], hooksconfig={},
             runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='RespondeAI',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False,
          icon='assets/respondeai.ico')
