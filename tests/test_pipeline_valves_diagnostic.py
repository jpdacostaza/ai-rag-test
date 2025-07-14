#!/usr/bin/env python3
"""
Pipeline Valves Diagnostic Tool
==============================

Quick diagnostic to check pipeline valves configuration and memory system status.
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

async def check_pipeline_valves():
    """Check pipeline valves configuration"""
    logger.info("🔧 PIPELINE VALVES DIAGNOSTIC")
    logger.info("=" * 50)
    
    try:
        # Try to import and inspect the pipeline
        import sys
        import os
        
        # Add the project root to the path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # Import the pipeline
        from pipelines.enhanced_memory_pipeline import Pipeline
        
        # Create pipeline instance
        pipeline = Pipeline()
        
        logger.info("✅ Pipeline instance created successfully")
        
        # Check valves configuration
        logger.info(f"📋 VALVES CONFIGURATION:")
        logger.info(f"   Type: {pipeline.type}")
        logger.info(f"   Name: {pipeline.name}")
        
        if hasattr(pipeline, 'valves'):
            valves = pipeline.valves
            logger.info(f"   Pipelines: {getattr(valves, 'pipelines', 'Not set')}")
            logger.info(f"   Priority: {getattr(valves, 'priority', 'Not set')}")
            logger.info(f"   Backend URL: {getattr(valves, 'backend_url', 'Not set')}")
            logger.info(f"   Enable Memory: {getattr(valves, 'enable_memory', 'Not set')}")
            logger.info(f"   Max Memories: {getattr(valves, 'max_memories', 'Not set')}")
            logger.info(f"   API Timeout: {getattr(valves, 'api_timeout', 'Not set')}")
            logger.info(f"   Debug Mode: {getattr(valves, 'debug_mode', 'Not set')}")
        else:
            logger.error("❌ No valves found on pipeline instance")
        
        # Check memory system components
        logger.info(f"\n🧠 MEMORY SYSTEM COMPONENTS:")
        logger.info(f"   API Client: {'✅ Available' if hasattr(pipeline, 'api_client') else '❌ Not available'}")
        logger.info(f"   Auth Manager: {'✅ Available' if hasattr(pipeline, 'auth_manager') else '❌ Not available'}")
        logger.info(f"   Memory Processor: {'✅ Available' if hasattr(pipeline, 'memory_processor') else '❌ Not available'}")
        
        # Check memory manager property
        logger.info(f"\n🔗 MEMORY MANAGER:")
        if hasattr(pipeline, 'memory_manager'):
            memory_manager = pipeline.memory_manager
            logger.info(f"   Memory Manager: {'✅ Available' if memory_manager else '❌ None'}")
            if memory_manager:
                logger.info(f"   Type: {type(memory_manager)}")
                logger.info(f"   Has get_relevant_memories: {'✅ Yes' if hasattr(memory_manager, 'get_relevant_memories') else '❌ No'}")
                logger.info(f"   Has store_memory: {'✅ Yes' if hasattr(memory_manager, 'store_memory') else '❌ No'}")
        else:
            logger.error("❌ No memory_manager property found")
        
        # Check if memory is enabled
        enable_memory = getattr(pipeline.valves, 'enable_memory', False) if hasattr(pipeline, 'valves') else False
        logger.info(f"\n🎯 MEMORY STATUS:")
        logger.info(f"   Memory Enabled: {'✅ YES' if enable_memory else '❌ NO'}")
        
        if not enable_memory:
            logger.warning("⚠️ MEMORY IS DISABLED - This will cause 'Pipeline memory retrieval method not available' warnings")
            logger.info("💡 Recommendation: Check memory system component availability and enable memory in valves")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pipeline diagnostic failed: {str(e)}")
        return False

async def check_memory_api_connectivity():
    """Check connectivity to memory API"""
    logger.info(f"\n🌐 MEMORY API CONNECTIVITY CHECK:")
    logger.info("=" * 50)
    
    memory_api_url = "http://localhost:5001"
    
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test health endpoint
            async with session.get(f"{memory_api_url}/health") as response:
                if response.status == 200:
                    logger.info(f"✅ Memory API Health: OK (HTTP {response.status})")
                else:
                    logger.warning(f"⚠️ Memory API Health: HTTP {response.status}")
            
            # Test store endpoint with a test payload
            test_payload = {
                "user_id": "test_user",
                "content": "Test connectivity check",
                "metadata": {"type": "connectivity_test"}
            }
            
            async with session.post(f"{memory_api_url}/store", json=test_payload) as response:
                if response.status == 200:
                    logger.info(f"✅ Memory API Store: OK (HTTP {response.status})")
                else:
                    logger.warning(f"⚠️ Memory API Store: HTTP {response.status}")
                    
    except Exception as e:
        logger.error(f"❌ Memory API connectivity failed: {str(e)}")

async def main():
    """Main diagnostic function"""
    logger.info("🚀 STARTING PIPELINE VALVES DIAGNOSTIC")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("=" * 80)
    
    # Check pipeline valves
    pipeline_ok = await check_pipeline_valves()
    
    # Check memory API connectivity
    await check_memory_api_connectivity()
    
    logger.info("=" * 80)
    logger.info(f"🏁 DIAGNOSTIC COMPLETE")
    
    if pipeline_ok:
        logger.info("✅ Pipeline diagnostic completed successfully")
    else:
        logger.error("❌ Pipeline diagnostic found issues")

if __name__ == "__main__":
    asyncio.run(main())
