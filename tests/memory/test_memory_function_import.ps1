#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test memory filter function import and functionality
.DESCRIPTION
    This script tests if the memory function was imported correctly
#>

param(
    [string]$OpenWebUIUrl = "http://localhost:3000"
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param($Message, $Color = $Reset)
    Write-Host "${Color}${Message}${Reset}"
}

Write-ColorOutput "🔍 Testing Memory Function Import..." $Green

try {
    # Test if the function endpoint exists
    Write-ColorOutput "📡 Checking functions endpoint..." $Blue
    $functions = Invoke-RestMethod -Uri "$OpenWebUIUrl/api/v1/functions" -Method Get -TimeoutSec 10
    
    if ($functions) {
        Write-ColorOutput "✅ Functions endpoint accessible" $Green
        
        # Look for memory filter function
        $memoryFunction = $functions | Where-Object { $_.id -eq "memory_filter" }
        
        if ($memoryFunction) {
            Write-ColorOutput "✅ Memory Filter function found!" $Green
            Write-ColorOutput "Function Details:" $Blue
            Write-ColorOutput "  ID: $($memoryFunction.id)" $Reset
            Write-ColorOutput "  Name: $($memoryFunction.name)" $Reset
            Write-ColorOutput "  Type: $($memoryFunction.type)" $Reset
            Write-ColorOutput "  Active: $($memoryFunction.is_active)" $Reset
            Write-ColorOutput "  Global: $($memoryFunction.is_global)" $Reset
            
            if ($memoryFunction.is_active) {
                Write-ColorOutput "✅ Function is enabled" $Green
            } else {
                Write-ColorOutput "⚠️ Function is disabled - enable it in Admin → Functions" $Yellow
            }
        } else {
            Write-ColorOutput "❌ Memory Filter function not found" $Red
            Write-ColorOutput "Available functions:" $Blue
            $functions | ForEach-Object { 
                Write-ColorOutput "  - $($_.name) ($($_.id))" $Reset 
            }
        }
    } else {
        Write-ColorOutput "❌ No functions found" $Red
    }
}
catch {
    Write-ColorOutput "❌ Error testing functions: $($_.Exception.Message)" $Red
    Write-ColorOutput "Make sure OpenWebUI is running at $OpenWebUIUrl" $Yellow
}

# Test memory API connectivity
Write-ColorOutput "🧠 Testing Memory API connectivity..." $Blue
try {
    $memoryHealth = Invoke-RestMethod -Uri "http://localhost:8003/health" -Method Get -TimeoutSec 5
    if ($memoryHealth) {
        Write-ColorOutput "✅ Memory API is accessible" $Green
    }
}
catch {
    Write-ColorOutput "⚠️ Memory API not accessible (this is OK if using Docker internal networking)" $Yellow
}

Write-ColorOutput "🎯 Test completed!" $Green
