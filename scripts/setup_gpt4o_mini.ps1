# PowerShell script to set up gpt-4o-mini model for OpenWebUI
# This script configures OpenAI API and ensures the model is available

Write-Host "Setting up gpt-4o-mini model for OpenWebUI..." -ForegroundColor Green

# Check if OPENAI_API_KEY is set
if (-not $env:OPENAI_API_KEY) {
    Write-Host "OPENAI_API_KEY not found in environment variables." -ForegroundColor Yellow
    $apiKey = Read-Host "Please enter your OpenAI API key"
    if ($apiKey) {
        [Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $apiKey, "User")
        $env:OPENAI_API_KEY = $apiKey
        Write-Host "OpenAI API key set successfully!" -ForegroundColor Green
    } else {
        Write-Host "API key is required to use gpt-4o-mini. Exiting..." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "OpenAI API key found in environment." -ForegroundColor Green
}

# Create .env file for Docker containers
$envContent = @"
OPENAI_API_KEY=$env:OPENAI_API_KEY
DEFAULT_MODEL=gpt-4o-mini
OPENAI_API_MAX_TOKENS=8192
MEMORY_CONTEXT_LENGTH=16384
USE_OLLAMA=false
EMBEDDING_MODEL=nomic-embed-text
RAG_TOP_K=10
"@

$envPath = "e:\Projects\opt\backend\.env"
$envContent | Out-File -FilePath $envPath -Encoding UTF8
Write-Host ".env file created at $envPath" -ForegroundColor Green

# Restart Docker containers to pick up new configuration
Write-Host "Restarting Docker containers with new configuration..." -ForegroundColor Yellow
Set-Location "e:\Projects\opt\backend"

docker-compose down
Start-Sleep 2
docker-compose up -d

Write-Host "Setup complete! gpt-4o-mini should now be available in OpenWebUI." -ForegroundColor Green
Write-Host "Note: The model will be accessed via OpenAI API, no local download needed." -ForegroundColor Cyan
