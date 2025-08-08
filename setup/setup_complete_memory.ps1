# Complete Memory System Setup with Functions + Pipelines
# ======================================================

Write-Host "🚀 Starting Complete Memory System with Functions + Pipelines" -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Green

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

# Start the main services first
Write-Host "🔄 Starting main Docker services..." -ForegroundColor Yellow
docker-compose up -d --remove-orphans

Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep 45

Write-Host "🔍 Checking service health..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "🛠️ Installing Memory Function..." -ForegroundColor Yellow
docker-compose --profile installer run --rm function_installer

Write-Host ""
Write-Host "🛠️ Installing Memory Pipeline..." -ForegroundColor Yellow
docker-compose --profile installer run --rm pipeline_installer

Write-Host ""
Write-Host "🎯 Complete Setup Instructions:" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Wait for all services to be healthy (check: docker-compose ps)" -ForegroundColor White
Write-Host ""
Write-Host "2. Access OpenWebUI at: http://localhost:8080" -ForegroundColor White
Write-Host "   - Create an account if you haven't already" -ForegroundColor Gray
Write-Host ""
Write-Host "3. For PIPELINE-based memory (recommended for user isolation):" -ForegroundColor White
Write-Host "   a. Go to Admin Panel > Settings > Connections" -ForegroundColor Gray
Write-Host "   b. Click + to add a new connection" -ForegroundColor Gray
Write-Host "   c. Set API URL to: http://localhost:9099" -ForegroundColor Gray
Write-Host "   d. Set API Key to: 0p3n-w3bu!" -ForegroundColor Gray
Write-Host "   e. Save and verify the connection" -ForegroundColor Gray
Write-Host "   f. Go to Admin Panel > Settings > Pipelines" -ForegroundColor Gray
Write-Host "   g. Verify Enhanced Memory Pipeline is listed" -ForegroundColor Gray
Write-Host "   h. In chat, select models with the Pipelines icon" -ForegroundColor Gray
Write-Host ""
Write-Host "4. For FUNCTION-based memory (fallback):" -ForegroundColor White
Write-Host "   a. Go to Admin Panel > Settings > Functions" -ForegroundColor Gray
Write-Host "   b. Verify Enhanced Memory Function is enabled" -ForegroundColor Gray
Write-Host "   c. Use any model normally" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 Service URLs:" -ForegroundColor Cyan
Write-Host "- OpenWebUI: http://localhost:8080" -ForegroundColor White
Write-Host "- Pipelines: http://localhost:9099 (for user-specific memory)" -ForegroundColor White
Write-Host "- Backend API: http://localhost:3000" -ForegroundColor White
Write-Host "- Memory API: http://localhost:5001" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Debugging:" -ForegroundColor Cyan
Write-Host "- Pipeline logs: docker logs backend-pipelines" -ForegroundColor White
Write-Host "- Function logs: docker logs backend-openwebui" -ForegroundColor White
Write-Host "- Memory API logs: docker logs backend-memory-api" -ForegroundColor White
Write-Host "- Backend logs: docker logs backend-main" -ForegroundColor White
Write-Host ""
Write-Host "💡 Memory System Features:" -ForegroundColor Cyan
Write-Host "- Functions: DISABLED (Enhanced Memory Pipeline provides proper user isolation)" -ForegroundColor White
Write-Host "- Pipelines: Advanced memory (proper user isolation by email/ID)" -ForegroundColor White
Write-Host ""
Write-Host "✅ Complete memory system setup finished!" -ForegroundColor Green
Write-Host "   Both Functions and Pipelines are now available for testing." -ForegroundColor Green
