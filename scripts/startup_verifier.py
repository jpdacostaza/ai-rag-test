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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class StartupVerifier:
    def __init__(self):
        self.openwebui_url = os.getenv("OPENWEBUI_URL", "http://openwebui:8080")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.db_path = "/tmp/openwebui/webui.db"
        self.default_model = "llama3.2:3b"
        
    async def run_startup_verification(self) -> bool:
        """Run startup verification and auto-fixing"""
        logger.info("🔍 Starting startup verification...")
        
        try:
            # Wait for services to be ready
            await self.wait_for_services()
            
            # Check and fix model
            model_ok = await self.verify_and_fix_model()
            
            # Check and fix function
            function_ok = await self.verify_and_fix_function()
            
            if model_ok and function_ok:
                logger.info("✅ 🎉 STARTUP VERIFICATION PASSED!")
                logger.info("🎯 System is ready: Model available, Function active")
                return True
            else:
                logger.error("❌ 🚨 STARTUP VERIFICATION FAILED!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Startup verification error: {str(e)}")
            return False

    async def wait_for_services(self) -> bool:
        """Wait for essential services"""
        logger.info("⏳ Waiting for services...")
        
        # Wait for OpenWebUI
        for attempt in range(30):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(self.openwebui_url)
                    if response.status_code == 200:
                        logger.info("✅ OpenWebUI is ready")
                        break
            except:
                pass
            await asyncio.sleep(5)
        
        # Wait for Ollama
        for attempt in range(30):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(self.ollama_url)
                    # Ollama returns 404 for root but is working
                    if response.status_code in [200, 404]:
                        logger.info("✅ Ollama is ready")
                        break
            except:
                pass
            await asyncio.sleep(5)
        
        return True

    async def verify_and_fix_model(self) -> bool:
        """Verify model exists, download if missing"""
        logger.info(f"🤖 Verifying model {self.default_model}...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                
                if response.status_code == 200:
                    models = response.json()
                    existing_models = [model['name'] for model in models.get('models', [])]
                    
                    if self.default_model in existing_models:
                        logger.info(f"✅ Model {self.default_model} is available")
                        return True
                    
                    # Model missing, download it
                    logger.info(f"📥 Model missing, downloading {self.default_model}...")
                    
                    download_response = await client.post(
                        f"{self.ollama_url}/api/pull",
                        json={"name": self.default_model},
                        timeout=600.0
                    )
                    
                    if download_response.status_code == 200:
                        logger.info(f"✅ Model {self.default_model} downloaded successfully")
                        return True
                    else:
                        logger.error(f"❌ Model download failed: {download_response.status_code}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Model verification error: {str(e)}")
            return False

    async def verify_and_fix_function(self) -> bool:
        """Verify function exists and is active, install if missing"""
        logger.info("🔧 Verifying memory function...")
        
        try:
            if not os.path.exists(self.db_path):
                logger.warning("⚠️  Database not found, function cannot be verified")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if function exists and is active
            cursor.execute("SELECT id, is_active, is_global FROM function WHERE id = ?", ("memory_function",))
            result = cursor.fetchone()
            
            if result:
                function_id, is_active, is_global = result
                
                if is_active and is_global:
                    logger.info("✅ Memory function is active and global")
                    conn.close()
                    return True
                else:
                    # Function exists but not properly configured
                    logger.info("⚠️  Function exists but not properly configured, fixing...")
                    cursor.execute("""
                        UPDATE function 
                        SET is_active = ?, is_global = ?, updated_at = ?
                        WHERE id = ?
                    """, (True, True, int(time.time()), "memory_function"))
                    conn.commit()
                    conn.close()
                    logger.info("✅ Function configuration fixed")
                    return True
            else:
                # Function doesn't exist, install it
                logger.info("⚠️  Function missing, installing...")
                success = await self.install_missing_function(cursor)
                conn.close()
                return success
                
        except Exception as e:
            logger.error(f"❌ Function verification error: {str(e)}")
            return False

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
            
            logger.info("✅ Function installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Function installation error: {str(e)}")
            return False

    async def read_function_code(self) -> Optional[str]:
        """Read the memory function code"""
        possible_paths = [
            Path("/app/memory_function.py"),
            Path("./memory_function.py"),
            Path("/app/memory/functions/memory_function.py"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path.read_text(encoding='utf-8')
        
        logger.error("❌ Memory function file not found")
        return None

async def main():
    """Main entry point"""
    verifier = StartupVerifier()
    
    success = await verifier.run_startup_verification()
    
    if success:
        logger.info("🎉 ✅ STARTUP VERIFICATION COMPLETED!")
        sys.exit(0)
    else:
        logger.error("❌ 🚨 STARTUP VERIFICATION FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
