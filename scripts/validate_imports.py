#!/usr/bin/env python3
"""
Import Validation Script
Validates that all imports are working correctly after reorganization.
"""

import sys
import os
import importlib
from pathlib import Path

class ImportValidator:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.failed_imports = []
        self.successful_imports = []
        
    def test_import(self, module_name: str, description: str = ""):
        """Test if a module can be imported successfully"""
        try:
            module = importlib.import_module(module_name)
            self.successful_imports.append((module_name, description))
            print(f"✅ {module_name} - {description}")
            return True
        except Exception as e:
            self.failed_imports.append((module_name, str(e), description))
            print(f"❌ {module_name} - {description}: {e}")
            return False
    
    def validate_core_modules(self):
        """Validate core application modules"""
        print("\n🔧 Testing Core Modules...")
        
        # Core modules
        self.test_import("core.startup", "Application startup")
        self.test_import("core.main", "Main FastAPI application")
        self.test_import("core.error_handler", "Error handling")
        self.test_import("core.human_logging", "Logging system")
        
    def validate_config_modules(self):
        """Validate configuration modules"""
        print("\n⚙️  Testing Configuration Modules...")
        
        self.test_import("config.config_unified", "Unified configuration")
        self.test_import("config.pipeline_config", "Pipeline configuration")
        
    def validate_service_modules(self):
        """Validate service modules"""
        print("\n🔧 Testing Service Modules...")
        
        self.test_import("services.database_manager", "Database management")
        self.test_import("services.llm_service", "LLM service")
        self.test_import("services.memory_service", "Memory service")
        self.test_import("services.storage_manager", "Storage management")
        self.test_import("services.model_manager", "Model management")
        
    def validate_utility_modules(self):
        """Validate utility modules"""
        print("\n🛠️  Testing Utility Modules...")
        
        self.test_import("utilities.connection_factory", "Connection factory")
        self.test_import("utilities.cache_manager", "Cache management")
        self.test_import("utilities.error_patterns", "Error patterns")
        self.test_import("utilities.web_search_tool", "Web search tool")
        self.test_import("utilities.watchdog", "System watchdog")
        self.test_import("utilities.rag", "RAG utilities")
        
    def validate_route_modules(self):
        """Validate route modules"""
        print("\n🌐 Testing Route Modules...")
        
        self.test_import("routes.health", "Health endpoints")
        self.test_import("routes.chat", "Chat endpoints")
        self.test_import("routes.models", "Model endpoints")
        self.test_import("routes.upload", "Upload endpoints")
        
    def validate_model_modules(self):
        """Validate model modules"""
        print("\n📊 Testing Model Modules...")
        
        self.test_import("models.models", "Data models")
        
    def validate_script_modules(self):
        """Validate script modules"""
        print("\n📜 Testing Script Modules...")
        
        self.test_import("scripts.enhanced_integration", "Enhanced integration")
        self.test_import("scripts.enhanced_web_search_trigger", "Web search trigger")
        
    def check_circular_imports(self):
        """Check for potential circular import issues"""
        print("\n🔄 Checking for Circular Imports...")
        
        # Try importing main modules that might have circular dependencies
        critical_modules = [
            "core.main",
            "services.database_manager", 
            "routes.health",
            "routes.chat"
        ]
        
        for module_name in critical_modules:
            self.test_import(module_name, f"Circular import check")
    
    def validate_dockerfile_compatibility(self):
        """Check if critical modules for Docker containers work"""
        print("\n🐳 Testing Docker Compatibility...")
        
        # Core modules needed for container startup
        docker_critical = [
            "core.startup",
            "services.database_manager",
            "utilities.connection_factory",
            "core.human_logging"
        ]
        
        for module_name in docker_critical:
            self.test_import(module_name, f"Docker critical module")
    
    def run_full_validation(self):
        """Run complete import validation"""
        print("🚀 Starting Import Validation...")
        print("=" * 60)
        
        # Add the root directory to Python path
        sys.path.insert(0, str(self.root_dir))
        
        # Run all validation tests
        self.validate_core_modules()
        self.validate_config_modules()
        self.validate_service_modules()
        self.validate_utility_modules()
        self.validate_route_modules()
        self.validate_model_modules()
        self.validate_script_modules()
        self.check_circular_imports()
        self.validate_dockerfile_compatibility()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("📋 IMPORT VALIDATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.successful_imports) + len(self.failed_imports)
        success_rate = (len(self.successful_imports) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Successful imports: {len(self.successful_imports)}")
        print(f"❌ Failed imports: {len(self.failed_imports)}")
        print(f"📊 Success rate: {success_rate:.1f}%")
        
        if self.failed_imports:
            print("\n🚨 Failed Imports:")
            for module_name, error, description in self.failed_imports:
                print(f"  • {module_name}: {error}")
        
        print("\n✅ Import validation complete!")
        
        # Return success status
        return len(self.failed_imports) == 0

if __name__ == "__main__":
    root_directory = sys.argv[1] if len(sys.argv) > 1 else "."
    
    validator = ImportValidator(root_directory)
    success = validator.run_full_validation()
    
    sys.exit(0 if success else 1)
