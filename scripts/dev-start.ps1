# One-click local dev startup for CalmPath: Postgres (docker), backend
# (uvicorn on :8010), frontend (Expo web on :8081). Assumes the one-time
# setup in README.md ("Backend setup" / "Frontend setup") has already been
# run at least once (.venv exists, node_modules installed, .env files in
# place) - this script only starts things, it doesn't install anything.
#
# Usage (from anywhere): ./scripts/dev-start.ps1

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

function Test-PortListening {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

Write-Host "==> Starting Postgres (docker compose)..."
Push-Location (Join-Path $repoRoot "infra")
docker compose up -d
Pop-Location

if (Test-PortListening -Port 8010) {
    Write-Host "==> Backend already running on :8010, skipping."
} else {
    Write-Host "==> Starting backend (uvicorn, :8010) in a new window..."
    $apiDir = Join-Path $repoRoot "services\api"
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "cd '$apiDir'; ./.venv/Scripts/python -m uvicorn app.main:app --reload --port 8010"
    )
}

if (Test-PortListening -Port 8081) {
    Write-Host "==> Frontend already running on :8081, skipping."
} else {
    Write-Host "==> Starting frontend (Expo web, :8081) in a new window..."
    $mobileDir = Join-Path $repoRoot "apps\mobile"
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "cd '$mobileDir'; npm run web"
    )
}

Write-Host ""
Write-Host "Backend:  http://localhost:8010/docs"
Write-Host "Frontend: http://localhost:8081"
Write-Host "(Each server runs in its own window - close that window, or Ctrl+C inside it, to stop it.)"
