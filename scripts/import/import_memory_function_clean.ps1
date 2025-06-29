# OpenWebUI Function Import Script (PowerShell)
# This script imports our memory pipeline as a function into OpenWebUI's database

Write-Host "OpenWebUI Memory Pipeline Function Import" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Configuration
$OpenWebUIUrl = "http://localhost:3000"
$AdminEmail = "admin@theroot.za.net"
$AdminPassword = "admin"
$PipelineFile = "./memory/simple_working_pipeline.py"
$FunctionId = "simple_memory_pipeline"
$FunctionName = "Simple Memory Pipeline"
$FunctionDescription = "Memory pipeline that adds context from previous conversations using Redis and ChromaDB"

Write-Host "Waiting for OpenWebUI to be ready..." -ForegroundColor Yellow

# Wait for OpenWebUI to be ready
do {
    try {
        $healthCheck = Invoke-RestMethod -Uri "$OpenWebUIUrl/health" -Method Get -ErrorAction SilentlyContinue
        if ($healthCheck) { break }
    } catch {
        Write-Host "   Waiting for OpenWebUI..." -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
} while ($true)

Write-Host "OpenWebUI is ready!" -ForegroundColor Green

Write-Host "Getting API token..." -ForegroundColor Yellow

# Get API token by signing in
$signInBody = @{
    email = $AdminEmail
    password = $AdminPassword
} | ConvertTo-Json

try {
    $signInResponse = Invoke-RestMethod -Uri "$OpenWebUIUrl/api/v1/auths/signin" -Method Post -Body $signInBody -ContentType "application/json"
    $apiKey = $signInResponse.token
    
    if (-not $apiKey) {
        Write-Host "Failed to get API token. Response: $signInResponse" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Got API token: $($apiKey.Substring(0, 20))..." -ForegroundColor Green
} catch {
    Write-Host "Failed to sign in: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "Reading pipeline file..." -ForegroundColor Yellow

if (-not (Test-Path $PipelineFile)) {
    Write-Host "Pipeline file not found: $PipelineFile" -ForegroundColor Red
    exit 1
}

# Read the Python file content
$pythonCode = Get-Content -Path $PipelineFile -Raw

Write-Host "Creating function payload..." -ForegroundColor Yellow

# Create the function payload
$functionPayload = @{
    id = $FunctionId
    name = $FunctionName
    type = "filter"
    content = $pythonCode
    meta = @{
        description = $FunctionDescription
        manifest = @{
            type = "filter"
            requirements = @("httpx")
        }
    }
    is_active = $true
    is_global = $false
} | ConvertTo-Json -Depth 10

Write-Host "Importing function into OpenWebUI..." -ForegroundColor Yellow

try {
    $headers = @{
        "Authorization" = "Bearer $apiKey"
        "Content-Type" = "application/json"
    }
    
    $importResponse = Invoke-RestMethod -Uri "$OpenWebUIUrl/api/v1/functions/create" -Method Post -Body $functionPayload -Headers $headers
    
    Write-Host "Import response: $($importResponse | ConvertTo-Json)" -ForegroundColor Cyan
    
    if ($importResponse.id) {
        Write-Host "Function imported successfully!" -ForegroundColor Green
        Write-Host "   Function ID: $($importResponse.id)" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next Steps:" -ForegroundColor Yellow
        Write-Host "1. Go to OpenWebUI Admin -> Functions" -ForegroundColor White
        Write-Host "2. Find 'Simple Memory Pipeline' and enable it" -ForegroundColor White
        Write-Host "3. Go to Models -> llama3.2:3b -> Filters" -ForegroundColor White
        Write-Host "4. Add the memory pipeline as a filter" -ForegroundColor White
        Write-Host "5. Chat using llama3.2:3b with memory!" -ForegroundColor White
    } else {
        Write-Host "Function import failed!" -ForegroundColor Red
        Write-Host "Response: $($importResponse | ConvertTo-Json)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Function import failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "Memory Pipeline Function Import Complete!" -ForegroundColor Green
