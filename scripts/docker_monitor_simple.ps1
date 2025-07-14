# Simple Docker Restart and Monitor Script
param(
    [int]$MonitorDuration = 120
)

$ErrorActionPreference = "Continue"
$logFile = "logs\docker_restart_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
    $logMessage | Out-File -FilePath $logFile -Append -Encoding UTF8
}

function Get-ContainerStatus {
    param([string]$ContainerName)
    try {
        $status = docker ps -a --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
        return $status
    } catch {
        return "Error getting status for $ContainerName"
    }
}

# Main execution
Write-Log "🚀 Starting Docker restart and monitoring..." "INFO"

# Step 1: Stop all containers
Write-Log "📦 Stopping all containers..." "INFO"
docker-compose down 2>&1 | ForEach-Object { Write-Log $_ }

# Wait a moment
Start-Sleep -Seconds 5

# Step 2: Start all containers
Write-Log "🔄 Starting all containers..." "INFO"
docker-compose up -d 2>&1 | ForEach-Object { Write-Log $_ }

# Step 3: Monitor for specified duration
$containers = @("backend-backend-1", "backend-redis-1", "backend-chroma-1", "backend-gateway-1")
$startTime = Get-Date
$endTime = $startTime.AddSeconds($MonitorDuration)

Write-Log "👀 Monitoring containers for $MonitorDuration seconds..." "INFO"

while ((Get-Date) -lt $endTime) {
    Write-Log "🔍 Health check at $(Get-Date -Format 'HH:mm:ss')..." "INFO"
    
    foreach ($container in $containers) {
        $status = Get-ContainerStatus $container
        Write-Log "Container $container status:" "INFO"
        Write-Log "$status" "INFO"
        
        # Get recent logs
        try {
            $logs = docker logs --tail 5 $container 2>&1
            if ($logs) {
                Write-Log "Recent logs for $container`:" "INFO"
                $logs | ForEach-Object { Write-Log "  $_" "LOG" }
            }
        } catch {
            Write-Log "Could not get logs for $container" "WARN"
        }
    }
    
    # Check for errors in recent logs
    foreach ($container in $containers) {
        try {
            $errorLogs = docker logs --since="30s" $container 2>&1 | Where-Object { $_ -match "(error|failed|exception)" -and $_ -notmatch "(?i)(test|debug)" }
            if ($errorLogs) {
                Write-Log "🚨 Errors detected in $container`:" "ERROR"
                $errorLogs | ForEach-Object { Write-Log "   $_" "ERROR" }
            }
        } catch {
            # Container might not exist
        }
    }
    
    Start-Sleep -Seconds 30
}

# Final status report
Write-Log "📋 Final container status:" "INFO"
docker ps -a 2>&1 | ForEach-Object { Write-Log $_ "REPORT" }

Write-Log "✅ Monitoring completed!" "INFO"
Write-Log "📁 Full log saved to: $logFile" "INFO"
