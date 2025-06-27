#!/usr/bin/env python3
"""
Test script to debug embedding initialization
"""

import asyncio
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, '/opt/backend')

# Set environment variables
os.environ['EMBEDDING_MODEL'] = 'intfloat/e5-small-v2'
os.environ['EMBEDDING_PROVIDER'] = 'huggingface'
os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/opt/internal_cache/sentence_transformers'

from database_manager import DatabaseManager, db_manager
from human_logging import log_service_status

async def test_global_db_manager():
    """Test the global database manager initialization"""
    print("=== Testing Global Database Manager ===")
    
    print(f"Global db_manager: {db_manager}")
    print(f"db_manager type: {type(db_manager)}")
    
    if db_manager:
        print(f"db_manager._initialized: {db_manager._initialized}")
        print(f"db_manager._initialization_failed: {db_manager._initialization_failed}")
        print(f"db_manager.embedding_model: {db_manager.embedding_model}")
        print(f"db_manager.chroma_client: {db_manager.chroma_client}")
        
        # Try to manually initialize
        print("\nCalling ensure_initialized()...")
        try:
            result = await db_manager.ensure_initialized()
            print(f"ensure_initialized() returned: {result}")
            
            print(f"After ensure_initialized:")
            print(f"  _initialized: {db_manager._initialized}")
            print(f"  _initialization_failed: {db_manager._initialization_failed}")
            print(f"  embedding_model: {db_manager.embedding_model}")
            print(f"  chroma_client: {db_manager.chroma_client}")
            
        except Exception as e:
            print(f"❌ Error during ensure_initialized(): {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Global db_manager is None")

async def test_manual_init():
    """Test manual initialization of all components"""
    print("\n=== Testing Manual Initialization ===")
    
    if db_manager:
        try:
            print("Calling _initialize_all() directly...")
            await db_manager._initialize_all()
            
            print(f"After _initialize_all():")
            print(f"  _initialized: {db_manager._initialized}")
            print(f"  embedding_model: {db_manager.embedding_model}")
            print(f"  chroma_client: {db_manager.chroma_client}")
            
        except Exception as e:
            print(f"❌ Error during _initialize_all(): {e}")
            import traceback
            traceback.print_exc()

async def main():
    await test_global_db_manager()
    await test_manual_init()

if __name__ == "__main__":
    asyncio.run(main())
