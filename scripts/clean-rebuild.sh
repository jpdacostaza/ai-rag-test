#!/bin/bash
# 🧹 Complete Docker Cleanup and Rebuild Script for Orange Pi Testing
# This script will completely purge Docker and rebuild everything fresh

echo "🚨 COMPLETE DOCKER CLEANUP AND REBUILD"
echo "This will remove ALL Docker data and rebuild from scratch!"
echo ""

# Confirm before proceeding
read -p "Are you sure you want to PURGE ALL Docker data? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Cancelled by user"
    exit 1
fi

echo "🛑 Step 1: Stopping all containers..."
docker stop $(docker ps -aq) 2>/dev/null || true

echo "🗑️ Step 2: Removing all containers..."
docker rm $(docker ps -aq) --force 2>/dev/null || true

echo "🖼️ Step 3: Removing all images..."
docker rmi $(docker images -aq) --force 2>/dev/null || true

echo "📦 Step 4: Removing all volumes..."
docker volume rm $(docker volume ls -q) --force 2>/dev/null || true

echo "🌐 Step 5: Removing all networks..."
docker network rm $(docker network ls -q) 2>/dev/null || true

echo "🧹 Step 6: System prune (remove everything)..."
docker system prune -a --volumes --force

echo "📋 Step 7: Verify clean state..."
echo "Containers:"
docker ps -a
echo "Images:"
docker images
echo "Volumes:"
docker volume ls
echo "Networks:"
docker network ls

echo ""
echo "🏗️ Step 8: Rebuilding from scratch..."

# Remove any existing build cache
echo "Clearing build cache..."
docker builder prune -a --force

# Build with no cache
echo "Building containers with no cache..."
docker-compose build --no-cache --pull

echo "🚀 Step 9: Starting fresh containers..."
docker-compose up -d

echo ""
echo "✅ COMPLETE REBUILD FINISHED!"
echo "🔍 Checking container status..."
docker-compose ps

echo ""
echo "📊 Container logs preview:"
echo "To view logs: docker-compose logs -f [service-name]"
echo "To check Ollama: docker exec backend-ollama ollama list"
echo "To monitor: docker stats"

echo ""
echo "🎉 Fresh Docker environment ready for Orange Pi testing!"
