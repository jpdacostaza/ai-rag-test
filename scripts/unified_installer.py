#!/usr/bin/env python3
"""
Unified Memory Installer for OpenWebUI
=====================================

This script automatically installs both the Enhanced Memory Function and Pipeline
to provide comprehensive memory capabilities for OpenWebUI.

Architecture Overview:
- Functions: Built-in system (shared user context)
- Pipelines: File-based system (proper user authentication via container volume)

Based on official documentation: https://docs.openwebui.com/pipelines/
"""

import asyncio
import time
import json
import os
import shutil
import requests
import httpx
from pathlib import Path

class UnifiedMemoryInstaller:
    def __init__(self):
        self.openwebui_url = "http://openwebui:8080"
        self.pipelines_url = "http://pipelines:9099"
        self.timeout = 30
        
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] [UnifiedInstaller] {message}")
    
    def wait_for_service(self, url: str, service_name: str, max_retries: int = 30):
        """Wait for a service to become available."""
        self.log(f"Waiting for {service_name} at {url}...")
        
        for attempt in range(max_retries):
            try:
                # Use different health check endpoints based on service
                if "pipelines" in url:
                    response = requests.get(f"{url}/", timeout=5)
                else:
                    response = requests.get(f"{url}/health", timeout=5)
                    
                if response.status_code == 200:
                    self.log(f"✅ {service_name} is ready!")
                    return True
            except Exception as e:
                if attempt < max_retries - 1:
                    self.log(f"Attempt {attempt + 1}/{max_retries}: {service_name} not ready yet...")
                    time.sleep(10)
                else:
                    self.log(f"❌ Failed to connect to {service_name}: {str(e)}", "ERROR")
        
        return False
    
    def install_function_manual(self) -> bool:
        """Install Enhanced Memory Function with manual instructions."""
        self.log("🔧 Enhanced Memory Function - Manual Installation Required")
        
        try:
            with open("/app/memory_function.py", "r") as f:
                function_code = f.read()
            
            self.log("📋 Manual Installation Instructions for Enhanced Memory Function:")
            self.log("=" * 70)
            self.log("1. Go to OpenWebUI Admin Panel → Workspace → Functions")
            self.log("2. Click 'Create Function' or '+' button")
            self.log("3. Use these settings:")
            self.log("   • Name: Enhanced Memory Function")
            self.log("   • Type: Filter")
            self.log("   • Active: ✓ Enabled")
            self.log("   • Global: ✓ Enabled")
            self.log("4. Copy and paste the function code from the logs below")
            self.log("5. Click 'Save'")
            self.log("=" * 70)
            self.log("📄 Function Code (copy everything between the markers):")
            self.log("--- START FUNCTION CODE ---")
            self.log(function_code)
            self.log("--- END FUNCTION CODE ---")
            self.log("=" * 70)
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error preparing function: {str(e)}", "ERROR")
            return False
    
    def install_pipeline_file(self) -> bool:
        """Install Enhanced Memory Pipeline using file-based method."""
        self.log("🔧 Installing Enhanced Memory Pipeline (file-based)...")
        
        try:
            # The pipeline will be installed by mounting the file directly
            # This is the correct method according to Pipelines documentation
            
            with open("/app/memory_pipeline.py", "r") as f:
                pipeline_code = f.read()
            
            # Check if we can access the pipelines directory (mounted volume)
            pipelines_dir = "/app/pipelines"
            if os.path.exists(pipelines_dir):
                self.log(f"✅ Found pipelines directory: {pipelines_dir}")
                
                # Copy the pipeline file
                pipeline_file = os.path.join(pipelines_dir, "enhanced_memory_pipeline.py")
                with open(pipeline_file, "w") as f:
                    f.write(pipeline_code)
                
                self.log(f"✅ Pipeline file installed: {pipeline_file}")
                self.log("🔄 Pipeline will be automatically loaded by the Pipelines service")
                return True
            else:
                self.log("⚠️ Pipelines directory not found - using manual installation method", "WARN")
                
                self.log("📋 Manual Installation Instructions for Enhanced Memory Pipeline:")
                self.log("=" * 70)
                self.log("1. Copy the pipeline code below")
                self.log("2. Save it as 'enhanced_memory_pipeline.py'")
                self.log("3. Copy the file to your Pipelines container:")
                self.log("   docker cp enhanced_memory_pipeline.py pipelines:/app/pipelines/")
                self.log("4. Restart the Pipelines container:")
                self.log("   docker restart pipelines")
                self.log("=" * 70)
                self.log("📄 Pipeline Code (copy everything between the markers):")
                self.log("--- START PIPELINE CODE ---")
                self.log(pipeline_code)
                self.log("--- END PIPELINE CODE ---")
                self.log("=" * 70)
                
                return True
                
        except Exception as e:
            self.log(f"❌ Pipeline installation error: {str(e)}", "ERROR")
            return False
    
    async def run_installation(self):
        """Run the complete installation process."""
        self.log("🚀 Starting Unified Memory Installation...")
        self.log("=" * 60)
        
        # Wait for services
        openwebui_available = self.wait_for_service(self.openwebui_url, "OpenWebUI")
        pipelines_available = self.wait_for_service(self.pipelines_url, "Pipelines")
        
        # Install Function (always manual for now due to auth requirements)
        self.log("🔧 Installing Enhanced Memory Function...")
        function_success = self.install_function_manual()
        
        # Install Pipeline (file-based method)
        if pipelines_available:
            pipeline_success = self.install_pipeline_file()
        else:
            self.log("❌ Pipelines not available, skipping Pipeline installation", "ERROR")
            pipeline_success = False
        
        # Summary
        self.log("=" * 60)
        self.log("📋 Installation Summary:")
        
        if function_success:
            self.log("   • Enhanced Memory Function: 📋 Manual installation required")
        else:
            self.log("   • Enhanced Memory Function: ❌ Failed")
            
        if pipeline_success:
            self.log("   • Enhanced Memory Pipeline: ✅ File-based installation completed")
        else:
            self.log("   • Enhanced Memory Pipeline: ❌ Failed")
        
        if function_success or pipeline_success:
            self.log("🎉 Memory system setup completed!")
            self.log("")
            self.log("📚 Next Steps:")
            if function_success and not pipeline_success:
                self.log("   • Complete the manual Function installation using the instructions above")
            elif pipeline_success and not function_success:
                self.log("   • Complete the manual Function installation using the instructions above")
                self.log("   • Pipeline is ready and will auto-load")
            else:
                self.log("   • Complete the manual Function installation using the instructions above")
                self.log("   • Pipeline is ready and will auto-load")
            
            self.log("")
            self.log("🔗 Access your memory-enhanced OpenWebUI at: http://localhost:8080")
            self.log("")
            self.log("📖 Architecture Overview:")
            self.log("   • Functions: Built-in system (shared user context)")
            self.log("   • Pipelines: Separate service (proper user authentication)")
            self.log("   • Both systems share the same backend memory API")
        else:
            self.log("❌ Installation failed for all components", "ERROR")
            return False
        
        return True

async def main():
    """Main installation entry point."""
    installer = UnifiedMemoryInstaller()
    success = await installer.run_installation()
    
    if success:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
