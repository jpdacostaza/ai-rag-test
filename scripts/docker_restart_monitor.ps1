#!/usr/bin/env powershell
<#
.SYNOPSIS
Docker Restart and Comprehensive Log Monitoring Script

.DESCRIPTION
This script performs a complete Docker restart and monitors all container logs
for startup issues, errors, and system health validation.

.EXAMPLE
./docker_restart_monitor.ps1
#>

param(
    [string]$LogDir = "logs",
    [int]$MonitorDuration = 120,  # Monitor for 2 minutes after restart
    [switch]$SkipRestart = $false
)

# Create log directory
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "$LogDir/docker_restart_monitor_$timestamp.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $logEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | $Level | $Message"
    Write-Host $logEntry
    Add-Content -Path $logFile -Value $logEntry
}

function Test-DockerRunning {
    try {
        docker info | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Get-ContainerHealth {
    param([string]$ContainerName)
    
    try {
        $status = docker inspect --format='{{.State.Status}}' $ContainerName 2>$null
        $health = docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' $ContainerName 2>$null
        
        return @{
            Status = $status
            Health = $health
            Running = ($status -eq "running")
        }
    } catch {
        return @{
            Status = "not-found"
            Health = "unknown"
            Running = $false
        }
    }
}

function Get-ContainerLogs {
    param([string]$ContainerName, [int]$Lines = 50)
    
    Write-Log "=== $ContainerName LOGS (Last $Lines lines) ===" "CONTAINER"
    
    try {
        $logs = docker logs --tail $Lines $ContainerName 2>&1
        if ($logs) {
            $logs | ForEach-Object {
                $logLine = $_.ToString()
                # Highlight errors and warnings
                if ($logLine -match "(error|failed|exception)" -and $logLine -notmatch "(?i)(test|debug)") {
                    Write-Log "❌ $logLine" "ERROR"
                } elseif ($logLine -match "(warning|warn)" -and $logLine -notmatch "(?i)(test|debug)") {
                    Write-Log "⚠️  $logLine" "WARN"
                } elseif ($logLine -match "(ready|healthy|success|started)" -and $logLine -notmatch "(?i)(test|debug)") {
                    Write-Log "✅ $logLine" "SUCCESS"
                } else {
                    Write-Log "$logLine" "LOG"
                }
            }
        } else {
            Write-Log "No logs available for $ContainerName" "WARN"
        }
    } catch {
        Write-Log "Failed to get logs for $ContainerName`: $_" "ERROR"
    }
    
    Write-Log "=== END $ContainerName LOGS ===" "CONTAINER"
    Write-Log ""
}

function Test-ServiceEndpoint {
    param([string]$Url, [string]$ServiceName, [int]$TimeoutSeconds = 10)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec $TimeoutSeconds -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Log "✅ $ServiceName endpoint responding (HTTP $($response.StatusCode))" "SUCCESS"
            return $true
        } else {
            Write-Log "⚠️  $ServiceName endpoint returned HTTP $($response.StatusCode)" "WARN"
            return $false
        }
    } catch {
        Write-Log "❌ $ServiceName endpoint not responding: $_" "ERROR"
        return $false
    }
}

# Main execution
Write-Log "🚀 Docker Restart and Monitoring Script Started" "INFO"
Write-Log "Log file: $logFile" "INFO"
Write-Log "Monitor duration: $MonitorDuration seconds" "INFO"

# Check if Docker is running
if (!(Test-DockerRunning)) {
    Write-Log "❌ Docker is not running or not accessible" "ERROR"
    exit 1
}

# Step 1: Docker Restart (unless skipped)
if (!$SkipRestart) {
    Write-Log "🔄 Step 1: Stopping all containers..." "INFO"
    try {
        docker-compose down --remove-orphans
        Start-Sleep -Seconds 5
        Write-Log "✅ Containers stopped successfully" "SUCCESS"
    } catch {
        Write-Log "❌ Error stopping containers: $_" "ERROR"
    }

    Write-Log "🔄 Step 2: Starting all containers..." "INFO"
    try {
        docker-compose up -d
        Write-Log "✅ Containers started successfully" "SUCCESS"
    } catch {
        Write-Log "❌ Error starting containers: $_" "ERROR"
        exit 1
    }
} else {
    Write-Log "⏭️  Skipping Docker restart (--SkipRestart specified)" "INFO"
}

# Wait for containers to initialize
Write-Log "⏳ Waiting 15 seconds for containers to initialize..." "INFO"
Start-Sleep -Seconds 15

# Step 3: Monitor Container Status
Write-Log "📊 Step 3: Monitoring container status..." "INFO"

$containers = @(
    "backend-redis",
    "backend-chroma", 
    "backend-ollama",
    "backend-openwebui",
    "backend-pipelines"
)

foreach ($container in $containers) {
    $health = Get-ContainerHealth $container
    if ($health.Running) {
        Write-Log "✅ $container`: Status=$($health.Status), Health=$($health.Health)" "SUCCESS"
    } else {
        Write-Log "❌ $container`: Status=$($health.Status), Health=$($health.Health)" "ERROR"
    }
}

# Step 4: Collect Initial Logs
Write-Log "📝 Step 4: Collecting initial container logs..." "INFO"

foreach ($container in $containers) {
    Monitor-ContainerLogs $container 30
}

# Step 5: Test Service Endpoints
Write-Log "🌐 Step 5: Testing service endpoints..." "INFO"

$endpoints = @(
    @{ Url = "http://localhost:6379"; Name = "Redis"; Note = "TCP connection test" },
    @{ Url = "http://localhost:8000/api/v1/heartbeat"; Name = "ChromaDB" },
    @{ Url = "http://localhost:11434/api/tags"; Name = "Ollama" },
    @{ Url = "http://localhost:8080/health"; Name = "OpenWebUI" },
    @{ Url = "http://localhost:9099"; Name = "Pipelines" },
    @{ Url = "http://localhost:3000/health"; Name = "Backend API" }
)

foreach ($endpoint in $endpoints) {
    if ($endpoint.Url -like "*6379*") {
        # Special handling for Redis (TCP test)
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $tcpClient.ConnectAsync("localhost", 6379).Wait(5000)
            if ($tcpClient.Connected) {
                Write-Log "✅ Redis TCP connection successful" "SUCCESS"
                $tcpClient.Close()
            } else {
                Write-Log "❌ Redis TCP connection failed" "ERROR"
            }
        } catch {
            Write-Log "❌ Redis connection error: $_" "ERROR"
        }
    } else {
        Test-ServiceEndpoint $endpoint.Url $endpoint.Name
    }
}

# Step 6: Continuous Monitoring
Write-Log "👀 Step 6: Starting continuous monitoring for $MonitorDuration seconds..." "INFO"

$startTime = Get-Date
$endTime = $startTime.AddSeconds($MonitorDuration)
$lastCheck = Get-Date

while ((Get-Date) -lt $endTime) {
    Start-Sleep -Seconds 10
    
    # Check every 30 seconds
    if (((Get-Date) - $lastCheck).TotalSeconds -ge 30) {
        Write-Log "🔍 Health check at $(Get-Date -Format 'HH:mm:ss')..." "INFO"
        
        # Quick container status check
        foreach ($container in $containers) {
            $health = Get-ContainerHealth $container
            if (!$health.Running) {
                Write-Log "⚠️  $container is no longer running!" "ERROR"
                Get-ContainerLogs $container 20
            }
        }
        
        # Check for new errors in logs
        foreach ($container in $containers) {
            try {
                $recentLogs = docker logs --since="30s" $container 2>&1
                if ($recentLogs) {
                    $errorLogs = $recentLogs | Where-Object { $_ -match "(error|failed|exception)" -and $_ -notmatch "(?i)(test|debug)" }
                    if ($errorLogs) {
                        Write-Log "🚨 New errors detected in $container`:" "ERROR"
                        $errorLogs | ForEach-Object { Write-Log "   $_" "ERROR" }
                    }
                }
            } catch {
                # Ignore errors from containers that might not exist
            }
        }
        
        $lastCheck = Get-Date
    }
}

# Step 7: Final Status Report
Write-Log "📋 Step 7: Final status report..." "INFO"

foreach ($container in $containers) {
    $health = Get-ContainerHealth $container
    $status = if ($health.Running) { "✅ RUNNING" } else { "❌ FAILED" }
    Write-Log "$container`: $status (Health: $($health.Health))" "REPORT"
}

# Final endpoint tests
Write-Log "🔍 Final endpoint tests..." "INFO"
foreach ($endpoint in $endpoints) {
    if ($endpoint.Url -notlike "*6379*") {
        Test-ServiceEndpoint $endpoint.Url $endpoint.Name 5
    }
}

Write-Log "✅ Docker restart and monitoring completed!" "INFO"
Write-Log "📁 Full log saved to: $logFile" "INFO"

# Return exit code based on container health
$failedContainers = 0
foreach ($container in $containers) {
    $health = Get-ContainerHealth $container
    if (!$health.Running) {
        $failedContainers++
    }
}

if ($failedContainers -eq 0) {
    Write-Log "🎉 All containers are running successfully!" "SUCCESS"
    exit 0
} else {
    Write-Log "⚠️  $failedContainers container(s) failed to start properly" "WARN"
    exit $failedContainers
}
