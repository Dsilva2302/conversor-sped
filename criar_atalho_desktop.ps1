$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LauncherPath = Join-Path $ProjectRoot "ABRIR_PROGRAMA.vbs"
$IconPath = Join-Path $ProjectRoot "assets\sped_excel_icon.ico"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Conversor SPED para Excel.lnk"

if (-not (Test-Path $LauncherPath)) {
    throw "Arquivo nao encontrado: $LauncherPath"
}

if (-not (Test-Path $IconPath)) {
    throw "Icone nao encontrado: $IconPath"
}

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = """" + $LauncherPath + """"
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.IconLocation = $IconPath
$Shortcut.Description = "Abrir o Conversor SPED para Excel"
$Shortcut.Save()

Write-Host "Atalho criado na Area de Trabalho:" -ForegroundColor Green
Write-Host $ShortcutPath
Read-Host "Pressione ENTER para fechar"
