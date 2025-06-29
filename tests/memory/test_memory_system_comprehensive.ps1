#!/usr/bin/env pwsh
<#
.SYNOPSIS
Comprehensive Memory System Test Suite

.DESCRIPTION
Tests all aspects of the OpenWebUI memory system:
- Memory storage and retrieval
- Cross-chat persistence
- User isolation
- Semantic search
- Filter integration
- API endpoints
#>

Write-Host "🧠 Starting Comprehensive Memory System Tests..." -ForegroundColor Cyan
Write-Host "=" * 60

# Test Configuration
$memoryApiUrl = "http://localhost:8000"
$openWebUIUrl = "http://localhost:3000"
$testUserId = "test_user_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Test Results
$testResults = @()

function Test-Result {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Details = ""
    )
    
    $result = @{
        Test = $TestName
        Passed = $Passed
        Details = $Details
        Timestamp = Get-Date
    }
    
    $script:testResults += $result
    
    if ($Passed) {
        Write-Host "✅ $TestName" -ForegroundColor Green
    } else {
        Write-Host "❌ $TestName" -ForegroundColor Red
    }
    
    if ($Details) {
        Write-Host "   $Details" -ForegroundColor Gray
    }
}

# Test 1: Memory API Health Check
Write-Host "`n📡 Testing Memory API Health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$memoryApiUrl/health" -Method GET -TimeoutSec 5
    Test-Result "Memory API Health Check" $true "Status: $($response.status)"
} catch {
    Test-Result "Memory API Health Check" $false "Error: $($_.Exception.Message)"
}

# Test 2: Memory Storage
Write-Host "`n💾 Testing Memory Storage..." -ForegroundColor Yellow
$storageTests = @(
    @{ name = "Alice"; info = "likes programming and Python"; context = "work discussion" },
    @{ name = "Bob"; info = "works at Microsoft as a PM"; context = "networking event" },
    @{ name = "Carol"; info = "expert in machine learning"; context = "conference talk" }
)

foreach ($test in $storageTests) {
    try {
        $conversationId = "test_conv_$([guid]::NewGuid().ToString('N')[0..7] -join '')"
        $body = @{
            user_id = $testUserId
            conversation_id = $conversationId
            user_message = "Hi, my name is $($test.name). I $($test.info)."
            assistant_response = "Nice to meet you $($test.name)! I'll remember that you $($test.info)."
            response_time = 1.0
            context = @{ source = "test"; scenario = $test.context }
            source = "test"
        } | ConvertTo-Json -Depth 3
        
        $response = Invoke-RestMethod -Uri "$memoryApiUrl/api/learning/process_interaction" -Method POST -Body $body -ContentType "application/json"
        Test-Result "Store Memory: $($test.name)" $true "Stored successfully"
    } catch {
        Test-Result "Store Memory: $($test.name)" $false "Error: $($_.Exception.Message)"
    }
}

# Test 3: Memory Retrieval by Query
Write-Host "`n🔍 Testing Memory Retrieval..." -ForegroundColor Yellow
$retrievalTests = @(
    @{ query = "programming"; expectedMatch = "Alice" },
    @{ query = "Microsoft"; expectedMatch = "Bob" },
    @{ query = "machine learning"; expectedMatch = "Carol" },
    @{ query = "Python"; expectedMatch = "Alice" }
)

foreach ($test in $retrievalTests) {
    try {
        $body = @{
            user_id = $testUserId
            query = $test.query
            limit = 5
            threshold = 0.1
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$memoryApiUrl/api/memory/retrieve" -Method POST -Body $body -ContentType "application/json"
        
        $found = $false
        foreach ($memory in $response.memories) {
            if ($memory.content -like "*$($test.expectedMatch)*") {
                $found = $true
                break
            }
        }
        
        Test-Result "Retrieve Memory: $($test.query)" $found "Found $($response.count) memories, expected match: $($test.expectedMatch)"
    } catch {
        Test-Result "Retrieve Memory: $($test.query)" $false "Error: $($_.Exception.Message)"
    }
}

# Test 4: User Isolation
Write-Host "`n👥 Testing User Isolation..." -ForegroundColor Yellow
$user1 = "user1_test"
$user2 = "user2_test"

# Store memory for user1
try {
    $body1 = @{
        user_id = $user1
        conversation_id = "test_isolation_1"
        user_message = "My secret is that I love cats"
        assistant_response = "I'll remember your love for cats!"
        response_time = 1.0
        context = @{ source = "isolation_test" }
        source = "test"
    } | ConvertTo-Json -Depth 3
    
    Invoke-RestMethod -Uri "$memoryApiUrl/api/learning/process_interaction" -Method POST -Body $body1 -ContentType "application/json" | Out-Null
    
    # Try to retrieve user1's memory as user2
    $body2 = @{
        user_id = $user2
        query = "cats"
        limit = 5
        threshold = 0.1
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$memoryApiUrl/api/memory/retrieve" -Method POST -Body $body2 -ContentType "application/json"
    
    $isolated = $response.count -eq 0
    Test-Result "User Memory Isolation" $isolated "User2 found $($response.count) memories from User1 (should be 0)"
} catch {
    Test-Result "User Memory Isolation" $false "Error: $($_.Exception.Message)"
}

# Test 5: Semantic Search Quality
Write-Host "`n🎯 Testing Semantic Search Quality..." -ForegroundColor Yellow
$semanticTests = @(
    @{ store = "I am a software engineer working on AI systems"; query = "developer"; shouldMatch = $true },
    @{ store = "I enjoy hiking and outdoor activities"; query = "nature"; shouldMatch = $true },
    @{ store = "I have a PhD in computer science"; query = "education"; shouldMatch = $true }
)

foreach ($i, $test in [System.Linq.Enumerable]::Select($semanticTests, [Func[object,int,object]]{param($x,$idx) @{Index=$idx; Data=$x}})) {
    try {
        $semanticUserId = "semantic_test_$i"
        
        # Store the memory
        $storeBody = @{
            user_id = $semanticUserId
            conversation_id = "semantic_test_$i"
            user_message = $test.Data.store
            assistant_response = "I understand."
            response_time = 1.0
            context = @{ source = "semantic_test" }
            source = "test"
        } | ConvertTo-Json -Depth 3
        
        Invoke-RestMethod -Uri "$memoryApiUrl/api/learning/process_interaction" -Method POST -Body $storeBody -ContentType "application/json" | Out-Null
        
        # Wait a moment for processing
        Start-Sleep -Seconds 1
        
        # Retrieve with semantic query
        $retrieveBody = @{
            user_id = $semanticUserId
            query = $test.Data.query
            limit = 5
            threshold = 0.2
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$memoryApiUrl/api/memory/retrieve" -Method POST -Body $retrieveBody -ContentType "application/json"
        
        $found = $response.count -gt 0
        $passed = $test.Data.shouldMatch ? $found : !$found
        
        Test-Result "Semantic Search: $($test.Data.query)" $passed "Query '$($test.Data.query)' found $($response.count) results"
    } catch {
        Test-Result "Semantic Search: $($test.Data.query)" $false "Error: $($_.Exception.Message)"
    }
}

# Test 6: Memory Filter Integration
Write-Host "`n🔧 Testing Memory Filter Integration..." -ForegroundColor Yellow
try {
    # Check if OpenWebUI is accessible
    $openWebUIResponse = Invoke-WebRequest -Uri "$openWebUIUrl/api/config" -Method GET -TimeoutSec 5
    Test-Result "OpenWebUI Accessibility" $true "OpenWebUI is accessible"
    
    # Check if memory filter is loaded
    try {
        $functionsResponse = Invoke-RestMethod -Uri "$openWebUIUrl/api/v1/functions/" -Method GET -TimeoutSec 5
        $memoryFilterExists = $functionsResponse | Where-Object { $_.id -eq "memory_filter" }
        Test-Result "Memory Filter Installation" ($memoryFilterExists -ne $null) "Memory filter found in functions list"
    } catch {
        Test-Result "Memory Filter Installation" $false "Could not check functions: $($_.Exception.Message)"
    }
    
} catch {
    Test-Result "OpenWebUI Accessibility" $false "Error: $($_.Exception.Message)"
}

# Test 7: Cross-Chat Memory Persistence
Write-Host "`n🔄 Testing Cross-Chat Memory Persistence..." -ForegroundColor Yellow
$persistenceUserId = "persistence_test_user"

try {
    # Store memory in "chat 1"
    $chat1Body = @{
        user_id = $persistenceUserId
        conversation_id = "chat_1_persistence"
        user_message = "Remember that my favorite color is blue"
        assistant_response = "I'll remember that blue is your favorite color!"
        response_time = 1.0
        context = @{ chat_id = "chat_1" }
        source = "test"
    } | ConvertTo-Json -Depth 3
    
    Invoke-RestMethod -Uri "$memoryApiUrl/api/learning/process_interaction" -Method POST -Body $chat1Body -ContentType "application/json" | Out-Null
    
    # Retrieve memory in "chat 2"
    $retrieveBody = @{
        user_id = $persistenceUserId
        query = "favorite color"
        limit = 5
        threshold = 0.2
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$memoryApiUrl/api/memory/retrieve" -Method POST -Body $retrieveBody -ContentType "application/json"
    
    $found = $false
    foreach ($memory in $response.memories) {
        if ($memory.content -like "*blue*") {
            $found = $true
            break
        }
    }
    
    Test-Result "Cross-Chat Memory Persistence" $found "Memory from chat 1 accessible in chat 2"
} catch {
    Test-Result "Cross-Chat Memory Persistence" $false "Error: $($_.Exception.Message)"
}

# Test 8: Memory System Performance
Write-Host "`n⚡ Testing Memory System Performance..." -ForegroundColor Yellow
try {
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    # Test storage performance
    $storageTime = Measure-Command {
        $body = @{
            user_id = "perf_test_user"
            conversation_id = "perf_test_conv"
            user_message = "This is a performance test message"
            assistant_response = "Performance test response"
            response_time = 1.0
            context = @{ source = "performance_test" }
            source = "test"
        } | ConvertTo-Json -Depth 3
        
        Invoke-RestMethod -Uri "$memoryApiUrl/api/learning/process_interaction" -Method POST -Body $body -ContentType "application/json" | Out-Null
    }
    
    # Test retrieval performance
    $retrievalTime = Measure-Command {
        $body = @{
            user_id = "perf_test_user"
            query = "performance"
            limit = 5
            threshold = 0.2
        } | ConvertTo-Json
        
        Invoke-RestMethod -Uri "$memoryApiUrl/api/memory/retrieve" -Method POST -Body $body -ContentType "application/json" | Out-Null
    }
    
    $storageMs = [math]::Round($storageTime.TotalMilliseconds, 2)
    $retrievalMs = [math]::Round($retrievalTime.TotalMilliseconds, 2)
    
    $performanceGood = $storageMs -lt 2000 -and $retrievalMs -lt 2000
    Test-Result "Memory System Performance" $performanceGood "Storage: ${storageMs}ms, Retrieval: ${retrievalMs}ms"
    
} catch {
    Test-Result "Memory System Performance" $false "Error: $($_.Exception.Message)"
}

# Test Summary
Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "🎯 Test Results Summary" -ForegroundColor Cyan
Write-Host "=" * 60

$passed = ($testResults | Where-Object { $_.Passed }).Count
$total = $testResults.Count
$passRate = [math]::Round(($passed / $total) * 100, 1)

Write-Host "Total Tests: $total"
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $($total - $passed)" -ForegroundColor Red
Write-Host "Pass Rate: $passRate%" -ForegroundColor $(if($passRate -ge 80) { "Green" } else { "Yellow" })

Write-Host "`n📊 Detailed Results:" -ForegroundColor Cyan
foreach ($result in $testResults) {
    $status = if ($result.Passed) { "✅" } else { "❌" }
    $color = if ($result.Passed) { "Green" } else { "Red" }
    Write-Host "$status $($result.Test)" -ForegroundColor $color
    if ($result.Details) {
        Write-Host "   $($result.Details)" -ForegroundColor Gray
    }
}

if ($passRate -ge 80) {
    Write-Host "`n🎉 Memory System is working well!" -ForegroundColor Green
} elseif ($passRate -ge 60) {
    Write-Host "`n⚠️  Memory System has some issues that need attention." -ForegroundColor Yellow
} else {
    Write-Host "`n🚨 Memory System needs significant fixes." -ForegroundColor Red
}

Write-Host "`n🔧 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Review failed tests and fix issues"
Write-Host "2. Test memory system in actual chat scenarios"
Write-Host "3. Monitor performance under load"
Write-Host "4. Tune semantic search thresholds if needed"
Write-Host "5. Consider implementing memory cleanup/archiving"

Write-Host "`nTest completed at $(Get-Date)" -ForegroundColor Gray
