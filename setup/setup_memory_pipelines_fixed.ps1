# Enhanced Memory System with Pipelines Setup
# ===========================================

Write-Host "🚀 Starting Enhanced Memory System with Pipelines" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Create necessary directories
Write-Host "📁 Creating required directories..." -ForegroundColor Yellow
$directories = @(
    "storage\pipelines",
    "storage\openwebui", 
    "storage\backend",
    "storage\memory",
    "storage\redis",
    "storage\chroma",
    "storage\ollama",
    "storage\models"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Gray
    }
}

# Copy memory pipeline to pipelines directory
Write-Host "📁 Setting up memory pipeline..." -ForegroundColor Yellow
Copy-Item "memory_pipeline.py" "storage\pipelines\" -Force

# Start the services
Write-Host "🔄 Starting Docker services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep 30

Write-Host "🔍 Checking service health..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "🎯 Setup Instructions:" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Wait for all services to start (check with: docker-compose ps)" -ForegroundColor White
Write-Host ""
Write-Host "2. Access OpenWebUI at: http://localhost:8080" -ForegroundColor White
Write-Host "   - Create an account if you haven't already" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Go to Admin Panel > Settings > Connections" -ForegroundColor White
Write-Host "   - Click the + button to add a new connection" -ForegroundColor Gray
Write-Host "   - Set API URL to: http://localhost:9099" -ForegroundColor Gray
Write-Host "   - Set API Key to: 0p3n-w3bu!" -ForegroundColor Gray
Write-Host "   - Save and verify the connection" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Go to Admin Panel > Settings > Pipelines" -ForegroundColor White
Write-Host "   - You should see Enhanced Memory Pipeline" -ForegroundColor Gray
Write-Host "   - Configure the valves if needed:" -ForegroundColor Gray
Write-Host "     * backend_url: http://backend:3000 (internal container URL)" -ForegroundColor Gray
Write-Host "     * debug: true (for testing)" -ForegroundColor Gray
Write-Host ""
Write-Host "5. In a chat, select a model that routes through Pipelines" -ForegroundColor White
Write-Host "   - Look for the Pipelines icon next to model names" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 Service URLs:" -ForegroundColor Cyan
Write-Host "- OpenWebUI: http://localhost:8080" -ForegroundColor White
Write-Host "- Pipelines: http://localhost:9099" -ForegroundColor White
Write-Host "- Backend API: http://localhost:3000" -ForegroundColor White
Write-Host "- Memory API: http://localhost:8001" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Debugging:" -ForegroundColor Cyan
Write-Host "- Pipeline logs: docker logs backend-pipelines" -ForegroundColor White
Write-Host "- Memory API logs: docker logs backend-memory-api" -ForegroundColor White
Write-Host "- Backend logs: docker logs backend-main" -ForegroundColor White
Write-Host ""
Write-Host "✅ Setup complete! Your memory system now has proper user identification." -ForegroundColor Green
