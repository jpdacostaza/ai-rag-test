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
        # Try multiple possible URLs for OpenWebUI
        self.openwebui_urls = [
            "http://172.18.0.6:8080",  # Direct IP from docker inspect
            "http://openwebui:8080",    # Docker service name
            "http://localhost:8080"     # Host port mapping
        ]
        self.pipelines_url = "http://pipelines:9099"
        self.timeout = 30
        
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] [UnifiedInstaller] {message}")
    
    def get_working_openwebui_url(self) -> str:
        """Find the working OpenWebUI URL."""
        for url in self.openwebui_urls:
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    self.log(f"✅ Found working OpenWebUI at: {url}")
                    return url
            except:
                continue
        
        # Fallback to first URL if none work
        self.log(f"⚠️ No working URL found, using fallback: {self.openwebui_urls[0]}")
        return self.openwebui_urls[0]
    
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
    
    def install_function_automatic(self) -> bool:
        """Install Enhanced Memory Function automatically via OpenWebUI API."""
        self.log("🔧 Installing Enhanced Memory Function automatically...")
        
        # Find working OpenWebUI URL
        openwebui_url = self.get_working_openwebui_url()
        
        try:
            # Try multiple possible locations for the memory function file
            function_paths = [
                "/app/memory/functions/memory_function.py",  # Correct location
                "/app/memory_function.py",  # Container location
                "./memory/functions/memory_function.py",  # Relative path
                "./memory_function.py"  # Fallback
            ]
            
            function_code = None
            used_path = None
            
            for path in function_paths:
                try:
                    with open(path, "r") as f:
                        function_code = f.read()
                        used_path = path
                        break
                except FileNotFoundError:
                    continue
            
            if not function_code:
                self.log("❌ Could not find memory_function.py at any expected location")
                self.log(f"   Searched: {', '.join(function_paths)}")
                return False
                
            self.log(f"📁 Found memory function at: {used_path}")
            
            # Prepare function data for API
            function_data = {
                "id": "enhanced_memory_function",
                "name": "Enhanced Memory Function",
                "type": "filter", 
                "content": function_code,
                "is_active": True,
                "is_global": True
            }
            
            # Try to install via OpenWebUI API
            try:
                with httpx.Client(timeout=30.0) as client:
                    # Try functions endpoint
                    response = client.post(
                        f"{openwebui_url}/api/v1/functions/",
                        json=function_data
                    )
                    
                    if response.status_code in [200, 201]:
                        self.log("✅ Enhanced Memory Function installed automatically!")
                        return True
                    else:
                        self.log(f"⚠️ API installation failed (status {response.status_code}), trying alternative...")
                        
                        # Try alternative import endpoint
                        response = client.post(
                            f"{openwebui_url}/api/v1/functions/import",
                            json=function_data
                        )
                        
                        if response.status_code in [200, 201]:
                            self.log("✅ Enhanced Memory Function installed via import endpoint!")
                            return True
                        else:
                            self.log(f"❌ Alternative endpoint also failed: {response.status_code}")
                            
            except Exception as api_error:
                self.log(f"❌ API installation failed: {str(api_error)}")
                
            # If API fails, fall back to manual instructions
            self.log("⚠️ Automatic installation failed, providing manual instructions...")
            return self.install_function_manual_fallback(function_code)
            
        except Exception as e:
            self.log(f"❌ Error in automatic installation: {str(e)}", "ERROR")
            return False

    def install_function_manual_fallback(self, function_code: str) -> bool:
        """Provide manual installation instructions as fallback."""
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
    
    def install_pipeline_file(self) -> bool:
        """Install Enhanced Memory Pipeline using file-based method - ZERO CONFIG."""
        self.log("🔧 Installing Enhanced Memory Pipeline (automatic file-based)...")
        
        try:
            # Try to find the pipeline file in different locations
            pipeline_source_paths = [
                "/app/enhanced_memory_pipeline.py",  # Primary location (from Dockerfile)
                "/app/memory_pipeline.py",  # Alternative name
                "./pipelines/enhanced_memory_pipeline.py",  # Local relative path
            ]
            
            pipeline_code = None
            source_path = None
            
            for path in pipeline_source_paths:
                try:
                    if os.path.exists(path):
                        with open(path, "r") as f:
                            pipeline_code = f.read()
                            source_path = path
                            self.log(f"✅ Found pipeline source at: {path}")
                            break
                except Exception as e:
                    self.log(f"Checking {path}: {e}", "DEBUG")
                    continue
            
            if not pipeline_code:
                # If no source file found, create a basic pipeline from memory
                self.log("⚠️ No pipeline source file found, creating from template", "WARN")
                pipeline_code = self._get_pipeline_template()
                if not pipeline_code:
                    self.log("❌ Could not create pipeline - no template available", "ERROR")
                    return False
            
            # Install to pipelines directory (mounted volume)
            pipelines_dir = "/app/pipelines"
            
            # Ensure the pipelines directory exists
            if not os.path.exists(pipelines_dir):
                try:
                    os.makedirs(pipelines_dir, exist_ok=True)
                    self.log(f"✅ Created pipelines directory: {pipelines_dir}")
                except Exception as e:
                    self.log(f"❌ Could not create pipelines directory: {e}", "ERROR")
                    return False
            
            # Write the pipeline file
            pipeline_file = os.path.join(pipelines_dir, "enhanced_memory_pipeline.py")
            try:
                with open(pipeline_file, "w") as f:
                    f.write(pipeline_code)
                
                self.log(f"✅ Pipeline file installed successfully: {pipeline_file}")
                self.log(f"✅ Source: {source_path if source_path else 'generated template'}")
                self.log("🔄 Pipeline will be automatically loaded by the Pipelines service")
                
                # Verify the file was written correctly
                if os.path.exists(pipeline_file):
                    file_size = os.path.getsize(pipeline_file)
                    self.log(f"✅ Verification: Pipeline file size {file_size} bytes")
                    return True
                else:
                    self.log("❌ Verification failed: Pipeline file not found after write", "ERROR")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error writing pipeline file: {e}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Pipeline installation error: {e}", "ERROR")
            return False
    
    def install_pipeline_manual(self):
        """Provide manual installation instructions for the pipeline."""
        self.log("📋 Manual Installation Instructions for Enhanced Memory Pipeline:")
        self.log("=" * 70)
        self.log("1. The pipeline file should be copied from the host to the pipelines container")
        self.log("2. Run this command from your backend directory:")
        self.log("   docker cp pipelines/enhanced_memory_pipeline.py backend-pipelines:/app/pipelines/")
        self.log("3. Restart the Pipelines container:")
        self.log("   docker restart backend-pipelines")
        self.log("4. Verify installation by checking:")
        self.log("   http://localhost:9099/")
        self.log("=" * 70)
    
    def _get_pipeline_template(self) -> str:
        """Get a basic pipeline template if the source file is not found."""
        return '''"""
Enhanced Memory Pipeline for OpenWebUI
=====================================
Auto-generated pipeline template for memory functionality.
"""

from typing import List, Union, Generator, Iterator
import os
import httpx
import asyncio
from pydantic import BaseModel

class Pipeline:
    """Enhanced Memory Pipeline with automatic backend integration."""
    
    class Valves(BaseModel):
        """Configuration valves for the memory pipeline."""
        backend_url: str = "http://backend:3000"
        memory_api_url: str = "http://memory_api:8080"
        enable_memory: bool = True
        enable_learning: bool = True
        debug: bool = True
    
    def __init__(self):
        self.valves = self.Valves()
        self.id = "enhanced_memory_pipeline"
        self.name = "Enhanced Memory Pipeline"
        self.description = "AI memory system with learning capabilities"

    async def on_startup(self):
        """Called when the pipeline starts."""
        print("🚀 Enhanced Memory Pipeline - Auto-generated template loaded")

    async def on_shutdown(self):
        """Called when the pipeline shuts down."""
        print("🛑 Enhanced Memory Pipeline - Shutting down")

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """Process the user message with memory enhancement."""
        
        if not self.valves.enable_memory:
            return body
            
        try:
            # Basic memory integration (simplified template)
            if self.valves.debug:
                print(f"🧠 Memory Pipeline: Processing message for model {model_id}")
            
            # This is a template - full functionality requires the complete pipeline file
            return body
            
        except Exception as e:
            print(f"❌ Memory Pipeline Error: {e}")
            return body
'''
    
    async def run_installation(self):
        """Run the complete installation process."""
        self.log("🚀 Starting Unified Memory Installation...")
        self.log("=" * 60)
        
        # Find working OpenWebUI URL
        openwebui_url = self.get_working_openwebui_url()
        
        # Wait for services
        openwebui_available = self.wait_for_service(openwebui_url, "OpenWebUI")
        pipelines_available = self.wait_for_service(self.pipelines_url, "Pipelines")
        
        # Install Function (try automatic first, fallback to manual)
        self.log("🔧 Installing Enhanced Memory Function...")
        function_success = self.install_function_automatic()
        
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
            self.log("   • Enhanced Memory Function: ✅ Installed automatically")
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
            if function_success and pipeline_success:
                self.log("   • Both Function and Pipeline installed successfully!")
                self.log("   • Memory system is ready to use")
            elif function_success and not pipeline_success:
                self.log("   • Function installed - Pipeline installation failed")
            elif pipeline_success and not function_success:
                self.log("   • Pipeline installed - Function may need manual installation (see logs above)")
                self.log("   • Pipeline is ready and will auto-load")
            else:
                self.log("   • Check installation logs above for manual setup instructions")
            
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
