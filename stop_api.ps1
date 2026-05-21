$ErrorActionPreference = "Stop"

$connections = Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue

if (-not $connections) {
    Write-Host "Nenhuma API encontrada na porta 8765."
    exit 0
}

$processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -gt 0 }

foreach ($processId in $processIds) {
    Write-Host "Parando processo $processId na porta 8765..."
    Stop-Process -Id $processId -Force
}

Write-Host "API parada."
