# 🧹 Complete Docker Cleanup and Rebuild Script for Orange Pi Testing
# This script will completely purge Docker and rebuild everything fresh

Write-Host "🚨 COMPLETE DOCKER CLEANUP AND REBUILD" -ForegroundColor Red
Write-Host "This will remove ALL Docker data and rebuild from scratch!" -ForegroundColor Yellow
Write-Host ""

# Confirm before proceeding
$confirm = Read-Host "Are you sure you want to PURGE ALL Docker data? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "❌ Cancelled by user" -ForegroundColor Red
    exit 1
}

Write-Host "🛑 Step 1: Stopping all containers..." -ForegroundColor Cyan
docker stop $(docker ps -aq) 2>$null

Write-Host "🗑️ Step 2: Removing all containers..." -ForegroundColor Cyan
docker rm $(docker ps -aq) --force 2>$null

Write-Host "🖼️ Step 3: Removing all images..." -ForegroundColor Cyan
docker rmi $(docker images -aq) --force 2>$null

Write-Host "📦 Step 4: Removing all volumes..." -ForegroundColor Cyan
docker volume rm $(docker volume ls -q) --force 2>$null

Write-Host "🌐 Step 5: Removing all networks..." -ForegroundColor Cyan
docker network rm $(docker network ls -q) 2>$null

Write-Host "🧹 Step 6: System prune (remove everything)..." -ForegroundColor Cyan
docker system prune -a --volumes --force

Write-Host "🔄 Step 7: Restart Docker Desktop..." -ForegroundColor Cyan
Write-Host "Please restart Docker Desktop manually, then press Enter to continue..."
Read-Host

Write-Host "📋 Step 8: Verify clean state..." -ForegroundColor Cyan
Write-Host "Containers:" -ForegroundColor Yellow
docker ps -a
Write-Host "Images:" -ForegroundColor Yellow
docker images
Write-Host "Volumes:" -ForegroundColor Yellow
docker volume ls
Write-Host "Networks:" -ForegroundColor Yellow
docker network ls

Write-Host ""
Write-Host "🏗️ Step 9: Rebuilding from scratch..." -ForegroundColor Green

# Remove any existing build cache
Write-Host "Clearing build cache..." -ForegroundColor Cyan
docker builder prune -a --force

# Build with no cache
Write-Host "Building containers with no cache..." -ForegroundColor Cyan
docker-compose build --no-cache --pull

Write-Host "🚀 Step 10: Starting fresh containers..." -ForegroundColor Green
docker-compose up -d

Write-Host ""
Write-Host "✅ COMPLETE REBUILD FINISHED!" -ForegroundColor Green
Write-Host "🔍 Checking container status..." -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "📊 Container logs preview:" -ForegroundColor Yellow
Write-Host "To view logs: docker-compose logs -f [service-name]" -ForegroundColor Gray
Write-Host "To check Ollama: docker exec backend-ollama ollama list" -ForegroundColor Gray
Write-Host "To monitor: docker stats" -ForegroundColor Gray

Write-Host ""
Write-Host "🎉 Fresh Docker environment ready for Orange Pi testing!" -ForegroundColor Green
