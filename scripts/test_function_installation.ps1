#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test Memory Function Installation Status
.DESCRIPTION
    This script tests whether the memory function has been successfully installed in OpenWebUI
.PARAMETER OpenWebUIUrl
    The URL where OpenWebUI is running (default: http://localhost:3000)
#>

param(
    [string]$OpenWebUIUrl = "http://localhost:3000"
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

Write-ColorOutput "🔍 Memory Function Installation Test" $Cyan
Write-ColorOutput "====================================" $Cyan

# Test 1: Check if OpenWebUI is accessible
Write-ColorOutput "`n1️⃣ Testing OpenWebUI accessibility..." $Blue
try {
    Invoke-RestMethod -Uri $OpenWebUIUrl -Method Get -TimeoutSec 10 | Out-Null
    Write-ColorOutput "✅ OpenWebUI is accessible at $OpenWebUIUrl" $Green
} catch {
    Write-ColorOutput "❌ OpenWebUI is not accessible: $($_.Exception.Message)" $Red
    Write-ColorOutput "   Make sure OpenWebUI is running with: docker-compose up -d" $Yellow
    exit 1
}

# Test 2: Check if Memory API is accessible
Write-ColorOutput "`n2️⃣ Testing Memory API accessibility..." $Blue
try {
    $memoryResponse = Invoke-RestMethod -Uri "http://localhost:8001/" -Method Get -TimeoutSec 10
    Write-ColorOutput "✅ Memory API is accessible" $Green
    Write-ColorOutput "   Version: $($memoryResponse.version)" $Reset
    Write-ColorOutput "   Features: $($memoryResponse.features -join ', ')" $Reset
} catch {
    Write-ColorOutput "❌ Memory API is not accessible: $($_.Exception.Message)" $Red
    Write-ColorOutput "   Make sure memory_api container is running" $Yellow
}

# Test 3: Check for auto-installer files
Write-ColorOutput "`n3️⃣ Checking auto-installer preparation files..." $Blue
$installFiles = @(
    "storage/openwebui/FUNCTION_INSTALLATION_INSTRUCTIONS.txt",
    "storage/openwebui/memory_function_code.py",
    "storage/openwebui/memory_function.json"
)

$filesFound = 0
foreach ($file in $installFiles) {
    if (Test-Path $file) {
        Write-ColorOutput "✅ Found: $file" $Green
        $filesFound++
    } else {
        Write-ColorOutput "⚠️  Missing: $file" $Yellow
    }
}

if ($filesFound -eq $installFiles.Count) {
    Write-ColorOutput "✅ All auto-installer files are present" $Green
} else {
    Write-ColorOutput "⚠️  Some auto-installer files are missing - run: docker-compose up function_installer" $Yellow
}

# Test 4: Check auto-installer logs
Write-ColorOutput "`n4️⃣ Checking auto-installer status..." $Blue
try {
    $installerLogs = docker logs backend-function-installer --tail 10 2>$null
    if ($installerLogs -match "Installation preparation completed") {
        Write-ColorOutput "✅ Auto-installer completed successfully" $Green
    } else {
        Write-ColorOutput "⚠️  Auto-installer may not have run yet" $Yellow
        Write-ColorOutput "   Run: docker-compose up function_installer" $Reset
    }
} catch {
    Write-ColorOutput "⚠️  Could not check auto-installer logs" $Yellow
}

# Test 5: Check if function code is available for manual installation
Write-ColorOutput "`n5️⃣ Checking function code availability..." $Blue
if (Test-Path "memory_function.py") {
    $codeLines = (Get-Content "memory_function.py" | Measure-Object -Line).Lines
    Write-ColorOutput "✅ Function code available: $codeLines lines" $Green
} else {
    Write-ColorOutput "❌ Function code not found: memory_function.py" $Red
}

# Test 6: Manual installation check instructions
Write-ColorOutput "`n6️⃣ Manual Installation Check..." $Blue
Write-ColorOutput "To check if the function is manually installed:" $Reset
Write-ColorOutput "1. Go to $OpenWebUIUrl" $Cyan
Write-ColorOutput "2. Login as admin" $Reset
Write-ColorOutput "3. Go to Admin → Functions" $Reset
Write-ColorOutput "4. Look for 'Enhanced Memory Function' or 'memory_function'" $Reset

# Summary and next steps
Write-ColorOutput "`n📋 Summary and Next Steps:" $Cyan
Write-ColorOutput "========================================" $Cyan

if ($filesFound -eq $installFiles.Count) {
    Write-ColorOutput "✅ System is ready for manual function installation" $Green
    Write-ColorOutput "`n🔧 To complete installation:" $Blue
    Write-ColorOutput "1. Open $OpenWebUIUrl in browser" $Reset
    Write-ColorOutput "2. Login as admin → Functions → Add Function" $Reset
    Write-ColorOutput "3. Copy content from: storage/openwebui/memory_function_code.py" $Reset
    Write-ColorOutput "4. Paste into function editor" $Reset
    Write-ColorOutput "5. Set ID: memory_function" $Reset
    Write-ColorOutput "6. Set Name: Enhanced Memory Function" $Reset
    Write-ColorOutput "7. Enable Active & Global checkboxes" $Reset
    Write-ColorOutput "8. Save function" $Reset
} else {
    Write-ColorOutput "⚠️  System needs setup - run auto-installer first:" $Yellow
    Write-ColorOutput "   docker-compose up function_installer" $Reset
}

Write-ColorOutput "`n💡 For automatic installation scripts:" $Cyan
Write-ColorOutput "   PowerShell: .\scripts\install_memory_function.ps1" $Reset
Write-ColorOutput "   Python: python scripts/install_memory_function.py" $Reset
