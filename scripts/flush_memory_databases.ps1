<#!
.SYNOPSIS
    Flush Redis keys and wipe Chroma vector store for the memory system.

.DESCRIPTION
    Safely clears ONLY user memory data (Redis + Chroma) without deleting models or other cached assets.
    Default mode:
      1. Stops dependent services (openwebui, memory-api, backend, pipelines)
      2. Flushes all Redis data (FLUSHALL)
      3. Stops Chroma and removes its data directory contents (./storage/chroma)
      4. Restarts services in dependency order

    Full mode (-Full) performs a broader reset (docker compose down + targeted directory cleanup) but preserves model & cache dirs.

.PARAMETER Full
    Perform a broader reset using `docker compose down` before wiping Chroma and then `up -d`.

.EXAMPLE
    pwsh ./scripts/flush_memory_databases.ps1

.EXAMPLE
    pwsh ./scripts/flush_memory_databases.ps1 -Full

.NOTES
    Run from repository root where docker-compose.yml lives.
#>
param(
    [switch]$Full
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO ] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN ] $msg" -ForegroundColor Yellow }
function Write-Ok($msg)   { Write-Host "[ OK  ] $msg" -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "[FAIL ] $msg" -ForegroundColor Red }

# Basic sanity check
if (-not (Test-Path './docker-compose.yml')) {
    Write-Err 'Run this script from the repository root (docker-compose.yml not found).'
    exit 1
}

# Confirm
Write-Warn 'This will ERASE all Redis keys and ALL Chroma vectors (user memory).'
if (-not $Full) {
    Write-Warn 'Models, pipelines cache, and Ollama data will remain.'
} else {
    Write-Warn 'Full mode: containers will be brought down, memory stores wiped, then stack restarted.'
}

$confirmation = Read-Host 'Type YES to continue'
if ($confirmation -ne 'YES') {
    Write-Info 'Aborted by user.'
    exit 0
}

if ($Full) {
    Write-Info 'Bringing full stack down...'
    docker compose down || throw 'docker compose down failed'
} else {
    Write-Info 'Stopping dependent application services...'
    docker compose stop openwebui memory-api backend pipelines 2>$null | Out-Null
}

# Redis flush
if (-not $Full) {
    Write-Info 'Flushing Redis (FLUSHALL)...'
    try {
        docker compose exec -T redis redis-cli FLUSHALL | Out-Null
        Write-Ok 'Redis flushed.'
    } catch {
        Write-Err "Redis flush failed: $_"
        if (-not $Full) { Write-Warn 'Continuing; ensure redis container is running.' }
    }
}

# Stop Chroma (if not already in Full mode where it is down)
if (-not $Full) {
    Write-Info 'Stopping Chroma service...'
    docker compose stop chroma 2>$null | Out-Null
}

# Wipe Chroma storage directory
$chromaPath = Join-Path (Get-Location) 'storage/chroma'
if (Test-Path $chromaPath) {
    Write-Info "Removing Chroma data contents in $chromaPath ..."
    try {
        Get-ChildItem -Path $chromaPath -Force -Recurse | Remove-Item -Force -Recurse
        Write-Ok 'Chroma directory emptied.'
    } catch {
        Write-Err "Failed to clear Chroma directory: $_"
        exit 1
    }
} else {
    Write-Warn 'Chroma storage directory not found (skipping).'
}

if ($Full) {
    Write-Info 'Starting core stack (detached)...'
    docker compose up -d redis chroma || throw 'Failed to start redis/chroma'
    Write-Info 'Starting remaining services...'
    docker compose up -d backend memory-api pipelines openwebui || throw 'Failed to start application services'
} else {
    Write-Info 'Restarting Chroma...'
    docker compose up -d chroma || throw 'Failed to start chroma'

    Write-Info 'Restarting application services...'
    docker compose up -d backend memory-api pipelines openwebui || throw 'Failed to restart services'
}

Write-Ok 'Memory data flush complete.'
Write-Info 'Validate by initiating a new conversation and confirming no prior memories are injected.'
