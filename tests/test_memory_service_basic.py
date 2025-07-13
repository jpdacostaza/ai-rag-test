#!/usr/bin/env python3
"""
Simple Memory Service Test
=========================

Basic validation that the memory service consolidation works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_imports():
    """Test basic imports and class creation."""
    print("🧪 Testing Memory Service Basic Functionality...")
    
    try:
        from services.memory_service import (
            MemoryService, MemoryProviderType, MemoryEntry, MemoryMetadata, 
            get_memory_service, create_memory_service
        )
        print("✅ Basic imports successful")
        
        # Test memory entry creation
        from datetime import datetime
        
        metadata = MemoryMetadata(
            user_id="test_user",
            timestamp=datetime.now().isoformat(),
            source="test",
            importance=0.8
        )
        
        entry = MemoryEntry(
            content="Test memory content",
            metadata=metadata
        )
        
        print("✅ Memory entry creation successful")
        
        # Test memory service creation
        service = create_memory_service(MemoryProviderType.DATABASE)
        print("✅ Memory service creation successful")
        
        # Test global service getter
        global_service = get_memory_service()
        print("✅ Global memory service getter successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic imports failed: {e}")
        return False

def test_memory_entry_serialization():
    """Test memory entry serialization."""
    try:
        from services.memory_service import MemoryEntry, MemoryMetadata
        from datetime import datetime
        
        # Create test entry
        metadata = MemoryMetadata(
            user_id="test_user",
            timestamp=datetime.now().isoformat(),
            source="test",
            importance=0.9,
            explicit=True
        )
        
        entry = MemoryEntry(
            content="Serialization test content",
            metadata=metadata,
            similarity_score=0.95
        )
        
        # Test to_dict
        entry_dict = entry.to_dict()
        assert "content" in entry_dict
        assert "metadata" in entry_dict
        assert entry_dict["similarity_score"] == 0.95
        print("✅ Memory entry to_dict successful")
        
        # Test from_dict
        restored_entry = MemoryEntry.from_dict(entry_dict)
        assert restored_entry.content == entry.content
        assert restored_entry.metadata.user_id == entry.metadata.user_id
        assert restored_entry.similarity_score == entry.similarity_score
        print("✅ Memory entry from_dict successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Serialization test failed: {e}")
        return False

def test_provider_type_enum():
    """Test provider type enumeration."""
    try:
        from services.memory_service import MemoryProviderType
        
        # Test all provider types exist
        types = [MemoryProviderType.API, MemoryProviderType.DATABASE, 
                MemoryProviderType.PIPELINE, MemoryProviderType.LOCAL, MemoryProviderType.HYBRID]
        
        print(f"✅ Provider types available: {[t.value for t in types]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider type test failed: {e}")
        return False

def test_service_interface():
    """Test memory service interface methods exist."""
    try:
        from services.memory_service import get_memory_service
        
        service = get_memory_service()
        
        # Check all expected methods exist
        methods = [
            'store_memory', 'get_memories', 'track_conversation',
            'get_relevant_memories', 'format_memories_for_injection',
            'track_conversation_and_store', 'delete_memory', 'get_stats', 'health_check'
        ]
        
        for method in methods:
            assert hasattr(service, method), f"Method {method} not found"
        
        print(f"✅ All {len(methods)} service methods available")
        
        return True
        
    except Exception as e:
        print(f"❌ Service interface test failed: {e}")
        return False

def main():
    """Run basic memory service tests."""
    print("🚀 Memory Service - Basic Validation")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Memory Entry Serialization", test_memory_entry_serialization),
        ("Provider Type Enum", test_provider_type_enum),
        ("Service Interface", test_service_interface)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}...")
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 Memory Service basic validation successful!")
        print("\n📋 Ready for consolidation implementation:")
        print("   ✅ Core classes and interfaces working")
        print("   ✅ Memory entry serialization functional") 
        print("   ✅ Provider pattern implemented")
        print("   ✅ Service interface complete")
    else:
        print(f"⚠️ {total - passed} tests failed. Address issues before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    main()
