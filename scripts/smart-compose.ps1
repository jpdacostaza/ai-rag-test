# Smart Docker Compose wrapper for Windows - Unified Configuration
# PowerShell version with auto-architecture detection

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$DockerComposeArgs
)

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir

# Function to detect ARM64 architecture
function Test-ARM64Architecture {
    $arch = [System.Environment]::GetEnvironmentVariable("PROCESSOR_ARCHITECTURE")
    $archAlt = [System.Environment]::GetEnvironmentVariable("PROCESSOR_ARCHITEW6432")
    
    # Check for ARM64 indicators
    if ($arch -eq "ARM64" -or $archAlt -eq "ARM64") {
        return $true
    }
    
    # Additional check for uname-style output if available
    try {
        $unameOutput = & uname -m 2>$null
        if ($unameOutput -match "aarch64|arm64") {
            return $true
        }
    }
    catch {
        # uname not available, that's fine
    }
    
    return $false
}

# Function to set ARM64 environment variables for unified configuration
function Set-ARM64Environment {
    Write-Host "🔧 ARM64 detected - applying optimizations..." -ForegroundColor Cyan
    $env:ARM64_OPTIMIZED = "true"
    $env:OLLAMA_NUMA = "false"
    
    # Detect available memory for optimal settings
    try {
        $totalMemoryMB = [Math]::Round((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1MB)
        
        if ($totalMemoryMB -ge 30000) {
            # High memory ARM64 (32GB+) - ARM-based Windows devices with 32GB
            Write-Host "🚀 High-memory ARM64 detected (${totalMemoryMB}MB) - applying performance optimizations" -ForegroundColor Green
            $env:OLLAMA_MAX_LOADED_MODELS = "2"         # Can handle 2 models with 32GB
            $env:OLLAMA_MAX_VRAM = "12288"              # 12GB VRAM allocation
            $env:EMBEDDING_BATCH_SIZE = "64"            # Larger batches for better performance
            $env:REDIS_MAX_MEMORY = "1024mb"            # 1GB Redis cache
            $env:OLLAMA_NUM_PARALLEL = "4"              # 4 parallel requests for high-memory ARM64
            $env:OLLAMA_NUM_THREADS = "8"               # 8 CPU threads
        }
        else {
            # Standard ARM64 (16GB or less)
            Write-Host "💾 Standard ARM64 detected (${totalMemoryMB}MB) - applying conservative optimizations" -ForegroundColor Yellow
            $env:OLLAMA_MAX_LOADED_MODELS = "1"
            $env:OLLAMA_MAX_VRAM = "4096"
            $env:EMBEDDING_BATCH_SIZE = "16"
            $env:REDIS_MAX_MEMORY = "256mb"
            $env:OLLAMA_NUM_PARALLEL = "2"              # 2 parallel requests for standard ARM64
            $env:OLLAMA_NUM_THREADS = "4"               # 4 CPU threads for conservative use
        }
    }
    catch {
        # Fallback values for ARM64
        Write-Host "⚠️ Could not detect memory, using conservative ARM64 defaults" -ForegroundColor Yellow
        $env:OLLAMA_MAX_LOADED_MODELS = "1"
        $env:OLLAMA_MAX_VRAM = "4096"
        $env:EMBEDDING_BATCH_SIZE = "16"
        $env:REDIS_MAX_MEMORY = "256mb"
        $env:OLLAMA_NUM_PARALLEL = "2"
        $env:OLLAMA_NUM_THREADS = "4"
    }
    
    Write-Host "📄 Using unified docker-compose.yml with ARM64 optimizations" -ForegroundColor Green
}

# Function to set standard environment variables for x86_64
function Set-StandardEnvironment {
    Write-Host "💻 x86_64 detected - using standard configuration..." -ForegroundColor Green
    $env:ARM64_OPTIMIZED = "false"
    $env:OLLAMA_NUMA = "true"
    
    # Detect available memory for optimal settings
    try {
        $totalMemoryMB = [Math]::Round((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory / 1MB)
        
        if ($totalMemoryMB -ge 30000) {
            # High memory x86_64 (32GB+) - High-end Windows systems
            Write-Host "🚀 High-memory x86_64 detected (${totalMemoryMB}MB) - applying performance optimizations" -ForegroundColor Green
            $env:OLLAMA_MAX_LOADED_MODELS = "3"         # Can handle 3 models with good RAM
            $env:OLLAMA_MAX_VRAM = "16384"              # 16GB VRAM allocation
            $env:EMBEDDING_BATCH_SIZE = "128"           # Large batches for performance
            $env:REDIS_MAX_MEMORY = "2048mb"            # 2GB Redis cache
            $env:OLLAMA_NUM_PARALLEL = "6"              # 6 parallel requests for high-end systems
            $env:OLLAMA_NUM_THREADS = "16"              # 16 CPU threads for high-end systems
        }
        else {
            # Standard x86_64 (16GB or less)
            Write-Host "💾 Standard x86_64 detected (${totalMemoryMB}MB) - applying standard optimizations" -ForegroundColor Yellow
            $env:OLLAMA_MAX_LOADED_MODELS = "2"
            $env:OLLAMA_MAX_VRAM = "8192"
            $env:EMBEDDING_BATCH_SIZE = "32"
            $env:REDIS_MAX_MEMORY = "512mb"
            $env:OLLAMA_NUM_PARALLEL = "4"              # 4 parallel requests for standard systems
            $env:OLLAMA_NUM_THREADS = "8"               # 8 CPU threads for standard systems
        }
    }
    catch {
        # Fallback values for x86_64
        Write-Host "⚠️ Could not detect memory, using standard x86_64 defaults" -ForegroundColor Yellow
        $env:OLLAMA_MAX_LOADED_MODELS = "2"
        $env:OLLAMA_MAX_VRAM = "8192"
        $env:EMBEDDING_BATCH_SIZE = "32"
        $env:REDIS_MAX_MEMORY = "512mb"
        $env:OLLAMA_NUM_PARALLEL = "4"
        $env:OLLAMA_NUM_THREADS = "8"
    }
    
    Write-Host "📄 Using unified docker-compose.yml with standard optimizations" -ForegroundColor Green
}

# Function to run docker-compose with unified configuration
function Invoke-DockerCompose {
    param([string[]]$ComposeArgs)
    
    Set-Location $BackendDir
    
    if (Test-ARM64Architecture) {
        Write-Host "🔍 ARM64 architecture detected ($([System.Environment]::GetEnvironmentVariable('PROCESSOR_ARCHITECTURE')))"
        Write-Host "✅ Applying ARM64 optimizations automatically"
        
        # Set ARM64 environment variables
        Set-ARM64Environment
        
        Write-Host "✅ Using unified docker-compose.yml with auto-detected optimizations" -ForegroundColor Green
        & docker compose @ComposeArgs
    }
    else {
        $arch = [System.Environment]::GetEnvironmentVariable("PROCESSOR_ARCHITECTURE")
        Write-Host "🔍 x86_64 architecture detected ($arch)" -ForegroundColor Green
        Set-StandardEnvironment
        Write-Host "✅ Using unified docker-compose.yml with auto-detected optimizations" -ForegroundColor Green
        & docker compose @ComposeArgs
    }
}

# Main execution
Write-Host "🚀 Smart Docker Compose - Unified Configuration" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

try {
    # Run docker-compose with all passed arguments
    Invoke-DockerCompose -ComposeArgs $DockerComposeArgs
}
catch {
    Write-Error "Failed to run docker compose: $_"
    exit 1
}
