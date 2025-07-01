#!/usr/bin/env python3
"""
Integrated Memory API with Auto-Setup
====================================

This script provides an integrated approach that:
1. Starts the memory API service
2. Automatically downloads models via Ollama
3. Installs the memory function in OpenWebUI
4. Activates and validates the complete system
5. Runs as a single, reliable service

This eliminates the need for multiple setup containers and provides
a more robust, integrated solution.
"""

import os
import sys
import time
import json
import sqlite3
import asyncio
import threading
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

# Configuration
OLLAMA_API = "http://ollama:11434"
OPENWEBUI_API = "http://openwebui:8080"
OPENWEBUI_DB_PATH = "/tmp/openwebui/webui.db"
MEMORY_FUNCTION_PATH = "/app/memory/functions/memory_function.py"
DEFAULT_MODEL = "llama3.2:3b"
FALLBACK_MODELS = ["phi3:mini", "gemma2:2b"]
MAX_RETRIES = 20
RETRY_DELAY = 15

class IntegratedLogger:
    """Integrated logging system."""
    
    def __init__(self):
        self.start_time = time.time()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        elapsed = time.time() - self.start_time
        emoji = {
            "INFO": "📝", "SUCCESS": "✅", "WARNING": "⚠️", 
            "ERROR": "❌", "DEBUG": "🔍", "MEMORY": "🧠",
            "MODEL": "🤖", "FUNCTION": "⚙️", "API": "🌐"
        }.get(level, "📝")
        print(f"[{timestamp}] {emoji} [{level}] [{elapsed:.1f}s] {message}", flush=True)

class ServiceWaiter:
    """Service readiness waiter."""
    
    def __init__(self, logger: IntegratedLogger):
        self.logger = logger
    
    def wait_for_service(self, name: str, url: str, endpoint: str = "/health", timeout: int = 300) -> bool:
        """Wait for a service to become ready."""
        self.logger.log(f"Waiting for {name} to be ready...", "INFO")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    self.logger.log(f"{name} is ready!", "SUCCESS")
                    return True
                self.logger.log(f"{name} responded with status {response.status_code}", "DEBUG")
            except Exception as e:
                self.logger.log(f"{name} not ready: {e}", "DEBUG")
            
            time.sleep(RETRY_DELAY)
        
        self.logger.log(f"{name} failed to become ready within {timeout}s", "ERROR")
        return False

class ModelManager:
    """Integrated model management."""
    
    def __init__(self, logger: IntegratedLogger):
        self.logger = logger
    
    def check_model_exists(self, model_name: str) -> bool:
        """Check if model exists."""
        try:
            response = requests.get(f"{OLLAMA_API}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model.get("name") == model_name for model in models)
        except Exception as e:
            self.logger.log(f"Error checking model: {e}", "DEBUG")
        return False
    
    def download_model(self, model_name: str) -> bool:
        """Download model with progress tracking."""
        if self.check_model_exists(model_name):
            self.logger.log(f"Model {model_name} already exists", "SUCCESS")
            return True
        
        self.logger.log(f"Downloading model: {model_name}", "MODEL")
        
        try:
            response = requests.post(
                f"{OLLAMA_API}/api/pull",
                json={"name": model_name},
                timeout=1800,  # 30 minutes
                stream=True
            )
            
            if response.status_code != 200:
                self.logger.log(f"Download failed: HTTP {response.status_code}", "ERROR")
                return False
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        status = data.get('status', '')
                        if 'downloading' in status.lower():
                            self.logger.log(f"Download progress: {status}", "DEBUG")
                        elif status == 'success':
                            self.logger.log(f"Model {model_name} downloaded successfully", "SUCCESS")
                            return True
                        elif 'error' in data:
                            self.logger.log(f"Download error: {data['error']}", "ERROR")
                            return False
                    except json.JSONDecodeError:
                        continue
            
            return False
            
        except Exception as e:
            self.logger.log(f"Model download failed: {e}", "ERROR")
            return False
    
    def ensure_model_available(self) -> bool:
        """Ensure at least one model is available."""
        models_to_try = [DEFAULT_MODEL] + FALLBACK_MODELS
        
        for model in models_to_try:
            self.logger.log(f"Trying to download model: {model}", "MODEL")
            if self.download_model(model):
                self.logger.log(f"Successfully set up model: {model}", "SUCCESS")
                return True
        
        self.logger.log("Failed to download any model", "ERROR")
        return False

class FunctionManager:
    """Integrated function management."""
    
    def __init__(self, logger: IntegratedLogger):
        self.logger = logger
    
    def wait_for_database(self) -> bool:
        """Wait for OpenWebUI database to be available."""
        self.logger.log("Waiting for OpenWebUI database...", "FUNCTION")
        
        for attempt in range(MAX_RETRIES):
            db_path = Path(OPENWEBUI_DB_PATH)
            if db_path.exists():
                try:
                    # Test database connection
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    conn.close()
                    
                    if tables:
                        self.logger.log("OpenWebUI database is ready", "SUCCESS")
                        return True
                    
                except Exception as e:
                    self.logger.log(f"Database not ready: {e}", "DEBUG")
            
            self.logger.log(f"Database not ready (attempt {attempt + 1}/{MAX_RETRIES})", "DEBUG")
            time.sleep(RETRY_DELAY)
        
        return False
    
    def read_function_code(self) -> Optional[str]:
        """Read the memory function code."""
        try:
            function_path = Path(MEMORY_FUNCTION_PATH)
            if not function_path.exists():
                self.logger.log(f"Function file not found: {MEMORY_FUNCTION_PATH}", "ERROR")
                return None
            
            with open(function_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if len(code) < 100:
                self.logger.log("Function code appears to be empty or too short", "ERROR")
                return None
            
            self.logger.log(f"Function code loaded: {len(code)} characters", "SUCCESS")
            return code
            
        except Exception as e:
            self.logger.log(f"Error reading function code: {e}", "ERROR")
            return None
    
    def install_function(self, function_code: str) -> bool:
        """Install function in OpenWebUI database."""
        try:
            db_path = Path(OPENWEBUI_DB_PATH)
            if not db_path.exists():
                self.logger.log("Database not found", "ERROR")
                return False
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check if function table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='function'")
            if not cursor.fetchone():
                self.logger.log("Creating function table...", "FUNCTION")
                cursor.execute("""
                    CREATE TABLE function (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_global BOOLEAN DEFAULT FALSE,
                        created_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL
                    )
                """)
            
            # Check if memory function already exists
            cursor.execute("SELECT id FROM function WHERE id = ?", ("memory_function",))
            if cursor.fetchone():
                self.logger.log("Memory function already installed", "SUCCESS")
                conn.close()
                return True
            
            # Install function
            timestamp = int(time.time())
            meta = json.dumps({
                "description": "Enhanced memory function that adds context from previous conversations",
                "manifest": {}
            })
            cursor.execute("""
                INSERT INTO function (id, user_id, name, type, content, is_active, is_global, meta, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "memory_function",
                "",  # Global function
                "Enhanced Memory Function",
                "function",
                function_code,
                True,
                True,
                meta,
                timestamp,
                timestamp
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.log("Memory function installed successfully", "SUCCESS")
            return True
            
        except Exception as e:
            self.logger.log(f"Function installation failed: {e}", "ERROR")
            return False
    
    def verify_function(self) -> bool:
        """Verify function installation."""
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
            
            if result and result[2] and result[3]:  # is_active and is_global
                self.logger.log(f"Function verified: {result[1]}", "SUCCESS")
                return True
            
            return False
            
        except Exception as e:
            self.logger.log(f"Function verification failed: {e}", "ERROR")
            return False

class IntegratedMemoryAPI:
    """Main integrated memory API with auto-setup."""
    
    def __init__(self):
        self.logger = IntegratedLogger()
        self.waiter = ServiceWaiter(self.logger)
        self.model_manager = ModelManager(self.logger)
        self.function_manager = FunctionManager(self.logger)
        self.setup_complete = False
        self.api_process = None
    
    def run_background_setup(self):
        """Run background setup process."""
        def setup_thread():
            self.logger.log("🚀 Starting integrated auto-setup...", "INFO")
            
            try:
                # Wait for Ollama
                if not self.waiter.wait_for_service("Ollama", OLLAMA_API, "/api/tags"):
                    self.logger.log("Ollama service failed to start", "ERROR")
                    return
                
                # Wait for OpenWebUI
                if not self.waiter.wait_for_service("OpenWebUI", OPENWEBUI_API):
                    self.logger.log("OpenWebUI service failed to start", "ERROR")
                    return
                
                # Setup model
                if not self.model_manager.ensure_model_available():
                    self.logger.log("Model setup failed", "ERROR")
                    return
                
                # Wait for database
                if not self.function_manager.wait_for_database():
                    self.logger.log("Database setup failed", "ERROR")
                    return
                
                # Install function
                function_code = self.function_manager.read_function_code()
                if not function_code:
                    self.logger.log("Failed to read function code", "ERROR")
                    return
                
                if not self.function_manager.install_function(function_code):
                    self.logger.log("Function installation failed", "ERROR")
                    return
                
                # Verify function
                if not self.function_manager.verify_function():
                    self.logger.log("Function verification failed", "ERROR")
                    return
                
                self.setup_complete = True
                self.logger.log("🎉 Integrated auto-setup completed successfully!", "SUCCESS")
                self.logger.log("✅ Model downloaded and available", "SUCCESS")
                self.logger.log("✅ Memory function installed and active", "SUCCESS")
                self.logger.log("✅ System fully operational", "SUCCESS")
                
            except Exception as e:
                self.logger.log(f"Setup failed with error: {e}", "ERROR")
        
        # Start setup in background thread
        setup_thread = threading.Thread(target=setup_thread, daemon=True)
        setup_thread.start()
        return setup_thread
    
    def start_memory_api(self):
        """Start the main memory API service."""
        self.logger.log("🧠 Starting Memory API service...", "API")
        
        # Start the main memory API
        try:
            # Import and start the memory API
            os.chdir('/app')
            import sys
            sys.path.insert(0, '/app')
            
            from memory.api.main import app
            import uvicorn
            
            # Start uvicorn in a separate thread
            def run_api():
                uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
            
            api_thread = threading.Thread(target=run_api, daemon=True)
            api_thread.start()
            
            self.logger.log("Memory API started successfully", "SUCCESS")
            return api_thread
            
        except Exception as e:
            self.logger.log(f"Failed to start Memory API: {e}", "ERROR")
            return None
    
    def run(self):
        """Run the integrated service."""
        self.logger.log("🚀 Starting Integrated Memory API with Auto-Setup", "INFO")
        
        # Start memory API service
        api_thread = self.start_memory_api()
        if not api_thread:
            self.logger.log("Failed to start Memory API", "ERROR")
            sys.exit(1)
        
        # Start background setup
        setup_thread = self.run_background_setup()
        
        # Keep the main process running
        try:
            while True:
                time.sleep(30)
                
                # Log status periodically
                if self.setup_complete:
                    self.logger.log("✅ System operational - Memory API running with auto-setup complete", "INFO")
                else:
                    self.logger.log("⏳ Memory API running - Auto-setup in progress...", "INFO")
                    
        except KeyboardInterrupt:
            self.logger.log("Shutting down...", "INFO")
            sys.exit(0)
        except Exception as e:
            self.logger.log(f"Unexpected error: {e}", "ERROR")
            sys.exit(1)

def main():
    """Main entry point."""
    integrated_api = IntegratedMemoryAPI()
    integrated_api.run()

if __name__ == "__main__":
    main()
