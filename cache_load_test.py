"""
Load test cache performance
"""
import requests
import time
import threading
import concurrent.futures

BASE_URL = "http://localhost:9099"

def make_chat_request(user_id, message, iteration):
    """Make a single chat request"""
    try:
        start = time.time()
        response = requests.post(f"{BASE_URL}/chat", json={
            "user_id": user_id,
            "message": message,
            "model": "llama3.2:3b"
        }, timeout=30)
        duration = (time.time() - start) * 1000
        return {
            "status": response.status_code,
            "duration": duration,
            "iteration": iteration,
            "user_id": user_id
        }
    except Exception as e:
        return {
            "status": "error",
            "duration": 0,
            "iteration": iteration,
            "user_id": user_id,
            "error": str(e)
        }

def cache_load_test():
    """Test cache performance under load"""
    print("🚀 Cache Load Test")
    print("=" * 50)
    
    # Get baseline stats
    initial_stats = requests.get(f"{BASE_URL}/debug/cache").json()
    print(f"📊 Initial: {initial_stats['hit_count']} hits, {initial_stats['miss_count']} misses")
    
    # Test parameters
    users = ["load_user_1", "load_user_2", "load_user_3"]
    messages = ["What is Python?", "Explain AI", "What is 5+5?"]
    repetitions = 3  # Each user will ask each question 3 times
    
    print(f"\n🔄 Testing {len(users)} users × {len(messages)} messages × {repetitions} reps = {len(users) * len(messages) * repetitions} requests")
    
    # Create all requests
    requests_to_make = []
    for user in users:
        for message in messages:
            for rep in range(repetitions):
                requests_to_make.append((user, message, rep))
    
    # Execute requests with concurrency
    results = []
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_request = {
            executor.submit(make_chat_request, user, message, rep): (user, message, rep)
            for user, message, rep in requests_to_make
        }
        
        completed = 0
        for future in concurrent.futures.as_completed(future_to_request):
            result = future.result()
            results.append(result)
            completed += 1
            if completed % 5 == 0:
                print(f"   Progress: {completed}/{len(requests_to_make)}")
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r["status"] == 200]
    failed = [r for r in results if r["status"] != 200]
    
    print(f"\n📊 Load Test Results:")
    print(f"   Total Requests: {len(results)}")
    print(f"   Successful: {len(successful)}")
    print(f"   Failed: {len(failed)}")
    print(f"   Success Rate: {len(successful)/len(results)*100:.1f}%")
    print(f"   Total Time: {total_time:.2f}s")
    print(f"   Requests/sec: {len(results)/total_time:.2f}")
    
    if successful:
        durations = [r["duration"] for r in successful]
        print(f"   Avg Response Time: {sum(durations)/len(durations):.2f}ms")
        print(f"   Min Response Time: {min(durations):.2f}ms")
        print(f"   Max Response Time: {max(durations):.2f}ms")
        
        # Analyze cache performance
        fast_responses = [d for d in durations if d < 100]  # Sub-100ms = likely cached
        print(f"   Fast Responses (<100ms): {len(fast_responses)} ({len(fast_responses)/len(durations)*100:.1f}%)")
    
    # Check final cache stats
    final_stats = requests.get(f"{BASE_URL}/debug/cache").json()
    print(f"\n📈 Cache Performance:")
    print(f"   Initial: {initial_stats['hit_count']} hits, {initial_stats['miss_count']} misses")
    print(f"   Final: {final_stats['hit_count']} hits, {final_stats['miss_count']} misses")
    
    hits_gained = final_stats['hit_count'] - initial_stats['hit_count']
    misses_gained = final_stats['miss_count'] - initial_stats['miss_count']
    
    print(f"   Gained: {hits_gained} hits, {misses_gained} misses")
    
    if hits_gained + misses_gained > 0:
        session_hit_rate = hits_gained / (hits_gained + misses_gained) * 100
        print(f"   Session Hit Rate: {session_hit_rate:.1f}%")
        
        expected_hits = len(users) * len(messages) * (repetitions - 1)  # First of each should be miss
        actual_hit_efficiency = hits_gained / expected_hits * 100 if expected_hits > 0 else 0
        print(f"   Cache Efficiency: {actual_hit_efficiency:.1f}% (expected ~{expected_hits} hits)")
        
        if session_hit_rate > 50:
            print("   ✅ Cache is performing well!")
        elif session_hit_rate > 25:
            print("   ⚠️  Cache is working but could be better")
        else:
            print("   ❌ Cache performance needs improvement")

if __name__ == "__main__":
    cache_load_test()
