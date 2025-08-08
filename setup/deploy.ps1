# Enhanced Memory System - Simplified Deployment Script (Windows)

param(
    [switch]$Clean,
    [switch]$Verify,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Logs
)

# Configuration
$ComposeFile = "docker-compose.simplified.yml"
$ProjectName = "enhanced-memory"

# Functions
function Write-Info {
    param($Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

function Write-Success {
    param($Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param($Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning {
    param($Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check Docker
    try {
        docker --version | Out-Null
    } catch {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    
    # Check Docker Compose
    try {
        docker-compose --version | Out-Null
    } catch {
        Write-Error "Docker Compose is not available. Please ensure Docker Desktop is properly installed."
        exit 1
    }
    
    # Check Docker daemon
    try {
        docker info | Out-Null
    } catch {
        Write-Error "Docker daemon is not running. Please start Docker Desktop first."
        exit 1
    }
    
    Write-Success "Prerequisites check passed"
}

# Stop and clean up existing deployment
function Stop-ExistingDeployment {
    param([bool]$CleanImages)
    
    Write-Info "Cleaning up existing deployment..."
    
    # Stop services
    try {
        docker-compose -f $ComposeFile -p $ProjectName down --remove-orphans 2>$null
    } catch {
        # Ignore errors if no existing deployment
    }
    
    # Remove old containers
    try {
        docker container prune -f 2>$null
    } catch {
        # Ignore errors
    }
    
    # Remove unused images (optional)
    if ($CleanImages) {
        Write-Warning "Removing unused Docker images..."
        try {
            docker image prune -f 2>$null
        } catch {
            # Ignore errors
        }
    }
    
    Write-Success "Cleanup completed"
}

# Build and start services
function Start-Services {
    Write-Info "Building and starting services..."
    
    # Build images
    Write-Info "Building application images..."
    docker-compose -f $ComposeFile -p $ProjectName build --no-cache
    
    # Start core services first
    Write-Info "Starting core data services..."
    docker-compose -f $ComposeFile -p $ProjectName up -d redis chroma ollama
    
    # Wait for core services to be healthy
    Write-Info "Waiting for core services to be ready..."
    Start-Sleep 30
    
    # Start application services
    Write-Info "Starting application services..."
    docker-compose -f $ComposeFile -p $ProjectName up -d backend memory-api
    
    # Wait for application services
    Write-Info "Waiting for application services to be ready..."
    Start-Sleep 20
    
    # Start OpenWebUI services
    Write-Info "Starting OpenWebUI services..."
    docker-compose -f $ComposeFile -p $ProjectName up -d open-webui pipelines
    
    # Wait for OpenWebUI to be ready
    Write-Info "Waiting for OpenWebUI to be ready..."
    Start-Sleep 15
    
    # Run installer
    Write-Info "Running automatic configuration..."
    docker-compose -f $ComposeFile -p $ProjectName up installer
    
    Write-Success "All services started successfully"
}

# Verify deployment
function Test-Deployment {
    Write-Info "Verifying deployment..."
    
    # Check service status
    Write-Info "Checking service status..."
    docker-compose -f $ComposeFile -p $ProjectName ps
    
    # Health checks
    Write-Info "Performing health checks..."
    
    # Backend API
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Success "Backend API is healthy"
        }
    } catch {
        Write-Error "Backend API health check failed"
    }
    
    # Memory API
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5001/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Success "Memory API is healthy"
        }
    } catch {
        Write-Error "Memory API health check failed"
    }
    
    # Ollama
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Success "Ollama service is healthy"
        }
    } catch {
        Write-Warning "Ollama service may still be starting up"
    }
    
    # OpenWebUI
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Success "OpenWebUI is accessible"
        }
    } catch {
        Write-Error "OpenWebUI is not accessible"
    }
    
    Write-Success "Deployment verification completed"
}

# Download default model
function Get-DefaultModel {
    Write-Info "Downloading default model (llama3.2:3b)..."
    try {
        docker exec enhanced-ollama ollama pull llama3.2:3b
        Write-Success "Model download completed"
    } catch {
        Write-Warning "Model download failed. You can download it later from OpenWebUI."
    }
}

# Display access information
function Show-AccessInfo {
    Write-Host ""
    Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Access URLs:" -ForegroundColor Cyan
    Write-Host "   OpenWebUI:    http://localhost:8080" -ForegroundColor White
    Write-Host "   Backend API:  http://localhost:3000" -ForegroundColor White
    Write-Host "   Memory API:   http://localhost:5001" -ForegroundColor White
    Write-Host "   Ollama:       http://localhost:11434" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Open http://localhost:8080 in your browser" -ForegroundColor White
    Write-Host "   2. Create your first user account" -ForegroundColor White
    Write-Host "   3. The Enhanced Memory System is automatically configured" -ForegroundColor White
    Write-Host "   4. Start chatting - your conversations will be remembered!" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 Management Commands:" -ForegroundColor Cyan
    Write-Host "   View logs:    docker-compose -f $ComposeFile -p $ProjectName logs -f" -ForegroundColor White
    Write-Host "   Stop system:  docker-compose -f $ComposeFile -p $ProjectName down" -ForegroundColor White
    Write-Host "   Restart:      docker-compose -f $ComposeFile -p $ProjectName restart" -ForegroundColor White
    Write-Host ""
}

# Main deployment flow
Write-Host "🚀 Enhanced Memory System - Simplified Deployment" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

if ($Stop) {
    Write-Info "Stopping Enhanced Memory System..."
    docker-compose -f $ComposeFile -p $ProjectName down
    Write-Success "System stopped"
    exit 0
}

if ($Restart) {
    Write-Info "Restarting Enhanced Memory System..."
    docker-compose -f $ComposeFile -p $ProjectName restart
    Test-Deployment
    Write-Success "System restarted"
    exit 0
}

if ($Logs) {
    docker-compose -f $ComposeFile -p $ProjectName logs -f
    exit 0
}

if ($Verify) {
    Test-Deployment
    exit 0
}

# Full deployment
Test-Prerequisites
Stop-ExistingDeployment -CleanImages $Clean
Start-Services
Test-Deployment
Get-DefaultModel
Show-AccessInfo
