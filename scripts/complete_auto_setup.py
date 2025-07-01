#!/usr/bin/env python3
"""
Complete Auto-Setup System
==========================

This script automatically:
1. Downloads the default model (llama3.2:3b) if not present
2. Installs the memory function as a global function in OpenWebUI
3. Configures all necessary settings without manual intervention
4. Uses database direct access to bypass authentication restrictions

No manual configuration required - fully automated setup.
"""

import os
import sys
import time
import json
import sqlite3
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configuration
OLLAMA_API = "http://ollama:11434"
OPENWEBUI_API = "http://openwebui:8080"
MEMORY_API = "http://memory_api:8000"
DEFAULT_MODEL = "llama3.2:3b"
MAX_RETRIES = 10
RETRY_DELAY = 30
FUNCTION_CODE_PATH = "/app/memory_function.py"
OPENWEBUI_DB_PATH = "/app/backend/data/webui.db"

class Logger:
    """Enhanced logging with timestamps and colors."""
    
    @staticmethod
    def log(message: str, level: str = "INFO"):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        emoji = {
            "INFO": "📝",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🔍"
        }.get(level, "📝")
        print(f"[{timestamp}] {emoji} [{level}] {message}")

class ModelManager:
    """Manages Ollama model operations."""
    
    def __init__(self):
        self.logger = Logger()
        
    def wait_for_ollama(self) -> bool:
        """Wait for Ollama service to be ready."""
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(f"{OLLAMA_API}/api/tags", timeout=10)
                if response.status_code == 200:
                    self.logger.log("Ollama service is ready", "SUCCESS")
                    return True
            except Exception as e:
                self.logger.log(f"Ollama not ready (attempt {attempt + 1}/{MAX_RETRIES}): {e}", "WARNING")
                time.sleep(RETRY_DELAY)
        
        self.logger.log("Ollama service failed to start", "ERROR")
        return False
    
    def check_model_exists(self, model_name: str) -> bool:
        """Check if model exists in Ollama."""
        try:
            response = requests.get(f"{OLLAMA_API}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                for model in models:
                    if model.get("name") == model_name:
                        self.logger.log(f"Model {model_name} already exists", "SUCCESS")
                        return True
            return False
        except Exception as e:
            self.logger.log(f"Error checking model: {e}", "ERROR")
            return False
    
    def download_model(self, model_name: str) -> bool:
        """Download model if not present."""
        if self.check_model_exists(model_name):
            return True
            
        self.logger.log(f"Downloading model: {model_name}", "INFO")
        
        try:
            response = requests.post(
                f"{OLLAMA_API}/api/pull",
                json={"name": model_name},
                timeout=1800,  # 30 minutes timeout
                stream=True
            )
            
            if response.status_code == 200:
                # Monitor download progress
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'status' in data:
                                self.logger.log(f"Download progress: {data['status']}", "INFO")
                            if data.get('status') == 'success':
                                self.logger.log(f"Model {model_name} downloaded successfully", "SUCCESS")
                                return True
                        except json.JSONDecodeError:
                            continue
            
            self.logger.log(f"Failed to download model: {response.status_code}", "ERROR")
            return False
            
        except Exception as e:
            self.logger.log(f"Error downloading model: {e}", "ERROR")
            return False

class FunctionInstaller:
    """Manages OpenWebUI function installation via database."""
    
    def __init__(self):
        self.logger = Logger()
        
    def wait_for_openwebui(self) -> bool:
        """Wait for OpenWebUI service to be ready."""
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(f"{OPENWEBUI_API}/health", timeout=10)
                if response.status_code == 200:
                    self.logger.log("OpenWebUI service is ready", "SUCCESS")
                    return True
            except Exception as e:
                self.logger.log(f"OpenWebUI not ready (attempt {attempt + 1}/{MAX_RETRIES}): {e}", "WARNING")
                time.sleep(RETRY_DELAY)
        
        self.logger.log("OpenWebUI service failed to start", "ERROR")
        return False
    
    def read_function_code(self) -> Optional[str]:
        """Read the memory function code."""
        try:
            with open(FUNCTION_CODE_PATH, 'r') as f:
                code = f.read()
                self.logger.log("Function code loaded successfully", "SUCCESS")
                return code
        except Exception as e:
            self.logger.log(f"Error reading function code: {e}", "ERROR")
            return None
    
    def install_function_via_database(self, function_code: str) -> bool:
        """Install function directly via database access."""
        try:
            # Wait for database to be available
            db_path = Path(OPENWEBUI_DB_PATH)
            if not db_path.exists():
                self.logger.log("Database not found, waiting...", "WARNING")
                time.sleep(30)
                
            if not db_path.exists():
                self.logger.log("Database still not available", "ERROR")
                return False
            
            # Connect to database
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check if function already exists
            cursor.execute("SELECT id FROM function WHERE id = ?", ("memory_function",))
            if cursor.fetchone():
                self.logger.log("Memory function already installed", "SUCCESS")
                conn.close()
                return True
            
            # Create function entry
            function_data = {
                "id": "memory_function",
                "name": "Enhanced Memory Function",
                "type": "function",
                "content": function_code,
                "is_active": True,
                "is_global": True,
                "created_at": int(time.time()),
                "updated_at": int(time.time())
            }
            
            # Insert function
            cursor.execute("""
                INSERT INTO function (id, user_id, name, type, content, is_active, is_global, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                function_data["id"],
                "",  # Empty user_id for global functions
                function_data["name"],
                function_data["type"],
                function_data["content"],
                function_data["is_active"],
                function_data["is_global"],
                function_data["created_at"],
                function_data["updated_at"]
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.log("Memory function installed successfully via database", "SUCCESS")
            return True
            
        except Exception as e:
            self.logger.log(f"Database installation failed: {e}", "ERROR")
            return False
    
    def verify_function_installation(self) -> bool:
        """Verify function is properly installed."""
        try:
            db_path = Path(OPENWEBUI_DB_PATH)
            if not db_path.exists():
                return False
                
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, is_active, is_global 
                FROM function 
                WHERE id = 'memory_function'
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                self.logger.log(f"Function verified: {result}", "SUCCESS")
                return True
            else:
                self.logger.log("Function not found in database", "ERROR")
                return False
                
        except Exception as e:
            self.logger.log(f"Error verifying function: {e}", "ERROR")
            return False

class SystemSetup:
    """Main system setup coordinator."""
    
    def __init__(self):
        self.logger = Logger()
        self.model_manager = ModelManager()
        self.function_installer = FunctionInstaller()
    
    def wait_for_services(self) -> bool:
        """Wait for all required services to be ready."""
        self.logger.log("Waiting for services to be ready...", "INFO")
        
        services = [
            ("Ollama", self.model_manager.wait_for_ollama),
            ("OpenWebUI", self.function_installer.wait_for_openwebui)
        ]
        
        for service_name, wait_func in services:
            self.logger.log(f"Waiting for {service_name}...", "INFO")
            if not wait_func():
                self.logger.log(f"{service_name} failed to start", "ERROR")
                return False
        
        self.logger.log("All services are ready", "SUCCESS")
        return True
    
    def setup_model(self) -> bool:
        """Setup the default model."""
        self.logger.log(f"Setting up model: {DEFAULT_MODEL}", "INFO")
        return self.model_manager.download_model(DEFAULT_MODEL)
    
    def setup_function(self) -> bool:
        """Setup the memory function."""
        self.logger.log("Setting up memory function", "INFO")
        
        # Read function code
        function_code = self.function_installer.read_function_code()
        if not function_code:
            return False
        
        # Install function
        if self.function_installer.install_function_via_database(function_code):
            # Verify installation
            return self.function_installer.verify_function_installation()
        
        return False
    
    def run_complete_setup(self) -> bool:
        """Run the complete automated setup."""
        self.logger.log("🚀 Starting Complete Auto-Setup System", "INFO")
        
        # Wait for services
        if not self.wait_for_services():
            self.logger.log("Services not ready, setup failed", "ERROR")
            return False
        
        # Setup model
        if not self.setup_model():
            self.logger.log("Model setup failed", "ERROR")
            return False
        
        # Setup function
        if not self.setup_function():
            self.logger.log("Function setup failed", "ERROR")
            return False
        
        self.logger.log("🎉 Complete Auto-Setup finished successfully!", "SUCCESS")
        self.logger.log("✅ Model downloaded and available", "SUCCESS")
        self.logger.log("✅ Memory function installed and active", "SUCCESS")
        self.logger.log("✅ System ready for use without manual configuration", "SUCCESS")
        
        return True

def main():
    """Main entry point."""
    setup = SystemSetup()
    
    # Run setup with retries
    for attempt in range(3):
        if setup.run_complete_setup():
            sys.exit(0)
        else:
            setup.logger.log(f"Setup attempt {attempt + 1} failed, retrying...", "WARNING")
            time.sleep(60)
    
    setup.logger.log("All setup attempts failed", "ERROR")
    sys.exit(1)

if __name__ == "__main__":
    main()
