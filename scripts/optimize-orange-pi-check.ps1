# ===============================================================================
# Orange Pi 5 Plus Optimization Check Script (PowerShell)
# ===============================================================================
# This script helps you verify and apply optimizations for Orange Pi 5 Plus
# Run this from Windows PowerShell to check your system configuration
# ===============================================================================

Write-Host "🔧 Orange Pi 5 Plus Optimization Checker" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

Write-Host "`n📊 Checking Docker Configuration..." -ForegroundColor Yellow

# Check if Docker is running
try {
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker is running" -ForegroundColor Green
        
        # Check if Docker Compose is available
        $composeVersion = docker-compose --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker Compose is available: $($composeVersion)" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Docker Compose not found" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Docker is not running or not installed" -ForegroundColor Red
        Write-Host "   Please start Docker Desktop or install Docker" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Error checking Docker status" -ForegroundColor Red
    exit 1
}

Write-Host "`n🐳 Checking Current Container Status..." -ForegroundColor Yellow

# Check if containers are running
try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" 2>$null
    if ($containers) {
        Write-Host "Current containers:" -ForegroundColor Cyan
        Write-Host $containers
    } else {
        Write-Host "No containers currently running" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not retrieve container status" -ForegroundColor Yellow
}

Write-Host "`n📋 Configuration Files Check..." -ForegroundColor Yellow

# Check key configuration files
$configFiles = @(
    "docker-compose.yml",
    ".env",
    "scripts/optimize-orange-pi.sh"
)

foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file exists" -ForegroundColor Green
    } else {
        Write-Host "❌ $file missing" -ForegroundColor Red
    }
}

Write-Host "`n🎯 Recommended Actions for Orange Pi 5 Plus:" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

Write-Host "`n1. 🔧 System Level Optimizations (run on Orange Pi 5 Plus):" -ForegroundColor White
Write-Host "   # Copy and run the optimization script:" -ForegroundColor Gray
Write-Host "   scp scripts/optimize-orange-pi.sh user@your-orange-pi:~/" -ForegroundColor Gray
Write-Host "   ssh user@your-orange-pi" -ForegroundColor Gray
Write-Host "   chmod +x optimize-orange-pi.sh" -ForegroundColor Gray
Write-Host "   sudo ./optimize-orange-pi.sh" -ForegroundColor Gray

Write-Host "`n2. 🐳 Docker Service Management:" -ForegroundColor White
Write-Host "   # Start optimized services:" -ForegroundColor Gray
Write-Host "   docker-compose down" -ForegroundColor Gray
Write-Host "   docker-compose up -d" -ForegroundColor Gray

Write-Host "`n3. 📊 Performance Monitoring:" -ForegroundColor White
Write-Host "   # Monitor system performance:" -ForegroundColor Gray
Write-Host "   ./monitor-orange-pi.sh" -ForegroundColor Gray
Write-Host "   # Or check individual containers:" -ForegroundColor Gray
Write-Host "   docker stats" -ForegroundColor Gray

Write-Host "`n4. 🌡️  Temperature Monitoring:" -ForegroundColor White
Write-Host "   # Check CPU temperature regularly:" -ForegroundColor Gray
Write-Host "   watch -n 2 'cat /sys/class/thermal/thermal_zone0/temp'" -ForegroundColor Gray

Write-Host "`n5. 🔍 Troubleshooting Commands:" -ForegroundColor White
Write-Host "   # Check Ollama logs:" -ForegroundColor Gray
Write-Host "   docker logs backend-ollama -f" -ForegroundColor Gray
Write-Host "   # Check all service logs:" -ForegroundColor Gray
Write-Host "   docker-compose logs -f" -ForegroundColor Gray

Write-Host "`n⚠️  Important Notes for Orange Pi 5 Plus:" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Yellow
Write-Host "• Ensure adequate cooling (heatsink + fan recommended)" -ForegroundColor White
Write-Host "• Use a quality 5V 4A power supply" -ForegroundColor White
Write-Host "• Monitor CPU temperature during heavy workloads" -ForegroundColor White
Write-Host "• The qwen3:4b model requires significant resources" -ForegroundColor White
Write-Host "• CPU affinity (cores 1-7 for Ollama) is already configured" -ForegroundColor White

Write-Host "`n🚀 Expected Performance Improvements:" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host "• Faster Ollama response times" -ForegroundColor White
Write-Host "• Better CPU core utilization" -ForegroundColor White
Write-Host "• Reduced memory pressure and swapping" -ForegroundColor White
Write-Host "• More stable performance under sustained load" -ForegroundColor White
Write-Host "• Improved thermal management" -ForegroundColor White

Write-Host "`n✅ Optimization configuration is ready!" -ForegroundColor Green
Write-Host "Run the optimization script on your Orange Pi 5 Plus to apply system-level changes." -ForegroundColor Cyan

# Check if user wants to see current .env optimizations
Write-Host "`n📄 Would you like to see the current ARM64 optimizations in .env? (y/n): " -ForegroundColor Cyan -NoNewline
$response = Read-Host

if ($response -eq 'y' -or $response -eq 'Y') {
    if (Test-Path ".env") {
        Write-Host "`n📋 Current ARM64 Optimizations in .env:" -ForegroundColor Yellow
        Write-Host "=======================================" -ForegroundColor Yellow
        $envContent = Get-Content ".env" | Where-Object { $_ -match "ARM64|OLLAMA_NUM|THREAD|PARALLEL|TIMEOUT" }
        foreach ($line in $envContent) {
            Write-Host "  $line" -ForegroundColor Gray
        }
    } else {
        Write-Host "❌ .env file not found" -ForegroundColor Red
    }
}

Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
