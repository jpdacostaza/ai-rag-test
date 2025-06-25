"""
Sequential cache test to avoid overloading the LLM
"""
import requests
import time

BASE_URL = "http://localhost:9099"

def sequential_cache_test():
    """Test cache with sequential requests to avoid timeouts"""
    print("🔄 Sequential Cache Test")
    print("=" * 40)
    
    # Get baseline
    initial_stats = requests.get(f"{BASE_URL}/debug/cache").json()
    print(f"📊 Starting: {initial_stats['hit_count']} hits, {initial_stats['miss_count']} misses")
    
    test_cases = [
        {"user_id": "seq_user1", "message": "What is 1+1?"},
        {"user_id": "seq_user1", "message": "What is 1+1?"},  # Should cache hit
        {"user_id": "seq_user2", "message": "What is 1+1?"},  # Different user, should cache miss
        {"user_id": "seq_user1", "message": "What is 2+2?"},  # Same user, different message
        {"user_id": "seq_user1", "message": "What is 1+1?"},  # Should cache hit again
    ]
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['user_id']} asks '{test_case['message']}'")
        
        start = time.time()
        try:
            response = requests.post(f"{BASE_URL}/chat", json={
                **test_case,
                "model": "llama3.2:3b"
            }, timeout=45)
            
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                result = response.json()['response'][:30] + "..."
                print(f"   ✅ Success: {duration:.2f}ms - '{result}'")
                results.append({"status": "success", "duration": duration})
                
                # Quick speed analysis
                if duration < 100:
                    print("   🚀 Very fast (likely cached)")
                elif duration < 1000:
                    print("   ⚡ Fast")
                else:
                    print("   🐌 Slow (likely not cached)")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                results.append({"status": "failed", "duration": duration})
                
        except Exception as e:
            duration = (time.time() - start) * 1000
            print(f"   ❌ Error: {str(e)[:50]}...")
            results.append({"status": "error", "duration": duration})
        
        # Check cache stats after each request
        stats = requests.get(f"{BASE_URL}/debug/cache").json()
        hits = stats['hit_count'] - initial_stats['hit_count']
        misses = stats['miss_count'] - initial_stats['miss_count'] 
        print(f"   📊 Cache: +{hits} hits, +{misses} misses")
        
        # Wait between requests to avoid overload
        time.sleep(1)
    
    # Final analysis
    print(f"\n📊 Final Results:")
    successful = [r for r in results if r["status"] == "success"]
    print(f"   Successful requests: {len(successful)}/{len(results)}")
    
    if successful:
        durations = [r["duration"] for r in successful]
        print(f"   Average response time: {sum(durations)/len(durations):.2f}ms")
        fast_responses = [d for d in durations if d < 100]
        print(f"   Fast responses (<100ms): {len(fast_responses)}")
    
    final_stats = requests.get(f"{BASE_URL}/debug/cache").json()
    total_hits = final_stats['hit_count'] - initial_stats['hit_count']
    total_misses = final_stats['miss_count'] - initial_stats['miss_count']
    
    print(f"\n🎯 Cache Analysis:")
    print(f"   Expected pattern: miss, hit, miss, miss, hit")
    print(f"   Actual: {total_hits} hits from {total_hits + total_misses} requests")
    
    if total_hits >= 2:
        print("   ✅ Cache is working correctly!")
    elif total_hits >= 1:
        print("   ⚠️  Cache is partially working")
    else:
        print("   ❌ Cache not working as expected")
    
    # Final stats
    print(f"\n📈 Updated Cache Stats:")
    print(f"   Hit Rate: {final_stats['hit_rate']}")
    print(f"   Total Requests: {final_stats['total_requests']}")
    print(f"   Cache Size: {final_stats['size']}")

if __name__ == "__main__":
    sequential_cache_test()
