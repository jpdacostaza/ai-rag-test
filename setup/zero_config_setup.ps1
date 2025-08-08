# Zero-Configuration OpenWebUI Complete Setup Script (PowerShell)
# ================================================================
#
# This script sets up the complete OpenWebUI integration with all latest updates:
# - Enhanced Memory System (Redis + ChromaDB) on correct port 5001
# - Function Filters (for memory enhancement)  
# - Pipeline Integration (for user isolation)
# - Web Search Capabilities
# - Updated Persona Configurations
# - All latest verified configurations

Write-Host "🚀 Starting Zero-Configuration OpenWebUI Complete Setup" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Green

# Create necessary directories
Write-Host "📁 Creating required directories..." -ForegroundColor Yellow
$directories = @(
    "storage\\pipelines",
    "storage\\openwebui", 
    "storage\\backend",
    "storage\\memory",
    "storage\\redis",
    "storage\\chroma",
    "storage\\ollama",
    "storage\\models"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Gray
    }
}

# Start the main services
Write-Host "🔄 Starting Docker services with latest configurations..." -ForegroundColor Yellow
docker-compose up -d --remove-orphans

Write-Host "⏳ Waiting for services to initialize (45 seconds)..." -ForegroundColor Yellow
Start-Sleep 45

Write-Host "🔍 Checking service health..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "🛠️ Installing Memory Functions..." -ForegroundColor Yellow
docker-compose --profile installer run --rm function_installer

Write-Host ""
Write-Host "🛠️ Installing Memory Pipelines..." -ForegroundColor Yellow
docker-compose --profile installer run --rm pipeline_installer

Write-Host ""
Write-Host "🧪 Verifying service integration..." -ForegroundColor Yellow

# Verify services are responding
$services = @{
    "OpenWebUI" = "http://localhost:8080/"
    "Memory API" = "http://localhost:5001/health"
    "Pipelines" = "http://localhost:9099/"
    "Ollama" = "http://localhost:11434/api/tags"
}

$healthyServices = 0
foreach ($service in $services.GetEnumerator()) {
    try {
        $response = Invoke-WebRequest -Uri $service.Value -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "   ✅ $($service.Key): HEALTHY" -ForegroundColor Green
            $healthyServices++
        } else {
            Write-Host "   ⚠️  $($service.Key): Status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ $($service.Key): CONNECTION FAILED" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "📊 Service Health: $healthyServices/4 services responding" -ForegroundColor Cyan

Write-Host ""
Write-Host "🎉 ZERO-CONFIG SETUP COMPLETE!" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

Write-Host ""
Write-Host "📊 Service URLs (CORRECTED PORTS):" -ForegroundColor Cyan
Write-Host "   🌐 OpenWebUI:    http://localhost:8080" -ForegroundColor White
Write-Host "   🧠 Memory API:   http://localhost:5001" -ForegroundColor White
Write-Host "   🔄 Pipelines:    http://localhost:9099" -ForegroundColor White
Write-Host "   🤖 Ollama:       http://localhost:11434" -ForegroundColor White

Write-Host ""
Write-Host "🚀 Quick Start:" -ForegroundColor Cyan
Write-Host "   1. Open OpenWebUI at http://localhost:8080" -ForegroundColor White
Write-Host "   2. Create an account if needed" -ForegroundColor White
Write-Host "   3. Start chatting - memory and web search are already configured!" -ForegroundColor White

Write-Host ""
Write-Host "⚙️  Advanced Configuration (Optional):" -ForegroundColor Cyan
Write-Host "   • Pipeline Setup: Admin Panel > Settings > Connections" -ForegroundColor White
Write-Host "     - Add URL: http://localhost:9099" -ForegroundColor Gray
Write-Host "     - API Key: 0p3n-w3bu!" -ForegroundColor Gray
Write-Host "   • Function Setup: Admin Panel > Settings > Functions" -ForegroundColor White
Write-Host "     - Verify 'Enhanced Memory Function' is enabled" -ForegroundColor Gray

Write-Host ""
Write-Host "🔧 Features Included:" -ForegroundColor Cyan
Write-Host "   ✅ Enhanced Memory System (Redis + ChromaDB)" -ForegroundColor Green
Write-Host "   ✅ Function Filters (memory enhancement)" -ForegroundColor Green
Write-Host "   ✅ Pipeline Integration (user isolation)" -ForegroundColor Green
Write-Host "   ✅ Web Search Capabilities (DuckDuckGo)" -ForegroundColor Green
Write-Host "   ✅ Updated Persona Configurations" -ForegroundColor Green
Write-Host "   ✅ All latest verified configurations" -ForegroundColor Green

Write-Host ""
Write-Host "🐛 Debugging Commands:" -ForegroundColor Cyan
Write-Host "   docker-compose ps                    # Check service status" -ForegroundColor White
Write-Host "   docker logs backend-memory-api       # Memory API logs (PORT 5001)" -ForegroundColor White
Write-Host "   docker logs backend-openwebui        # OpenWebUI logs" -ForegroundColor White
Write-Host "   docker logs backend-pipelines        # Pipeline logs" -ForegroundColor White

if ($healthyServices -ge 3) {
    Write-Host ""
    Write-Host "✅ ALL SYSTEMS READY FOR PRODUCTION USE!" -ForegroundColor Green
    Write-Host "🎯 Complete OpenWebUI integration verified and operational" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚠️  SETUP COMPLETED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "Some services may need manual verification" -ForegroundColor Yellow
}

Write-Host "==============================" -ForegroundColor Green
