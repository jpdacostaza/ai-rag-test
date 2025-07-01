#!/usr/bin/env python3
"""
Fully Automated System Setup
============================

This script automatically handles:
1. Model downloading (llama3.2:3b if not present)
2. Function installation (memory function as global)
3. System verification

No manual intervention required.
"""

import json
import time
import logging
import sys
import os
import sqlite3
import hashlib
import asyncio
from pathlib import Path
from typing import Optional, Dict, List
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class AutoSetupSystem:
    def __init__(self):
        self.openwebui_url = os.getenv("OPENWEBUI_URL", "http://openwebui:8080")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.db_path = "/tmp/openwebui/webui.db"
        self.default_model = "llama3.2:3b"
        self.max_retries = 60  # 10 minutes
        
    async def run_complete_setup(self) -> bool:
        """Run complete automated setup"""
        logger.info("🚀 Starting fully automated system setup...")
        
        try:
            # Step 1: Wait for services
            if not await self.wait_for_services():
                return False
            
            # Step 2: Download model if needed
            if not await self.ensure_model_downloaded():
                logger.error("❌ Model download failed")
                return False
            
            # Step 3: Install function automatically
            if not await self.install_function_automatically():
                logger.error("❌ Function installation failed")
                return False
            
            # Step 4: Verify setup
            if not await self.verify_complete_setup():
                logger.error("❌ Setup verification failed")
                return False
            
            logger.info("🎉 ✅ COMPLETE AUTOMATED SETUP SUCCESSFUL!")
            logger.info("🎯 System is ready: Model downloaded, Function installed, Everything verified!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed with error: {str(e)}")
            return False

    async def wait_for_services(self) -> bool:
        """Wait for all required services to be ready"""
        logger.info("⏳ Waiting for services to be ready...")
        
        services = [
            ("OpenWebUI", self.openwebui_url),
            ("Ollama", self.ollama_url)
        ]
        
        for service_name, url in services:
            logger.info(f"🔍 Checking {service_name} at {url}...")
            
            for attempt in range(self.max_retries):
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(url)
                        if response.status_code == 200:
                            logger.info(f"✅ {service_name} is ready!")
                            break
                        elif response.status_code == 404 and service_name == "Ollama":
                            # Ollama returns 404 for root but is working
                            logger.info(f"✅ {service_name} is ready!")
                            break
                except Exception as e:
                    logger.debug(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                
                if attempt == self.max_retries - 1:
                    logger.error(f"❌ {service_name} did not become ready")
                    return False
                
                await asyncio.sleep(10)
        
        logger.info("✅ All services are ready!")
        return True

    async def ensure_model_downloaded(self) -> bool:
        """Ensure the default model is downloaded"""
        logger.info(f"🤖 Ensuring model {self.default_model} is available...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Check if model exists
                response = await client.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    models = response.json()
                    existing_models = [model['name'] for model in models.get('models', [])]
                    
                    if self.default_model in existing_models:
                        logger.info(f"✅ Model {self.default_model} already exists!")
                        return True
                    
                    # Model doesn't exist, download it
                    logger.info(f"📥 Downloading model {self.default_model}...")
                    
                    download_response = await client.post(
                        f"{self.ollama_url}/api/pull",
                        json={"name": self.default_model},
                        timeout=600.0  # 10 minutes for download
                    )
                    
                    if download_response.status_code == 200:
                        logger.info(f"✅ Model {self.default_model} downloaded successfully!")
                        return True
                    else:
                        logger.error(f"❌ Model download failed: {download_response.status_code}")
                        return False
                else:
                    logger.error(f"❌ Failed to check models: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Model download error: {str(e)}")
            return False

    async def install_function_automatically(self) -> bool:
        """Install memory function automatically using multiple methods"""
        logger.info("🔧 Installing memory function automatically...")
        
        # Method 1: Direct database insertion with admin user creation
        if await self.install_via_enhanced_database():
            return True
        
        # Method 2: Admin user creation + API
        if await self.install_via_admin_creation():
            return True
        
        # Method 3: Direct database modification (bypass auth)
        if await self.install_via_database_bypass():
            return True
        
        logger.error("❌ All automatic installation methods failed")
        return False

    async def install_via_enhanced_database(self) -> bool:
        """Install function via enhanced database method with admin user"""
        logger.info("🔧 Installing via enhanced database method...")
        
        function_code = await self.read_function_code()
        if not function_code:
            return False

        try:
            if not os.path.exists(self.db_path):
                logger.warning(f"⚠️  Database not found at {self.db_path}")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure admin user exists
            await self.ensure_admin_user_exists(cursor)
            
            # Check if functions table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='function'")
            if not cursor.fetchone():
                logger.warning("⚠️  Functions table not found")
                conn.close()
                return False
            
            # Get admin user ID
            cursor.execute("SELECT id FROM user WHERE email = ? OR role = 'admin' LIMIT 1", ('admin@openwebui.com',))
            admin_result = cursor.fetchone()
            
            if not admin_result:
                logger.error("❌ No admin user found")
                conn.close()
                return False
            
            admin_user_id = admin_result[0]
            
            # Install function
            function_id = "memory_function"
            function_name = "Enhanced Memory Function"
            created_at = int(time.time())
            
            cursor.execute("SELECT id FROM function WHERE id = ?", (function_id,))
            if cursor.fetchone():
                logger.info("⚠️  Function exists, updating...")
                cursor.execute("""
                    UPDATE function 
                    SET name = ?, content = ?, is_active = ?, is_global = ?, updated_at = ?, user_id = ?
                    WHERE id = ?
                """, (function_name, function_code, True, True, created_at, admin_user_id, function_id))
            else:
                logger.info("📦 Installing new function...")
                cursor.execute("""
                    INSERT INTO function (id, name, content, type, is_active, is_global, created_at, updated_at, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (function_id, function_name, function_code, "function", True, True, created_at, created_at, admin_user_id))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Function installed successfully via enhanced database!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Enhanced database installation failed: {str(e)}")
            return False

    async def ensure_admin_user_exists(self, cursor) -> bool:
        """Ensure an admin user exists in the database"""
        try:
            # Check if admin user exists
            cursor.execute("SELECT id FROM user WHERE email = ? OR role = 'admin'", ('admin@openwebui.com',))
            if cursor.fetchone():
                logger.info("✅ Admin user already exists")
                return True
            
            # Create admin user
            admin_id = f"admin_{int(time.time())}"
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()  # Default password
            created_at = int(time.time())
            
            cursor.execute("""
                INSERT INTO user (id, name, email, role, profile_image_url, created_at, updated_at, password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (admin_id, "Auto Admin", "admin@openwebui.com", "admin", "", created_at, created_at, password_hash))
            
            logger.info("✅ Admin user created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Admin user creation failed: {str(e)}")
            return False

    async def install_via_admin_creation(self) -> bool:
        """Install function by creating admin user and using API"""
        logger.info("🔧 Installing via admin creation method...")
        
        # This would involve creating an admin user and using their session
        # Implementation would be similar to enhanced database but with API calls
        # For now, return False to try next method
        return False

    async def install_via_database_bypass(self) -> bool:
        """Install function by bypassing authentication checks"""
        logger.info("🔧 Installing via database bypass method...")
        
        function_code = await self.read_function_code()
        if not function_code:
            return False

        try:
            if not os.path.exists(self.db_path):
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create a dummy user_id if needed
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
            
            cursor.execute("SELECT id FROM function WHERE id = ?", (function_id,))
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE function 
                    SET name = ?, content = ?, is_active = ?, is_global = ?, updated_at = ?, user_id = ?
                    WHERE id = ?
                """, (function_name, function_code, True, True, created_at, user_id, function_id))
            else:
                cursor.execute("""
                    INSERT INTO function (id, name, content, type, is_active, is_global, created_at, updated_at, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (function_id, function_name, function_code, "function", True, True, created_at, created_at, user_id))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Function installed successfully via database bypass!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database bypass installation failed: {str(e)}")
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
                logger.info(f"📖 Reading function code from {path}")
                return path.read_text(encoding='utf-8')
        
        logger.error("❌ Memory function file not found")
        return None

    async def verify_complete_setup(self) -> bool:
        """Verify that everything is working correctly"""
        logger.info("🔍 Verifying complete setup...")
        
        # Verify model is available
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    models = response.json()
                    existing_models = [model['name'] for model in models.get('models', [])]
                    
                    if self.default_model not in existing_models:
                        logger.error(f"❌ Model {self.default_model} not found")
                        return False
                    
                    logger.info(f"✅ Model {self.default_model} verified")
                else:
                    logger.error("❌ Could not verify model")
                    return False
        except Exception as e:
            logger.error(f"❌ Model verification failed: {str(e)}")
            return False
        
        # Verify function is installed
        try:
            if not os.path.exists(self.db_path):
                logger.error("❌ Database not found for function verification")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, is_active, is_global FROM function WHERE id = ?", ("memory_function",))
            result = cursor.fetchone()
            
            if not result:
                logger.error("❌ Memory function not found in database")
                conn.close()
                return False
            
            function_id, is_active, is_global = result
            
            if not is_active:
                logger.error("❌ Memory function is not active")
                conn.close()
                return False
            
            if not is_global:
                logger.error("❌ Memory function is not global")
                conn.close()
                return False
            
            logger.info("✅ Memory function verified (active and global)")
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Function verification failed: {str(e)}")
            return False
        
        logger.info("🎉 ✅ COMPLETE SETUP VERIFICATION SUCCESSFUL!")
        return True

async def main():
    """Main entry point"""
    setup = AutoSetupSystem()
    
    success = await setup.run_complete_setup()
    
    if success:
        logger.info("🎉 🚀 FULLY AUTOMATED SETUP COMPLETED SUCCESSFULLY!")
        logger.info("📋 Summary:")
        logger.info("  ✅ Model downloaded and available")
        logger.info("  ✅ Memory function installed as global")
        logger.info("  ✅ All services verified and working")
        logger.info("🎯 System is ready for use!")
        sys.exit(0)
    else:
        logger.error("❌ 🚨 AUTOMATED SETUP FAILED!")
        logger.error("Manual intervention may be required.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
