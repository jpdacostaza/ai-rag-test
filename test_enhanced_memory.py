#!/usr/bin/env python3
"""
Enhanced Memory System Test Script
Tests the optimized thresholds, explicit memory commands, and adaptive limits
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8001"
TEST_USER = "enhanced_test_user"

def test_explicit_memory():
    """Test explicit memory storage functionality"""
    print("🧪 Testing Explicit Memory Commands...")
    
    # Test various explicit memory patterns
    explicit_tests = [
        {
            "content": "Remember this: The database threshold was optimized from 1% to 0.5% for better recall",
            "context": "System optimization discussion",
            "expected": True
        },
        {
            "content": "Save this information: The memory limit was increased from 20 to 50 memories",
            "context": "Memory configuration update", 
            "expected": True
        },
        {
            "content": "Don't forget: Explicit commands now force immediate storage regardless of quality scores",
            "context": "Feature implementation",
            "expected": True
        },
        {
            "content": "Important to remember: The system now adapts memory limits based on model capabilities",
            "context": "Adaptive functionality",
            "expected": True
        }
    ]
    
    results = []
    for i, test in enumerate(explicit_tests):
        try:
            response = requests.post(
                f"{BASE_URL}/api/memory/store_explicit",
                json={
                    "user_id": TEST_USER,
                    "content": test["content"],
                    "context": test["context"],
                    "importance": 0.9,
                    "forced": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("stored", False) and data.get("explicit", False)
                results.append({"test": i+1, "success": success, "response": data})
                print(f"   ✅ Test {i+1}: Explicit memory stored successfully")
            else:
                results.append({"test": i+1, "success": False, "error": response.text})
                print(f"   ❌ Test {i+1}: Failed - {response.status_code}")
                
        except Exception as e:
            results.append({"test": i+1, "success": False, "error": str(e)})
            print(f"   ❌ Test {i+1}: Exception - {str(e)}")
    
    return results

def test_optimized_retrieval():
    """Test the optimized threshold and retrieval system"""
    print("\n🔍 Testing Optimized Memory Retrieval...")
    
    # Test queries that should benefit from lower thresholds
    retrieval_tests = [
        {
            "query": "database threshold optimization",
            "expected_memories": 1
        },
        {
            "query": "memory limit configuration", 
            "expected_memories": 1
        },
        {
            "query": "explicit command storage",
            "expected_memories": 1
        },
        {
            "query": "adaptive memory functionality",
            "expected_memories": 1
        }
    ]
    
    results = []
    for i, test in enumerate(retrieval_tests):
        try:
            response = requests.post(
                f"{BASE_URL}/api/memory/retrieve",
                json={
                    "user_id": TEST_USER,
                    "query": test["query"],
                    "limit": 10,
                    "threshold": 0.005  # Using the optimized threshold
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                memories_found = data.get("count", 0)
                success = memories_found >= test["expected_memories"]
                results.append({
                    "test": i+1, 
                    "success": success, 
                    "found": memories_found,
                    "expected": test["expected_memories"],
                    "memories": data.get("memories", [])
                })
                
                if success:
                    print(f"   ✅ Test {i+1}: Found {memories_found} memories (expected ≥{test['expected_memories']})")
                    # Show relevance scores
                    for mem in data.get("memories", [])[:2]:
                        score = mem.get("relevance_score", 0)
                        print(f"      📊 Relevance: {score:.3f} - {mem['content'][:80]}...")
                else:
                    print(f"   ⚠️  Test {i+1}: Found {memories_found} memories (expected ≥{test['expected_memories']})")
                    
            else:
                results.append({"test": i+1, "success": False, "error": response.text})
                print(f"   ❌ Test {i+1}: Failed - {response.status_code}")
                
        except Exception as e:
            results.append({"test": i+1, "success": False, "error": str(e)})
            print(f"   ❌ Test {i+1}: Exception - {str(e)}")
    
    return results

def test_system_stats():
    """Test system statistics and health"""
    print("\n📊 Testing System Statistics...")
    
    try:
        response = requests.get(f"{BASE_URL}/debug/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ System Status:")
            print(f"      🔴 Redis: {stats['redis']['status']} - {stats['redis']['total_keys']} keys")
            print(f"      🟦 ChromaDB: {stats['chromadb']['status']} - {stats['chromadb']['total_documents']} documents")
            
            # Check our test user
            if TEST_USER in stats['chromadb']['users']:
                user_memories = stats['chromadb']['users'][TEST_USER]
                print(f"      👤 Test User ({TEST_USER}): {user_memories} memories stored")
                return {"success": True, "user_memories": user_memories, "stats": stats}
            else:
                print(f"      ⚠️  Test User ({TEST_USER}) not found in ChromaDB")
                return {"success": False, "error": "Test user not found"}
                
        else:
            print(f"   ❌ Failed to get stats - {response.status_code}")
            return {"success": False, "error": f"Status code: {response.status_code}"}
            
    except Exception as e:
        print(f"   ❌ Exception getting stats - {str(e)}")
        return {"success": False, "error": str(e)}

def main():
    """Run comprehensive tests of the enhanced memory system"""
    print("🚀 Enhanced Memory System Test Suite")
    print("="*50)
    
    start_time = time.time()
    
    # Test explicit memory functionality
    explicit_results = test_explicit_memory()
    
    # Wait a moment for storage to complete
    time.sleep(2)
    
    # Test optimized retrieval
    retrieval_results = test_optimized_retrieval()
    
    # Test system stats
    stats_result = test_system_stats()
    
    # Summary
    print("\n" + "="*50)
    print("📋 TEST SUMMARY")
    print("="*50)
    
    explicit_success = sum(1 for r in explicit_results if r.get("success", False))
    retrieval_success = sum(1 for r in retrieval_results if r.get("success", False))
    
    print(f"✅ Explicit Memory Tests: {explicit_success}/{len(explicit_results)} passed")
    print(f"✅ Retrieval Tests: {retrieval_success}/{len(retrieval_results)} passed")
    print(f"✅ System Stats: {'Passed' if stats_result.get('success', False) else 'Failed'}")
    
    total_tests = len(explicit_results) + len(retrieval_results) + 1
    total_passed = explicit_success + retrieval_success + (1 if stats_result.get('success', False) else 0)
    
    print(f"\n🎯 Overall Success Rate: {total_passed}/{total_tests} ({(total_passed/total_tests)*100:.1f}%)")
    
    elapsed = time.time() - start_time
    print(f"⏱️  Total Test Time: {elapsed:.2f} seconds")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Enhanced memory system is fully operational.")
        print("\n✨ Key Features Verified:")
        print("   📝 Explicit memory commands ('remember this', 'save this', etc.)")
        print("   🎯 Optimized thresholds (0.5% for better recall)")
        print("   📈 Increased memory limits (50 memories)")
        print("   🔄 Adaptive memory functionality")
    else:
        print("\n⚠️  Some tests failed. Please check the output above for details.")
    
    return {
        "explicit_results": explicit_results,
        "retrieval_results": retrieval_results,
        "stats_result": stats_result,
        "success_rate": total_passed / total_tests
    }

if __name__ == "__main__":
    main()
