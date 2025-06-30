#!/usr/bin/env python3
"""
Automatic Memory Function Installer
==================================

This script automatically installs the memory function into OpenWebUI
when the containers start up. It waits for OpenWebUI to be ready and
then installs the function.
"""

import json
import time
import logging
import sys
import os
from pathlib import Path
from typing import Optional
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/function_installer.log')
    ]
)
logger = logging.getLogger(__name__)

class FunctionInstaller:
    def __init__(self, openwebui_url: str = None, max_retries: int = 30):
        self.openwebui_url = openwebui_url or os.getenv("OPENWEBUI_URL", "http://openwebui:8080")
        self.max_retries = max_retries
        self.retry_delay = 10  # seconds
        
    def wait_for_openwebui(self) -> bool:
        """Wait for OpenWebUI to be ready"""
        logger.info(f"🔍 Waiting for OpenWebUI at {self.openwebui_url}...")
        
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{self.openwebui_url}/api/v1/auths")
                    if response.status_code == 200:
                        logger.info("✅ OpenWebUI is ready!")
                        return True
            except Exception as e:
                logger.debug(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")
            
            if attempt < self.max_retries - 1:
                logger.info(f"⏳ OpenWebUI not ready, waiting {self.retry_delay}s... (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(self.retry_delay)
        
        logger.error("❌ OpenWebUI did not become ready within the timeout period")
        return False

    def read_function_code(self) -> Optional[str]:
        """Read the memory function code"""
        possible_paths = [
            Path("/app/memory_function.py"),
            Path("/opt/backend/memory_function.py"),
            Path("./memory_function.py"),
            Path("/memory_function.py")
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"📖 Reading function code from {path}")
                return path.read_text(encoding='utf-8')
        
        logger.error("❌ Memory function file not found in any expected location")
        logger.error(f"   Searched paths: {[str(p) for p in possible_paths]}")
        return None

    def install_function(self) -> bool:
        """Install the memory function"""
        logger.info("🔧 Installing memory function...")
        
        # Read function code
        function_code = self.read_function_code()
        if not function_code:
            return False

        # Create function payload
        function_payload = {
            "id": "memory_function",
            "name": "Enhanced Memory Function",
            "type": "function",
            "content": function_code,
            "is_active": True,
            "is_global": True
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                headers = {"Content-Type": "application/json"}
                
                # Check if function already exists
                try:
                    functions_response = client.get(f"{self.openwebui_url}/api/v1/functions/")
                    if functions_response.status_code == 200:
                        existing_functions = functions_response.json()
                        existing_function = None
                        
                        for func in existing_functions:
                            if func.get('id') == 'memory_function':
                                existing_function = func
                                break

                        if existing_function:
                            logger.info("⚠️  Memory function exists, updating...")
                            response = client.put(
                                f"{self.openwebui_url}/api/v1/functions/memory_function",
                                json=function_payload,
                                headers=headers
                            )
                        else:
                            logger.info("📦 Installing new memory function...")
                            response = client.post(
                                f"{self.openwebui_url}/api/v1/functions/",
                                json=function_payload,
                                headers=headers
                            )
                    else:
                        logger.warning(f"Could not check existing functions: {functions_response.status_code}")
                        # Try to install anyway
                        response = client.post(
                            f"{self.openwebui_url}/api/v1/functions/",
                            json=function_payload,
                            headers=headers
                        )
                except Exception as e:
                    logger.warning(f"Error checking existing functions: {e}")
                    # Try to install anyway
                    response = client.post(
                        f"{self.openwebui_url}/api/v1/functions/",
                        json=function_payload,
                        headers=headers
                    )

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info("✅ Memory function installed successfully!")
                    logger.info(f"   Function ID: {result.get('id', 'N/A')}")
                    logger.info(f"   Function Name: {result.get('name', 'N/A')}")
                    return True
                else:
                    logger.error(f"❌ Failed to install: HTTP {response.status_code}")
                    logger.error(f"   Response: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to install memory function: {str(e)}")
            return False

    def verify_installation(self) -> bool:
        """Verify the function was installed correctly"""
        logger.info("🔍 Verifying installation...")
        
        try:
            with httpx.Client(timeout=10.0) as client:
                functions_response = client.get(f"{self.openwebui_url}/api/v1/functions/")
                if functions_response.status_code == 200:
                    functions = functions_response.json()
                    
                    for func in functions:
                        if func.get('id') == 'memory_function':
                            logger.info("✅ Memory function verified successfully!")
                            logger.info(f"   Status: {'Active' if func.get('is_active') else 'Inactive'}")
                            logger.info(f"   Global: {'Yes' if func.get('is_global') else 'No'}")
                            return True
                    
                    logger.warning("⚠️  Function not found in verification")
                    return False
                else:
                    logger.error(f"❌ Verification failed: HTTP {functions_response.status_code}")
                    return False
                    
        except Exception as e:
            logger.warning(f"⚠️  Could not verify installation: {str(e)}")
            return False

    def run(self) -> bool:
        """Run the complete installation process"""
        logger.info("🚀 Starting Automatic Memory Function Installation")
        logger.info("=" * 50)
        
        # Wait for OpenWebUI to be ready
        if not self.wait_for_openwebui():
            return False
        
        # Install the function
        if not self.install_function():
            return False
        
        # Verify installation
        self.verify_installation()
        
        logger.info("🎉 Installation process completed!")
        return True

def main():
    installer = FunctionInstaller()
    success = installer.run()
    
    if success:
        logger.info("✅ Memory function installation successful")
        sys.exit(0)
    else:
        logger.error("❌ Memory function installation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
