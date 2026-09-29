$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $PSScriptRoot -ErrorAction Stop
& .\.venv\Scripts\python.exe make_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Falha ao gerar o icone.' }
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm RespondeAI.spec
if ($LASTEXITCODE -ne 0) { throw 'Falha ao gerar o executavel.' }
Write-Host 'Executavel pronto: dist\RespondeAI.exe'
