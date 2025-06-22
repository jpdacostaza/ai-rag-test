#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import time
import traceback
from datetime import datetime
from typing import Optional, Dict, Any

import redis

from cache_manager import CacheManager

"""
Real-world Cache Manager Demo
Demonstrates cache functionality in realistic scenarios including:
- Chat session caching
- System prompt change handling
- Performance optimization
- Format validation
- Cache statistics and monitoring
"""

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CacheManagerDemo:
    """Real-world demonstration of cache manager functionality."""

    def __init__(self):
        """Initialize demo environment."""
        self.redis_client: Optional[redis.Redis] = None
        self.cache_manager: Optional[CacheManager] = None
        self.demo_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_sets": 0,
            "json_rejections": 0,
            "system_prompt_changes": 0,
        }

    def setup_demo_environment(self) -> bool:
        """Setup Redis and cache manager for demo."""
        try:
            print("🔧 Setting up demo environment...")

            # Connect to Redis (use main DB for demo)
            self.redis_client = redis.Redis(
                host="localhost",
                port=6379,
                db=0,  # Use main database
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            self.redis_client.ping()
            print("✅ Redis connection successful")

            # Initialize CacheManager
            self.cache_manager = CacheManager(self.redis_client)
            print("✅ CacheManager initialized")

            return True
        except Exception as e:
            print(f"❌ Failed to setup demo environment: {e}")
            return False

    def generate_chat_key(self, user_id: str, conversation_context: str) -> str:
        """Generate a cache key for chat responses."""
        # Create hash of conversation context for caching
        context_hash = hashlib.sha256(conversation_context.encode()).hexdigest()[:16]
        return f"chat:{user_id}:{context_hash}"

    def simulate_llm_response(self, prompt: str, delay: float = 0.5) -> str:
        """Simulate LLM response generation with artificial delay."""
        time.sleep(delay)  # Simulate LLM processing time
        
        # Generate realistic responses based on prompt content
        if "python" in prompt.lower():
            return "Python is a high-level programming language known for its simplicity and readability. It's excellent for beginners and supports multiple programming paradigms including object-oriented, functional, and procedural programming."
        elif "machine learning" in prompt.lower():
            return "Machine Learning is a subset of artificial intelligence that enables computers to learn and improve from data without being explicitly programmed. Popular libraries include scikit-learn, TensorFlow, and PyTorch."
        elif "web development" in prompt.lower():
            return "Web development involves creating websites and web applications. Frontend technologies include HTML, CSS, and JavaScript, while backend technologies include Python (Django/Flask), Node.js, and various databases."
        else:
            return f"This is a helpful response about: {prompt[:50]}... The response provides detailed information and practical guidance."

    def demo_basic_caching(self):
        """Demonstrate basic caching functionality."""
        print("\n🎯 Demo 1: Basic Chat Response Caching")
        print("-" * 50)

        if not self.cache_manager:
            print("❌ Cache manager not initialized")
            return

        user_id = "demo_user_1"
        prompt = "What is Python programming?"
        cache_key = self.generate_chat_key(user_id, prompt)

        # First request - cache miss
        print(f"👤 User: {prompt}")
        print("🔍 Checking cache...")

        start_time = time.time()
        cached_response = self.cache_manager.get_with_validation(cache_key)
        cache_time = time.time() - start_time

        if cached_response is None:
            print("❌ Cache miss - generating new response")
            self.demo_stats["cache_misses"] += 1

            # Generate response (simulate LLM call)
            print("🧠 Calling LLM...")
            start_time = time.time()
            response = self.simulate_llm_response(prompt)
            llm_time = time.time() - start_time

            # Cache the response
            cache_success = self.cache_manager.set_with_validation(cache_key, response, 600)
            if cache_success:
                print("💾 Response cached successfully")
                self.demo_stats["cache_sets"] += 1
            else:
                print("⚠️ Failed to cache response")

            print(f"🤖 Response: {response}")
            print(f"⏱️ Total time: {llm_time:.3f}s (LLM: {llm_time:.3f}s, Cache: {cache_time:.3f}s)")
        else:
            print("✅ Cache hit!")
            self.demo_stats["cache_hits"] += 1
            response = cached_response
            print(f"🤖 Cached Response: {response}")
            print(f"⏱️ Total time: {cache_time:.3f}s (Cache only)")

        # Second request - should be cache hit
        print(f"\n👤 User asks same question again: {prompt}")
        print("🔍 Checking cache...")

        start_time = time.time()
        cached_response = self.cache_manager.get_with_validation(cache_key)
        cache_time = time.time() - start_time

        if cached_response:
            print("✅ Cache hit! (much faster)")
            self.demo_stats["cache_hits"] += 1
            print(f"🤖 Cached Response: {cached_response}")
            print(f"⏱️ Total time: {cache_time:.3f}s (Cache only)")
        else:
            print("❌ Unexpected cache miss")

    def demo_json_rejection(self):
        """Demonstrate JSON response rejection."""
        print("\n🎯 Demo 2: JSON Response Format Rejection")
        print("-" * 50)

        if not self.cache_manager:
            print("❌ Cache manager not initialized")
            return

        user_id = "demo_user_2"
        prompt = "Give me a JSON response"
        cache_key = self.generate_chat_key(user_id, prompt)

        # Simulate a JSON response that should be rejected
        json_responses = [
            '{"response": "This is JSON format"}',
            '{"answer": "JSON should not be cached", "reason": "format validation"}',
            '{"error": "This looks like an error response"}',
        ]

        for i, json_response in enumerate(json_responses, 1):
            print(f"\n📝 Attempt {i}: Trying to cache JSON response")
            print(f"   Content: {json_response}")

            cache_success = self.cache_manager.set_with_validation(
                f"{cache_key}_{i}", json_response, 60
            )

            if cache_success:
                print("❌ ERROR: JSON response was incorrectly cached!")
            else:
                print("✅ JSON response correctly rejected")
                self.demo_stats["json_rejections"] += 1

    def demo_system_prompt_change_detection(self):
        """Demonstrate system prompt change detection."""
        print("\n🎯 Demo 3: System Prompt Change Detection")
        print("-" * 50)

        if not self.cache_manager:
            print("❌ Cache manager not initialized")
            return

        # Initial system prompt
        initial_prompt = "You are a helpful assistant that provides clear and concise answers."
        print(f"📋 Initial system prompt: {initial_prompt}")

        # Check for system prompt changes
        self.cache_manager.check_system_prompt_change(initial_prompt)
        print("✅ System prompt stored")

        # Cache some responses with current system prompt
        for i in range(3):
            cache_key = f"demo:system_test:{i}"
            response = f"Response {i+1} with initial system prompt"
            success = self.cache_manager.set_with_validation(cache_key, response, 600)
            if success:
                print(f"💾 Cached response {i+1}")
                self.demo_stats["cache_sets"] += 1

        # Simulate system prompt change
        print("\n📝 Changing system prompt...")
        if not self.redis_client:
            print("❌ Redis client not available")
            return
            
        self.redis_client.set("user_preferences:user_a", "dark_mode=true")
        self.redis_client.set("session:abc123", "active")

        # Get initial stats
        stats_before = self.cache_manager.get_cache_stats()
        print(f"📊 Stats before prompt change: {stats_before}")

        new_prompt = "You are a creative assistant that provides innovative and out-of-the-box solutions."
        print(f"📋 New system prompt: {new_prompt}")

        # Detect prompt change and clear cache
        self.cache_manager.check_system_prompt_change(new_prompt)
        self.demo_stats["system_prompt_changes"] += 1

        stats_after = self.cache_manager.get_cache_stats()
        print(f"📊 Stats after prompt change: {stats_after}")

        # Try to retrieve previously cached responses (should be cache miss)
        for i in range(3):
            cache_key = f"demo:system_test:{i}"
            cached = self.cache_manager.get_with_validation(cache_key)
            if cached:
                print(f"❌ ERROR: Old response {i+1} still in cache after prompt change!")
            else:
                print(f"✅ Response {i+1} correctly cleared from cache")

        # Cache new responses with new system prompt
        for i in range(2):
            new_cache_key = f"demo:new_system_test:{i}"
            response = f"Response {i+1} with new creative system prompt - very innovative!"
            cached = self.cache_manager.get_with_validation(new_cache_key)
            if not cached:
                print(f"💾 Caching new response {i+1} with updated prompt")
                success = self.cache_manager.set_with_validation(new_cache_key, response, 600)
                if success:
                    self.demo_stats["cache_sets"] += 1

    def demo_performance_benchmark(self):
        """Demonstrate cache performance benefits."""
        print("\n🎯 Demo 4: Performance Benchmark")
        print("-" * 50)

        if not self.cache_manager:
            print("❌ Cache manager not initialized")
            return

        test_queries = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "Explain neural networks",
            "What is deep learning?",
            "How to get started with AI?",
        ]

        print("🚀 Running performance benchmark...")
        print("   Testing cache hits vs LLM calls")

        total_cache_time = 0
        total_llm_time = 0
        cache_hit_count = 0
        llm_call_count = 0

        # Test each query twice - first will be LLM call, second should be cache hit
        for query in test_queries:
            cache_key = self.generate_chat_key("benchmark_user", query)

            # First call (LLM)
            start_time = time.time()
            cached_response = self.cache_manager.get_with_validation(cache_key)
            if not cached_response:
                response = self.simulate_llm_response(query, delay=0.8)  # Simulate slower LLM
                llm_time = time.time() - start_time
                total_llm_time += llm_time
                llm_call_count += 1

                self.cache_manager.set_with_validation(cache_key, response, 600)
                print(f"🧠 LLM call for: {query[:30]}... (took {llm_time:.3f}s)")

            # Second call (cache hit)
            start_time = time.time()
            cached_response = self.cache_manager.get_with_validation(cache_key)
            if cached_response:
                cache_time = time.time() - start_time
                total_cache_time += cache_time
                cache_hit_count += 1
                print(f"⚡ Cache hit for: {query[:30]}... (took {cache_time:.3f}s)")

        # Calculate and display performance metrics
        avg_llm_time = total_llm_time / llm_call_count if llm_call_count > 0 else 0
        avg_cache_time = total_cache_time / cache_hit_count if cache_hit_count > 0 else 0
        speedup = avg_llm_time / avg_cache_time if avg_cache_time > 0 else 0

        print(f"\n📊 Performance Results:")
        print(f"   📈 Average LLM time: {avg_llm_time:.3f}s")
        print(f"   ⚡ Average cache time: {avg_cache_time:.3f}s")
        print(f"   🚀 Speedup: {speedup:.1f}x faster with cache")

    def demo_cache_statistics(self):
        """Demonstrate cache statistics monitoring."""
        print("\n🎯 Demo 5: Cache Statistics")
        print("-" * 50)

        if not self.cache_manager:
            print("❌ Cache manager not initialized")
            return

        # Get current cache statistics
        stats = self.cache_manager.get_cache_stats()
        print("📊 Current Cache Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")

        # Calculate demo-specific metrics
        total_requests = self.demo_stats["cache_hits"] + self.demo_stats["cache_misses"]
        if total_requests > 0:
            hit_rate = (self.demo_stats["cache_hits"] / total_requests) * 100
            print(f"\n🎯 Demo Session Metrics:")
            print(f"   📊 Total requests: {total_requests}")
            print(f"   ✅ Cache hits: {self.demo_stats['cache_hits']}")
            print(f"   ❌ Cache misses: {self.demo_stats['cache_misses']}")
            print(f"   💾 Cache sets: {self.demo_stats['cache_sets']}")
            print(f"   📈 Hit rate: {hit_rate:.1f}%")

            if self.demo_stats["cache_sets"] > 0:
                efficiency_rate = (self.demo_stats["cache_hits"] / self.demo_stats["cache_sets"]) * 100
                print(f"   🎯 Cache efficiency: {efficiency_rate:.1f}%")

        print(f"   🚫 JSON rejections: {self.demo_stats['json_rejections']}")
        print(f"   🔄 System prompt changes: {self.demo_stats['system_prompt_changes']}")

    def run_full_demo(self):
        """Run complete cache manager demonstration."""
        print("🎬 Starting Cache Manager Demo")
        print("=" * 60)

        if not self.setup_demo_environment():
            print("❌ Demo setup failed")
            return

        try:
            # Run all demo scenarios
            self.demo_basic_caching()
            self.demo_json_rejection()
            self.demo_system_prompt_change_detection()
            self.demo_performance_benchmark()
            self.demo_cache_statistics()

        except Exception as e:
            print(f"❌ Demo error: {e}")
            traceback.print_exc()

        print("\n" + "=" * 60)
        print("🎬 Cache Manager Demo Complete")

    def generate_demo_report(self) -> Dict[str, Any]:
        """Generate comprehensive demo report."""
        if not self.cache_manager:
            return {"error": "Cache manager not initialized"}
            
        return {
            "demo_timestamp": datetime.now().isoformat(),
            "demo_statistics": self.demo_stats,
            "cache_statistics": self.cache_manager.get_cache_stats(),
            "environment": {
                "redis_connected": self.redis_client is not None,
                "cache_manager_ready": self.cache_manager is not None,
            },
            "performance_insights": {
                "total_operations": sum(self.demo_stats.values()),
                "cache_effectiveness": "High" if self.demo_stats["cache_hits"] > self.demo_stats["cache_misses"] else "Low"
            }
        }


def main():
    """Main demo execution."""
    demo = CacheManagerDemo()
    demo.run_full_demo()

    # Generate and save demo report
    report = demo.generate_demo_report()
    
    report_file = "cache_manager_demo_results.json"
    try:
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Demo report saved to: {report_file}")
    except Exception as e:
        print(f"❌ Failed to save report: {e}")


if __name__ == "__main__":
    main()
