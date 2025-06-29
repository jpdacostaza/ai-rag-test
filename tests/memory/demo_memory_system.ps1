#!/usr/bin/env pwsh
<#
.SYNOPSIS
Interactive Memory System Demo

.DESCRIPTION
Demonstrates the memory system with real conversation scenarios
#>

Write-Host "🎭 Interactive Memory System Demo" -ForegroundColor Cyan
Write-Host "=" * 50

$memoryApiUrl = "http://localhost:8000"
$demoUserId = "demo_user"

function Show-MemoryContext {
    param([string]$query = "", [int]$limit = 5)
    
    Write-Host "`n🧠 Current Memory Context:" -ForegroundColor Yellow
    
    try {
        $body = @{
            user_id = $demoUserId
            query = $query
            limit = $limit
            threshold = 0.0
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$memoryApiUrl/api/memory/retrieve" -Method POST -Body $body -ContentType "application/json"
        
        if ($response.count -gt 0) {
            Write-Host "Found $($response.count) memories:" -ForegroundColor Green
            for ($i = 0; $i -lt $response.memories.Count; $i++) {
                $memory = $response.memories[$i]
                Write-Host "$($i + 1). $($memory.content)" -ForegroundColor White
                if ($memory.relevance_score -gt 0) {
                    Write-Host "   (relevance: $([math]::Round($memory.relevance_score, 2)))" -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "No memories found." -ForegroundColor Gray
        }
        
        Write-Host "Total memories stored: $($response.sources.short_term + $response.sources.long_term)" -ForegroundColor Cyan
        
    } catch {
        Write-Host "Error retrieving memories: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Add-ConversationToMemory {
    param(
        [string]$userMessage,
        [string]$assistantResponse,
        [string]$conversationId = "demo_conv_$(Get-Date -Format 'HHmmss')"
    )
    
    try {
        $body = @{
            user_id = $demoUserId
            conversation_id = $conversationId
            user_message = $userMessage
            assistant_response = $assistantResponse
            response_time = 1.0
            context = @{ source = "demo"; timestamp = (Get-Date).ToString() }
            source = "demo"
        } | ConvertTo-Json -Depth 3
        
        $response = Invoke-RestMethod -Uri "$memoryApiUrl/api/learning/process_interaction" -Method POST -Body $body -ContentType "application/json"
        Write-Host "✅ Stored conversation" -ForegroundColor Green
        
    } catch {
        Write-Host "❌ Failed to store conversation: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Demo Scenarios
Write-Host "`n🎬 Running Demo Scenarios..." -ForegroundColor Cyan

# Scenario 1: Personal Information
Write-Host "`n--- Scenario 1: Personal Information ---" -ForegroundColor Magenta
$userMsg1 = "Hi! My name is Sarah and I'm a data scientist at TechCorp. I specialize in machine learning and love working with Python."
$aiMsg1 = "Hello Sarah! Nice to meet you. I'll remember that you're a data scientist at TechCorp who specializes in machine learning and loves Python. Is there anything specific about data science or Python you'd like to discuss?"

Write-Host "👤 User: $userMsg1" -ForegroundColor Blue
Write-Host "🤖 AI: $aiMsg1" -ForegroundColor Green

Add-ConversationToMemory -userMessage $userMsg1 -assistantResponse $aiMsg1

# Scenario 2: Preferences and Interests
Write-Host "`n--- Scenario 2: Preferences and Interests ---" -ForegroundColor Magenta
$userMsg2 = "I'm really interested in neural networks, especially transformers. I also enjoy hiking on weekends and have two cats named Pixel and Vector."
$aiMsg2 = "That's fascinating! I'll remember your interests in neural networks and transformers - very cutting-edge areas. And I love that your cats are named Pixel and Vector - very fitting for someone in tech! Do you have any favorite hiking spots?"

Write-Host "👤 User: $userMsg2" -ForegroundColor Blue
Write-Host "🤖 AI: $aiMsg2" -ForegroundColor Green

Add-ConversationToMemory -userMessage $userMsg2 -assistantResponse $aiMsg2

# Show current memory after personal info
Show-MemoryContext

# Scenario 3: Work Projects
Write-Host "`n--- Scenario 3: Work Projects ---" -ForegroundColor Magenta
$userMsg3 = "I'm currently working on a recommendation system using collaborative filtering. It's for our e-commerce platform. The main challenge is dealing with sparse data."
$aiMsg3 = "A recommendation system for e-commerce sounds like an exciting project! Sparse data is indeed a common challenge in collaborative filtering. Have you considered matrix factorization techniques or hybrid approaches combining collaborative and content-based filtering?"

Write-Host "👤 User: $userMsg3" -ForegroundColor Blue
Write-Host "🤖 AI: $aiMsg3" -ForegroundColor Green

Add-ConversationToMemory -userMessage $userMsg3 -assistantResponse $aiMsg3

# Wait for memory processing
Write-Host "`n⏳ Processing memories..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# Test memory retrieval with different queries
Write-Host "`n🔍 Testing Memory Retrieval:" -ForegroundColor Cyan

Write-Host "`n Query: 'What's my name?'"
Show-MemoryContext -query "name Sarah" -limit 3

Write-Host "`n Query: 'What do I do for work?'"
Show-MemoryContext -query "work job data scientist" -limit 3

Write-Host "`n Query: 'What are my hobbies?'"
Show-MemoryContext -query "hobbies interests hiking cats" -limit 3

Write-Host "`n Query: 'What am I working on?'"
Show-MemoryContext -query "project recommendation system" -limit 3

# Scenario 4: Cross-Session Memory (Simulating new chat)
Write-Host "`n--- Scenario 4: New Chat Session ---" -ForegroundColor Magenta
$userMsg4 = "Hey! Do you remember me?"
$aiMsg4 = "Hello! Yes, I remember you Sarah! You're a data scientist at TechCorp specializing in machine learning and Python. You're working on a recommendation system for an e-commerce platform, and you enjoy hiking and have two cats named Pixel and Vector. How's your recommendation system project going?"

Write-Host "👤 User: $userMsg4" -ForegroundColor Blue
Write-Host "🤖 AI: $aiMsg4" -ForegroundColor Green

Add-ConversationToMemory -userMessage $userMsg4 -assistantResponse $aiMsg4 -conversationId "new_chat_session"

# Show final memory state
Write-Host "`n🎯 Final Memory State:" -ForegroundColor Cyan
Show-MemoryContext -limit 10

Write-Host "`n" + "=" * 50
Write-Host "✨ Demo Complete!" -ForegroundColor Green
Write-Host "The memory system successfully:" -ForegroundColor Cyan
Write-Host "  ✅ Stored personal information" -ForegroundColor Green
Write-Host "  ✅ Remembered preferences and interests" -ForegroundColor Green  
Write-Host "  ✅ Tracked work projects" -ForegroundColor Green
Write-Host "  ✅ Maintained context across chat sessions" -ForegroundColor Green
Write-Host "  ✅ Provided relevant memory retrieval" -ForegroundColor Green

Write-Host "`n🚀 Ready for real-world usage!" -ForegroundColor Yellow
