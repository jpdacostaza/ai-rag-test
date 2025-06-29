#!/usr/bin/env pwsh
<#
.SYNOPSIS
Simple Memory System Test

.DESCRIPTION
Quick tests for the memory system functionality
#>

Write-Host "🧪 Simple Memory System Test" -ForegroundColor Cyan

$memoryApiUrl = "http://localhost:8000"
$testUserId = "simple_test_user"

# Test 1: Store a simple memory
Write-Host "`n1️⃣ Testing Memory Storage..." -ForegroundColor Yellow

$storeBody = @{
    user_id = $testUserId
    conversation_id = "test_conversation"
    user_message = "My name is Alex and I'm a software developer who loves coffee"
    assistant_response = "Nice to meet you Alex! I'll remember that you're a software developer who loves coffee."
    response_time = 1.0
    context = @{ source = "simple_test" }
    source = "test"
} | ConvertTo-Json -Depth 3

try {
    $response = Invoke-RestMethod -Uri "$memoryApiUrl/api/learning/process_interaction" -Method POST -Body $storeBody -ContentType "application/json"
    Write-Host "✅ Memory stored successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to store memory: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Wait for processing
Start-Sleep -Seconds 2

# Test 2: Retrieve the memory
Write-Host "`n2️⃣ Testing Memory Retrieval..." -ForegroundColor Yellow

$retrieveBody = @{
    user_id = $testUserId
    query = "Alex software developer"
    limit = 5
    threshold = 0.1
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$memoryApiUrl/api/memory/retrieve" -Method POST -Body $retrieveBody -ContentType "application/json"
    
    if ($response.count -gt 0) {
        Write-Host "✅ Found $($response.count) memories:" -ForegroundColor Green
        foreach ($memory in $response.memories) {
            Write-Host "  - $($memory.content)" -ForegroundColor White
        }
    } else {
        Write-Host "⚠️  No memories found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Failed to retrieve memory: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Test fallback retrieval (empty query)
Write-Host "`n3️⃣ Testing Fallback Retrieval..." -ForegroundColor Yellow

$fallbackBody = @{
    user_id = $testUserId
    query = ""
    limit = 5
    threshold = 0.0
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$memoryApiUrl/api/memory/retrieve" -Method POST -Body $fallbackBody -ContentType "application/json"
    
    if ($response.count -gt 0) {
        Write-Host "✅ Fallback found $($response.count) memories:" -ForegroundColor Green
        foreach ($memory in $response.memories) {
            Write-Host "  - $($memory.content)" -ForegroundColor White
        }
    } else {
        Write-Host "⚠️  No memories found in fallback" -ForegroundColor Yellow
    }
    
    $totalMemories = $response.sources.short_term + $response.sources.long_term
    Write-Host "📊 Total memories in system: $totalMemories" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Failed fallback retrieval: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Check filter function exists
Write-Host "`n4️⃣ Testing Filter Function..." -ForegroundColor Yellow

try {
    $functions = Invoke-RestMethod -Uri "http://localhost:3000/api/v1/functions/" -Method GET -TimeoutSec 5
    $memoryFilter = $functions | Where-Object { $_.id -eq "memory_filter" }
    
    if ($memoryFilter) {
        Write-Host "✅ Memory filter found in OpenWebUI" -ForegroundColor Green
        Write-Host "  Name: $($memoryFilter.name)" -ForegroundColor White
        Write-Host "  Type: $($memoryFilter.type)" -ForegroundColor White
    } else {
        Write-Host "❌ Memory filter not found in OpenWebUI" -ForegroundColor Red
    }
} catch {
    Write-Host "⚠️  Could not check OpenWebUI functions: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`n✨ Test Complete!" -ForegroundColor Green
Write-Host "If all tests passed, your memory system is working!" -ForegroundColor Cyan
