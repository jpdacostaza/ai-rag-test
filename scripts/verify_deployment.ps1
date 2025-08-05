# Zero-Config Deployment Verification Script (PowerShell)
# Run this script to verify the system is ready for cross-host deployment

Write-Host "🎯 Zero-Config Deployment Verification" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Check critical files exist in correct locations
Write-Host "📁 Checking file organization..." -ForegroundColor Yellow

if (Test-Path "memory\api\enhanced_memory_api.py") {
    Write-Host "✅ Enhanced Memory API found in correct location: memory/api/" -ForegroundColor Green
} else {
    Write-Host "❌ Enhanced Memory API missing from memory/api/" -ForegroundColor Red
    exit 1
}

if (Test-Path "memory\functions\memory_filter_function.py") {
    Write-Host "✅ Memory Filter Function found in correct location: memory/functions/" -ForegroundColor Green
} else {
    Write-Host "❌ Memory Filter Function missing from memory/functions/" -ForegroundColor Red
    exit 1
}

if (Test-Path "docker-compose.yml") {
    Write-Host "✅ Docker Compose configuration found" -ForegroundColor Green
} else {
    Write-Host "❌ Docker Compose configuration missing" -ForegroundColor Red
    exit 1
}

if (Test-Path ".env") {
    Write-Host "✅ Environment configuration found" -ForegroundColor Green
} else {
    Write-Host "❌ Environment configuration missing" -ForegroundColor Red
    exit 1
}

# Check service name consistency
Write-Host ""
Write-Host "🔧 Checking service name consistency..." -ForegroundColor Yellow

# Check docker-compose.yml for memory-api service
$dockerContent = Get-Content "docker-compose.yml" -Raw
if ($dockerContent -match "memory-api:") {
    Write-Host "✅ Docker service name: memory-api" -ForegroundColor Green
} else {
    Write-Host "❌ Memory-api service not found in docker-compose.yml" -ForegroundColor Red
    exit 1
}

# Check .env consistency
$envContent = Get-Content ".env" | Where-Object { $_ -match "MEMORY_API_URL=" }
if ($envContent -match "memory-api:5001") {
    Write-Host "✅ Environment URL matches service name: $envContent" -ForegroundColor Green
} else {
    Write-Host "❌ Environment URL mismatch: $envContent" -ForegroundColor Red
    exit 1
}

# Check Dockerfile consistency
if (Test-Path "Dockerfile.memory") {
    $dockerfileContent = Get-Content "Dockerfile.memory" -Raw
    if ($dockerfileContent -match "memory\.api\.main:app") {
        Write-Host "✅ Dockerfile.memory correctly references memory.api.main:app" -ForegroundColor Green
    } else {
        Write-Host "❌ Dockerfile.memory missing correct entry point" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Dockerfile.memory not found" -ForegroundColor Red
    exit 1
}

# Check for hardcoded localhost in critical files
Write-Host ""
Write-Host "🌐 Checking for hardcoded localhost references..." -ForegroundColor Yellow

$localhostFiles = @()
Get-ChildItem -Path @("config", "pipelines", "memory") -Recurse -Include "*.py" -ErrorAction SilentlyContinue | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match "localhost" -and $content -notmatch "#.*localhost") {
        $localhostFiles += $_.Name
    }
}

if ($localhostFiles.Count -eq 0) {
    Write-Host "✅ No hardcoded localhost found in critical service files" -ForegroundColor Green
} else {
    Write-Host "⚠️  Found localhost references in $($localhostFiles.Count) files" -ForegroundColor Yellow
    Write-Host "   (Some may be acceptable for external API configuration)" -ForegroundColor Gray
}

# Final verification
Write-Host ""
Write-Host "🚀 Deployment Readiness Summary" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
Write-Host "✅ File organization: Complete" -ForegroundColor Green
Write-Host "✅ Service names: Consistent" -ForegroundColor Green
Write-Host "✅ Docker configuration: Ready" -ForegroundColor Green
Write-Host "✅ Environment variables: Configured" -ForegroundColor Green
Write-Host "✅ Zero-config deployment: READY" -ForegroundColor Green
Write-Host ""
Write-Host "📋 To deploy on another host:" -ForegroundColor Yellow
Write-Host "   1. Copy entire project directory" -ForegroundColor White
Write-Host "   2. Run: docker-compose up -d" -ForegroundColor White
Write-Host "   3. Access OpenWebUI at: http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "🎉 System verified and ready for deployment!" -ForegroundColor Green
