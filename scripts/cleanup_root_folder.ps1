#!/usr/bin/env pwsh
<#
.SYNOPSIS
Clean up root folder by organizing files into appropriate directories

.DESCRIPTION
Moves miscellaneous files from root to organized subdirectories
#>

Write-Host "🧹 Cleaning up root folder..." -ForegroundColor Cyan

# Ensure directories exist
$directories = @(
    "docs/guides",
    "docs/status", 
    "docs/templates",
    "scripts/import",
    "scripts/memory",
    "scripts/test",
    "tests/memory",
    "tests/data",
    "config"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "📁 Created directory: $dir" -ForegroundColor Green
    }
}

# Move documentation files
Write-Host "`n📚 Moving documentation files..." -ForegroundColor Yellow

$docFiles = @(
    @{ src = "MANUAL_IMPORT_GUIDE.md"; dest = "docs/guides/" },
    @{ src = "MEMORY_PIPELINE_SETUP_GUIDE.md"; dest = "docs/guides/" },
    @{ src = "MEMORY_PIPELINE_USAGE_GUIDE.md"; dest = "docs/guides/" },
    @{ src = "MEMORY_PIPELINE_TEST_PLAN.md"; dest = "docs/guides/" },
    @{ src = "FINAL_PROJECT_STATUS.md"; dest = "docs/status/" },
    @{ src = "PROJECT_STATUS_JUNE28.md"; dest = "docs/status/" },
    @{ src = "MEMORY_SYSTEM_SUCCESS_REPORT.md"; dest = "docs/status/" },
    @{ src = "ENVIRONMENT_RESET_LOG.md"; dest = "docs/status/" },
    @{ src = "README_NEW.md"; dest = "docs/" },
    @{ src = "README_OLD.md"; dest = "docs/" }
)

foreach ($file in $docFiles) {
    if (Test-Path $file.src) {
        Move-Item $file.src $file.dest -Force
        Write-Host "  ✅ Moved $($file.src) → $($file.dest)" -ForegroundColor Green
    }
}

# Move script files
Write-Host "`n⚙️ Moving script files..." -ForegroundColor Yellow

$scriptFiles = @(
    @{ src = "import_memory_function.ps1"; dest = "scripts/import/" },
    @{ src = "import_memory_function.sh"; dest = "scripts/import/" },
    @{ src = "import_memory_function_auto.ps1"; dest = "scripts/import/" },
    @{ src = "import_memory_function_clean.ps1"; dest = "scripts/import/" },
    @{ src = "import_function_debug.ps1"; dest = "scripts/import/" },
    @{ src = "update_memory_filter.ps1"; dest = "scripts/import/" },
    @{ src = "demo_memory_system.ps1"; dest = "scripts/memory/" },
    @{ src = "memory_system_status.ps1"; dest = "scripts/memory/" },
    @{ src = "test_complete_memory_system.ps1"; dest = "scripts/test/" },
    @{ src = "test_memory_simple.ps1"; dest = "scripts/test/" },
    @{ src = "test_memory_system_comprehensive.ps1"; dest = "scripts/test/" },
    @{ src = "test_memory_validation.ps1"; dest = "scripts/test/" },
    @{ src = "test_memory_function_import.ps1"; dest = "scripts/test/" },
    @{ src = "cleanup_backend.ps1"; dest = "scripts/" }
)

foreach ($file in $scriptFiles) {
    if (Test-Path $file.src) {
        Move-Item $file.src $file.dest -Force
        Write-Host "  ✅ Moved $($file.src) → $($file.dest)" -ForegroundColor Green
    }
}

# Move test data files
Write-Host "`n📊 Moving test data files..." -ForegroundColor Yellow

$testDataFiles = @(
    @{ src = "test_chat_completion.json"; dest = "tests/data/" },
    @{ src = "test_memory_conversation.json"; dest = "tests/data/" },
    @{ src = "test_memory_direct.json"; dest = "tests/data/" },
    @{ src = "test_memory_filter.json"; dest = "tests/data/" },
    @{ src = "simple_memory_function.json"; dest = "tests/data/" },
    @{ src = "test_memory_pipeline_filter.py"; dest = "tests/" }
)

foreach ($file in $testDataFiles) {
    if (Test-Path $file.src) {
        Move-Item $file.src $file.dest -Force
        Write-Host "  ✅ Moved $($file.src) → $($file.dest)" -ForegroundColor Green
    }
}

# Move configuration files
Write-Host "`n⚙️ Moving configuration files..." -ForegroundColor Yellow

$configFiles = @(
    @{ src = "function_template.json"; dest = "config/" },
    @{ src = "memory_functions.json"; dest = "config/" },
    @{ src = "persona.json"; dest = "config/" }
)

foreach ($file in $configFiles) {
    if (Test-Path $file.src) {
        Move-Item $file.src $file.dest -Force
        Write-Host "  ✅ Moved $($file.src) → $($file.dest)" -ForegroundColor Green
    }
}

# Create updated README_STRUCTURE.md
Write-Host "`n📋 Updating structure documentation..." -ForegroundColor Yellow

$structureContent = @"
# Backend Directory Structure

## 📁 Root Directory
- Core application files (main.py, config.py, etc.)
- Docker configuration files
- Requirements and environment files

## 📁 Key Directories

### `/docs/` - Documentation
- `guides/` - Setup and usage guides
- `status/` - Project status reports and logs
- `templates/` - Configuration templates

### `/scripts/` - Automation Scripts
- `import/` - Memory function import scripts
- `memory/` - Memory system utilities
- `test/` - Test execution scripts

### `/tests/` - Test Files
- `data/` - Test data and JSON files
- `memory/` - Memory-specific PowerShell tests
- `integration/` - Integration test files

### `/config/` - Configuration
- JSON configuration files
- Templates and schemas

### `/memory/` - Memory System
- Memory pipeline implementations
- Memory-related modules

### `/handlers/` - Exception Handlers
- Error handling modules

### `/pipelines/` - OpenWebUI Pipelines
- Pipeline route definitions

### `/routes/` - API Routes
- REST API endpoint definitions

### `/services/` - Business Logic
- Core service implementations

### `/utilities/` - Helper Functions
- Utility modules and helpers

### `/archive/` - Archived Files
- Old/deprecated files for reference

## 🚀 Getting Started
1. Review `README.md` for setup instructions
2. Check `docs/guides/` for detailed guides
3. Use scripts in `scripts/` for automation
4. Run tests from `tests/` directory

## 📝 Key Files
- `main.py` - Main application entry point
- `docker-compose.yml` - Docker services configuration
- `requirements.txt` - Python dependencies
- `enhanced_memory_api.py` - Memory system API
- `openwebui_api_bridge.py` - OpenWebUI integration bridge
"@

Set-Content -Path "README_STRUCTURE.md" -Value $structureContent
Write-Host "  ✅ Updated README_STRUCTURE.md" -ForegroundColor Green

Write-Host "`n" + "=" * 50 -ForegroundColor Cyan
Write-Host "🎉 Root folder cleanup complete!" -ForegroundColor Green
Write-Host "=" * 50

Write-Host "`n📊 Summary:" -ForegroundColor Yellow
Write-Host "✅ Documentation organized in docs/" -ForegroundColor Green
Write-Host "✅ Scripts organized in scripts/" -ForegroundColor Green  
Write-Host "✅ Test data organized in tests/data/" -ForegroundColor Green
Write-Host "✅ Configuration files in config/" -ForegroundColor Green
Write-Host "✅ Structure documentation updated" -ForegroundColor Green

Write-Host "`n🔍 Review the organized structure:" -ForegroundColor Cyan
Write-Host "tree /F" -ForegroundColor White
