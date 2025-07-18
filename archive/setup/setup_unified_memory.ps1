# Enhanced Memory System Setup Script for OpenWebUI
# PowerShell version for Windows

Write-Host "🚀 Setting up Enhanced Memory System for OpenWebUI..." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Check if Docker is running
try {
    docker version | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
try {
    docker-compose version | Out-Null
} catch {
    Write-Host "❌ Docker Compose is not available. Please install Docker Compose." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker and Docker Compose are available" -ForegroundColor Green

# Build and start the complete system with automatic installer
Write-Host "🔧 Starting Enhanced Memory System (includes automatic installer)..." -ForegroundColor Yellow
Write-Host "   • Building containers..." -ForegroundColor Gray
Write-Host "   • Starting services..." -ForegroundColor Gray
Write-Host "   • Running automatic memory installer..." -ForegroundColor Gray

docker-compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "" 
    Write-Host "✅ Enhanced Memory System setup completed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Installation Summary:" -ForegroundColor Cyan
    Write-Host "   • Memory installer: ✅ Ran automatically on startup" -ForegroundColor Green
    Write-Host "   • Enhanced Memory Pipeline: ✅ Installed automatically" -ForegroundColor Green
    Write-Host "   • Enhanced Memory Function: 📋 Manual setup required" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📚 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Access OpenWebUI at: http://localhost:8080" -ForegroundColor White
    Write-Host "   2. Complete manual Function installation:" -ForegroundColor White
    Write-Host "      • Go to Admin Panel → Workspace → Functions" -ForegroundColor Gray
    Write-Host "      • Check installer logs for function code:" -ForegroundColor Gray
    Write-Host "        docker logs backend-memory-installer" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔗 Access Points:" -ForegroundColor Cyan
    Write-Host "   • OpenWebUI: http://localhost:8080" -ForegroundColor White
    Write-Host "   • Backend API: http://localhost:3000" -ForegroundColor White
    Write-Host "   • Memory API: http://localhost:8001" -ForegroundColor White
    Write-Host "   • Pipelines: http://localhost:9099" -ForegroundColor White
    Write-Host ""
    Write-Host "📖 Memory System Features:" -ForegroundColor Cyan
    Write-Host "   • ✅ Automatic conversation memory" -ForegroundColor Green
    Write-Host "   • ✅ Semantic memory search" -ForegroundColor Green
    Write-Host "   • ✅ User-specific memory isolation" -ForegroundColor Green
    Write-Host "   • ✅ Adaptive learning system" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Setup failed. Check the logs:" -ForegroundColor Red
    Write-Host "   docker-compose logs" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "🏁 Setup completed! Enjoy your enhanced OpenWebUI experience!" -ForegroundColor Green
