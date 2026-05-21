$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\DanilodosSantosSilva\AppData\Local\Python\bin\python.exe"
$Url = "http://127.0.0.1:8765"

Set-Location $ProjectRoot

if (-not (Test-Path $PythonExe)) {
    Write-Host "Python nao encontrado em: $PythonExe" -ForegroundColor Red
    Read-Host "Pressione ENTER para fechar"
    exit 1
}

$portaOcupada = Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue
if ($portaOcupada) {
    Write-Host "O sistema ja esta aberto em $Url" -ForegroundColor Green
    Start-Process $Url
    Read-Host "Pressione ENTER para fechar"
    exit 0
}

Write-Host "Iniciando sistema local..." -ForegroundColor Cyan
Write-Host "O navegador sera aberto em: $Url"
Write-Host "Para parar, feche esta janela ou execute stop_api.ps1."
Start-Process $Url
& $PythonExe -m uvicorn app.api.main:app --host 127.0.0.1 --port 8765
