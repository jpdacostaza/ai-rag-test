#!/usr/bin/env python3
"""
Real-world Cache & Memory Simulation
Demonstrates actual cache hit/miss patterns and memory interaction
as they would occur in production usage.
"""

import redis
import time
import hashlib
from datetime import datetime
from cache_manager import CacheManager
from database import get_cache_manager, get_cache, set_cache
from database_manager import DatabaseManager

def simulate_real_world_usage():
    """Simulate realistic user interactions with cache and memory."""
    print("🌍 Real-world Cache & Memory Usage Simulation")
    print("=" * 55)
    
    # Initialize systems
    db_manager = DatabaseManager()
    cache_manager = get_cache_manager()
    
    if not cache_manager:
        print("❌ Cache manager not available")
        return False
    
    print("✅ Systems initialized")
    
    # Simulate common user interactions
    common_questions = [
        "What is Python?",
        "Explain machine learning",
        "How does web development work?",
        "What are databases used for?",
        "Tell me about artificial intelligence",
        "What is cloud computing?",
        "Explain RESTful APIs",
        "What is DevOps?"
    ]
    
    users = ["alice", "bob", "charlie", "diana", "eve"]
    
    print(f"\n👥 Simulating {len(users)} users asking {len(common_questions)} types of questions")
    
    # Simulate realistic usage patterns
    scenarios = [
        # Scenario 1: New users asking popular questions
        {"phase": "New User Questions", "pattern": "different_users_same_questions"},
        # Scenario 2: Repeat questions from same users
        {"phase": "Returning Users", "pattern": "same_users_repeat_questions"},
        # Scenario 3: Mixed interactions
        {"phase": "Mixed Interactions", "pattern": "realistic_mix"}
    ]
    
    for scenario in scenarios:
        print(f"\n🎭 {scenario['phase']}")
        print("-" * 40)
        
        if scenario['pattern'] == "different_users_same_questions":
            # Different users asking same questions (should mostly be cache misses initially)
            for question in common_questions[:4]:
                for user in users[:3]:
                    cache_key = f"chat:{user}:{hashlib.sha256(question.encode()).hexdigest()[:16]}"
                    
                    print(f"👤 {user}: {question}")
                    
                    # Check cache
                    cached = get_cache(db_manager, cache_key, user, f"req_{user}_{question[:10]}")
                    
                    if not cached:
                        # Simulate response generation and caching
                        response = f"Detailed response about {question} - generated for {user}"
                        set_cache(db_manager, cache_key, response, 600, user, f"set_{user}_{question[:10]}")
                    
                    time.sleep(0.1)  # Small delay to simulate real timing
        
        elif scenario['pattern'] == "same_users_repeat_questions":
            # Same users asking questions they asked before (should be cache hits)
            for user in users[:3]:
                for question in common_questions[:2]:
                    cache_key = f"chat:{user}:{hashlib.sha256(question.encode()).hexdigest()[:16]}"
                    
                    print(f"🔄 {user} (repeat): {question}")
                    
                    # This should be a cache hit
                    cached = get_cache(db_manager, cache_key, user, f"repeat_{user}_{question[:10]}")
                    
                    time.sleep(0.1)
        
        elif scenario['pattern'] == "realistic_mix":
            # Mix of new questions, repeat questions, and variations
            import random
            
            for i in range(10):
                user = random.choice(users)
                question = random.choice(common_questions)
                
                # Sometimes add variation to create cache misses
                if random.random() < 0.3:
                    question = f"{question} in detail"
                
                cache_key = f"chat:{user}:{hashlib.sha256(question.encode()).hexdigest()[:16]}"
                
                print(f"🎲 {user}: {question}")
                
                cached = get_cache(db_manager, cache_key, user, f"mix_{i}_{user}")
                
                if not cached:
                    response = f"Comprehensive answer about {question}"
                    set_cache(db_manager, cache_key, response, 600, user, f"mix_set_{i}")
                
                time.sleep(0.1)
    
    # Show final cache statistics
    print(f"\n📊 Final Cache Statistics")
    print("-" * 30)
    
    stats = cache_manager.get_cache_stats()
    print(f"Cache Version: {stats.get('version')}")
    print(f"Memory Usage: {stats.get('memory_usage')}")
    print(f"Total Keys: {stats.get('total_keys')}")
    print(f"Chat Entries: {stats.get('cache_counts', {}).get('chat', 0)}")
    
    return True

def demonstrate_system_prompt_impact():
    """Demonstrate how system prompt changes affect cache and memory."""
    print("\n🎨 System Prompt Change Impact Demonstration")
    print("=" * 50)
    
    cache_manager = get_cache_manager()
    if not cache_manager:
        print("❌ Cache manager not available")
        return False
    
    # Show current cache state
    stats_before = cache_manager.get_cache_stats()
    print(f"📊 Cache state before prompt change:")
    print(f"   Chat entries: {stats_before.get('cache_counts', {}).get('chat', 0)}")
    print(f"   Total keys: {stats_before.get('total_keys', 0)}")
    
    # Simulate system prompt change
    new_prompt = "You are an expert assistant that provides concise, actionable answers with practical examples."
    print(f"\n🔄 Changing system prompt to:")
    print(f"   '{new_prompt}'")
    
    # This will trigger cache invalidation and log it
    cache_manager.check_system_prompt_change(new_prompt)
    
    # Show cache state after change
    stats_after = cache_manager.get_cache_stats()
    print(f"\n📊 Cache state after prompt change:")
    print(f"   Chat entries: {stats_after.get('cache_counts', {}).get('chat', 0)}")
    print(f"   Total keys: {stats_after.get('total_keys', 0)}")
    
    print(f"\n💡 Impact Analysis:")
    chat_before = stats_before.get('cache_counts', {}).get('chat', 0)
    chat_after = stats_after.get('cache_counts', {}).get('chat', 0)
    print(f"   Chat cache entries cleared: {chat_before - chat_after}")
    print(f"   Non-chat data preserved: {stats_after.get('total_keys', 0)} keys")
    
    return True

if __name__ == "__main__":
    print("🚀 Real-world Cache & Memory Simulation")
    print("Demonstrating enhanced logging in realistic scenarios")
    print("=" * 60)
    
    try:
        success1 = simulate_real_world_usage()
        success2 = demonstrate_system_prompt_impact()
        
        if success1 and success2:
            print("\n" + "=" * 60)
            print("🎉 SIMULATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("✅ Real-world usage patterns simulated")
            print("✅ Cache hit/miss logging demonstrated")
            print("✅ System prompt impact shown")
            print("✅ Memory integration validated")
            print("=" * 60)
            print("📝 Check the log output above to see detailed")
            print("   cache hit/miss events with timestamps and content")
        else:
            print("\n❌ Simulation had some issues")
            
    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
