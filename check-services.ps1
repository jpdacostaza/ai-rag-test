#!/usr/bin/env pwsh
# AI RAG Backend - Service Status Checker
# Run this script to check the health of all services

Write-Host "🔍 AI RAG Backend Service Status Check" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

# Service endpoints
$services = @{
    "🔴 Redis Cache" = "redis://localhost:6379"
    "🟣 ChromaDB" = "http://localhost:8000/api/v2/version"
    "🤖 Ollama" = "http://localhost:11434/api/tags"
    "🚀 Backend API" = "http://localhost:3000/health/simple"
    "🧠 Memory API" = "http://localhost:5001/health"
    "📊 Pipelines" = "http://localhost:9099/"
    "🌐 OpenWebUI" = "http://localhost:8080/health"
}

foreach ($service in $services.GetEnumerator()) {
    $name = $service.Key
    $url = $service.Value
    
    try {
        if ($url.StartsWith("redis://")) {
            # Test Redis with docker exec
            $result = docker exec backend-redis redis-cli ping 2>$null
            if ($result -eq "PONG") {
                Write-Host "✅ $name - HEALTHY" -ForegroundColor Green
            } else {
                Write-Host "❌ $name - UNHEALTHY" -ForegroundColor Red
            }
        } else {
            # Test HTTP endpoints
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing 2>$null
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ $name - HEALTHY" -ForegroundColor Green
            } else {
                Write-Host "❌ $name - UNHEALTHY (Status: $($response.StatusCode))" -ForegroundColor Red
            }
        }
    }
    catch {
        Write-Host "❌ $name - UNREACHABLE" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🐳 Docker Container Status:" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "backend-"

Write-Host ""
Write-Host "📋 Service Access URLs:" -ForegroundColor Cyan
Write-Host "   Backend API:    http://localhost:3000" -ForegroundColor White
Write-Host "   Memory API:     http://localhost:5001" -ForegroundColor White  
Write-Host "   OpenWebUI:      http://localhost:8080" -ForegroundColor White
Write-Host "   Pipelines:      http://localhost:9099" -ForegroundColor White
Write-Host "   Ollama:         http://localhost:11434" -ForegroundColor White
Write-Host "   ChromaDB:       http://localhost:8000" -ForegroundColor White
Write-Host "   Redis:          localhost:6379" -ForegroundColor White
