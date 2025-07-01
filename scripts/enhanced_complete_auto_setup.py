#!/usr/bin/env python3
"""
Enhanced Complete Auto-Setup System
===================================

This script provides a comprehensive, bulletproof automated setup that:
1. Downloads multiple models (primary and fallback)
2. Installs the memory function as a global function
3. Configures all necessary settings and connections
4. Validates the entire system end-to-end
5. Provides detailed logging and error recovery
6. Ensures zero manual intervention is required

Features:
- Multi-model support with fallbacks
- Comprehensive service health checking
- Database validation and repair
- Network connectivity testing
- End-to-end system validation
- Automatic retry mechanisms
- Detailed progress reporting
"""

import os
import sys
import time
import json
import sqlite3
import hashlib
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Enhanced Configuration
OLLAMA_API = "http://ollama:11434"
OPENWEBUI_API = "http://openwebui:8080"
MEMORY_API = "http://memory_api:8000"
OPENWEBUI_DB_PATH = "/app/backend/data/webui.db"
FUNCTION_CODE_PATH = "/app/memory_function.py"

# Model Configuration with Fallbacks
PRIMARY_MODELS = [
    "llama3.2:3b",
    "llama3.1:8b",
    "codellama:7b"
]

FALLBACK_MODELS = [
    "phi3:mini",
    "gemma2:2b",
    "qwen2:1.5b"
]

# Timeouts and Retry Configuration
MAX_RETRIES = 15
RETRY_DELAY = 20
SERVICE_TIMEOUT = 30
MODEL_DOWNLOAD_TIMEOUT = 3600  # 1 hour
HEALTH_CHECK_INTERVAL = 5

class SetupPhase(Enum):
    """Setup phases for progress tracking."""
    INIT = "initialization"
    SERVICES = "service_readiness"
    MODELS = "model_download"
    FUNCTIONS = "function_installation"
    VALIDATION = "end_to_end_validation"
    COMPLETE = "setup_complete"

@dataclass
class SetupResult:
    """Result of a setup operation."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    phase: Optional[SetupPhase] = None

class EnhancedLogger:
    """Advanced logging with structured output and progress tracking."""
    
    def __init__(self):
        self.start_time = time.time()
        self.current_phase = SetupPhase.INIT
        self.phase_start_time = time.time()
    
    def set_phase(self, phase: SetupPhase):
        """Set the current setup phase."""
        if self.current_phase != SetupPhase.INIT:
            duration = time.time() - self.phase_start_time
            self.log(f"Phase {self.current_phase.value} completed in {duration:.2f}s", "SUCCESS")
        
        self.current_phase = phase
        self.phase_start_time = time.time()
        self.log(f"Starting phase: {phase.value}", "INFO")
    
    def log(self, message: str, level: str = "INFO", details: Optional[Dict] = None):
        """Enhanced logging with timestamps and structured data."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        elapsed = time.time() - self.start_time
        
        emoji = {
            "INFO": "📝",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌",
            "DEBUG": "🔍",
            "PROGRESS": "⏳",
            "NETWORK": "🌐",
            "DATABASE": "💾",
            "MODEL": "🤖",
            "FUNCTION": "⚙️"
        }.get(level, "📝")
        
        base_msg = f"[{timestamp}] {emoji} [{level}] [{self.current_phase.value}] [{elapsed:.1f}s] {message}"
        print(base_msg)
        
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def progress(self, current: int, total: int, operation: str):
        """Log progress information."""
        percentage = (current / total) * 100 if total > 0 else 0
        self.log(f"{operation}: {current}/{total} ({percentage:.1f}%)", "PROGRESS")

class ServiceHealthChecker:
    """Comprehensive service health checking."""
    
    def __init__(self, logger: EnhancedLogger):
        self.logger = logger
    
    def check_network_connectivity(self) -> SetupResult:
        """Check network connectivity between services."""
        services = [
            ("Ollama", OLLAMA_API),
            ("OpenWebUI", OPENWEBUI_API),
            ("Memory API", MEMORY_API)
        ]
        
        results = {}
        for service_name, url in services:
            try:
                response = requests.get(f"{url}/health", timeout=5)
                results[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds(),
                    "status_code": response.status_code
                }
            except Exception as e:
                results[service_name] = {
                    "status": "unreachable",
                    "error": str(e)
                }
        
        healthy_services = sum(1 for r in results.values() if r.get("status") == "healthy")
        total_services = len(services)
        
        if healthy_services == total_services:
            return SetupResult(True, "All services are healthy", results)
        else:
            return SetupResult(False, f"Only {healthy_services}/{total_services} services healthy", results)
    
    def wait_for_service(self, service_name: str, url: str, health_endpoint: str = "/health") -> SetupResult:
        """Wait for a specific service to become healthy."""
        self.logger.log(f"Waiting for {service_name} to become ready...", "NETWORK")
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(f"{url}{health_endpoint}", timeout=SERVICE_TIMEOUT)
                if response.status_code == 200:
                    self.logger.log(f"{service_name} is ready", "SUCCESS")
                    return SetupResult(True, f"{service_name} is ready")
                
                self.logger.log(f"{service_name} not ready: HTTP {response.status_code} (attempt {attempt + 1}/{MAX_RETRIES})", "WARNING")
                
            except Exception as e:
                self.logger.log(f"{service_name} not ready: {e} (attempt {attempt + 1}/{MAX_RETRIES})", "WARNING")
            
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
        
        return SetupResult(False, f"{service_name} failed to become ready after {MAX_RETRIES} attempts")

class EnhancedModelManager:
    """Advanced model management with multiple download strategies."""
    
    def __init__(self, logger: EnhancedLogger):
        self.logger = logger
        self.downloaded_models = set()
    
    def list_available_models(self) -> List[str]:
        """List all available models in Ollama."""
        try:
            response = requests.get(f"{OLLAMA_API}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model.get("name", "") for model in models if model.get("name")]
            return []
        except Exception as e:
            self.logger.log(f"Error listing models: {e}", "ERROR")
            return []
    
    def check_model_exists(self, model_name: str) -> bool:
        """Check if a specific model exists."""
        available_models = self.list_available_models()
        exists = model_name in available_models
        if exists:
            self.downloaded_models.add(model_name)
        return exists
    
    def download_model_with_progress(self, model_name: str) -> SetupResult:
        """Download model with detailed progress tracking."""
        if self.check_model_exists(model_name):
            return SetupResult(True, f"Model {model_name} already exists")
        
        self.logger.log(f"Starting download of model: {model_name}", "MODEL")
        
        try:
            response = requests.post(
                f"{OLLAMA_API}/api/pull",
                json={"name": model_name},
                timeout=MODEL_DOWNLOAD_TIMEOUT,
                stream=True
            )
            
            if response.status_code != 200:
                return SetupResult(False, f"Failed to start download: HTTP {response.status_code}")
            
            total_size = 0
            downloaded_size = 0
            last_progress_time = time.time()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        status = data.get('status', '')
                        
                        # Track progress
                        if 'total' in data and 'completed' in data:
                            total_size = data['total']
                            downloaded_size = data['completed']
                            
                            # Log progress every 10 seconds
                            if time.time() - last_progress_time > 10:
                                progress = (downloaded_size / total_size * 100) if total_size > 0 else 0
                                self.logger.log(f"Download progress: {progress:.1f}% ({downloaded_size}/{total_size} bytes)", "PROGRESS")
                                last_progress_time = time.time()
                        
                        if status == 'success':
                            self.logger.log(f"Model {model_name} downloaded successfully", "SUCCESS")
                            self.downloaded_models.add(model_name)
                            return SetupResult(True, f"Model {model_name} downloaded successfully")
                        
                        if 'error' in data:
                            return SetupResult(False, f"Download error: {data['error']}")
                            
                    except json.JSONDecodeError:
                        continue
            
            return SetupResult(False, "Download completed but no success status received")
            
        except Exception as e:
            return SetupResult(False, f"Download failed: {e}")
    
    def setup_models_with_fallbacks(self) -> SetupResult:
        """Setup models with fallback strategy."""
        self.logger.log("Starting comprehensive model setup", "MODEL")
        
        # Try primary models first
        for i, model in enumerate(PRIMARY_MODELS):
            self.logger.progress(i + 1, len(PRIMARY_MODELS), "Primary model setup")
            result = self.download_model_with_progress(model)
            if result.success:
                return SetupResult(True, f"Primary model {model} set up successfully", {"model": model})
        
        self.logger.log("Primary models failed, trying fallback models", "WARNING")
        
        # Try fallback models
        for i, model in enumerate(FALLBACK_MODELS):
            self.logger.progress(i + 1, len(FALLBACK_MODELS), "Fallback model setup")
            result = self.download_model_with_progress(model)
            if result.success:
                return SetupResult(True, f"Fallback model {model} set up successfully", {"model": model})
        
        return SetupResult(False, "All model downloads failed")

class EnhancedFunctionInstaller:
    """Advanced function installation with validation."""
    
    def __init__(self, logger: EnhancedLogger):
        self.logger = logger
    
    def validate_database_schema(self) -> SetupResult:
        """Validate and repair database schema if needed."""
        try:
            db_path = Path(OPENWEBUI_DB_PATH)
            if not db_path.exists():
                return SetupResult(False, "Database file does not exist")
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check if function table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='function'")
            if not cursor.fetchone():
                self.logger.log("Function table missing, creating...", "DATABASE")
                # Create function table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS function (
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
                conn.commit()
            
            conn.close()
            return SetupResult(True, "Database schema validated")
            
        except Exception as e:
            return SetupResult(False, f"Database validation failed: {e}")
    
    def read_function_code(self) -> SetupResult:
        """Read and validate function code."""
        try:
            if not Path(FUNCTION_CODE_PATH).exists():
                return SetupResult(False, f"Function code file not found: {FUNCTION_CODE_PATH}")
            
            with open(FUNCTION_CODE_PATH, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if len(code) < 100:  # Basic validation
                return SetupResult(False, "Function code appears to be too short or empty")
            
            # Basic syntax check
            try:
                compile(code, FUNCTION_CODE_PATH, 'exec')
            except SyntaxError as e:
                return SetupResult(False, f"Function code has syntax errors: {e}")
            
            return SetupResult(True, "Function code validated", {"code": code, "size": len(code)})
            
        except Exception as e:
            return SetupResult(False, f"Error reading function code: {e}")
    
    def install_function_enhanced(self, function_code: str) -> SetupResult:
        """Install function with enhanced error handling."""
        try:
            # Validate database first
            db_result = self.validate_database_schema()
            if not db_result.success:
                return db_result
            
            db_path = Path(OPENWEBUI_DB_PATH)
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check if function already exists
            cursor.execute("SELECT id, name, is_active FROM function WHERE id = ?", ("memory_function",))
            existing = cursor.fetchone()
            
            if existing:
                self.logger.log(f"Function already exists: {existing}", "SUCCESS")
                conn.close()
                return SetupResult(True, "Function already installed", {"existing": existing})
            
            # Create function entry with required meta field
            timestamp = int(time.time())
            function_meta = {
                "description": "Enhanced memory function for storing and retrieving conversation context",
                "version": "1.0.0",
                "author": "System",
                "tags": ["memory", "storage", "conversation"]
            }
            
            function_data = {
                "id": "memory_function",
                "user_id": "",  # Global function - empty for global
                "name": "Enhanced Memory Function",
                "type": "function",
                "content": function_code,
                "meta": json.dumps(function_meta),  # Required meta field
                "is_active": 1,  # SQLite boolean as integer
                "is_global": 1,  # SQLite boolean as integer
                "created_at": timestamp,
                "updated_at": timestamp,
                "valves": "{}"  # Empty valves JSON
            }
            
            # Insert function with all required fields
            cursor.execute("""
                INSERT INTO function (id, user_id, name, type, content, meta, is_active, is_global, created_at, updated_at, valves)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                function_data["id"],
                function_data["user_id"],
                function_data["name"],
                function_data["type"],
                function_data["content"],
                function_data["meta"],
                function_data["meta"],
                function_data["is_active"],
                function_data["is_global"],
                function_data["created_at"],
                function_data["updated_at"],
                function_data["valves"]
            ))
            
            conn.commit()
            conn.close()
            
            return SetupResult(True, "Function installed successfully", function_data)
            
        except Exception as e:
            return SetupResult(False, f"Function installation failed: {e}")
    
    def verify_function_installation(self) -> SetupResult:
        """Comprehensive function installation verification."""
        try:
            db_path = Path(OPENWEBUI_DB_PATH)
            if not db_path.exists():
                return SetupResult(False, "Database not found")
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, type, is_active, is_global, created_at, updated_at,
                       LENGTH(content) as content_length
                FROM function 
                WHERE id = 'memory_function'
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return SetupResult(False, "Function not found in database")
            
            function_info = {
                "id": result[0],
                "name": result[1],
                "type": result[2],
                "is_active": bool(result[3]),
                "is_global": bool(result[4]),
                "created_at": result[5],
                "updated_at": result[6],
                "content_length": result[7]
            }
            
            # Validate function properties
            if not function_info["is_active"]:
                return SetupResult(False, "Function is not active", function_info)
            
            if not function_info["is_global"]:
                return SetupResult(False, "Function is not global", function_info)
            
            if function_info["content_length"] < 100:
                return SetupResult(False, "Function content is too short", function_info)
            
            return SetupResult(True, "Function verification successful", function_info)
            
        except Exception as e:
            return SetupResult(False, f"Function verification failed: {e}")

class SystemValidator:
    """End-to-end system validation."""
    
    def __init__(self, logger: EnhancedLogger):
        self.logger = logger
    
    def validate_complete_system(self) -> SetupResult:
        """Perform comprehensive system validation."""
        self.logger.log("Starting end-to-end system validation", "INFO")
        
        validation_results = {}
        
        # 1. Service connectivity
        self.logger.log("Validating service connectivity...", "NETWORK")
        try:
            services = [
                ("Ollama", OLLAMA_API, "/api/tags"),
                ("OpenWebUI", OPENWEBUI_API, "/health"),
                ("Memory API", MEMORY_API, "/health")
            ]
            
            for service_name, url, endpoint in services:
                try:
                    response = requests.get(f"{url}{endpoint}", timeout=10)
                    validation_results[f"{service_name}_connectivity"] = {
                        "status": "pass" if response.status_code == 200 else "fail",
                        "response_time": response.elapsed.total_seconds(),
                        "status_code": response.status_code
                    }
                except Exception as e:
                    validation_results[f"{service_name}_connectivity"] = {
                        "status": "fail",
                        "error": str(e)
                    }
        
        except Exception as e:
            validation_results["service_connectivity"] = {"status": "fail", "error": str(e)}
        
        # 2. Model availability
        self.logger.log("Validating model availability...", "MODEL")
        try:
            response = requests.get(f"{OLLAMA_API}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                validation_results["model_availability"] = {
                    "status": "pass" if len(models) > 0 else "fail",
                    "model_count": len(models),
                    "models": [m.get("name") for m in models]
                }
            else:
                validation_results["model_availability"] = {
                    "status": "fail",
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            validation_results["model_availability"] = {"status": "fail", "error": str(e)}
        
        # 3. Function installation
        self.logger.log("Validating function installation...", "FUNCTION")
        try:
            db_path = Path(OPENWEBUI_DB_PATH)
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM function WHERE id = 'memory_function' AND is_active = 1")
                count = cursor.fetchone()[0]
                conn.close()
                
                validation_results["function_installation"] = {
                    "status": "pass" if count > 0 else "fail",
                    "function_count": count
                }
            else:
                validation_results["function_installation"] = {
                    "status": "fail",
                    "error": "Database not found"
                }
        except Exception as e:
            validation_results["function_installation"] = {"status": "fail", "error": str(e)}
        
        # Evaluate overall status
        total_checks = len(validation_results)
        passed_checks = sum(1 for r in validation_results.values() if r.get("status") == "pass")
        
        overall_success = passed_checks == total_checks
        
        return SetupResult(
            overall_success,
            f"System validation: {passed_checks}/{total_checks} checks passed",
            {"results": validation_results, "summary": {"total": total_checks, "passed": passed_checks}}
        )

class EnhancedSystemSetup:
    """Main enhanced system setup coordinator."""
    
    def __init__(self):
        self.logger = EnhancedLogger()
        self.health_checker = ServiceHealthChecker(self.logger)
        self.model_manager = EnhancedModelManager(self.logger)
        self.function_installer = EnhancedFunctionInstaller(self.logger)
        self.validator = SystemValidator(self.logger)
    
    def run_enhanced_setup(self) -> SetupResult:
        """Run the complete enhanced setup process."""
        self.logger.log("🚀 Starting Enhanced Complete Auto-Setup System", "INFO")
        
        try:
            # Phase 1: Service Readiness
            self.logger.set_phase(SetupPhase.SERVICES)
            
            # Wait for Ollama
            ollama_result = self.health_checker.wait_for_service("Ollama", OLLAMA_API, "/api/tags")
            if not ollama_result.success:
                return SetupResult(False, "Ollama service not ready", phase=SetupPhase.SERVICES)
            
            # Wait for OpenWebUI
            openwebui_result = self.health_checker.wait_for_service("OpenWebUI", OPENWEBUI_API, "/health")
            if not openwebui_result.success:
                return SetupResult(False, "OpenWebUI service not ready", phase=SetupPhase.SERVICES)
            
            # Phase 2: Model Setup
            self.logger.set_phase(SetupPhase.MODELS)
            model_result = self.model_manager.setup_models_with_fallbacks()
            if not model_result.success:
                return SetupResult(False, "Model setup failed", phase=SetupPhase.MODELS)
            
            # Phase 3: Function Installation
            self.logger.set_phase(SetupPhase.FUNCTIONS)
            
            # Read function code
            code_result = self.function_installer.read_function_code()
            if not code_result.success:
                return SetupResult(False, "Failed to read function code", phase=SetupPhase.FUNCTIONS)
            
            # Install function
            install_result = self.function_installer.install_function_enhanced(code_result.details["code"])
            if not install_result.success:
                return SetupResult(False, "Function installation failed", phase=SetupPhase.FUNCTIONS)
            
            # Verify function installation
            verify_result = self.function_installer.verify_function_installation()
            if not verify_result.success:
                return SetupResult(False, "Function verification failed", phase=SetupPhase.FUNCTIONS)
            
            # Phase 4: End-to-End Validation
            self.logger.set_phase(SetupPhase.VALIDATION)
            validation_result = self.validator.validate_complete_system()
            if not validation_result.success:
                return SetupResult(False, "System validation failed", phase=SetupPhase.VALIDATION)
            
            # Phase 5: Complete
            self.logger.set_phase(SetupPhase.COMPLETE)
            
            self.logger.log("🎉 Enhanced Auto-Setup completed successfully!", "SUCCESS")
            self.logger.log("✅ All services are healthy and connected", "SUCCESS")
            self.logger.log(f"✅ Model downloaded: {model_result.details.get('model', 'Unknown')}", "SUCCESS")
            self.logger.log("✅ Memory function installed and verified", "SUCCESS")
            self.logger.log("✅ System fully validated and ready for use", "SUCCESS")
            
            return SetupResult(True, "Enhanced auto-setup completed successfully", phase=SetupPhase.COMPLETE)
            
        except Exception as e:
            self.logger.log(f"Unexpected error during setup: {e}", "ERROR")
            return SetupResult(False, f"Setup failed with error: {e}")

def main():
    """Main entry point with enhanced error handling."""
    setup = EnhancedSystemSetup()
    
    # Run setup with intelligent retries
    max_attempts = 3
    for attempt in range(max_attempts):
        setup.logger.log(f"Starting setup attempt {attempt + 1}/{max_attempts}", "INFO")
        
        result = setup.run_enhanced_setup()
        
        if result.success:
            setup.logger.log("Setup completed successfully!", "SUCCESS")
            sys.exit(0)
        else:
            setup.logger.log(f"Setup attempt {attempt + 1} failed: {result.message}", "ERROR")
            if result.details:
                setup.logger.log("Failure details:", "DEBUG", result.details)
            
            if attempt < max_attempts - 1:
                setup.logger.log(f"Retrying in {RETRY_DELAY} seconds...", "WARNING")
                time.sleep(RETRY_DELAY)
    
    setup.logger.log("All setup attempts failed", "ERROR")
    sys.exit(1)

if __name__ == "__main__":
    main()
