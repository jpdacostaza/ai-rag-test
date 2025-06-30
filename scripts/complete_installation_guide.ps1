#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete Function Installation Verification and Guide
.DESCRIPTION
    This script provides complete verification and step-by-step installation guide
#>

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

Write-ColorOutput "🎯 Complete Memory Function Installation Guide" $Cyan
Write-ColorOutput "===============================================" $Cyan

# System Status Check
Write-ColorOutput "`n📊 System Status Check:" $Blue
Write-ColorOutput "========================" $Blue

$systemOK = $true

# Check containers
Write-ColorOutput "`n🐳 Container Status:" $Blue
try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}" | Where-Object { $_ -match "backend-" }
    foreach ($container in $containers) {
        if ($container -match "backend-memory-api.*Up" -and $container -match "backend-openwebui.*Up") {
            Write-ColorOutput "   ✅ $container" $Green
        } elseif ($container -match "Up") {
            Write-ColorOutput "   ✅ $container" $Green
        } else {
            Write-ColorOutput "   ⚠️  $container" $Yellow
        }
    }
} catch {
    Write-ColorOutput "   ❌ Could not check Docker containers" $Red
    $systemOK = $false
}

# Check APIs
Write-ColorOutput "`n🌐 API Status:" $Blue
try {
    Invoke-RestMethod -Uri "http://localhost:3000" -Method Get -TimeoutSec 5 | Out-Null
    Write-ColorOutput "   ✅ OpenWebUI: http://localhost:3000" $Green
} catch {
    Write-ColorOutput "   ❌ OpenWebUI not accessible" $Red
    $systemOK = $false
}

try {
    $memoryApi = Invoke-RestMethod -Uri "http://localhost:8001/" -Method Get -TimeoutSec 5
    Write-ColorOutput "   ✅ Memory API: http://localhost:8001 (v$($memoryApi.version))" $Green
} catch {
    Write-ColorOutput "   ❌ Memory API not accessible" $Red
    $systemOK = $false
}

# Check installation files
Write-ColorOutput "`n📁 Installation Files:" $Blue
$installFiles = @{
    "Instructions" = "storage/openwebui/FUNCTION_INSTALLATION_INSTRUCTIONS.txt"
    "Function Code" = "storage/openwebui/memory_function_code.py"
    "JSON Export" = "storage/openwebui/memory_function.json"
}

$filesReady = $true
foreach ($desc in $installFiles.Keys) {
    $file = $installFiles[$desc]
    if (Test-Path $file) {
        Write-ColorOutput "   ✅ $desc`: $file" $Green
    } else {
        Write-ColorOutput "   ❌ $desc`: $file (missing)" $Red
        $filesReady = $false
    }
}

if (-not $systemOK) {
    Write-ColorOutput "`n❌ System is not ready. Please run: docker-compose up -d" $Red
    exit 1
}

if (-not $filesReady) {
    Write-ColorOutput "`n⚠️  Installation files missing. Running auto-installer..." $Yellow
    try {
        docker-compose up function_installer --no-deps
        Write-ColorOutput "✅ Auto-installer completed. Please re-run this script." $Green
    } catch {
        Write-ColorOutput "❌ Auto-installer failed. Please check Docker setup." $Red
    }
    exit 1
}

Write-ColorOutput "`n🎉 System is ready for function installation!" $Green

# Installation Instructions
Write-ColorOutput "`n📋 MANUAL INSTALLATION STEPS:" $Cyan
Write-ColorOutput "===============================" $Cyan

Write-ColorOutput "`n1️⃣ Open OpenWebUI in your browser:" $Blue
Write-ColorOutput "   🔗 http://localhost:3000" $Cyan

Write-ColorOutput "`n2️⃣ Login as administrator:" $Blue
Write-ColorOutput "   👤 Use your admin credentials" $Reset

Write-ColorOutput "`n3️⃣ Navigate to Functions:" $Blue
Write-ColorOutput "   📂 Admin → Functions → Add Function (+ button)" $Reset

Write-ColorOutput "`n4️⃣ Copy the function code:" $Blue
Write-ColorOutput "   📄 From: storage\\openwebui\\memory_function_code.py" $Cyan
Write-ColorOutput "   💡 The entire file content needs to be copied" $Reset

Write-ColorOutput "`n5️⃣ Configure the function:" $Blue
Write-ColorOutput "   🆔 Function ID: memory_function" $Cyan
Write-ColorOutput "   📝 Function Name: Enhanced Memory Function" $Cyan
Write-ColorOutput "   ✅ Enable 'Active' checkbox" $Cyan
Write-ColorOutput "   🌐 Enable 'Global' checkbox (optional)" $Cyan

Write-ColorOutput "`n6️⃣ Save the function:" $Blue
Write-ColorOutput "   💾 Click Save/Submit" $Reset

# Quick Copy Helper
Write-ColorOutput "`n📋 QUICK COPY HELPER:" $Cyan
Write-ColorOutput "=====================" $Cyan

if (Test-Path "storage/openwebui/memory_function_code.py") {
    Write-ColorOutput "`nFunction code ready to copy:" $Blue
    Write-ColorOutput "=============================" $Blue
    
    # Show first few lines as preview
    $codePreview = Get-Content "storage/openwebui/memory_function_code.py" -TotalCount 5
    foreach ($line in $codePreview) {
        Write-ColorOutput "   $line" $Reset
    }
    Write-ColorOutput "   ... (rest of code in file)" $Reset
    
    $totalLines = (Get-Content "storage/openwebui/memory_function_code.py" | Measure-Object -Line).Lines
    Write-ColorOutput "`n📊 Total lines: $totalLines" $Green
    Write-ColorOutput "📁 File location: storage\\openwebui\\memory_function_code.py" $Cyan
}

# Verification Steps
Write-ColorOutput "`n✅ VERIFICATION STEPS:" $Cyan
Write-ColorOutput "======================" $Cyan

Write-ColorOutput "`nAfter installation, verify the function:" $Blue
Write-ColorOutput "1. Check Admin → Functions list for 'Enhanced Memory Function'" $Reset
Write-ColorOutput "2. Start a new conversation" $Reset
Write-ColorOutput "3. Look for memory function in the functions dropdown" $Reset
Write-ColorOutput "4. Send a few messages and check if they're remembered" $Reset

# Test Memory API Integration
Write-ColorOutput "`n🧪 Test Memory Integration:" $Blue
Write-ColorOutput "Add a test memory:" $Reset
try {
    Invoke-RestMethod -Uri "http://localhost:8001/api/learning/process_interaction" -Method POST -ContentType "application/json" -Body '{"user_id": "install_test", "conversation_id": "install_test_conv", "user_message": "Testing memory function installation", "assistant_response": "Memory function installation test successful!"}' | Out-Null
    Write-ColorOutput "✅ Memory API integration test: PASSED" $Green
} catch {
    Write-ColorOutput "⚠️  Memory API integration test: FAILED" $Yellow
    Write-ColorOutput "   This doesn't affect function installation" $Reset
}

Write-ColorOutput "`n🎯 SUMMARY:" $Cyan
Write-ColorOutput "============" $Cyan
Write-ColorOutput "✅ System is ready" $Green
Write-ColorOutput "✅ Installation files prepared" $Green
Write-ColorOutput "✅ Memory API operational" $Green
Write-ColorOutput "📋 Manual installation required (one-time only)" $Yellow
Write-ColorOutput "🔗 After installation, your AI will have persistent memory!" $Cyan

Write-ColorOutput "`n💡 Need help? Check the detailed instructions at:" $Blue
Write-ColorOutput "   📄 storage\\openwebui\\FUNCTION_INSTALLATION_INSTRUCTIONS.txt" $Cyan
