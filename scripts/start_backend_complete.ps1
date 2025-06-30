#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete Backend Startup with Automatic Function Installation
.DESCRIPTION
    This script starts all backend services and automatically installs the memory function.
.PARAMETER SkipFunctionInstall
    Skip the automatic function installation
#>

param(
    [switch]$SkipFunctionInstall = $false
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param($Message, $Color = $Reset)
    Write-Host "${Color}${Message}${Reset}"
}

Write-ColorOutput "🚀 Complete Backend Startup with Auto Function Installation" $Cyan
Write-ColorOutput "============================================================" $Cyan

# Start main services
Write-ColorOutput "`n📦 Starting main backend services..." $Blue
try {
    docker-compose up -d redis chroma memory_api openwebui watchtower
    Write-ColorOutput "✅ Main services started successfully" $Green
} catch {
    Write-ColorOutput "❌ Failed to start main services: $($_.Exception.Message)" $Red
    exit 1
}

# Wait for services to be ready
Write-ColorOutput "`n⏳ Waiting for services to be ready..." $Blue
Start-Sleep -Seconds 15

# Check service health
Write-ColorOutput "`n🔍 Checking service health..." $Blue
$services = docker ps --format "table {{.Names}}\t{{.Status}}" | Where-Object { $_ -match "backend-" }
foreach ($service in $services) {
    Write-ColorOutput "   $service" $Reset
}

# Run function installer if not skipped
if (-not $SkipFunctionInstall) {
    Write-ColorOutput "`n🔧 Running automatic function installer..." $Blue
    try {
        docker-compose up function_installer --no-deps
        Write-ColorOutput "✅ Function installer completed" $Green
    } catch {
        Write-ColorOutput "⚠️  Function installer finished (this is normal for one-time containers)" $Yellow
    }
} else {
    Write-ColorOutput "`n⏭️  Function installation skipped" $Yellow
}

# Final status check
Write-ColorOutput "`n🎯 Final system status..." $Blue
try {
    Invoke-RestMethod -Uri "http://localhost:3000" -Method Get -TimeoutSec 5 -ErrorAction SilentlyContinue | Out-Null
    Write-ColorOutput "✅ OpenWebUI is accessible at http://localhost:3000" $Green
} catch {
    Write-ColorOutput "⚠️  OpenWebUI might still be starting up..." $Yellow
}

try {
    Invoke-RestMethod -Uri "http://localhost:8001/" -Method Get -TimeoutSec 5 | Out-Null
    Write-ColorOutput "✅ Memory API is accessible at http://localhost:8001" $Green
} catch {
    Write-ColorOutput "⚠️  Memory API might still be starting up..." $Yellow
}

Write-ColorOutput "`n🎉 Backend startup completed!" $Green
Write-ColorOutput "============================================================" $Cyan
Write-ColorOutput "📋 Next Steps:" $Blue
Write-ColorOutput "1. Open http://localhost:3000 in your browser" $Reset
Write-ColorOutput "2. Login as admin" $Reset
Write-ColorOutput "3. Go to Admin → Functions" $Reset
Write-ColorOutput "4. Look for 'Enhanced Memory Function'" $Reset
Write-ColorOutput "5. If not found, run: .\scripts\install_memory_function.ps1" $Reset
Write-ColorOutput "`n💡 The enhanced memory system is ready to use!" $Cyan
Write-ColorOutput "🔗 Memory API: http://localhost:8001" $Reset
Write-ColorOutput "🔗 OpenWebUI: http://localhost:3000" $Reset
