$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistDir = Join-Path $ProjectRoot "dist"
$PackageDir = Join-Path $DistDir "Instalador_Conversor_SPED"
$ZipPath = Join-Path $DistDir "Instalador_Conversor_SPED.zip"
$ExePath = Join-Path $DistDir "ConversorSPED.exe"

if (-not (Test-Path $ExePath)) {
    throw "Executavel nao encontrado. Rode CRIAR_INSTALADOR_WINDOWS.bat ou gere o executavel primeiro."
}

if (Test-Path $PackageDir) {
    Remove-Item $PackageDir -Recurse -Force
}
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

New-Item -ItemType Directory -Path $PackageDir | Out-Null
Copy-Item $ExePath (Join-Path $PackageDir "ConversorSPED.exe") -Force
Copy-Item (Join-Path $ProjectRoot "installer\Instalar_Conversor_SPED.bat") (Join-Path $PackageDir "Instalar_Conversor_SPED.bat") -Force
Copy-Item (Join-Path $ProjectRoot "installer\Instalar_Conversor_SPED.ps1") (Join-Path $PackageDir "Instalar_Conversor_SPED.ps1") -Force
Copy-Item (Join-Path $ProjectRoot "installer\LEIA-ME-INSTALACAO.txt") (Join-Path $PackageDir "LEIA-ME-INSTALACAO.txt") -Force

Compress-Archive -Path (Join-Path $PackageDir "*") -DestinationPath $ZipPath -Force

Write-Host "Instalador ZIP criado:" -ForegroundColor Green
Write-Host $ZipPath
