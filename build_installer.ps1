$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Users\DanilodosSantosSilva\AppData\Local\Python\bin\python.exe"
$BuildDir = Join-Path $ProjectRoot "build"
$DistDir = Join-Path $ProjectRoot "dist"
$InstallerWork = Join-Path $env:TEMP "ConversorSPEDPayload"
$SetupExe = Join-Path $DistDir "Conversor_SPED_Setup.exe"
$TempSetupExe = Join-Path $env:TEMP "Conversor_SPED_Setup.exe"
$SedFile = Join-Path $BuildDir "conversor_sped_iexpress.sed"

Set-Location $ProjectRoot

if (-not (Test-Path $PythonExe)) {
    throw "Python nao encontrado em: $PythonExe"
}

if (-not (Test-Path $DistDir)) {
    New-Item -ItemType Directory -Path $DistDir | Out-Null
}

Write-Host "Gerando executavel com PyInstaller..." -ForegroundColor Cyan
& $PythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name ConversorSPED `
    --icon "assets\sped_excel_icon.ico" `
    --add-data "assets;assets" `
    --hidden-import "uvicorn.logging" `
    --hidden-import "uvicorn.loops" `
    --hidden-import "uvicorn.loops.auto" `
    --hidden-import "uvicorn.protocols" `
    --hidden-import "uvicorn.protocols.http" `
    --hidden-import "uvicorn.protocols.http.auto" `
    --hidden-import "uvicorn.protocols.websockets" `
    --hidden-import "uvicorn.protocols.websockets.auto" `
    --hidden-import "uvicorn.lifespan" `
    --hidden-import "uvicorn.lifespan.on" `
    desktop_launcher.py

if (Test-Path $InstallerWork) {
    Remove-Item $InstallerWork -Recurse -Force
}
New-Item -ItemType Directory -Path $InstallerWork | Out-Null

Copy-Item (Join-Path $DistDir "ConversorSPED.exe") (Join-Path $InstallerWork "ConversorSPED.exe") -Force
Copy-Item "installer\Instalar_Conversor_SPED.ps1" (Join-Path $InstallerWork "Instalar_Conversor_SPED.ps1") -Force
Copy-Item "installer\Instalar_Conversor_SPED.bat" (Join-Path $InstallerWork "Instalar_Conversor_SPED.bat") -Force

if (Test-Path $SetupExe) {
    Remove-Item $SetupExe -Force
}
if (Test-Path $TempSetupExe) {
    Remove-Item $TempSetupExe -Force
}

$Sed = @"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=
DisplayLicense=
FinishMessage=Conversor SPED para Excel instalado com sucesso.
TargetName=$TempSetupExe
FriendlyName=Conversor SPED para Excel
AppLaunched=Instalar_Conversor_SPED.bat
PostInstallCmd=<None>
AdminQuietInstCmd=
UserQuietInstCmd=
SourceFiles=SourceFiles
[Strings]
FILE0=Instalar_Conversor_SPED.bat
FILE1=Instalar_Conversor_SPED.ps1
FILE2=ConversorSPED.exe
[SourceFiles]
SourceFiles0=$InstallerWork
[SourceFiles0]
%FILE0%=
%FILE1%=
%FILE2%=
"@

New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
Set-Content -Path $SedFile -Value $Sed -Encoding ASCII

Write-Host "Gerando instalador..." -ForegroundColor Cyan
& "$env:WINDIR\System32\iexpress.exe" /N /Q $SedFile

if (-not (Test-Path $TempSetupExe)) {
    throw "Falha ao gerar instalador: $TempSetupExe"
}

Copy-Item $TempSetupExe $SetupExe -Force

Write-Host "Instalador criado:" -ForegroundColor Green
Write-Host $SetupExe
