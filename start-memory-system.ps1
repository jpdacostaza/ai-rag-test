# start-memory-system.ps1 - Start the complete memory pipeline system on Windows

Write-Host "🚀 Starting Complete Memory Pipeline System" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Create necessary directories
Write-Host "📁 Creating storage directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "storage/memory" | Out-Null
New-Item -ItemType Directory -Force -Path "storage/pipelines" | Out-Null
New-Item -ItemType Directory -Force -Path "storage/openwebui" | Out-Null
New-Item -ItemType Directory -Force -Path "storage/backend" | Out-Null
New-Item -ItemType Directory -Force -Path "storage/redis" | Out-Null
New-Item -ItemType Directory -Force -Path "storage/chroma" | Out-Null
New-Item -ItemType Directory -Force -Path "storage/ollama" | Out-Null

# Start the services
Write-Host "🐳 Starting Docker services..." -ForegroundColor Yellow
docker-compose up -d memory_api
Write-Host "⏳ Waiting for Memory API to start..." -ForegroundColor Cyan
Start-Sleep 10

docker-compose up -d pipelines
Write-Host "⏳ Waiting for Pipelines server to start..." -ForegroundColor Cyan
Start-Sleep 15

docker-compose up -d openwebui
Write-Host "⏳ Waiting for OpenWebUI to start..." -ForegroundColor Cyan
Start-Sleep 20

Write-Host "✅ System Status Check:" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green

# Check Memory API
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Memory API: Running on http://localhost:8000" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Memory API: Failed to start" -ForegroundColor Red
}

# Check Pipelines Server
try {
    $headers = @{"Authorization" = "Bearer 0p3n-w3bu!"}
    $response = Invoke-WebRequest -Uri "http://localhost:9098/" -Headers $headers -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Pipelines Server: Running on http://localhost:9098" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Pipelines Server: Failed to start" -ForegroundColor Red
}

# Check OpenWebUI
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ OpenWebUI: Running on http://localhost:3000" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ OpenWebUI: Failed to start" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Magenta
Write-Host "1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "2. Create an admin account (first time only)" -ForegroundColor White
Write-Host "3. Start a conversation and test memory functionality" -ForegroundColor White
Write-Host ""
Write-Host "📋 Test Conversation:" -ForegroundColor Cyan
Write-Host "Say: 'Hi! My name is [Your Name] and I work as [Your Job] at [Company].'" -ForegroundColor White
Write-Host "Then: 'What do you remember about me?'" -ForegroundColor White
Write-Host ""
Write-Host "🔧 To stop the system: docker-compose down" -ForegroundColor Yellow
