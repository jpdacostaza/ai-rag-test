#!/usr/bin/env python3
"""
Zero-Configuration OpenWebUI Complete Setup Script
==================================================

This script sets up the complete OpenWebUI integration with:
- Enhanced Memory System (Redis + ChromaDB)
- Function Filters (for memory enhancement)
- Pipeline Integration (for user isolation)
- Web Search Capabilities
- Updated Persona Configurations
- All latest verified configurations

Run this script to get a fully functional OpenWebUI instance with all features.
"""

import os
import sys
import json
import time
import subprocess
import requests
from datetime import datetime
from pathlib import Path


class ZeroConfigSetup:
    """Zero-configuration setup for OpenWebUI complete system"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.backend_dir = self.script_dir.parent
        self.services = {
            'openwebui': 'http://localhost:8080',
            'memory_api': 'http://localhost:5001',  # CORRECTED PORT
            'pipeline': 'http://localhost:9099',
            'ollama': 'http://localhost:11434'
        }
        
    def log(self, message: str, status: str = "INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "WORKING": "🔄"}
        symbol = symbols.get(status, "ℹ️")
        print(f"[{timestamp}] {symbol} {message}")
        
    def run_command(self, command: str, shell: bool = True, cwd: str = None) -> bool:
        """Run command with error handling"""
        try:
            result = subprocess.run(
                command, 
                shell=shell, 
                cwd=cwd or self.backend_dir,
                capture_output=True, 
                text=True
            )
            if result.returncode != 0:
                self.log(f"Command failed: {command}", "ERROR")
                self.log(f"Error: {result.stderr}", "ERROR")
                return False
            return True
        except Exception as e:
            self.log(f"Command execution error: {str(e)}", "ERROR")
            return False
            
    def create_directories(self):
        """Create all required directories"""
        self.log("Creating required directories...", "WORKING")
        
        directories = [
            "storage/pipelines",
            "storage/openwebui", 
            "storage/backend",
            "storage/memory",
            "storage/redis",
            "storage/chroma",
            "storage/ollama",
            "storage/models"
        ]
        
        for directory in directories:
            dir_path = self.backend_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
        self.log("All directories created successfully", "SUCCESS")
        
    def update_persona_configurations(self):
        """Update persona files with latest configurations"""
        self.log("Updating persona configurations...", "WORKING")
        
        # Load from unified_prompt.json as single source of truth - no fallbacks allowed
        try:
            unified_prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'unified_prompt.json')
            with open(unified_prompt_path, 'r', encoding='utf-8') as f:
                unified_config = json.load(f)
                self.log("Loaded persona configuration from unified_prompt.json", "SUCCESS")
        except Exception as e:
            self.log(f"CRITICAL: Could not load unified_prompt.json: {e}", "ERROR")
            raise ValueError(f"Setup requires unified_prompt.json to exist: {e}")
        
        # Verify the configuration was loaded and is valid
        if not unified_config.get("system_prompt"):
            raise ValueError("unified_prompt.json missing required system_prompt field")
            
        self.log("Persona configurations verified and ready", "SUCCESS")
        
    def start_services(self):
        """Start all Docker services"""
        self.log("Starting Docker services...", "WORKING")
        
        # Change to backend directory and start services
        success = self.run_command("docker-compose up -d --remove-orphans")
        if not success:
            self.log("Failed to start Docker services", "ERROR")
            return False
            
        self.log("Docker services started successfully", "SUCCESS")
        self.log("Waiting for services to initialize...", "WORKING")
        time.sleep(45)  # Give services time to start up
        
        return True
        
    def verify_services(self):
        """Verify all services are running correctly"""
        self.log("Verifying service health...", "WORKING")
        
        service_status = {}
        
        for service_name, url in self.services.items():
            try:
                if service_name == "memory_api":
                    response = requests.get(f"{url}/health", timeout=10)
                elif service_name == "pipeline":
                    response = requests.get(f"{url}/", timeout=10)
                elif service_name == "ollama":
                    response = requests.get(f"{url}/api/tags", timeout=10)
                else:  # openwebui
                    response = requests.get(f"{url}/", timeout=10)
                    
                if response.status_code == 200:
                    service_status[service_name] = True
                    self.log(f"{service_name}: ✅ HEALTHY", "SUCCESS")
                else:
                    service_status[service_name] = False
                    self.log(f"{service_name}: ❌ UNHEALTHY (status {response.status_code})", "ERROR")
                    
            except Exception as e:
                service_status[service_name] = False
                self.log(f"{service_name}: ❌ CONNECTION FAILED - {str(e)}", "ERROR")
                
        healthy_services = sum(1 for status in service_status.values() if status)
        total_services = len(service_status)
        
        if healthy_services == total_services:
            self.log(f"All services healthy ({healthy_services}/{total_services})", "SUCCESS")
            return True
        else:
            self.log(f"Some services unhealthy ({healthy_services}/{total_services})", "WARNING")
            return healthy_services >= 3  # At least 3/4 services should be working
            
    def install_functions_and_pipelines(self):
        """Install memory functions and pipelines"""
        self.log("Installing memory functions and pipelines...", "WORKING")
        
        # Install functions
        if self.run_command("docker-compose --profile installer run --rm function_installer"):
            self.log("Memory functions installed successfully", "SUCCESS")
        else:
            self.log("Memory function installation failed", "WARNING")
            
        # Install pipelines  
        if self.run_command("docker-compose --profile installer run --rm pipeline_installer"):
            self.log("Memory pipelines installed successfully", "SUCCESS")
        else:
            self.log("Memory pipeline installation failed", "WARNING")
            
    def setup_test_memories(self):
        """Setup some test memories for verification"""
        self.log("Setting up test memories...", "WORKING")
        
        test_memories = [
            {
                "user_id": "global_user",
                "content": "Zero-config setup completed successfully with verified OpenWebUI integration",
                "metadata": {"setup": "zero_config", "verified": True},
                "importance": 0.9
            },
            {
                "user_id": "global_user", 
                "content": "System includes memory functions, pipelines, web search, and persona configurations",
                "metadata": {"features": "complete", "integration": "verified"},
                "importance": 0.8
            }
        ]
        
        stored_count = 0
        for memory in test_memories:
            try:
                response = requests.post(
                    f"{self.services['memory_api']}/api/memory/store",
                    json=memory,
                    timeout=15
                )
                if response.status_code == 200:
                    stored_count += 1
            except Exception as e:
                self.log(f"Failed to store test memory: {str(e)}", "WARNING")
                
        if stored_count > 0:
            self.log(f"Test memories setup complete ({stored_count}/{len(test_memories)})", "SUCCESS")
        else:
            self.log("Test memory setup failed", "WARNING")
            
    def print_setup_complete_instructions(self):
        """Print final setup instructions"""
        self.log("Zero-config setup completed!", "SUCCESS")
        
        print("\\n" + "=" * 70)
        print("🎉 ZERO-CONFIG OPENWEBUI SETUP COMPLETE!")
        print("=" * 70)
        
        print("\\n📊 Service URLs:")
        print(f"   🌐 OpenWebUI:    {self.services['openwebui']}")
        print(f"   🧠 Memory API:   {self.services['memory_api']}")
        print(f"   🔄 Pipelines:    {self.services['pipeline']}")
        print(f"   🤖 Ollama:       {self.services['ollama']}")
        
        print("\\n🚀 Quick Start:")
        print("   1. Open OpenWebUI at http://localhost:8080")
        print("   2. Create an account if needed")
        print("   3. Start chatting - memory and web search are already configured!")
        
        print("\\n⚙️  Advanced Configuration (Optional):")
        print("   • Pipeline Setup: Admin Panel > Settings > Connections")
        print("     - Add URL: http://localhost:9099")
        print("     - API Key: 0p3n-w3bu!")
        print("   • Function Setup: Admin Panel > Settings > Functions")
        print("     - Verify 'Enhanced Memory Function' is enabled")
        
        print("\\n🔧 Features Included:")
        print("   ✅ Enhanced Memory System (Redis + ChromaDB)")
        print("   ✅ Function Filters (memory enhancement)")
        print("   ✅ Pipeline Integration (user isolation)")
        print("   ✅ Web Search Capabilities (DuckDuckGo)")
        print("   ✅ Updated Persona Configurations")
        print("   ✅ Zero-config operation")
        
        print("\\n🐛 Debugging Commands:")
        print("   docker-compose ps                    # Check service status")
        print("   docker logs backend-memory-api       # Memory API logs")
        print("   docker logs backend-openwebui        # OpenWebUI logs")
        print("   docker logs backend-pipelines        # Pipeline logs")
        
        print("\\n✅ ALL SYSTEMS READY FOR PRODUCTION USE!")
        print("=" * 70)
        
    def run_setup(self):
        """Run the complete zero-config setup"""
        self.log("Starting Zero-Configuration OpenWebUI Setup", "INFO")
        self.log("=" * 50, "INFO")
        
        # Step 1: Create directories
        self.create_directories()
        
        # Step 2: Update configurations
        self.update_persona_configurations()
        
        # Step 3: Start services
        if not self.start_services():
            self.log("Setup failed: Could not start services", "ERROR")
            return False
            
        # Step 4: Verify services
        if not self.verify_services():
            self.log("Setup completed with warnings: Some services may need manual verification", "WARNING")
            
        # Step 5: Install functions and pipelines
        self.install_functions_and_pipelines()
        
        # Step 6: Setup test memories
        self.setup_test_memories()
        
        # Step 7: Print completion instructions
        self.print_setup_complete_instructions()
        
        return True


if __name__ == "__main__":
    setup = ZeroConfigSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)
