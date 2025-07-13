#!/usr/bin/env python3
"""
Pipeline Management Tool
========================

Manages deployment of different pipeline versions (monolithic vs modular).
"""

import os
import shutil
import sys
import argparse
from pathlib import Path

# Import error handling patterns for script reliability
try:
    from utilities.error_patterns import handle_service_errors
    ERROR_PATTERNS_AVAILABLE = True
except ImportError:
    ERROR_PATTERNS_AVAILABLE = False
    # Fallback decorator for standalone script usage
    def handle_service_errors(func):
        return func


class PipelineManager:
    """Manages pipeline deployments and configurations."""
    
    def __init__(self):
        self.root_dir = Path.cwd()
        self.storage_pipelines = self.root_dir / "storage" / "pipelines"
        self.modular_pipelines = self.root_dir / "pipelines"
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with consistent formatting."""
        print(f"[PIPELINE MANAGER {level}] {message}")
    
    def list_available_pipelines(self):
        """List all available pipeline implementations."""
        self.log("Available Pipeline Implementations:")
        self.log("=" * 50)
        
        # Check monolithic pipeline
        monolithic_path = self.storage_pipelines / "enhanced_memory_pipeline.py"
        if monolithic_path.exists():
            size = monolithic_path.stat().st_size
            self.log(f"✅ Monolithic: {monolithic_path} ({size:,} bytes)")
        else:
            self.log("❌ Monolithic: Not found")
        
        # Check modular pipeline
        modular_path = self.modular_pipelines / "enhanced_memory_pipeline_modular.py"
        if modular_path.exists():
            size = modular_path.stat().st_size
            self.log(f"✅ Modular: {modular_path} ({size:,} bytes)")
            
            # List modular components
            memory_system_path = self.modular_pipelines / "memory_system"
            if memory_system_path.exists():
                self.log("   📁 Modular Components:")
                for component in memory_system_path.glob("*.py"):
                    if component.name != "__init__.py":
                        comp_size = component.stat().st_size
                        self.log(f"      • {component.name}: {comp_size:,} bytes")
        else:
            self.log("❌ Modular: Not found")
    
    @handle_service_errors
    def deploy_monolithic(self):
        """Deploy the monolithic pipeline version."""
        try:
            source = self.storage_pipelines / "enhanced_memory_pipeline.py"
            if not source.exists():
                self.log("❌ Monolithic pipeline not found", "ERROR")
                return False
            
            self.log("🚀 Deploying Monolithic Pipeline...")
            self.log(f"📁 Source: {source}")
            self.log("✅ Monolithic pipeline is already active in storage/pipelines/")
            self.log("💡 To activate: Restart the pipelines service")
            return True
            
        except Exception as e:
            self.log(f"❌ Error deploying monolithic pipeline: {e}", "ERROR")
            return False
    
    @handle_service_errors
    def deploy_modular(self):
        """Deploy the modular pipeline version."""
        try:
            # Check if modular pipeline exists
            modular_source = self.modular_pipelines / "enhanced_memory_pipeline_modular.py"
            memory_system_source = self.modular_pipelines / "memory_system"
            
            if not modular_source.exists():
                self.log("❌ Modular pipeline not found", "ERROR")
                return False
            
            if not memory_system_source.exists():
                self.log("❌ Memory system components not found", "ERROR")
                return False
            
            self.log("🚀 Deploying Modular Pipeline...")
            
            # Copy modular pipeline to storage/pipelines
            target = self.storage_pipelines / "enhanced_memory_pipeline.py"
            shutil.copy2(modular_source, target)
            self.log(f"📁 Copied main pipeline: {modular_source} -> {target}")
            
            # Copy memory system components
            target_memory_system = self.storage_pipelines / "memory_system"
            if target_memory_system.exists():
                shutil.rmtree(target_memory_system)
            shutil.copytree(memory_system_source, target_memory_system)
            self.log(f"📁 Copied memory system: {memory_system_source} -> {target_memory_system}")
            
            self.log("✅ Modular pipeline deployed successfully!")
            self.log("💡 To activate: Restart the pipelines service")
            return True
            
        except Exception as e:
            self.log(f"❌ Error deploying modular pipeline: {e}", "ERROR")
            return False
    
    def show_pipeline_structure(self):
        """Show the current pipeline directory structure."""
        self.log("Current Pipeline Structure:")
        self.log("=" * 40)
        
        # Show storage/pipelines structure
        self.log("📁 storage/pipelines/ (Active Deployment):")
        if self.storage_pipelines.exists():
            for item in sorted(self.storage_pipelines.rglob("*")):
                if item.is_file() and item.suffix == ".py":
                    rel_path = item.relative_to(self.storage_pipelines)
                    size = item.stat().st_size
                    self.log(f"   📄 {rel_path} ({size:,} bytes)")
        
        # Show pipelines structure
        self.log("\n📁 pipelines/ (Modular Source):")
        if self.modular_pipelines.exists():
            for item in sorted(self.modular_pipelines.rglob("*")):
                if item.is_file() and item.suffix == ".py":
                    rel_path = item.relative_to(self.modular_pipelines)
                    size = item.stat().st_size
                    self.log(f"   📄 {rel_path} ({size:,} bytes)")
    
    def compare_implementations(self):
        """Compare monolithic vs modular implementations."""
        self.log("Pipeline Implementation Comparison:")
        self.log("=" * 50)
        
        # Get file sizes
        monolithic_path = self.storage_pipelines / "enhanced_memory_pipeline.py"
        modular_main = self.modular_pipelines / "enhanced_memory_pipeline_modular.py"
        memory_system_dir = self.modular_pipelines / "memory_system"
        
        mono_size = monolithic_path.stat().st_size if monolithic_path.exists() else 0
        
        modular_size = 0
        if modular_main.exists():
            modular_size += modular_main.stat().st_size
        if memory_system_dir.exists():
            for component in memory_system_dir.glob("*.py"):
                modular_size += component.stat().st_size
        
        self.log(f"📊 Monolithic: {mono_size:,} bytes (1 file)")
        self.log(f"📊 Modular: {modular_size:,} bytes (multiple files)")
        self.log(f"📊 Size Difference: {modular_size - mono_size:+,} bytes")
        
        self.log("\n🔍 Advantages:")
        self.log("Monolithic:")
        self.log("  ✅ Single file deployment")
        self.log("  ✅ No import dependencies")
        self.log("  ✅ Simpler debugging")
        
        self.log("Modular:")
        self.log("  ✅ Better code organization")
        self.log("  ✅ Easier to maintain/extend")
        self.log("  ✅ Component-based debugging")
        self.log("  ✅ Reusable components")
        self.log("  ✅ Better separation of concerns")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Pipeline Management Tool")
    parser.add_argument("action", choices=[
        "list", "deploy-mono", "deploy-modular", "structure", "compare"
    ], help="Action to perform")
    
    args = parser.parse_args()
    
    manager = PipelineManager()
    
    if args.action == "list":
        manager.list_available_pipelines()
    elif args.action == "deploy-mono":
        success = manager.deploy_monolithic()
        sys.exit(0 if success else 1)
    elif args.action == "deploy-modular":
        success = manager.deploy_modular()
        sys.exit(0 if success else 1)
    elif args.action == "structure":
        manager.show_pipeline_structure()
    elif args.action == "compare":
        manager.compare_implementations()


if __name__ == "__main__":
    main()
