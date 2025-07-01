#!/usr/bin/env python3
"""
Continuous System Monitor
========================

This service runs continuously to monitor and maintain:
1. Model availability
2. Function status
3. System health

Automatically fixes issues as they arise.
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

class SystemMonitor:
    def __init__(self):
        self.openwebui_url = os.getenv("OPENWEBUI_URL", "http://openwebui:8080")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.db_path = "/tmp/openwebui/webui.db"
        self.default_model = "llama3.2:3b"
        self.check_interval = int(os.getenv("CHECK_INTERVAL", "300"))  # 5 minutes default
        
    async def run_continuous_monitoring(self):
        """Run continuous system monitoring"""
        logger.info("🔄 Starting continuous system monitoring...")
        logger.info(f"⏱️  Check interval: {self.check_interval} seconds")
        
        while True:
            try:
                await self.perform_health_check()
                logger.info(f"😴 Sleeping for {self.check_interval} seconds...")
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("⏹️  Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitor error: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def perform_health_check(self):
        """Perform comprehensive health check"""
        logger.info("🩺 Performing health check...")
        
        try:
            # Check services
            services_ok = await self.check_services_health()
            
            # Check model
            model_ok = await self.check_model_health()
            
            # Check function
            function_ok = await self.check_function_health()
            
            if services_ok and model_ok and function_ok:
                logger.info("✅ 💚 ALL SYSTEMS HEALTHY")
            else:
                logger.warning("⚠️  🔧 SOME ISSUES DETECTED - AUTO-FIXING...")
                await self.auto_fix_issues()
                
        except Exception as e:
            logger.error(f"❌ Health check error: {str(e)}")

    async def check_services_health(self) -> bool:
        """Check if all services are responding"""
        services = [
            ("OpenWebUI", self.openwebui_url),
            ("Ollama", self.ollama_url),
        ]
        
        all_healthy = True
        
        for service_name, url in services:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url)
                    if response.status_code in [200, 404]:  # 404 is OK for Ollama root
                        logger.debug(f"✅ {service_name} healthy")
                    else:
                        logger.warning(f"⚠️  {service_name} returned {response.status_code}")
                        all_healthy = False
            except Exception as e:
                logger.warning(f"⚠️  {service_name} connection failed: {str(e)}")
                all_healthy = False
        
        return all_healthy

    async def check_model_health(self) -> bool:
        """Check if default model is available"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                
                if response.status_code == 200:
                    models = response.json()
                    existing_models = [model['name'] for model in models.get('models', [])]
                    
                    if self.default_model in existing_models:
                        logger.debug(f"✅ Model {self.default_model} available")
                        return True
                    else:
                        logger.warning(f"⚠️  Model {self.default_model} missing")
                        return False
                else:
                    logger.warning(f"⚠️  Cannot check models: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.warning(f"⚠️  Model check failed: {str(e)}")
            return False

    async def check_function_health(self) -> bool:
        """Check if memory function is installed and active"""
        try:
            if not os.path.exists(self.db_path):
                logger.warning("⚠️  Database not accessible")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, is_active, is_global FROM function WHERE id = ?", ("memory_function",))
            result = cursor.fetchone()
            
            if result:
                function_id, is_active, is_global = result
                
                if is_active and is_global:
                    logger.debug("✅ Memory function active and global")
                    conn.close()
                    return True
                else:
                    logger.warning("⚠️  Memory function not properly configured")
                    conn.close()
                    return False
            else:
                logger.warning("⚠️  Memory function not found")
                conn.close()
                return False
                
        except Exception as e:
            logger.warning(f"⚠️  Function check failed: {str(e)}")
            return False

    async def auto_fix_issues(self):
        """Automatically fix detected issues"""
        logger.info("🔧 Starting auto-fix procedures...")
        
        # Fix model if missing
        if not await self.check_model_health():
            await self.fix_model_issue()
        
        # Fix function if not properly configured
        if not await self.check_function_health():
            await self.fix_function_issue()
        
        logger.info("🔧 Auto-fix procedures completed")

    async def fix_model_issue(self):
        """Fix model-related issues"""
        logger.info(f"📥 Downloading missing model {self.default_model}...")
        
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/pull",
                    json={"name": self.default_model}
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Model {self.default_model} downloaded successfully")
                else:
                    logger.error(f"❌ Model download failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Model fix failed: {str(e)}")

    async def fix_function_issue(self):
        """Fix function-related issues"""
        logger.info("🔧 Fixing memory function issues...")
        
        try:
            if not os.path.exists(self.db_path):
                logger.error("❌ Cannot fix function: database not accessible")
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if function exists
            cursor.execute("SELECT id FROM function WHERE id = ?", ("memory_function",))
            result = cursor.fetchone()
            
            if result:
                # Function exists, fix configuration
                logger.info("🔧 Fixing function configuration...")
                cursor.execute("""
                    UPDATE function 
                    SET is_active = ?, is_global = ?, updated_at = ?
                    WHERE id = ?
                """, (True, True, int(time.time()), "memory_function"))
                conn.commit()
                logger.info("✅ Function configuration fixed")
            else:
                # Function doesn't exist, install it
                logger.info("📦 Installing missing function...")
                await self.install_function(cursor)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Function fix failed: {str(e)}")

    async def install_function(self, cursor):
        """Install missing function"""
        try:
            function_code = await self.read_function_code()
            if not function_code:
                logger.error("❌ Cannot install function: code not found")
                return
            
            # Ensure we have a user
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
            
        except Exception as e:
            logger.error(f"❌ Function installation failed: {str(e)}")

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
        
        return None

async def main():
    """Main entry point"""
    monitor = SystemMonitor()
    
    try:
        await monitor.run_continuous_monitoring()
    except KeyboardInterrupt:
        logger.info("🛑 System monitor stopped")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
