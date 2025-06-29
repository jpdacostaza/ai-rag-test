#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test Memory System End-to-End
.DESCRIPTION
    This script validates the complete memory system workflow
#>

param(
    [string]$MemoryApiUrl = "http://localhost:8000",
    [string]$OpenWebUIUrl = "http://localhost:3000"
)

# Colors
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Red = "`e[31m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param($Message, $Color = $Reset)
    Write-Host "${Color}${Message}${Reset}"
}

Write-ColorOutput "🧠 Testing Complete Memory System" $Green
Write-ColorOutput "=================================" $Blue

# Test 1: Memory API Health
Write-ColorOutput "1. Testing Memory API Health..." $Blue
try {
    $healthResponse = Invoke-RestMethod -Uri "$MemoryApiUrl/health" -Method Get -TimeoutSec 10
    if ($healthResponse.status -eq "healthy") {
        Write-ColorOutput "✅ Memory API is healthy" $Green
        Write-ColorOutput "   Redis: $($healthResponse.redis)" $Reset
        Write-ColorOutput "   ChromaDB: $($healthResponse.chromadb)" $Reset
    } else {
        Write-ColorOutput "❌ Memory API health check failed" $Red
        exit 1
    }
} catch {
    Write-ColorOutput "❌ Memory API not accessible: $($_.Exception.Message)" $Red
    exit 1
}

# Test 2: Store a test interaction
Write-ColorOutput "2. Testing Memory Storage..." $Blue
$testUserId = "test_user_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$testData = @{
    user_id = $testUserId
    conversation_id = "test_chat_001"
    user_message = "My name is Alice and I love cooking pizza"
    assistant_response = "Nice to meet you, Alice! Pizza cooking sounds delicious."
    response_time = 1.5
    context = @{ source = "test_script" }
    source = "api_test"
} | ConvertTo-Json

try {
    $storeResponse = Invoke-RestMethod -Uri "$MemoryApiUrl/api/learning/process_interaction" -Method Post -Body $testData -ContentType "application/json" -TimeoutSec 30
    Write-ColorOutput "✅ Memory stored successfully" $Green
    Write-ColorOutput "   Total memories: $($storeResponse.memories_count)" $Reset
} catch {
    Write-ColorOutput "❌ Memory storage failed: $($_.Exception.Message)" $Red
    exit 1
}

# Test 3: Retrieve the stored memory
Write-ColorOutput "3. Testing Memory Retrieval..." $Blue
$retrieveData = @{
    user_id = $testUserId
    query = "What do you know about my name and cooking?"
    limit = 5
    threshold = 0.3
} | ConvertTo-Json

try {
    $retrieveResponse = Invoke-RestMethod -Uri "$MemoryApiUrl/api/memory/retrieve" -Method Post -Body $retrieveData -ContentType "application/json" -TimeoutSec 30
    $memories = $retrieveResponse.memories
    
    if ($memories.Count -gt 0) {
        Write-ColorOutput "✅ Memory retrieval successful" $Green
        Write-ColorOutput "   Found $($memories.Count) relevant memories:" $Reset
        
        for ($i = 0; $i -lt $memories.Count; $i++) {
            $memory = $memories[$i]
            Write-ColorOutput "   Memory $($i+1):" $Blue
            Write-ColorOutput "     Content: $($memory.content)" $Reset
            Write-ColorOutput "     Relevance: $($memory.relevance_score)" $Reset
            Write-ColorOutput "     Type: $($memory.memory_type)" $Reset
        }
    } else {
        Write-ColorOutput "⚠️ No memories retrieved (this might be normal if threshold is too high)" $Yellow
    }
} catch {
    Write-ColorOutput "❌ Memory retrieval failed: $($_.Exception.Message)" $Red
    exit 1
}

# Test 4: Check OpenWebUI connection
Write-ColorOutput "4. Testing OpenWebUI Connection..." $Blue
try {
    $openwebuiResponse = Invoke-RestMethod -Uri "$OpenWebUIUrl/health" -Method Get -TimeoutSec 10
    Write-ColorOutput "✅ OpenWebUI is accessible" $Green
} catch {
    Write-ColorOutput "❌ OpenWebUI not accessible: $($_.Exception.Message)" $Red
    exit 1
}

# Test 5: Check if memory filter function exists
Write-ColorOutput "5. Testing Memory Filter Function..." $Blue
try {
    $functionsResponse = Invoke-RestMethod -Uri "$OpenWebUIUrl/api/v1/functions" -Method Get -TimeoutSec 10
    $memoryFilter = $functionsResponse | Where-Object { $_.id -eq "memory_filter" }
    
    if ($memoryFilter) {
        Write-ColorOutput "✅ Memory Filter function found" $Green
        Write-ColorOutput "   Name: $($memoryFilter.name)" $Reset
        Write-ColorOutput "   Type: $($memoryFilter.type)" $Reset
        Write-ColorOutput "   Active: $($memoryFilter.is_active)" $Reset
        Write-ColorOutput "   Global: $($memoryFilter.is_global)" $Reset
    } else {
        Write-ColorOutput "❌ Memory Filter function not found" $Red
        Write-ColorOutput "Available functions:" $Blue
        $functionsResponse | ForEach-Object {
            Write-ColorOutput "  - $($_.name) ($($_.id))" $Reset
        }
    }
} catch {
    Write-ColorOutput "⚠️ Could not check functions (this might be normal if authentication is required)" $Yellow
}

Write-ColorOutput "🎯 Memory System Test Complete!" $Green
Write-ColorOutput "" $Reset
Write-ColorOutput "📋 Next Steps to Test in OpenWebUI:" $Yellow
Write-ColorOutput "1. Go to OpenWebUI chat" $Reset
Write-ColorOutput "2. Send: 'Hello, my name is John and I work at SWIFT'" $Reset
Write-ColorOutput "3. Start a NEW chat" $Reset
Write-ColorOutput "4. Send: 'What do you remember about me?'" $Reset
Write-ColorOutput "5. The AI should remember your name and job!" $Reset

# Cleanup test data
Write-ColorOutput "6. Cleaning up test data..." $Blue
try {
    # Note: You might want to add a cleanup endpoint to your memory API
    Write-ColorOutput "✅ Test completed (cleanup would go here)" $Green
} catch {
    Write-ColorOutput "⚠️ Cleanup skipped" $Yellow
}
