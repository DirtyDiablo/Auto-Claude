# BD Knowledge API Startup Script (PowerShell)
# Run with: .\scripts\start_knowledge_api.ps1
# For background: .\scripts\start_knowledge_api.ps1 -Background

param(
    [switch]$Background = $false
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "knowledge_api.log"

# Create logs directory
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  BD Knowledge API Startup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if already running
$existing = Get-NetTCPConnection -LocalPort 8100 -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "API already running on port 8100" -ForegroundColor Yellow
    Write-Host "To stop: Stop-Process -Id (Get-NetTCPConnection -LocalPort 8100).OwningProcess"
    exit 0
}

Set-Location $ProjectRoot

if ($Background) {
    Write-Host "Starting in background..." -ForegroundColor Green
    Write-Host "Log file: $LogFile" -ForegroundColor Gray

    $job = Start-Job -ScriptBlock {
        param($root, $log)
        Set-Location $root
        python Engine8_Knowledge/api.py *>> $log
    } -ArgumentList $ProjectRoot, $LogFile

    Start-Sleep -Seconds 3

    # Check if started
    $running = Get-NetTCPConnection -LocalPort 8100 -ErrorAction SilentlyContinue
    if ($running) {
        Write-Host "API started successfully!" -ForegroundColor Green
        Write-Host "URL: http://localhost:8100" -ForegroundColor Cyan
        Write-Host "Health: http://localhost:8100/health" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "To view logs: Get-Content $LogFile -Tail 50 -Wait"
        Write-Host "To stop: Stop-Job $($job.Id); Remove-Job $($job.Id)"
    } else {
        Write-Host "Failed to start API. Check logs." -ForegroundColor Red
    }
} else {
    Write-Host "Starting Knowledge API on http://localhost:8100" -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
    Write-Host ""
    python Engine8_Knowledge/api.py
}
