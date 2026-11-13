# VOLTIS — lancement local guidé (Windows PowerShell)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONUTF8 = "1"

Write-Host ""
Write-Host "  VOLTIS — Agentic AI for the Electricity Sector" -ForegroundColor Yellow
Write-Host "  Dashboard 8033 · MCP 8100 · A2A 8101-8105" -ForegroundColor Cyan
Write-Host ""

$python = "py"
if (Get-Command py -ErrorAction SilentlyContinue) {
    $python = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
} else {
    Write-Error "Python 3.12+ est requis."
}

& $python -c "import streamlit, fastapi, langgraph" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Installation des dépendances…" -ForegroundColor Yellow
    & $python -m pip install -r requirements.txt
}

Write-Host "  Démarrage des services…" -ForegroundColor Green
& $python main.py
