#!/usr/bin/env python3
"""
Startup Verifier and Auto-Fixer
===============================

This script runs on every startup to ensure:
1. Default model is available
2. Memory function is installed and active
3. System is properly configured

Automatically fixes any issues found.
"""

import json
import time
import logging
import sys
import os
import sqlite3
import asyncio
from pathlib import Path
from typing import Optional
import httpx

# Import error handling patterns for startup verification consistency
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utilities.error_patterns import (
        handle_service_errors, handle_database_errors, handle_api_errors
    )
    from utilities.connection_factory import DatabaseConnectionFactory
    ERROR_PATTERNS_AVAILABLE = True
except ImportError:
    ERROR_PATTERNS_AVAILABLE = False
    # Fallback decorators for standalone script usage
    def handle_service_errors(func):
        return func
    def handle_database_errors(func):
        return func
    def handle_api_errors(func):
        return func
    DatabaseConnectionFactory = None

# Configure logging
try:
    from core.unified_logging import setup_logging, get_logger
    setup_logging()
    logger = get_logger(__name__)
except ImportError:
    # Fallback for standalone usage
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

class StartupVerifier:
    def __init__(self):
        self.openwebui_url = os.getenv("OPENWEBUI_URL", "http://openwebui:8080")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.db_path = "/tmp/openwebui/webui.db"
        self.default_model = "hf.co/lmstudio-community/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M"
        
    @handle_service_errors
    async def run_startup_verification(self) -> bool:
        """Run startup verification and auto-fixing"""
        logger.info("[SEARCH] Starting startup verification...")
        
        try:
            # Wait for services to be ready
            await self.wait_for_services()
            
            # Check and fix model
            model_ok = await self.verify_and_fix_model()
            
            # Check and fix function
            function_ok = await self.verify_and_fix_function()
            
            if model_ok and function_ok:
                logger.info("[OK]  STARTUP VERIFICATION PASSED!")
                logger.info(" System is ready: Model available, Function active")
                return True
            else:
                logger.error("[FAIL] *** STARTUP VERIFICATION FAILED!")
                return False
                
        except Exception as e:
            logger.error(f"[FAIL] Startup verification error: {str(e)}")
            return False

    @handle_api_errors
    async def wait_for_services(self) -> bool:
        """Wait for essential services"""
        logger.info(" Waiting for services...")
        
        # Wait for OpenWebUI
        for attempt in range(30):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(self.openwebui_url)
                    if response.status_code == 200:
                        logger.info("[OK] OpenWebUI is ready")
                        break
            except Exception:
                pass
            await asyncio.sleep(5)
        
        # Wait for Ollama
        for attempt in range(30):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(self.ollama_url)
                    # Ollama returns 404 for root but is working
                    if response.status_code in [200, 404]:
                        logger.info("[OK] Ollama is ready")
                        break
            except Exception:
                pass
            await asyncio.sleep(5)
        
        return True

    @handle_api_errors
    async def verify_and_fix_model(self) -> bool:
        """Verify model exists, download if missing"""
        logger.info(f" Verifying model {self.default_model}...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                
                if response.status_code == 200:
                    models = response.json()
                    existing_models = [model['name'] for model in models.get('models', [])]
                    
                    if self.default_model in existing_models:
                        logger.info(f"[OK] Model {self.default_model} is available")
                        return True
                    
                    # Model missing, download it
                    logger.info(f" Model missing, downloading {self.default_model}...")
                    
                    download_response = await client.post(
                        f"{self.ollama_url}/api/pull",
                        json={"name": self.default_model},
                        timeout=600.0
                    )
                    
                    if download_response.status_code == 200:
                        logger.info(f"[OK] Model {self.default_model} downloaded successfully")
                        return True
                    else:
                        logger.error(f"[FAIL] Model download failed: {download_response.status_code}")
                        return False
                        
        except Exception as e:
            logger.error(f"[FAIL] Model verification error: {str(e)}")
            return False

    @handle_database_errors
    async def verify_and_fix_function(self) -> bool:
        """Verify function exists and is active, install if missing"""
        logger.info(" Verifying memory function...")
        
        try:
            if not os.path.exists(self.db_path):
                logger.warning("[WARN]  Database not found, function cannot be verified")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if function exists and is active
            cursor.execute("SELECT id, is_active, is_global FROM function WHERE id = ?", ("memory_function"))
            result = cursor.fetchone()
            
            if result:
                function_id, is_active, is_global = result
                
                if is_active and is_global:
                    logger.info("[OK] Memory function is active and global")
                    conn.close()
                    return True
                else:
                    # Function exists but not properly configured
                    logger.info("[WARN]  Function exists but not properly configured, fixing...")
                    cursor.execute("""
                        UPDATE function 
                        SET is_active = ?, is_global = ?, updated_at = ?
                        WHERE id = ?
                    """, (True, True, int(time.time()), "memory_function"))
                    conn.commit()
                    conn.close()
                    logger.info("[OK] Function configuration fixed")
                    return True
            else:
                # Function doesn't exist, install it
                logger.info("[WARN]  Function missing, installing...")
                success = await self.install_missing_function(cursor)
                conn.close()
                return success
                
        except Exception as e:
            logger.error(f"[FAIL] Function verification error: {str(e)}")
            return False

    @handle_database_errors
    async def install_missing_function(self, cursor) -> bool:
        """Install missing function"""
        try:
            function_code = await self.read_function_code()
            if not function_code:
                return False
            
            # Ensure we have a user to assign the function to
            cursor.execute("SELECT id FROM user LIMIT 1")
            user_result = cursor.fetchone()
            
            if not user_result:
                # Create system user
                system_user_id = "system"
                created_at = int(time.time())
                cursor.execute("""
                    INSERT INTO user (id, name, email, role, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (system_user_id, "System", "system@openwebui.com", "admin", created_at, created_at))
                user_id = system_user_id
            else:
                user_id = user_result[0]
            
            # Install function
            function_id = "memory_function"
            function_name = "Enhanced Memory Function"
            created_at = int(time.time())
            
            cursor.execute("""
                INSERT INTO function (id, name, content, type, is_active, is_global, created_at, updated_at, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (function_id, function_name, function_code, "function", True, True, created_at, created_at, user_id))
            
            logger.info("[OK] Function installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"[FAIL] Function installation error: {str(e)}")
            return False

    async def read_function_code(self) -> Optional[str]:
        """Read the memory function code"""
        possible_paths = [
            Path("/app/functions/filters/enhanced_memory_function_filter_v5_1_final.py"),  # Correct location
            Path("./functions/filters/enhanced_memory_function_filter_v5_1_final.py"),  # Relative correct path
            # Memory function paths (current structure)
            Path("functions/filters/enhanced_memory_function_filter_v5_1_final.py"),
            Path("/app/functions/filters/enhanced_memory_function_filter_v5_1_final.py"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path.read_text(encoding='utf-8')
        
        logger.error("[FAIL] Memory function file not found")
        return None

async def main():
    """Main entry point"""
    verifier = StartupVerifier()
    
    success = await verifier.run_startup_verification()
    
    if success:
        logger.info(" [OK] STARTUP VERIFICATION COMPLETED!")
        sys.exit(0)
    else:
        logger.error("[FAIL] *** STARTUP VERIFICATION FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
