$ErrorActionPreference = "SilentlyContinue"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\DanilodosSantosSilva\AppData\Local\Python\bin\python.exe"
$Url = "http://127.0.0.1:8765"

Set-Location $ProjectRoot

if (-not (Test-Path $PythonExe)) {
    Start-Process $Url
    exit 1
}

$portaOcupada = Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue
if ($portaOcupada) {
    Start-Process $Url
    exit 0
}

Start-Process -FilePath $PythonExe `
    -ArgumentList @("-m", "uvicorn", "app.api.main:app", "--host", "127.0.0.1", "--port", "8765") `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden

for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:8765/health" -UseBasicParsing -TimeoutSec 1 | Out-Null
        Start-Process $Url
        exit 0
    } catch {
    }
}

Start-Process $Url
