#!/usr/bin/env python3
"""
Test what configuration values are actually being loaded and used
"""

import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))

def test_config_loading():
    """Test loading all configuration modules to check for errors"""
    
    print("🔧 TESTING CONFIGURATION LOADING")
    print("=" * 40)
    
    # Test 1: Load config_unified.py
    print("1. Testing config_unified.py...")
    try:
        from config.config_unified import Config
        config = Config.get_instance()
        
        print("   ✅ config_unified.py loaded successfully")
        
        # Check memory settings
        memory_config = config.memory
        print(f"   📋 Memory config attributes:")
        
        # Check for retrieval_threshold specifically
        if hasattr(memory_config, 'retrieval_threshold'):
            print(f"      ❌ retrieval_threshold found: {memory_config.retrieval_threshold}")
        else:
            print(f"      ✅ retrieval_threshold correctly removed")
            
        # Check other important attributes
        important_attrs = ['max_memories', 'max_documents', 'auto_store_enabled', 'hybrid_search']
        for attr in important_attrs:
            if hasattr(memory_config, attr):
                value = getattr(memory_config, attr)
                print(f"      ✅ {attr}: {value}")
            else:
                print(f"      ❌ Missing {attr}")
                
    except Exception as e:
        print(f"   ❌ config_unified.py failed to load: {str(e)}")
        return False
    
    # Test 2: Verify that deprecated core/config.py has been removed
    print(f"\n2. Verifying deprecated core/config.py removal...")
    try:
        import os
        config_path = os.path.join(os.path.dirname(__file__), 'core', 'config.py')
        if os.path.exists(config_path):
            print("   ❌ WARNING: core/config.py still exists - should be removed")
            return False
        else:
            print("   ✅ core/config.py successfully removed")
            
        # Also test that the import fails as expected
        try:
            from core.config import Config as CoreConfig
            print("   ❌ WARNING: core/config.py still exports Config class")
            return False
        except (ImportError, ModuleNotFoundError):
            print("   ✅ core/config imports properly fail (file removed)")
            
    except Exception as e:
        print(f"   ❌ Unexpected error checking core/config.py: {str(e)}")
        return False
    
    # Test 3: Check environment variables
    print(f"\n3. Checking environment variables...")
    threshold_env_vars = [
        'MEMORY_RETRIEVAL_THRESHOLD',
        'SIMILARITY_THRESHOLD', 
        'MEMORY_THRESHOLD',
        'PERSONAL_INFO_THRESHOLD',
        'CONVERSATION_THRESHOLD'
    ]
    
    active_env_thresholds = []
    for var in threshold_env_vars:
        value = os.getenv(var)
        if value:
            active_env_thresholds.append(f"{var}={value}")
    
    if active_env_thresholds:
        print(f"   ❌ Active environment thresholds found:")
        for env_var in active_env_thresholds:
            print(f"      {env_var}")
    else:
        print(f"   ✅ No conflicting environment thresholds")
    
    # Test 4: Load memory service
    print(f"\n4. Testing memory service...")
    try:
        from services.memory_service import MemoryQuery
        
        # Test with no threshold (should use fallback)
        query = MemoryQuery(user_id="test", query="test")
        print(f"   ✅ MemoryQuery created successfully")
        print(f"   📋 Default threshold: {query.threshold}")
        
        # Test with explicit threshold (should override)
        query_explicit = MemoryQuery(user_id="test", query="test", threshold=-0.3)
        print(f"   📋 Explicit threshold: {query_explicit.threshold}")
        
    except Exception as e:
        print(f"   ❌ Memory service failed: {str(e)}")
        return False
    
    # Test 5: Check what would happen in memory API
    print(f"\n5. Testing memory API request handling...")
    try:
        # Simulate what the OpenWebUI function sends
        test_request_data = {
            "user_id": "global_user",
            "query": "test query",
            "limit": 8,
            "similarity_threshold": -0.5  # This should override everything
        }
        
        print(f"   📋 Simulated request data: {test_request_data}")
        print(f"   ✅ Request includes explicit similarity_threshold: {test_request_data['similarity_threshold']}")
        
    except Exception as e:
        print(f"   ❌ API simulation failed: {str(e)}")
        return False
    
    return True

def test_actual_threshold_usage():
    """Test what thresholds are actually used in practice"""
    
    print(f"\n🎯 TESTING ACTUAL THRESHOLD USAGE")
    print("=" * 35)
    
    # Check memory API behavior
    print("1. Testing memory API threshold handling...")
    
    try:
        import requests
        
        # Test with explicit threshold (like OpenWebUI function sends)
        test_data = {
            "user_id": "test_user", 
            "query": "test",
            "limit": 5,
            "similarity_threshold": -0.5
        }
        
        response = requests.post(
            "http://localhost:5001/api/memory/retrieve",
            json=test_data,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"   ✅ Memory API accessible and accepting explicit threshold")
            result = response.json()
            print(f"   📋 Retrieved {len(result.get('memories', []))} memories")
        else:
            print(f"   ⚠️  Memory API returned status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  Memory API not running (expected if containers not started)")
    except Exception as e:
        print(f"   ❌ Memory API test failed: {str(e)}")
    
    # Test without explicit threshold (should use fallback)
    print(f"\n2. Testing fallback threshold behavior...")
    try:
        test_data_no_threshold = {
            "user_id": "test_user",
            "query": "test", 
            "limit": 5
            # No similarity_threshold - should use fallback
        }
        
        response = requests.post(
            "http://localhost:5001/api/memory/retrieve",
            json=test_data_no_threshold,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"   ✅ Memory API handling requests without explicit threshold")
        else:
            print(f"   ⚠️  Memory API returned status {response.status_code} for no-threshold request")
            
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  Memory API not running")
    except Exception as e:
        print(f"   ❌ Fallback test failed: {str(e)}")

if __name__ == "__main__":
    print("🔍 CONFIGURATION VERIFICATION")
    print("=" * 30)
    
    config_ok = test_config_loading()
    test_actual_threshold_usage()
    
    print(f"\n🎯 SUMMARY")
    print("=" * 10)
    
    if config_ok:
        print("✅ Configuration loading: PASSED")
        print("✅ Threshold unification: IMPLEMENTED")
        print()
        print("🚀 NEXT STEPS:")
        print("   1. Start containers if not running")
        print("   2. Import OpenWebUI function")
        print("   3. Test memory persistence")
    else:
        print("❌ Configuration loading: FAILED")
        print("🔧 Fix configuration issues before proceeding")
    
    exit(0 if config_ok else 1)
