#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Import memory filter function into OpenWebUI using the correct API endpoint
#>

$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImIwNmQ0YWYzLWY4MGUtNGQxZC1hY2JjLTE4Yjc3ODVmY2NiYiJ9.ecE0CkTMrtrrxEk4viPlo4ZnuvCWbVTJwhLAkFVKRL4"
$baseUrl = "http://localhost:3000"

Write-Host "🔍 Testing OpenWebUI API endpoints..." -ForegroundColor Blue

# Test different API endpoints to find the correct one
$endpoints = @(
    "/api/v1/functions",
    "/api/functions", 
    "/functions",
    "/api/v1/functions/create"
)

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

foreach ($endpoint in $endpoints) {
    try {
        Write-Host "Testing: $baseUrl$endpoint" -ForegroundColor Yellow
        $response = Invoke-RestMethod -Uri "$baseUrl$endpoint" -Method Get -Headers $headers -TimeoutSec 10
        Write-Host "✅ SUCCESS: $endpoint" -ForegroundColor Green
        Write-Host "Response type: $($response.GetType().Name)" -ForegroundColor Cyan
        
        if ($response -is [Array]) {
            Write-Host "Found $($response.Count) functions" -ForegroundColor Cyan
        } elseif ($response -is [PSCustomObject]) {
            Write-Host "Response keys: $($response.PSObject.Properties.Name -join ', ')" -ForegroundColor Cyan
        }
        break
    }
    catch {
        Write-Host "❌ FAILED: $endpoint - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Now let's try to create the function
Write-Host "`n📦 Reading memory filter function..." -ForegroundColor Blue
$functionCode = Get-Content "memory_filter_function.py" -Raw

if ($functionCode) {
    Write-Host "✅ Function code loaded ($($functionCode.Length) characters)" -ForegroundColor Green
    
    # Create function data
    $functionData = @{
        id = "memory_filter"
        name = "Memory Filter"
        type = "filter"
        content = $functionCode
        meta = @{
            description = "Memory filter function that adds context from previous conversations"
            manifest = @{}
        }
        is_active = $true
        is_global = $false
    }
    
    $jsonData = $functionData | ConvertTo-Json -Depth 10
    
    # Try to create the function
    Write-Host "`n🚀 Attempting to create function..." -ForegroundColor Blue
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/functions/create" -Method Post -Body $jsonData -Headers $headers -TimeoutSec 60
        Write-Host "✅ Successfully created memory filter function!" -ForegroundColor Green
        Write-Host "Function ID: $($response.id)" -ForegroundColor Cyan
        $response | ConvertTo-Json -Depth 3
    }
    catch {
        Write-Host "❌ Function creation failed: $($_.Exception.Message)" -ForegroundColor Red
        
        # Try alternative endpoint
        try {
            Write-Host "🔄 Trying alternative endpoint..." -ForegroundColor Yellow
            $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/functions" -Method Post -Body $jsonData -Headers $headers -TimeoutSec 60
            Write-Host "✅ Successfully created memory filter function!" -ForegroundColor Green
            $response | ConvertTo-Json -Depth 3
        }
        catch {
            Write-Host "❌ Alternative endpoint also failed: $($_.Exception.Message)" -ForegroundColor Red
            
            if ($_.Exception.Response) {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $responseBody = $reader.ReadToEnd()
                Write-Host "Response body: $responseBody" -ForegroundColor Red
            }
        }
    }
}
else {
    Write-Host "❌ Could not read function code from memory_filter_function.py" -ForegroundColor Red
}
