#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Install Enhanced Memory Function in OpenWebUI
.DESCRIPTION
    This script installs the enhanced memory function into OpenWebUI manually
#>

param(
    [string]$OpenWebUIUrl = "http://localhost:8080",
    [switch]$Force = $false
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param($Message, $Color = $Reset)
    Write-Host "${Color}${Message}${Reset}"
}

Write-ColorOutput "🔧 Enhanced Memory Function Installer" $Cyan
Write-ColorOutput "=====================================" $Cyan

# Check if OpenWebUI is accessible
Write-ColorOutput "`n🔍 Checking OpenWebUI accessibility..." $Blue
try {
    $response = Invoke-RestMethod -Uri "$OpenWebUIUrl/health" -Method Get -TimeoutSec 10
    Write-ColorOutput "✅ OpenWebUI is accessible" $Green
} catch {
    Write-ColorOutput "❌ OpenWebUI is not accessible at $OpenWebUIUrl" $Red
    Write-ColorOutput "💡 Make sure OpenWebUI is running: docker-compose up -d openwebui" $Yellow
    exit 1
}

# Load the memory function
Write-ColorOutput "`n📖 Loading memory function code..." $Blue
$functionPath = "memory_function.py"
if (-not (Test-Path $functionPath)) {
    Write-ColorOutput "❌ Memory function file not found: $functionPath" $Red
    exit 1
}

$functionCode = Get-Content -Path $functionPath -Raw -Encoding UTF8

# Prepare function data
$functionData = @{
    id = "enhanced_memory_function"
    name = "Enhanced Memory Function"
    type = "filter"
    content = $functionCode
    meta = @{
        description = "Stores and retrieves conversation context using the backend memory API"
        author = "AI Backend System"
        version = "2.0.0"
    }
} | ConvertTo-Json -Depth 10

# Install function
Write-ColorOutput "`n🚀 Installing function in OpenWebUI..." $Blue
try {
    # Try primary endpoint
    $headers = @{
        "Content-Type" = "application/json"
    }
    
    $response = Invoke-RestMethod -Uri "$OpenWebUIUrl/api/v1/functions/" -Method Post -Body $functionData -Headers $headers -TimeoutSec 30
    Write-ColorOutput "✅ Memory function installed successfully!" $Green
    
} catch {
    Write-ColorOutput "⚠️  Primary endpoint failed, trying alternative..." $Yellow
    
    try {
        # Try import endpoint
        $response = Invoke-RestMethod -Uri "$OpenWebUIUrl/api/v1/functions/import" -Method Post -Body $functionData -Headers $headers -TimeoutSec 30
        Write-ColorOutput "✅ Memory function installed via import endpoint!" $Green
        
    } catch {
        Write-ColorOutput "❌ Failed to install function: $($_.Exception.Message)" $Red
        Write-ColorOutput "💡 You may need to install the function manually through the OpenWebUI interface" $Yellow
        exit 1
    }
}

Write-ColorOutput "`n🎉 Installation completed successfully!" $Green
Write-ColorOutput "============================================" $Cyan
Write-ColorOutput "📋 Next Steps:" $Blue
Write-ColorOutput "1. Open $OpenWebUIUrl in your browser" $Reset
Write-ColorOutput "2. Go to Admin → Functions" $Reset
Write-ColorOutput "3. Find 'Enhanced Memory Function'" $Reset
Write-ColorOutput "4. Configure the valves (API URLs, etc.)" $Reset
Write-ColorOutput "5. Enable the function for your models" $Reset
Write-ColorOutput "`n💡 The enhanced memory system is now ready!" $Cyan
