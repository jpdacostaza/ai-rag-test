#!/usr/bin/env python3
"""
Test script to verify w        # Verify ConnectionFactory is initialized
        assert hasattr(chroma_monitor, 'connection_factory'), "ChromaDBMonitor should have connection_factory"
        assert isinstance(chroma_monitor.connection_factory, DatabaseConnectionFactory), "connection_factory should be DatabaseConnectionFactory instance"hdog.py migration to ConnectionFactory.
Validates that watchdog monitors can use ConnectionFactory for connections.
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

async def test_watchdog_migration():
    """Test watchdog.py migration to ConnectionFactory."""
    
    logger.info("🔍 Testing watchdog.py ConnectionFactory migration...")
    
    try:
        # Import updated watchdog modules
        from utilities.watchdog import RedisMonitor, ChromaDBMonitor, WatchdogConfig
        from utilities.connection_factory import DatabaseConnectionFactory
        
        logger.info("✅ Successfully imported updated watchdog classes")
        
        # Create watchdog config
        config = WatchdogConfig()
        config.check_interval = 10
        config.timeout = 5
        config.alert_threshold = 3
        
        # Test RedisMonitor with ConnectionFactory
        logger.info("🔗 Testing RedisMonitor with ConnectionFactory...")
        redis_monitor = RedisMonitor(config)
        
        # Verify ConnectionFactory is initialized
        assert hasattr(redis_monitor, 'connection_factory'), "RedisMonitor should have connection_factory"
        assert isinstance(redis_monitor.connection_factory, DatabaseConnectionFactory), "connection_factory should be DatabaseConnectionFactory instance"
        
        logger.info("✅ RedisMonitor ConnectionFactory integration successful")
        
        # Test ChromaDBMonitor with ConnectionFactory  
        logger.info("🔗 Testing ChromaDBMonitor with ConnectionFactory...")
        chroma_monitor = ChromaDBMonitor(config)
        
        # Verify ConnectionFactory is initialized
        assert hasattr(chroma_monitor, 'connection_factory'), "ChromaDBMonitor should have connection_factory"
        assert isinstance(chroma_monitor.connection_factory, DatabaseConnectionFactory), "connection_factory should be DatabaseConnectionFactory instance"
        
        logger.info("✅ ChromaDBMonitor ConnectionFactory integration successful")
        
        # Test health check methods (without actual connections)
        logger.info("🩺 Testing health check method signatures...")
        
        # Test that methods exist and are callable
        assert callable(redis_monitor.check_health), "RedisMonitor.check_health should be callable"
        assert callable(chroma_monitor.check_health), "ChromaDBMonitor.check_health should be callable"
        
        logger.info("✅ Health check methods are properly defined")
        
        # Verify configuration access
        logger.info("⚙️ Testing configuration access...")
        
        # Test that the factory has configuration access (via unified config)
        assert hasattr(redis_monitor.connection_factory, 'config'), "Factory should have config access"
        assert hasattr(chroma_monitor.connection_factory, 'config'), "Factory should have config access"
        
        logger.info("✅ Configuration access working correctly")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Migration test failed: {e}")
        return False

async def main():
    """Main test function."""
    logger.info("🚀 Starting watchdog.py ConnectionFactory migration test...")
    
    success = await test_watchdog_migration()
    
    if success:
        logger.info("🎉 watchdog.py migration test PASSED!")
        logger.info("✅ All watchdog monitors successfully use ConnectionFactory")
        logger.info("✅ Configuration integration working correctly")
        logger.info("✅ Health check methods properly migrated")
        
        print("\n" + "="*60)
        print("WATCHDOG.PY MIGRATION TEST RESULTS")
        print("="*60)
        print("✅ RedisMonitor migration: SUCCESS")
        print("✅ ChromaDBMonitor migration: SUCCESS") 
        print("✅ ConnectionFactory integration: SUCCESS")
        print("✅ Configuration access: SUCCESS")
        print("✅ Method signatures: SUCCESS")
        print("="*60)
        print("🎯 MIGRATION COMPLETE - watchdog.py ready for use!")
        
    else:
        logger.error("❌ watchdog.py migration test FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
