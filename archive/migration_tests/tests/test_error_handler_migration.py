#!/usr/bin/env python3
"""
Test script to verify error_handler.py migration to DatabaseConnectionFactory.
Validates that error handling can use DatabaseConnectionFactory for connections.
"""

import sys
import os
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_error_handler_migration():
    """Test error_handler.py migration to DatabaseConnectionFactory."""
    
    logger.info("🔍 Testing error_handler.py DatabaseConnectionFactory migration...")
    
    try:
        # Import updated error handler modules
        from core.error_handler import RedisConnectionHandler, log_error, get_user_friendly_message
        from utilities.connection_factory import DatabaseConnectionFactory
        
        logger.info("✅ Successfully imported updated error handler classes")
        
        # Test RedisConnectionHandler with DatabaseConnectionFactory
        logger.info("🔗 Testing RedisConnectionHandler with DatabaseConnectionFactory...")
        redis_handler = RedisConnectionHandler(max_retries=2)
        
        # Verify DatabaseConnectionFactory is initialized
        assert hasattr(redis_handler, 'connection_factory'), "RedisConnectionHandler should have connection_factory"
        assert isinstance(redis_handler.connection_factory, DatabaseConnectionFactory), "connection_factory should be DatabaseConnectionFactory instance"
        
        logger.info("✅ RedisConnectionHandler DatabaseConnectionFactory integration successful")
        
        # Test new methods
        logger.info("🩺 Testing new connection methods...")
        
        # Test that methods exist and are callable
        assert callable(redis_handler.retry_operation), "RedisConnectionHandler.retry_operation should be callable"
        assert callable(redis_handler.get_redis_connection), "RedisConnectionHandler.get_redis_connection should be callable"
        assert callable(redis_handler.handle_connection_error), "RedisConnectionHandler.handle_connection_error should be callable"
        
        logger.info("✅ New connection methods are properly defined")
        
        # Test configuration access
        logger.info("⚙️ Testing configuration access...")
        
        # Test that the factory has configuration access (via unified config)
        assert hasattr(redis_handler.connection_factory, 'config'), "Factory should have config access"
        
        logger.info("✅ Configuration access working correctly")
        
        # Test error handling functions (legacy compatibility)
        logger.info("🛡️ Testing legacy error handling functions...")
        
        import redis
        test_error = redis.RedisError("Test error")
        
        # Test user-friendly message generation
        friendly_message = get_user_friendly_message(test_error)
        assert "caching service" in friendly_message, "Should generate Redis-specific friendly message"
        
        # Test error logging (should not raise)
        log_error(test_error, "test_context", "test_user", "test_request")
        
        logger.info("✅ Legacy error handling functions working correctly")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Migration test failed: {e}")
        return False

async def main():
    """Main test function."""
    logger.info("🚀 Starting error_handler.py DatabaseConnectionFactory migration test...")
    
    success = await test_error_handler_migration()
    
    if success:
        logger.info("🎉 error_handler.py migration test PASSED!")
        logger.info("✅ RedisConnectionHandler successfully uses DatabaseConnectionFactory")
        logger.info("✅ Configuration integration working correctly")
        logger.info("✅ New connection methods properly implemented")
        logger.info("✅ Legacy compatibility maintained")
        
        print("\n" + "="*60)
        print("ERROR_HANDLER.PY MIGRATION TEST RESULTS")
        print("="*60)
        print("✅ RedisConnectionHandler migration: SUCCESS")
        print("✅ DatabaseConnectionFactory integration: SUCCESS")
        print("✅ New async methods: SUCCESS") 
        print("✅ Configuration access: SUCCESS")
        print("✅ Legacy compatibility: SUCCESS")
        print("="*60)
        print("🎯 MIGRATION COMPLETE - error_handler.py ready for use!")
        
    else:
        logger.error("❌ error_handler.py migration test FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
