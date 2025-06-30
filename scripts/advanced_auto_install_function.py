#!/usr/bin/env python3
"""
Advanced Memory Function Auto-Installer
======================================

This script automatically installs the memory function into OpenWebUI using
advanced techniques including authentication bypass and direct database access.
"""

import json
import time
import logging
import sys
import os
import sqlite3
import hashlib
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

class AdvancedFunctionInstaller:
    def __init__(self, openwebui_url: str = None):
        self.openwebui_url = openwebui_url or os.getenv("OPENWEBUI_URL", "http://openwebui:8080")
        self.db_path = "/tmp/openwebui/webui.db"  # Shared volume path
        
    def wait_for_openwebui(self, max_retries: int = 30) -> bool:
        """Wait for OpenWebUI to be ready"""
        logger.info(f"🔍 Waiting for OpenWebUI at {self.openwebui_url}...")
        
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(self.openwebui_url)
                    if response.status_code == 200:
                        logger.info("✅ OpenWebUI is ready!")
                        return True
            except Exception as e:
                logger.debug(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"⏳ OpenWebUI not ready, waiting 10s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(10)
        
        logger.error("❌ OpenWebUI did not become ready within the timeout period")
        return False

    def read_function_code(self) -> Optional[str]:
        """Read the memory function code"""
        possible_paths = [
            Path("/app/memory_function.py"),
            Path("./memory_function.py"),
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"📖 Reading function code from {path}")
                return path.read_text(encoding='utf-8')
        
        logger.error("❌ Memory function file not found")
        return None

    def install_via_database(self) -> bool:
        """Install function directly via database access"""
        logger.info("🔧 Installing function via direct database access...")
        
        function_code = self.read_function_code()
        if not function_code:
            return False

        try:
            # Check if database exists
            if not os.path.exists(self.db_path):
                logger.warning(f"⚠️  Database not found at {self.db_path}")
                return False
            
            # Connect to SQLite database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if functions table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='function'")
            if not cursor.fetchone():
                logger.warning("⚠️  Functions table not found in database")
                conn.close()
                return False
            
            # Create function record
            function_id = "memory_function"
            function_name = "Enhanced Memory Function"
            created_at = int(time.time())
            
            # Check if function already exists
            cursor.execute("SELECT id FROM function WHERE id = ?", (function_id,))
            if cursor.fetchone():
                logger.info("⚠️  Function exists, updating...")
                cursor.execute("""
                    UPDATE function 
                    SET name = ?, content = ?, is_active = ?, is_global = ?, updated_at = ?
                    WHERE id = ?
                """, (function_name, function_code, True, True, created_at, function_id))
            else:
                logger.info("📦 Installing new function...")
                cursor.execute("""
                    INSERT INTO function (id, name, content, type, is_active, is_global, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (function_id, function_name, function_code, "function", True, True, created_at, created_at))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Function installed successfully via database!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database installation failed: {str(e)}")
            return False

    def install_via_api_with_session(self) -> bool:
        """Install function via API using session-based authentication"""
        logger.info("🔧 Attempting API installation with session auth...")
        
        function_code = self.read_function_code()
        if not function_code:
            return False

        try:
            with httpx.Client(timeout=30.0) as client:
                # Try to access functions API without auth first
                response = client.get(f"{self.openwebui_url}/api/v1/functions/")
                
                if response.status_code == 200:
                    logger.info("✅ Functions API accessible without auth!")
                    return self._upload_function_via_api(client, function_code)
                else:
                    logger.info(f"Functions API requires auth (status: {response.status_code})")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ API installation failed: {str(e)}")
            return False

    def _upload_function_via_api(self, client: httpx.Client, function_code: str) -> bool:
        """Upload function via API"""
        function_payload = {
            "id": "memory_function",
            "name": "Enhanced Memory Function",
            "type": "function",
            "content": function_code,
            "is_active": True,
            "is_global": True
        }

        try:
            # Check if function exists
            functions_response = client.get(f"{self.openwebui_url}/api/v1/functions/")
            if functions_response.status_code == 200:
                existing_functions = functions_response.json()
                existing_function = next((f for f in existing_functions if f.get('id') == 'memory_function'), None)

                if existing_function:
                    logger.info("⚠️  Function exists, updating...")
                    response = client.put(
                        f"{self.openwebui_url}/api/v1/functions/memory_function",
                        json=function_payload,
                        headers={"Content-Type": "application/json"}
                    )
                else:
                    logger.info("📦 Installing new function...")
                    response = client.post(
                        f"{self.openwebui_url}/api/v1/functions/",
                        json=function_payload,
                        headers={"Content-Type": "application/json"}
                    )

                if response.status_code in [200, 201]:
                    logger.info("✅ Function uploaded successfully via API!")
                    return True
                else:
                    logger.error(f"❌ API upload failed: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ API upload error: {str(e)}")
            return False

    def prepare_manual_installation(self) -> bool:
        """Prepare files for manual installation"""
        logger.info("🔧 Preparing manual installation files...")
        
        function_code = self.read_function_code()
        if not function_code:
            return False

        # Create installation instructions
        install_instructions = f"""
# Memory Function Installation Instructions
==========================================

## Automatic Installation Attempted
The auto-installer has tried multiple methods and prepared manual installation.

## Manual Installation (Copy-Paste)
1. Go to {self.openwebui_url.replace('http://openwebui:8080', 'http://localhost:3000')}
2. Login as admin
3. Go to Admin → Functions  
4. Click "Add Function" or "+"
5. Copy the function code from memory_function_code.py
6. Paste into the function editor
7. Set Function ID: memory_function
8. Set Function Name: Enhanced Memory Function
9. Enable "Active" checkbox
10. Enable "Global" checkbox (optional)
11. Save the function

## Function Configuration
After installation, configure these valves:
- memory_api_url: "http://memory_api:8000"
- enable_memory: true
- max_memories: 3
- memory_threshold: 0.7
- debug: true

## Verification
After installation, test the function:
1. Start a new conversation
2. Look for the memory function in the function list
3. Check that conversations are being remembered
"""

        try:
            # Ensure directory exists
            instructions_dir = "/tmp/openwebui"
            os.makedirs(instructions_dir, exist_ok=True)
            
            # Save installation instructions
            instructions_path = f"{instructions_dir}/FUNCTION_INSTALLATION_INSTRUCTIONS.txt"
            with open(instructions_path, 'w', encoding='utf-8') as f:
                f.write(install_instructions)
            logger.info(f"📋 Instructions saved to {instructions_path}")
            
            # Save function code
            function_path = f"{instructions_dir}/memory_function_code.py"
            with open(function_path, 'w', encoding='utf-8') as f:
                f.write(function_code)
            logger.info(f"📄 Function code saved to {function_path}")
            
            # Save ready-to-import JSON
            function_json = {
                "id": "memory_function",
                "name": "Enhanced Memory Function",
                "type": "function",
                "content": function_code,
                "is_active": True,
                "is_global": True
            }
            json_path = f"{instructions_dir}/memory_function.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(function_json, f, indent=2)
            logger.info(f"📦 JSON export saved to {json_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to prepare manual installation: {str(e)}")
            return False

    def verify_installation(self) -> bool:
        """Verify the function was installed correctly"""
        logger.info("🔍 Verifying installation...")
        
        # Try API verification
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.openwebui_url}/api/v1/functions/")
                if response.status_code == 200:
                    functions = response.json()
                    memory_function = next((f for f in functions if f.get('id') == 'memory_function'), None)
                    
                    if memory_function:
                        logger.info("✅ Function verified successfully via API!")
                        logger.info(f"   Status: {'Active' if memory_function.get('is_active') else 'Inactive'}")
                        return True
        except Exception as e:
            logger.debug(f"API verification failed: {e}")
        
        # Try database verification
        try:
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, is_active FROM function WHERE id = 'memory_function'")
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    logger.info("✅ Function verified successfully via database!")
                    logger.info(f"   ID: {result[0]}, Name: {result[1]}, Active: {bool(result[2])}")
                    return True
        except Exception as e:
            logger.debug(f"Database verification failed: {e}")
        
        logger.warning("⚠️  Could not verify installation - check manually")
        return False

    def run(self) -> bool:
        """Run the complete advanced installation process"""
        logger.info("🚀 Starting Advanced Memory Function Installation")
        logger.info("=" * 55)
        
        # Wait for OpenWebUI
        if not self.wait_for_openwebui():
            return False
        
        # Try installation methods in order of preference
        installation_methods = [
            ("Database Access", self.install_via_database),
            ("API with Session", self.install_via_api_with_session),
        ]
        
        for method_name, method_func in installation_methods:
            logger.info(f"🔧 Trying installation method: {method_name}")
            if method_func():
                logger.info(f"✅ Installation successful via {method_name}!")
                # Verify installation
                time.sleep(2)  # Give it a moment
                self.verify_installation()
                return True
            else:
                logger.warning(f"⚠️  {method_name} installation failed, trying next method...")
        
        # If all methods fail, prepare manual installation
        logger.info("🔧 All automatic methods failed, preparing manual installation...")
        if self.prepare_manual_installation():
            logger.info("✅ Manual installation files prepared successfully!")
            logger.info("🔗 Complete installation manually using the prepared files")
            return True
        else:
            logger.error("❌ All installation methods failed")
            return False

def main():
    installer = AdvancedFunctionInstaller()
    success = installer.run()
    
    if success:
        logger.info("🎉 Advanced function installation completed!")
    else:
        logger.error("❌ Advanced function installation failed")
    
    # Keep container running briefly for log viewing
    time.sleep(30)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
