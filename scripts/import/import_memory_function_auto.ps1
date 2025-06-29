#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automatically import memory filter function into OpenWebUI
.DESCRIPTION
    This script automates the process of:
    1. Signing up/logging in to OpenWebUI
    2. Creating the memory filter function via API
    3. Enabling the function
    Based on the pattern from open-webui/open-webui/discussions/8955
#>

param(
    [string]$OpenWebUIUrl = "http://localhost:3000",
    [string]$AdminEmail = "admin@example.com",
    [string]$AdminUser = "admin", 
    [string]$AdminPass = "password123",
    [string]$FunctionFile = "memory_filter_function.py"
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

function Test-OpenWebUIHealth {
    param($Url)
    
    try {
        Write-ColorOutput "🔍 Testing OpenWebUI health at $Url..." $Blue
        $response = Invoke-RestMethod -Uri "$Url/health" -Method Get -TimeoutSec 10
        if ($response) {
            Write-ColorOutput "✅ OpenWebUI is healthy" $Green
            return $true
        }
    }
    catch {
        Write-ColorOutput "❌ OpenWebUI health check failed: $($_.Exception.Message)" $Red
        return $false
    }
    return $false
}

function Get-AuthToken {
    param($Url, $Email, $Password, $Name)
    
    try {
        Write-ColorOutput "🔐 Attempting to sign up admin user..." $Blue
        
        $signupData = @{
            name = $Name
            email = $Email
            password = $Password
        } | ConvertTo-Json
        
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri "$Url/api/v1/auths/signup" -Method Post -Body $signupData -Headers $headers -TimeoutSec 30
        
        if ($response.token) {
            Write-ColorOutput "✅ Successfully signed up/logged in" $Green
            return $response.token
        }
        else {
            Write-ColorOutput "❌ No token received in signup response" $Red
            return $null
        }
    }
    catch {
        # If signup fails, try signin instead
        Write-ColorOutput "⚠️ Signup failed, trying signin..." $Yellow
        
        try {
            $signinData = @{
                email = $Email
                password = $Password
            } | ConvertTo-Json
            
            $response = Invoke-RestMethod -Uri "$Url/api/v1/auths/signin" -Method Post -Body $signinData -Headers $headers -TimeoutSec 30
            
            if ($response.token) {
                Write-ColorOutput "✅ Successfully signed in" $Green
                return $response.token
            }
            else {
                Write-ColorOutput "❌ No token received in signin response" $Red
                return $null
            }
        }
        catch {
            Write-ColorOutput "❌ Both signup and signin failed: $($_.Exception.Message)" $Red
            return $null
        }
    }
}

function Import-MemoryFunction {
    param($Url, $Token, $FunctionCode)
    
    try {
        Write-ColorOutput "📦 Importing memory filter function..." $Blue
        
        # Prepare function data
        $functionData = @{
            id = "memory_filter"
            name = "Memory Filter"
            type = "filter"
            content = $FunctionCode
            meta = @{
                description = "Memory filter function that adds context from previous conversations"
                manifest = @{}
            }
            is_active = $true
            is_global = $false
        } | ConvertTo-Json -Depth 10
        
        $headers = @{
            "Authorization" = "Bearer $Token"
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri "$Url/api/v1/functions/create" -Method Post -Body $functionData -Headers $headers -TimeoutSec 60
        
        if ($response) {
            Write-ColorOutput "✅ Successfully imported memory filter function" $Green
            Write-ColorOutput "Function ID: $($response.id)" $Blue
            return $true
        }
        else {
            Write-ColorOutput "❌ Function import failed - no response" $Red
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ Function import failed: $($_.Exception.Message)" $Red
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-ColorOutput "Response: $responseBody" $Red
        }
        return $false
    }
}

function Enable-Function {
    param($Url, $Token, $FunctionId)
    
    try {
        Write-ColorOutput "🔧 Enabling memory filter function..." $Blue
        
        $headers = @{
            "Authorization" = "Bearer $Token"
            "Content-Type" = "application/json"
        }
        
        # Get function details first
        $function = Invoke-RestMethod -Uri "$Url/api/v1/functions/id/$FunctionId" -Method Get -Headers $headers
        
        if ($function) {
            # Update to enable
            $function.is_active = $true
            $updateData = $function | ConvertTo-Json -Depth 10
            
            $response = Invoke-RestMethod -Uri "$Url/api/v1/functions/id/$FunctionId/update" -Method Post -Body $updateData -Headers $headers
            
            if ($response) {
                Write-ColorOutput "✅ Successfully enabled memory filter function" $Green
                return $true
            }
        }
    }
    catch {
        Write-ColorOutput "⚠️ Function enable failed (may already be enabled): $($_.Exception.Message)" $Yellow
        return $false
    }
    
    return $false
}

# Main execution
Write-ColorOutput "🚀 Starting OpenWebUI Memory Function Import" $Green
Write-ColorOutput "Target: $OpenWebUIUrl" $Blue

# Check if OpenWebUI is running
if (-not (Test-OpenWebUIHealth -Url $OpenWebUIUrl)) {
    Write-ColorOutput "❌ OpenWebUI is not accessible. Please ensure it's running at $OpenWebUIUrl" $Red
    exit 1
}

# Check if function file exists
if (-not (Test-Path $FunctionFile)) {
    Write-ColorOutput "❌ Function file not found: $FunctionFile" $Red
    exit 1
}

# Read function code
Write-ColorOutput "📖 Reading function code from $FunctionFile..." $Blue
$functionCode = Get-Content $FunctionFile -Raw

# Get authentication token
$token = Get-AuthToken -Url $OpenWebUIUrl -Email $AdminEmail -Password $AdminPass -Name $AdminUser

if (-not $token) {
    Write-ColorOutput "❌ Failed to authenticate with OpenWebUI" $Red
    exit 1
}

Write-ColorOutput "🔑 Authentication successful" $Green

# Import the function
if (Import-MemoryFunction -Url $OpenWebUIUrl -Token $token -FunctionCode $functionCode) {
    Write-ColorOutput "✅ Memory function import completed successfully!" $Green
    
    # Try to enable the function
    Enable-Function -Url $OpenWebUIUrl -Token $token -FunctionId "memory_filter"
    
    Write-ColorOutput "📋 Next steps:" $Yellow
    Write-ColorOutput "1. Go to OpenWebUI Admin → Functions" $Reset
    Write-ColorOutput "2. Find 'Memory Filter' and ensure it's enabled" $Reset
    Write-ColorOutput "3. Go to Models → llama3.2:3b → Settings" $Reset
    Write-ColorOutput "4. Add 'Memory Filter' to the Filters section" $Reset
    Write-ColorOutput "5. Test memory functionality in chat" $Reset
}
else {
    Write-ColorOutput "❌ Memory function import failed" $Red
    exit 1
}

Write-ColorOutput "🎉 Import process completed!" $Green
