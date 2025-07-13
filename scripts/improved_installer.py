#!/usr/bin/env python3
"""
Improved Pipeline and Module Installer
Handles installation of OpenWebUI functions and pipelines more reliably.
"""

import asyncio
import aiohttp
import json
import time
import logging
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'installer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)

logger = logging.getLogger('ImprovedInstaller')

class ImprovedInstaller:
    def __init__(self):
        self.openwebui_url = os.getenv('OPENWEBUI_URL', 'http://localhost:8080')
        self.pipelines_url = os.getenv('PIPELINES_URL', 'http://localhost:9099')
        self.max_retries = 20
        self.retry_delay = 10
        
        # File paths - adjust for Docker vs host environment
        self.base_path = '/app' if os.path.exists('/app') else '.'
        self.functions_dir = os.path.join(self.base_path, 'memory', 'functions')
        self.pipelines_dir = os.path.join(self.base_path, 'pipelines')
        
        logger.info(f"Base path: {self.base_path}")
        logger.info(f"Functions dir: {self.functions_dir}")
        logger.info(f"Pipelines dir: {self.pipelines_dir}")
        
    async def wait_for_service(self, service_name: str, url: str, health_endpoint: str = '/health') -> bool:
        """Wait for a service to become available"""
        logger.info(f"⏳ Waiting for {service_name} at {url}...")
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for attempt in range(self.max_retries):
                try:
                    async with session.get(f"{url}{health_endpoint}") as response:
                        if response.status == 200:
                            logger.info(f"✅ {service_name} is ready!")
                            return True
                        else:
                            logger.info(f"🔄 {service_name} returned status {response.status}, retrying...")
                            
                except Exception as e:
                    logger.info(f"🔄 Attempt {attempt + 1}/{self.max_retries}: {service_name} not ready yet - {str(e)}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    
        logger.error(f"❌ Failed to connect to {service_name} after {self.max_retries} attempts")
        return False

    def ensure_directories(self):
        """Ensure required directories exist"""
        directories = [self.functions_dir, self.pipelines_dir]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"📁 Created directory: {directory}")
            else:
                logger.info(f"📁 Directory exists: {directory}")

    def install_memory_function(self) -> bool:
        """Install the memory function file"""
        logger.info("🔧 Installing Enhanced Memory Function...")
        
        # Source file path
        source_file = os.path.join(self.base_path, 'memory', 'functions', 'memory_function.py')
        
        if not os.path.exists(source_file):
            logger.error(f"❌ Source file not found: {source_file}")
            # Try alternative paths
            alt_paths = [
                os.path.join(self.base_path, 'memory_function.py'),
                './memory_function.py',
                './memory/functions/memory_function.py'
            ]
            
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    logger.info(f"📁 Found alternative source: {alt_path}")
                    source_file = alt_path
                    break
            else:
                logger.error("❌ No memory function source file found")
                return False
        
        # Ensure target directory exists
        os.makedirs(self.functions_dir, exist_ok=True)
        
        # Copy file
        target_file = os.path.join(self.functions_dir, 'memory_function.py')
        try:
            shutil.copy2(source_file, target_file)
            
            # Verify installation
            if os.path.exists(target_file):
                file_size = os.path.getsize(target_file)
                logger.info(f"✅ Memory function installed successfully: {target_file}")
                logger.info(f"✅ File size: {file_size} bytes")
                return True
            else:
                logger.error(f"❌ File copy failed: {target_file}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error copying memory function: {str(e)}")
            return False

    def install_memory_pipeline(self) -> bool:
        """Install the memory pipeline file"""
        logger.info("🔧 Installing Enhanced Memory Pipeline...")
        
        # Source file path
        source_file = os.path.join(self.base_path, 'pipelines', 'enhanced_memory_pipeline.py')
        
        if not os.path.exists(source_file):
            logger.error(f"❌ Source file not found: {source_file}")
            # Try alternative paths
            alt_paths = [
                './pipelines/enhanced_memory_pipeline.py',
                './enhanced_memory_pipeline.py'
            ]
            
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    logger.info(f"📁 Found alternative source: {alt_path}")
                    source_file = alt_path
                    break
            else:
                logger.error("❌ No memory pipeline source file found")
                return False
        
        # Ensure target directory exists
        os.makedirs(self.pipelines_dir, exist_ok=True)
        
        # Target file path (in the pipelines service directory)
        target_file = os.path.join(self.pipelines_dir, 'enhanced_memory_pipeline.py')
        
        try:
            shutil.copy2(source_file, target_file)
            
            # Verify installation
            if os.path.exists(target_file):
                file_size = os.path.getsize(target_file)
                logger.info(f"✅ Memory pipeline installed successfully: {target_file}")
                logger.info(f"✅ File size: {file_size} bytes")
                return True
            else:
                logger.error(f"❌ File copy failed: {target_file}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error copying memory pipeline: {str(e)}")
            return False

    async def verify_installations(self) -> Dict[str, bool]:
        """Verify that installations are working"""
        logger.info("🔍 Verifying installations...")
        results = {}
        
        # Check if OpenWebUI can access the function
        try:
            async with aiohttp.ClientSession() as session:
                # Check OpenWebUI API
                async with session.get(f"{self.openwebui_url}/api/config") as response:
                    if response.status == 200:
                        results['openwebui_api'] = True
                        logger.info("✅ OpenWebUI API accessible")
                    else:
                        results['openwebui_api'] = False
                        logger.warning(f"⚠️ OpenWebUI API returned {response.status}")
        except Exception as e:
            results['openwebui_api'] = False
            logger.error(f"❌ OpenWebUI API check failed: {str(e)}")
        
        # Check if Pipelines can access the pipeline
        try:
            async with aiohttp.ClientSession() as session:
                # Check Pipelines API
                async with session.get(f"{self.pipelines_url}/") as response:
                    if response.status == 200:
                        results['pipelines_api'] = True
                        logger.info("✅ Pipelines API accessible")
                    else:
                        results['pipelines_api'] = False
                        logger.warning(f"⚠️ Pipelines API returned {response.status}")
        except Exception as e:
            results['pipelines_api'] = False
            logger.error(f"❌ Pipelines API check failed: {str(e)}")
        
        # Check file installations
        function_file = os.path.join(self.functions_dir, 'memory_function.py')
        pipeline_file = os.path.join(self.pipelines_dir, 'enhanced_memory_pipeline.py')
        
        results['function_file'] = os.path.exists(function_file)
        results['pipeline_file'] = os.path.exists(pipeline_file)
        
        if results['function_file']:
            logger.info(f"✅ Memory function file present: {function_file}")
        else:
            logger.error(f"❌ Memory function file missing: {function_file}")
            
        if results['pipeline_file']:
            logger.info(f"✅ Memory pipeline file present: {pipeline_file}")
        else:
            logger.error(f"❌ Memory pipeline file missing: {pipeline_file}")
        
        return results

    async def run_installation(self) -> bool:
        """Run the complete installation process"""
        logger.info("🚀 Starting Improved Installation Process")
        logger.info("=" * 60)
        
        # Ensure directories exist
        self.ensure_directories()
        
        # Wait for services (but don't fail if OpenWebUI isn't ready yet)
        pipelines_ready = await self.wait_for_service("Pipelines", self.pipelines_url, "/")
        if not pipelines_ready:
            logger.warning("⚠️ Pipelines service not ready, but continuing with file installation")
        
        # Install files regardless of service readiness
        function_success = self.install_memory_function()
        pipeline_success = self.install_memory_pipeline()
        
        # Verify installations
        verification_results = await self.verify_installations()
        
        # Print summary
        logger.info("=" * 60)
        logger.info("📋 Installation Summary:")
        logger.info(f"   • Memory Function: {'✅ Success' if function_success else '❌ Failed'}")
        logger.info(f"   • Memory Pipeline: {'✅ Success' if pipeline_success else '❌ Failed'}")
        logger.info(f"   • OpenWebUI API: {'✅ Ready' if verification_results.get('openwebui_api', False) else '❌ Not Ready'}")
        logger.info(f"   • Pipelines API: {'✅ Ready' if verification_results.get('pipelines_api', False) else '❌ Not Ready'}")
        
        overall_success = function_success and pipeline_success
        
        if overall_success:
            logger.info("🎉 Installation completed successfully!")
            logger.info("")
            logger.info("📚 Next Steps:")
            logger.info("   • Memory system is ready for use")
            logger.info("   • Function will be auto-loaded by OpenWebUI")
            logger.info("   • Pipeline will be auto-loaded by Pipelines service")
            logger.info("")
            logger.info("🔗 Access your memory-enhanced system at:")
            logger.info("   • OpenWebUI: http://localhost:8080")
            logger.info("   • Pipelines: http://localhost:9099")
        else:
            logger.error("❌ Installation had errors - check logs above")
        
        logger.info("=" * 60)
        return overall_success

async def main():
    """Main installer execution"""
    installer = ImprovedInstaller()
    success = await installer.run_installation()
    
    if success:
        logger.info("✅ Installer completed successfully")
        return 0
    else:
        logger.error("❌ Installer completed with errors")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
