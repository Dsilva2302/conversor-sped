$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\DanilodosSantosSilva\AppData\Local\Python\bin\python.exe"

Set-Location $ProjectRoot

if (-not (Test-Path $PythonExe)) {
    Write-Host "Python nao encontrado em: $PythonExe" -ForegroundColor Red
    Read-Host "Pressione ENTER para fechar"
    exit 1
}

Write-Host "Instalando dependencias..." -ForegroundColor Cyan
& $PythonExe -m pip install -r requirements.txt

Write-Host ""
Write-Host "Dependencias instaladas." -ForegroundColor Green
Read-Host "Pressione ENTER para fechar"
