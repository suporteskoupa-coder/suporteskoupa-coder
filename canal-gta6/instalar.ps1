# Instala tudo o que o pipeline precisa. Rode dentro da pasta canal-gta6:
#   powershell -ExecutionPolicy Bypass -File .\instalar.ps1
$ErrorActionPreference = "Stop"
Write-Host "1/4 Instalando ffmpeg, Python 3.12 e Git (pode pedir confirmacao)..."
winget install --silent --accept-package-agreements --accept-source-agreements Gyan.FFmpeg Python.Python.3.12 Git.Git
# recarrega o PATH sem fechar o PowerShell
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "2/4 Criando ambiente Python..."
if (-not (Test-Path .venv)) { py -3.12 -m venv .venv }
.\.venv\Scripts\python -m pip install -q --upgrade pip
.\.venv\Scripts\pip install -q -e ".[dev]"

Write-Host "3/4 Rodando os testes (leva alguns minutos)..."
.\.venv\Scripts\pytest -q
if ($LASTEXITCODE -ne 0) { Write-Host "Testes falharam - mostre a saida ao Claude." -ForegroundColor Red; exit 1 }

Write-Host "4/4 Conferindo a GPU..."
.\.venv\Scripts\python -c "from canal.encode import pick_encoder; print('Encoder:', pick_encoder())"
New-Item -ItemType Directory -Force entrada, saida, metricas | Out-Null
Write-Host "Pronto! Coloque os videos em canal-gta6\entrada e abra o Claude Code nesta pasta." -ForegroundColor Green
