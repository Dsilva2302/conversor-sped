$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\DanilodosSantosSilva\AppData\Local\Python\bin\python.exe"
$PastaTxt = Join-Path $ProjectRoot "TXT"
$PastaSaida = Join-Path $ProjectRoot "Relatorios_Gerados"

Set-Location $ProjectRoot

if (-not (Test-Path $PythonExe)) {
    Write-Host "Python nao encontrado em: $PythonExe" -ForegroundColor Red
    Read-Host "Pressione ENTER para fechar"
    exit 1
}

if (-not (Test-Path $PastaTxt)) {
    New-Item -ItemType Directory -Path $PastaTxt | Out-Null
}

if (-not (Test-Path $PastaSaida)) {
    New-Item -ItemType Directory -Path $PastaSaida | Out-Null
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Conversor SPED TXT para Excel" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pasta dos TXT: $PastaTxt"
Write-Host "Pasta de saida: $PastaSaida"
Write-Host ""

& $PythonExe -c "from app.core.parser_sped import main; main(r'$PastaTxt', r'$PastaSaida', True, True, True)"

Write-Host ""
Write-Host "Processamento finalizado. Abrindo pasta de relatorios..." -ForegroundColor Green
Start-Process $PastaSaida
Read-Host "Pressione ENTER para fechar"
