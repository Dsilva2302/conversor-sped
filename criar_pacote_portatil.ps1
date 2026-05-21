$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistDir = Join-Path $ProjectRoot "dist"
$PackageName = "Conversor_SPED_Excel_Portatil.zip"
$PackagePath = Join-Path $DistDir $PackageName

Set-Location $ProjectRoot

if (-not (Test-Path $DistDir)) {
    New-Item -ItemType Directory -Path $DistDir | Out-Null
}

if (Test-Path $PackagePath) {
    Remove-Item $PackagePath -Force
}

$TempDir = Join-Path $env:TEMP ("conversor_sped_" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $TempDir | Out-Null

$Ignore = @(
    "storage",
    "dist",
    "Relatorios_Gerados",
    "Relatorios_ajustados_contribuicoes",
    "Relatorios_ajustados_contribuicoes_lancamento",
    "Relatorios_ajustados_contribuicoes_sem_pais",
    "Relatorios_ajustados_contribuicoes_valores_espelhados",
    "Relatorios_ajustados_icms_lancamento",
    "Relatorios_ajustados_icms_lancamento_v2",
    "Relatorios_ajustados_icms_sem_EK_sem_duplicidade",
    "Relatorios_ajustados_icms_valores_espelhados",
    "__pycache__",
    ".git"
)

Get-ChildItem $ProjectRoot -Force | ForEach-Object {
    if ($Ignore -contains $_.Name) {
        return
    }
    Copy-Item $_.FullName -Destination $TempDir -Recurse -Force
}

Get-ChildItem $TempDir -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Compress-Archive -Path (Join-Path $TempDir "*") -DestinationPath $PackagePath -Force
Remove-Item $TempDir -Recurse -Force

Write-Host "Pacote criado:" -ForegroundColor Green
Write-Host $PackagePath
Read-Host "Pressione ENTER para fechar"
