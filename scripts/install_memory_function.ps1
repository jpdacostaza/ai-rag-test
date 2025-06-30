#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Install Memory Function into OpenWebUI
.DESCRIPTION
    This script installs the memory function into OpenWebUI by uploading the function code
    and configuring it properly.
.PARAMETER OpenWebUIUrl
    The URL where OpenWebUI is running (default: http://localhost:3000)
.PARAMETER ApiKey
    The API key for OpenWebUI admin access
#>

param(
    [string]$OpenWebUIUrl = "http://localhost:3000",
    [string]$ApiKey = ""
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

function Test-OpenWebUIConnection {
    param($Url)
    try {
        Invoke-RestMethod -Uri "$Url/api/v1/auths" -Method Get -TimeoutSec 10 | Out-Null
        return $true
    } catch {
        return $false
    }
}

Write-ColorOutput "🚀 OpenWebUI Memory Function Installer" $Cyan
Write-ColorOutput "====================================" $Cyan

# Check if OpenWebUI is accessible
Write-ColorOutput "`n🔍 Checking OpenWebUI connection..." $Blue
if (-not (Test-OpenWebUIConnection $OpenWebUIUrl)) {
    Write-ColorOutput "❌ Cannot connect to OpenWebUI at $OpenWebUIUrl" $Red
    Write-ColorOutput "   Please ensure OpenWebUI is running and accessible" $Yellow
    exit 1
}
Write-ColorOutput "✅ OpenWebUI is accessible" $Green

# Check if memory function file exists
$memoryFunctionPath = "memory_function.py"
if (-not (Test-Path $memoryFunctionPath)) {
    Write-ColorOutput "❌ Memory function file not found: $memoryFunctionPath" $Red
    Write-ColorOutput "   Please run this script from the backend directory" $Yellow
    exit 1
}

# Read the memory function code
Write-ColorOutput "`n📖 Reading memory function code..." $Blue
$functionCode = Get-Content $memoryFunctionPath -Raw

# Create function payload for OpenWebUI
$functionPayload = @{
    id = "memory_function"
    name = "Enhanced Memory Function"
    type = "function"
    content = $functionCode
    is_active = $true
    is_global = $true
} | ConvertTo-Json -Depth 10

Write-ColorOutput "✅ Function payload prepared" $Green

# Install function into OpenWebUI
Write-ColorOutput "`n🔧 Installing memory function..." $Blue

try {
    # Check if function already exists
    $existingFunctions = Invoke-RestMethod -Uri "$OpenWebUIUrl/api/v1/functions/" -Method Get -TimeoutSec 10
    $existingFunction = $existingFunctions | Where-Object { $_.id -eq "memory_function" }
    
    if ($existingFunction) {
        Write-ColorOutput "⚠️  Memory function already exists. Updating..." $Yellow
        $method = "PUT"
        $endpoint = "$OpenWebUIUrl/api/v1/functions/memory_function"
    } else {
        Write-ColorOutput "📦 Installing new memory function..." $Blue
        $method = "POST"
        $endpoint = "$OpenWebUIUrl/api/v1/functions/"
    }
    
    # Upload the function
    $headers = @{
        "Content-Type" = "application/json"
    }
    
    if ($ApiKey) {
        $headers["Authorization"] = "Bearer $ApiKey"
    }
    
    $response = Invoke-RestMethod -Uri $endpoint -Method $method -Body $functionPayload -Headers $headers -TimeoutSec 30
    
    Write-ColorOutput "✅ Memory function installed successfully!" $Green
    Write-ColorOutput "   Function ID: $($response.id)" $Reset
    Write-ColorOutput "   Function Name: $($response.name)" $Reset
    Write-ColorOutput "   Status: Active" $Reset
    
} catch {
    Write-ColorOutput "❌ Failed to install memory function" $Red
    Write-ColorOutput "   Error: $($_.Exception.Message)" $Yellow
    
    if ($_.Exception.Message -match "401|403") {
        Write-ColorOutput "   💡 Try providing an API key with -ApiKey parameter" $Cyan
        Write-ColorOutput "   💡 Or ensure you're logged in as admin in OpenWebUI" $Cyan
    }
    exit 1
}

# Verify installation
Write-ColorOutput "`n🔍 Verifying installation..." $Blue
try {
    $functions = Invoke-RestMethod -Uri "$OpenWebUIUrl/api/v1/functions/" -Method Get -TimeoutSec 10
    $installedFunction = $functions | Where-Object { $_.id -eq "memory_function" }
    
    if ($installedFunction) {
        Write-ColorOutput "✅ Verification successful!" $Green
        Write-ColorOutput "   Memory function is now available in OpenWebUI" $Reset
        Write-ColorOutput "   You can find it in: Admin → Functions → memory_function" $Cyan
    } else {
        Write-ColorOutput "⚠️  Function installed but not found in verification" $Yellow
    }
} catch {
    Write-ColorOutput "⚠️  Could not verify installation: $($_.Exception.Message)" $Yellow
}

Write-ColorOutput "`n🎉 Installation Complete!" $Green
Write-ColorOutput "========================================" $Cyan
Write-ColorOutput "Next steps:" $Blue
Write-ColorOutput "1. Go to OpenWebUI Admin → Functions" $Reset
Write-ColorOutput "2. Find 'Enhanced Memory Function'" $Reset
Write-ColorOutput "3. Configure the function settings if needed" $Reset
Write-ColorOutput "4. Test the function in a conversation" $Reset
Write-ColorOutput "`n💡 The function will automatically connect to your memory API" $Cyan
Write-ColorOutput "   at http://memory_api:8000 (or configured endpoint)" $Reset
