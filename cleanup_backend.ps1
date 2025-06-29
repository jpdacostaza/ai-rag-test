#!/usr/bin/env pwsh
<#
.SYNOPSIS
Backend Directory Cleanup Script

.DESCRIPTION
Organizes and cleans up the backend directory by:
- Moving documentation to docs/
- Moving test files to tests/
- Moving scripts to scripts/
- Removing temporary/redundant files
- Creating organized structure
#>

Write-Host "🧹 Starting Backend Directory Cleanup..." -ForegroundColor Cyan
Write-Host "=" * 50

# Create organized directory structure
$directories = @(
    "docs",
    "docs/status",
    "docs/guides", 
    "tests/memory",
    "tests/integration",
    "scripts/memory",
    "scripts/import",
    "archive"
)

Write-Host "`n📁 Creating directory structure..." -ForegroundColor Yellow
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ Created: $dir" -ForegroundColor Green
    }
}

# Move documentation files
Write-Host "`n📚 Moving documentation files..." -ForegroundColor Yellow
$docFiles = @(
    "backend_analysis_summary.md",
    "CONVERSATION_SYNC_SUMMARY_JUNE27.md", 
    "FINAL_PROJECT_STATUS.md",
    "MANUAL_IMPORT_GUIDE.md",
    "MEMORY_PIPELINE_SETUP_GUIDE.md",
    "MEMORY_PIPELINE_TEST_PLAN.md",
    "MEMORY_PIPELINE_USAGE_GUIDE.md",
    "MEMORY_SYSTEM_SUCCESS_REPORT.md",
    "PROJECT_STATUS_JUNE27_EOD.md",
    "PROJECT_STATUS_JUNE28.md"
)

foreach ($file in $docFiles) {
    if (Test-Path $file) {
        Move-Item $file "docs/" -Force
        Write-Host "✅ Moved: $file → docs/" -ForegroundColor Green
    }
}

# Move status documents to subdirectory
$statusFiles = @(
    "docs/PROJECT_STATUS_JUNE27_EOD.md",
    "docs/PROJECT_STATUS_JUNE28.md",
    "docs/FINAL_PROJECT_STATUS.md"
)

foreach ($file in $statusFiles) {
    if (Test-Path $file) {
        Move-Item $file "docs/status/" -Force
        Write-Host "✅ Moved: $file → docs/status/" -ForegroundColor Green
    }
}

# Move guides to subdirectory
$guideFiles = @(
    "docs/MANUAL_IMPORT_GUIDE.md",
    "docs/MEMORY_PIPELINE_SETUP_GUIDE.md",
    "docs/MEMORY_PIPELINE_TEST_PLAN.md", 
    "docs/MEMORY_PIPELINE_USAGE_GUIDE.md"
)

foreach ($file in $guideFiles) {
    if (Test-Path $file) {
        Move-Item $file "docs/guides/" -Force
        Write-Host "✅ Moved: $file → docs/guides/" -ForegroundColor Green
    }
}

# Move test files
Write-Host "`n🧪 Moving test files..." -ForegroundColor Yellow
$testFiles = @(
    "test_memory_simple.ps1",
    "test_memory_validation.ps1", 
    "test_memory_system_comprehensive.ps1",
    "demo_memory_system.ps1",
    "memory_system_status.ps1",
    "test_memory_function_import.ps1",
    "test_complete_memory_system.ps1"
)

foreach ($file in $testFiles) {
    if (Test-Path $file) {
        Move-Item $file "tests/memory/" -Force
        Write-Host "✅ Moved: $file → tests/memory/" -ForegroundColor Green
    }
}

# Move integration tests
$integrationTests = @(
    "test_complete_integration.py",
    "test_direct_pipeline.py",
    "test_memory_pipeline_filter.py",
    "test_openwebui_pipelines.py",
    "corrected_live_test.py",
    "live_pipeline_test.py",
    "debug_pipelines.py"
)

foreach ($file in $integrationTests) {
    if (Test-Path $file) {
        Move-Item $file "tests/integration/" -Force
        Write-Host "✅ Moved: $file → tests/integration/" -ForegroundColor Green
    }
}

# Move import scripts
Write-Host "`n📜 Moving script files..." -ForegroundColor Yellow
$importScripts = @(
    "import_memory_function.ps1",
    "import_memory_function.sh",
    "import_memory_function_auto.ps1",
    "import_memory_function_clean.ps1",
    "import_function_debug.ps1",
    "update_memory_filter.ps1"
)

foreach ($file in $importScripts) {
    if (Test-Path $file) {
        Move-Item $file "scripts/import/" -Force
        Write-Host "✅ Moved: $file → scripts/import/" -ForegroundColor Green
    }
}

# Move memory-related scripts
$memoryScripts = @(
    "start-memory-system.ps1",
    "start-memory-system.sh"
)

foreach ($file in $memoryScripts) {
    if (Test-Path $file) {
        Move-Item $file "scripts/memory/" -Force
        Write-Host "✅ Moved: $file → scripts/memory/" -ForegroundColor Green
    }
}

# Archive old/redundant files
Write-Host "`n📦 Archiving redundant files..." -ForegroundColor Yellow
$archiveFiles = @(
    "simple_memory_api.py",
    "persistent_memory_api.py",
    "memory_function.py",
    "function_template.json",
    "simple_memory_function.json",
    "memory_functions.json",
    "update_valves.json"
)

foreach ($file in $archiveFiles) {
    if (Test-Path $file) {
        Move-Item $file "archive/" -Force
        Write-Host "✅ Archived: $file" -ForegroundColor Green
    }
}

# Archive test data files
$testDataFiles = @(
    "test_chat_completion.json",
    "test_document.json",
    "test_memory_conversation.json",
    "test_memory_direct.json", 
    "test_memory_filter.json",
    "test_pipeline_inlet.json",
    "test_pipeline_inlet_correct.json",
    "memory_learning_review.json",
    "web_search_integration_validation.json"
)

foreach ($file in $testDataFiles) {
    if (Test-Path $file) {
        Move-Item $file "archive/" -Force
        Write-Host "✅ Archived: $file" -ForegroundColor Green
    }
}

# Remove workspace file (should be in root)
if (Test-Path "AI Test.code-workspace") {
    Remove-Item "AI Test.code-workspace" -Force
    Write-Host "✅ Removed: AI Test.code-workspace" -ForegroundColor Green
}

# Create organized README for the new structure
Write-Host "`n📄 Creating directory structure documentation..." -ForegroundColor Yellow

$readmeContent = @"
# Backend Directory Structure

This directory contains the OpenWebUI memory system backend with organized file structure.

## 📁 Directory Structure

### Core Application
- ``main.py`` - Main application entry point
- ``enhanced_memory_api.py`` - Enhanced memory API with Redis + ChromaDB
- ``memory_filter_function.py`` - OpenWebUI memory filter function
- ``openwebui_api_bridge.py`` - API bridge for pipeline integration
- ``docker-compose.yml`` - Docker composition for all services
- ``requirements.txt`` - Python dependencies

### Core Modules
- ``config.py`` - Configuration management
- ``models.py`` - Data models
- ``database.py`` - Database utilities
- ``security.py`` - Security utilities
- ``validation.py`` - Input validation

### Specialized Modules
- ``adaptive_learning.py`` - Adaptive learning system
- ``cache_manager.py`` - Caching functionality  
- ``database_manager.py`` - Database management
- ``enhanced_document_processing.py`` - Document processing
- ``enhanced_integration.py`` - System integration
- ``enhanced_streaming.py`` - Streaming capabilities
- ``error_handler.py`` - Error handling
- ``feedback_router.py`` - Feedback routing
- ``human_logging.py`` - Human interaction logging
- ``model_manager.py`` - Model management
- ``rag.py`` - RAG (Retrieval Augmented Generation)
- ``startup.py`` - Application startup
- ``storage_manager.py`` - Storage management
- ``upload.py`` - File upload handling
- ``user_profiles.py`` - User profile management
- ``watchdog.py`` - System monitoring
- ``web_search_tool.py`` - Web search integration

### Organized Directories

#### ``docs/`` - Documentation
- ``status/`` - Project status reports
- ``guides/`` - Setup and usage guides
- ``backend_analysis_summary.md``
- ``CONVERSATION_SYNC_SUMMARY_JUNE27.md``
- ``MEMORY_SYSTEM_SUCCESS_REPORT.md``

#### ``tests/`` - Test Files
- ``memory/`` - Memory system tests
  - ``test_memory_simple.ps1``
  - ``test_memory_validation.ps1``
  - ``test_memory_system_comprehensive.ps1``
  - ``demo_memory_system.ps1``
  - ``memory_system_status.ps1``
- ``integration/`` - Integration tests
  - ``test_complete_integration.py``
  - ``test_direct_pipeline.py``
  - ``test_memory_pipeline_filter.py``

#### ``scripts/`` - Utility Scripts
- ``import/`` - Function import scripts
  - ``import_memory_function.ps1``
  - ``update_memory_filter.ps1``
- ``memory/`` - Memory system scripts
  - ``start-memory-system.ps1``

#### ``memory/`` - Memory Pipeline Components
- Memory pipeline implementations
- Memory processing utilities

#### ``handlers/`` - Request Handlers
- Exception handlers
- Request processing

#### ``pipelines/`` - Pipeline Components
- Pipeline routes and implementations

#### ``routes/`` - API Routes
- REST API endpoint definitions

#### ``services/`` - Service Layer
- Business logic services

#### ``setup/`` - Setup and Configuration
- Installation and setup scripts

#### ``storage/`` - Storage Components
- Storage implementations and utilities

#### ``utilities/`` - Utility Functions
- Helper functions and utilities

#### ``archive/`` - Archived Files
- Old implementations
- Redundant files
- Test data files

## 🚀 Quick Start

1. **Start Services**: ``docker-compose up -d``
2. **Import Memory Filter**: ``scripts/import/import_memory_function.ps1``
3. **Test Memory System**: ``tests/memory/test_memory_simple.ps1``
4. **Check Status**: ``tests/memory/memory_system_status.ps1``

## 📚 Documentation

- **Setup Guide**: ``docs/guides/MEMORY_PIPELINE_SETUP_GUIDE.md``
- **Usage Guide**: ``docs/guides/MEMORY_PIPELINE_USAGE_GUIDE.md``
- **Test Plan**: ``docs/guides/MEMORY_PIPELINE_TEST_PLAN.md``
- **Success Report**: ``docs/MEMORY_SYSTEM_SUCCESS_REPORT.md``

## 🧪 Testing

- **Simple Test**: ``tests/memory/test_memory_simple.ps1``
- **Full Validation**: ``tests/memory/test_memory_validation.ps1``
- **Comprehensive Suite**: ``tests/memory/test_memory_system_comprehensive.ps1``
- **Interactive Demo**: ``tests/memory/demo_memory_system.ps1``

## 🔧 Management

- **Import Memory Filter**: ``scripts/import/import_memory_function.ps1``
- **Update Filter**: ``scripts/import/update_memory_filter.ps1``
- **Start Memory System**: ``scripts/memory/start-memory-system.ps1``
- **System Status**: ``tests/memory/memory_system_status.ps1``
"@

$readmeContent | Out-File -FilePath "README_STRUCTURE.md" -Encoding UTF8
Write-Host "✅ Created: README_STRUCTURE.md" -ForegroundColor Green

# Display final directory structure
Write-Host "`n📊 Final directory structure:" -ForegroundColor Cyan
try {
    tree /f | Select-Object -First 50
} catch {
    Write-Host "Directory structure created successfully!" -ForegroundColor Green
}

Write-Host "`n" + "=" * 50 -ForegroundColor Cyan
Write-Host "✨ Cleanup Complete!" -ForegroundColor Green
Write-Host "=" * 50

Write-Host "`n📋 Summary:" -ForegroundColor Cyan
Write-Host "✅ Organized documentation into docs/" -ForegroundColor Green
Write-Host "✅ Organized tests into tests/" -ForegroundColor Green  
Write-Host "✅ Organized scripts into scripts/" -ForegroundColor Green
Write-Host "✅ Archived redundant files" -ForegroundColor Green
Write-Host "✅ Created structure documentation" -ForegroundColor Green

Write-Host "`n🎯 Key locations:" -ForegroundColor Yellow
Write-Host "📚 Documentation: docs/" -ForegroundColor White
Write-Host "🧪 Tests: tests/memory/" -ForegroundColor White
Write-Host "📜 Scripts: scripts/" -ForegroundColor White
Write-Host "📦 Archive: archive/" -ForegroundColor White

Write-Host "`n🚀 Your backend directory is now organized and clean!" -ForegroundColor Cyan
