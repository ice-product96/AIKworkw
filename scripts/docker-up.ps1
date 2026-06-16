# Start full stack in Docker
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker not found. Install Docker Desktop and restart the terminal." -ForegroundColor Red
    exit 1
}

Write-Host "Building and starting containers..." -ForegroundColor Cyan
docker compose up --build -d

Write-Host ""
Write-Host "Stack is starting. URLs:" -ForegroundColor Green
Write-Host "  App:     http://localhost"
Write-Host "  API:     http://localhost:8000/docs"
Write-Host "  MinIO:   http://localhost:9001 (minioadmin / minioadmin)"
Write-Host ""
Write-Host "Admin: admin@example.com / password"
Write-Host "Logs:  docker compose logs -f"
