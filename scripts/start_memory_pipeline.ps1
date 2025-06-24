# Quick Start Script for OpenWebUI Memory Pipeline
# Date: June 24, 2025

Write-Host "🚀 Starting OpenWebUI Memory Pipeline System..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Start all Docker services
Write-Host "📦 Starting Docker containers..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "⏳ Waiting for services to start (60 seconds)..." -ForegroundColor Yellow
Start-Sleep 60

# Check service health
Write-Host "🏥 Checking service health..." -ForegroundColor Yellow
Write-Host "Backend Health:" -ForegroundColor Cyan
curl http://localhost:8001/health

Write-Host "`nPipeline Discovery:" -ForegroundColor Cyan
curl http://localhost:8001/pipelines

Write-Host "`nDocker Services:" -ForegroundColor Cyan
docker-compose ps

Write-Host "`n✅ System Status:" -ForegroundColor Green
Write-Host "- Backend: http://localhost:8001" -ForegroundColor White
Write-Host "- OpenWebUI: http://localhost:3000" -ForegroundColor White
Write-Host "- Pipeline Endpoints: http://localhost:8001/pipelines" -ForegroundColor White

Write-Host "`n🎯 NEXT STEPS:" -ForegroundColor Magenta
Write-Host "1. Open http://localhost:3000 in browser" -ForegroundColor White
Write-Host "2. Go to Settings → Admin → Pipelines" -ForegroundColor White
Write-Host "3. Enable 'Backend Memory Pipeline'" -ForegroundColor White
Write-Host "4. Test: Say 'My name is John' then ask 'What's my name?'" -ForegroundColor White

Write-Host "`n📋 STATUS: Ready for final activation!" -ForegroundColor Green
