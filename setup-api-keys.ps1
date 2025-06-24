# OpenWebUI API Key Management Setup Script (PowerShell)
# Provides interactive setup and management of OpenWebUI API keys

param(
    [switch]$Status,
    [switch]$Setup,
    [switch]$Env,
    [switch]$Test,
    [switch]$Help
)

# Colors and emojis
$Colors = @{
    Red = [System.ConsoleColor]::Red
    Green = [System.ConsoleColor]::Green
    Yellow = [System.ConsoleColor]::Yellow
    Blue = [System.ConsoleColor]::Blue
    Cyan = [System.ConsoleColor]::Cyan
    White = [System.ConsoleColor]::White
}

$Emojis = @{
    Check = "✅"
    Warning = "⚠️"
    Error = "❌"
    Info = "ℹ️"
    Key = "🔑"
    Gear = "⚙️"
    Rocket = "🚀"
}

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigFile = Join-Path $ScriptDir "openwebui_api_keys.json"
$ExampleFile = Join-Path $ScriptDir "openwebui_api_keys.example.json"

function Write-ColorText {
    param(
        [string]$Text,
        [System.ConsoleColor]$Color = [System.ConsoleColor]::White
    )
    Write-Host $Text -ForegroundColor $Color
}

function Write-Status {
    param(
        [string]$Message,
        [string]$Type = "info"
    )
    
    switch ($Type) {
        "success" { Write-ColorText "   $($Emojis.Check) $Message" $Colors.Green }
        "warning" { Write-ColorText "   $($Emojis.Warning) $Message" $Colors.Yellow }
        "error" { Write-ColorText "   $($Emojis.Error) $Message" $Colors.Red }
        default { Write-ColorText "   $($Emojis.Info) $Message" $Colors.White }
    }
}

function Write-Header {
    Write-ColorText "$($Emojis.Key) OpenWebUI API Key Management Setup" $Colors.Blue
    Write-ColorText "========================================" $Colors.Blue
}

function Test-Dependencies {
    Write-Host ""
    Write-ColorText "$($Emojis.Gear) Checking dependencies..." $Colors.Blue
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Python found: $pythonVersion" "success"
        } else {
            $python3Version = python3 --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Status "Python 3 found: $python3Version" "success"
                $global:PythonCmd = "python3"
            } else {
                Write-Status "Python not found. Please install Python." "error"
                return $false
            }
        }
        $global:PythonCmd = "python"
    } catch {
        Write-Status "Error checking Python: $_" "error"
        return $false
    }
    
    # Check if api_key_manager.py exists
    $apiManagerPath = Join-Path $ScriptDir "api_key_manager.py"
    if (Test-Path $apiManagerPath) {
        Write-Status "API Key Manager found" "success"
    } else {
        Write-Status "API Key Manager not found. Please ensure api_key_manager.py exists." "error"
        return $false
    }
    
    # Check Python dependencies
    try {
        & $global:PythonCmd -c "import requests, json, pathlib" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Python dependencies available" "success"
        } else {
            Write-Status "Missing Python dependencies. Install with: pip install requests" "warning"
        }
    } catch {
        Write-Status "Could not check Python dependencies" "warning"
    }
    
    return $true
}

function Test-ConfigStatus {
    Write-Host ""
    Write-Host "1. Checking configuration status..."
    
    if (Test-Path $ConfigFile) {
        Write-Status "Configuration file exists: $(Split-Path -Leaf $ConfigFile)" "success"
        
        # Try to read and parse basic info
        try {
            $configData = Get-Content $ConfigFile | ConvertFrom-Json
            
            $defaultKey = $configData.default.api_key
            if ($defaultKey -and $defaultKey -ne "YOUR_DEFAULT_API_KEY_HERE") {
                $keyPreview = $defaultKey.Substring([Math]::Max(0, $defaultKey.Length - 8))
                Write-Status "Default key configured: ...$keyPreview" "success"
            } else {
                Write-Status "No default key configured" "warning"
            }
            
            $users = $configData.users
            if ($users -and $users.PSObject.Properties.Count -gt 0) {
                $userList = ($users.PSObject.Properties.Name) -join ", "
                Write-Status "$($users.PSObject.Properties.Count) user(s) configured: $userList" "success"
            } else {
                Write-Status "No user keys configured" "warning"
            }
            
            $environments = $configData.environments
            if ($environments -and $environments.PSObject.Properties.Count -gt 0) {
                $envList = ($environments.PSObject.Properties.Name) -join ", "
                Write-Status "$($environments.PSObject.Properties.Count) environment(s) configured: $envList" "success"
            } else {
                Write-Status "No environment keys configured" "warning"
            }
        } catch {
            Write-Status "Error reading config: $_" "error"
        }
    } else {
        Write-Status "No configuration file found" "warning"
        if (Test-Path $ExampleFile) {
            Write-Status "Example file available: $(Split-Path -Leaf $ExampleFile)" "info"
        }
    }
}

function Test-EnvironmentVars {
    Write-Host ""
    Write-Host "2. Checking environment variables..."
    
    $apiKey = $env:OPENWEBUI_API_KEY
    if ($apiKey) {
        $keyPreview = $apiKey.Substring([Math]::Max(0, $apiKey.Length - 8))
        Write-Status "OPENWEBUI_API_KEY set: ...$keyPreview" "success"
        $baseUrl = if ($env:OPENWEBUI_BASE_URL) { $env:OPENWEBUI_BASE_URL } else { "http://localhost:3000" }
        Write-Status "OPENWEBUI_BASE_URL: $baseUrl" "success"
    } else {
        Write-Status "OPENWEBUI_API_KEY not set" "warning"
    }
}

function Test-UpdatedTools {
    Write-Host ""
    Write-Host "3. Checking updated diagnostic tools..."
      $tools = @(
        "debug\archived\demo-test\debug-tools\openwebui_memory_diagnostic.py",
        "debug\archived\demo-test\debug-tools\test_memory_cross_chat.py"
    )
    
    foreach ($tool in $tools) {
        $toolPath = Join-Path $ScriptDir $tool
        if (Test-Path $toolPath) {
            # Check if tool imports API key manager
            $content = Get-Content $toolPath -Raw
            if ($content -match "from api_key_manager import") {
                Write-Status "$(Split-Path -Leaf $tool) - Updated with API key support" "success"
            } else {
                Write-Status "$(Split-Path -Leaf $tool) - Found but not updated" "warning"
            }
        } else {
            Write-Status "$(Split-Path -Leaf $tool) - Not found" "warning"
        }
    }
}

function Show-SetupOptions {
    Write-Host ""
    Write-Host "4. Setup options:"
    Write-ColorText "   $($Emojis.Info) Interactive Python setup:" $Colors.White
    Write-ColorText "      python api_key_manager.py" $Colors.Cyan
    
    Write-Host ""
    Write-ColorText "   $($Emojis.Info) Environment variables (temporary):" $Colors.White
    Write-ColorText "      `$env:OPENWEBUI_API_KEY='your-key-here'" $Colors.Cyan
    Write-ColorText "      `$env:OPENWEBUI_BASE_URL='http://localhost:3000'" $Colors.Cyan
    
    Write-Host ""
    Write-ColorText "   $($Emojis.Info) Create config from example:" $Colors.White
    Write-ColorText "      Copy-Item openwebui_api_keys.example.json openwebui_api_keys.json" $Colors.Cyan
    Write-ColorText "      # Then edit openwebui_api_keys.json with your keys" $Colors.Cyan
}

function Show-UsageExamples {    Write-Host ""
    Write-Host "5. Usage examples:"
    Write-ColorText "   $($Emojis.Info) Run diagnostic with auto-detected keys:" $Colors.White
    Write-ColorText "      python debug\archived\demo-test\debug-tools\openwebui_memory_diagnostic.py" $Colors.Cyan
    
    Write-Host ""
    Write-ColorText "   $($Emojis.Info) Run with specific user:" $Colors.White
    Write-ColorText "      python debug\archived\demo-test\debug-tools\openwebui_memory_diagnostic.py --user=john" $Colors.Cyan
    
    Write-Host ""
    Write-ColorText "   $($Emojis.Info) Run with specific environment:" $Colors.White
    Write-ColorText "      python debug\archived\demo-test\debug-tools\openwebui_memory_diagnostic.py --env=production" $Colors.Cyan
    
    Write-Host ""
    Write-ColorText "   $($Emojis.Info) Test memory across chat sessions:" $Colors.White
    Write-ColorText "      python debug\archived\demo-test\debug-tools\test_memory_cross_chat.py" $Colors.Cyan
}

function Start-InteractiveSetup {
    Write-Host ""
    Write-ColorText "$($Emojis.Rocket) Starting interactive setup..." $Colors.Blue
    Write-Host "This will run the Python interactive setup tool."
    Write-Host ""
    
    $continue = Read-Host "Continue? (y/N)"
    if ($continue -match "^[Yy]") {
        Write-ColorText "$($Emojis.Info) Launching Python setup tool..." $Colors.White
        & $global:PythonCmd (Join-Path $ScriptDir "api_key_manager.py")
    } else {
        Write-ColorText "$($Emojis.Info) Setup cancelled." $Colors.White
    }
}

function Start-QuickEnvSetup {
    Write-Host ""
    Write-ColorText "$($Emojis.Rocket) Quick environment variable setup..." $Colors.Blue
    Write-Host "This will help you set environment variables for this session."
    Write-Host ""
    
    $apiKey = Read-Host "Enter your OpenWebUI API key"
    if (-not $apiKey) {
        Write-Status "No API key provided. Skipping." "warning"
        return
    }
    
    $baseUrl = Read-Host "Enter base URL [http://localhost:3000]"
    if (-not $baseUrl) {
        $baseUrl = "http://localhost:3000"
    }
    
    Write-Host ""
    Write-ColorText "$($Emojis.Info) Setting environment variables for this session..." $Colors.White
    $env:OPENWEBUI_API_KEY = $apiKey
    $env:OPENWEBUI_BASE_URL = $baseUrl
    
    Write-Status "Environment variables set for this session" "success"
    Write-Host ""
    Write-ColorText "$($Emojis.Info) To make these permanent, add to your PowerShell profile:" $Colors.White
    Write-ColorText "      `$env:OPENWEBUI_API_KEY='$apiKey'" $Colors.Cyan
    Write-ColorText "      `$env:OPENWEBUI_BASE_URL='$baseUrl'" $Colors.Cyan
}

function Test-Setup {
    Write-Host ""
    Write-ColorText "$($Emojis.Rocket) Testing current setup..." $Colors.Blue
    
    $diagnosticPath = Join-Path $ScriptDir "debug\archived\demo-test\debug-tools\openwebui_memory_diagnostic.py"
    if (Test-Path $diagnosticPath) {
        Write-ColorText "$($Emojis.Info) Running diagnostic tool..." $Colors.White
        try {
            & $global:PythonCmd $diagnosticPath
        } catch {
            Write-Status "Diagnostic tool failed. Check your API keys and OpenWebUI connection." "error"
        }
    } else {
        Write-Status "Diagnostic tool not found." "error"
    }
}

function Show-Documentation {
    Write-Host ""
    Write-ColorText "$($Emojis.Info) Documentation available:" $Colors.White
    
    $docPath = Join-Path $ScriptDir "API_KEY_MANAGEMENT.md"
    if (Test-Path $docPath) {
        Write-Status "Complete documentation: API_KEY_MANAGEMENT.md" "success"
        Write-ColorText "      Get-Content API_KEY_MANAGEMENT.md" $Colors.Cyan
    }
    
    if (Test-Path $ExampleFile) {
        Write-Status "Example configuration: openwebui_api_keys.example.json" "success"
        Write-ColorText "      Get-Content openwebui_api_keys.example.json" $Colors.Cyan
    }
}

function Show-MainMenu {
    while ($true) {
        Write-Host ""
        Write-ColorText "$($Emojis.Gear) Setup Menu:" $Colors.Blue
        Write-Host "1. Run full status check"
        Write-Host "2. Interactive Python setup"
        Write-Host "3. Quick environment variable setup"
        Write-Host "4. Test current setup"
        Write-Host "5. Show documentation"
        Write-Host "6. Exit"
        Write-Host ""
        
        $choice = Read-Host "Select option (1-6)"
        
        switch ($choice) {
            "1" {
                Test-ConfigStatus
                Test-EnvironmentVars
                Test-UpdatedTools
                Show-SetupOptions
                Show-UsageExamples
            }
            "2" { Start-InteractiveSetup }
            "3" { Start-QuickEnvSetup }
            "4" { Test-Setup }
            "5" { Show-Documentation }
            "6" {
                Write-ColorText "$($Emojis.Info) Goodbye!" $Colors.White
                return
            }
            default {
                Write-Status "Invalid option. Please select 1-6." "error"
            }
        }
    }
}

function Show-Help {
    Write-Host "Usage: .\setup-api-keys.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Status     Show configuration status"
    Write-Host "  -Setup      Run interactive setup"
    Write-Host "  -Env        Quick environment variable setup"
    Write-Host "  -Test       Test current setup"
    Write-Host "  -Help       Show this help"
    Write-Host ""
    Write-Host "Run without options for interactive menu."
}

# Main execution
function Main {
    Write-Header
    
    if ($Help) {
        Show-Help
        return
    }
    
    if (-not (Test-Dependencies)) {
        return
    }
    
    if ($Status) {
        Test-ConfigStatus
        Test-EnvironmentVars
        Test-UpdatedTools
        return
    }
    
    if ($Setup) {
        Start-InteractiveSetup
        return
    }
    
    if ($Env) {
        Start-QuickEnvSetup
        return
    }
    
    if ($Test) {
        Test-Setup
        return
    }
    
    # Default behavior - show status and offer menu
    Test-ConfigStatus
    Test-EnvironmentVars
    Show-SetupOptions
    Show-UsageExamples
    
    Write-Host ""
    $openMenu = Read-Host "Would you like to open the interactive menu? (y/N)"
    if ($openMenu -match "^[Yy]") {
        Show-MainMenu
    }
}

# Run main function
Main
