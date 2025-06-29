#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Update Memory Filter with lower threshold
#>

param(
    [string]$OpenWebUIUrl = "http://localhost:3000",
    [string]$Token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImIwNmQ0YWYzLWY4MGUtNGQxZC1hY2JjLTE4Yjc3ODVmY2NiYiJ9.ecE0CkTMrtrrxEk4viPlo4ZnuvCWbVTJwhLAkFVKRL4",
    [string]$FunctionFile = "memory_filter_function.py"
)

# Colors
$Green = "`e[32m"
$Blue = "`e[34m"
$Red = "`e[31m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param($Message, $Color = $Reset)
    Write-Host "${Color}${Message}${Reset}"
}

Write-ColorOutput "🔧 Updating Memory Filter Function..." $Green

# Read updated function code
$functionCode = Get-Content $FunctionFile -Raw

# Update the function
$functionData = @{
    id = "memory_filter"
    name = "Memory Filter"
    type = "filter"
    content = $functionCode
    meta = @{
        description = "Memory filter function that adds context from previous conversations (Updated with lower threshold)"
        manifest = @{}
    }
    is_active = $true
    is_global = $true
} | ConvertTo-Json -Depth 10

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

try {
    Write-ColorOutput "📦 Updating function..." $Blue
    $response = Invoke-RestMethod -Uri "$OpenWebUIUrl/api/v1/functions/id/memory_filter/update" -Method Post -Body $functionData -Headers $headers -TimeoutSec 60
    
    if ($response) {
        Write-ColorOutput "✅ Memory Filter updated successfully!" $Green
        Write-ColorOutput "New threshold: 0.3 (was 0.7)" $Blue
    } else {
        Write-ColorOutput "❌ Update failed - no response" $Red
    }
} catch {
    Write-ColorOutput "❌ Update failed: $($_.Exception.Message)" $Red
    Write-ColorOutput "Trying to create new function instead..." $Blue
    
    try {
        $response = Invoke-RestMethod -Uri "$OpenWebUIUrl/api/v1/functions/create" -Method Post -Body $functionData -Headers $headers -TimeoutSec 60
        Write-ColorOutput "✅ Function re-created successfully!" $Green
    } catch {
        Write-ColorOutput "❌ Re-create also failed: $($_.Exception.Message)" $Red
    }
}

Write-ColorOutput "🎯 Please test the memory again now!" $Green
