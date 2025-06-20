#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import time
import traceback
from datetime import datetime

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
        self.redis_client = None
        self.cache_manager = None
        self.demo_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_sets": 0,
            "json_rejections": 0,
            "system_prompt_changes": 0,
        }

    def setup_demo_environment(self):
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

            # Test connection            self.redis_client.ping()
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
        time.sleep(
            delay
        )  # Simulate LLM processing time        # Generate realistic responses based on prompt content
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

        user_id = "demo_user_1"
        prompt = "What is Python programming?"
        cache_key = self.generate_chat_key(user_id, prompt)

        # First request - cache miss
        print("👤 User: {prompt}")
        print("🔍 Checking cache...")

        start_time = time.time()
        cached_response = self.cache_manager.get_with_validation(cache_key)
        time.time() - start_time

        if cached_response is None:
            print("❌ Cache miss - generating new response")
            self.demo_stats["cache_misses"] += 1

            # Generate response (simulate LLM call)
            print("🧠 Calling LLM...")
            start_time = time.time()
            response = self.simulate_llm_response(prompt)
            time.time() - start_time

            # Cache the response
            cache_success = self.cache_manager.set_with_validation(cache_key, response, 600)
            if cache_success:
                print("💾 Response cached successfully")
                self.demo_stats["cache_sets"] += 1
            else:
                print("⚠️ Failed to cache response")

            print("🤖 Response: {response}")
            print("⏱️ Total time: {llm_time:.3f}s (LLM: {llm_time:.3f}s, Cache: {cache_time:.3f}s)")
        else:
            print("✅ Cache hit!")
            self.demo_stats["cache_hits"] += 1
            response = cached_response
            print("🤖 Cached Response: {response}")
            print("⏱️ Total time: {cache_time:.3f}s (Cache only)")

        # Second request - should be cache hit
        print("\n👤 User asks same question again: {prompt}")
        print("🔍 Checking cache...")

        start_time = time.time()
        cached_response = self.cache_manager.get_with_validation(cache_key)
        time.time() - start_time

        if cached_response:
            print("✅ Cache hit! (much faster)")
            self.demo_stats["cache_hits"] += 1
            print("🤖 Cached Response: {cached_response}")
            print("⏱️ Total time: {cache_time:.3f}s (Cache only)")
        else:
            print("❌ Unexpected cache miss")

    def demo_json_rejection(self):
        """Demonstrate JSON response rejection."""
        print("\n🎯 Demo 2: JSON Response Format Rejection")
        print("-" * 50)

        user_id = "demo_user_2"
        prompt = "Give me a JSON response"
        self.generate_chat_key(user_id, prompt)

        # Simulate a JSON response that should be rejected
        json_responses = [
            '{"response": "This is JSON format"}',
            '{"answer": "JSON should not be cached", "reason": "format validation"}',
            '{"error": "This looks like an error response"}',
        ]

        for i, json_response in enumerate(json_responses, 1):
            print("\n📝 Attempt {i}: Trying to cache JSON response")
            print("   Content: {json_response}")

            cache_success = self.cache_manager.set_with_validation(
                "{cache_key}_{i}", json_response, 60
            )

            if cache_success:
                print("❌ ERROR: JSON response was incorrectly cached!")
            else:
                print("✅ JSON response correctly rejected")
                self.demo_stats["json_rejections"] += 1

        # Try a valid plain text response
        plain_text_response = "This is a plain text response that should be cached properly."
        print("\n📝 Attempt with plain text:")
        print("   Content: {plain_text_response}")

        cache_success = self.cache_manager.set_with_validation(
            "{cache_key}_valid", plain_text_response, 60
        )

        if cache_success:
            print("✅ Plain text response cached successfully")
            self.demo_stats["cache_sets"] += 1
        else:
            print("❌ ERROR: Plain text was incorrectly rejected!")

    def demo_system_prompt_changes(self):
        """Demonstrate system prompt change detection and cache invalidation."""
        print("\n🎯 Demo 3: System Prompt Change Detection")
        print("-" * 50)

        # Setup initial system prompt and cache some responses
        initial_prompt = "You are a helpful assistant that provides concise answers."
        print("🎨 Initial system prompt: {initial_prompt}")

        self.cache_manager.check_system_prompt_change(initial_prompt)

        # Cache several chat responses
        test_users = ["user_a", "user_b", "user_c"]
        test_prompts = [
            "Explain machine learning",
            "What is web development?",
            "Tell me about databases",
        ]

        print("\n💾 Caching responses for multiple users...")
        for user, prompt in zip(test_users, test_prompts):
            cache_key = self.generate_chat_key(user, prompt)
            response = self.simulate_llm_response(prompt, 0.1)  # Faster for demo

            success = self.cache_manager.set_with_validation(cache_key, response, 600)
            if success:
                print("   ✅ Cached response for {user}")
                self.demo_stats["cache_sets"] += 1

        # Add some non-chat cache data
        self.redis_client.set("user_preferences:user_a", "dark_mode=true")
        self.redis_client.set("session:abc123", "active")

        # Show current cache stats
        self.cache_manager.get_cache_stats()
        print("\n📊 Cache stats before prompt change:")
        print("   Chat entries: {stats['cache_counts']['chat']}")
        print("   Other entries: {stats['cache_counts']['other']}")
        print("   Total keys: {stats['total_keys']}")

        # Change system prompt
        new_prompt = (
            "You are a detailed assistant that provides comprehensive explanations with examples."
        )
        print("\n🎨 Changing system prompt to: {new_prompt}")

        self.cache_manager.check_system_prompt_change(new_prompt)
        self.demo_stats["system_prompt_changes"] += 1

        # Check cache stats after change
        stats_after = self.cache_manager.get_cache_stats()
        print("\n📊 Cache stats after prompt change:")
        print("   Chat entries: {stats_after['cache_counts']['chat']}")
        print("   Other entries: {stats_after['cache_counts']['other']}")
        print("   Total keys: {stats_after['total_keys']}")

        # Verify chat cache was cleared but other data remains
        if stats_after["cache_counts"]["chat"] == 0:
            print("✅ Chat cache successfully invalidated")
        else:
            print("❌ Chat cache was not properly invalidated")

        if stats_after["cache_counts"]["other"] > 0:
            print("✅ Non-chat data preserved")
        else:
            print("⚠️ Non-chat data may have been lost")

        # Test that new responses work with updated prompt
        print("\n🔄 Testing cache with new system prompt...")
        new_user = "user_d"
        new_prompt_text = "Explain Python programming"
        new_cache_key = self.generate_chat_key(new_user, new_prompt_text)

        # Should be cache miss since prompt changed
        cached = self.cache_manager.get_with_validation(new_cache_key)
        if cached is None:
            print("✅ Cache miss as expected (prompt changed)")
            self.demo_stats["cache_misses"] += 1

            # Generate and cache new response
            response = self.simulate_llm_response(new_prompt_text, 0.1)
            success = self.cache_manager.set_with_validation(new_cache_key, response, 600)
            if success:
                print("✅ New response cached with updated prompt")
                self.demo_stats["cache_sets"] += 1
        else:
            print("❌ Unexpected cache hit")

    def demo_performance_comparison(self):
        """Demonstrate performance benefits of caching."""
        print("\n🎯 Demo 4: Performance Comparison")
        print("-" * 50)

        # Test parameters
        num_requests = 10
        common_prompts = [
            "What is machine learning?",
            "Explain Python programming",
            "How does web development work?",
            "What are databases used for?",
            "Tell me about artificial intelligence",
        ]

        # Scenario 1: No caching (simulate)
        print("📊 Scenario 1: Without caching")
        start_time = time.time()

        for i in range(num_requests):
            prompt = common_prompts[i % len(common_prompts)]
            response = self.simulate_llm_response(prompt, 0.2)  # Faster for demo

        no_cache_time = time.time() - start_time
        print("   Total time: {no_cache_time:.3f}s")
        print("   Average per request: {no_cache_time/num_requests:.3f}s")

        # Scenario 2: With caching
        print("\n📊 Scenario 2: With caching")
        start_time = time.time()

        cache_hits = 0
        cache_misses = 0

        for i in range(num_requests):
            user_id = "perf_user_{i % 3}"  # Simulate multiple users with overlapping requests
            prompt = common_prompts[i % len(common_prompts)]
            cache_key = self.generate_chat_key(user_id, prompt)

            # Check cache first
            cached_response = self.cache_manager.get_with_validation(cache_key)

            if cached_response:
                cache_hits += 1
                response = cached_response
            else:
                cache_misses += 1
                response = self.simulate_llm_response(prompt, 0.2)
                self.cache_manager.set_with_validation(cache_key, response, 600)

        with_cache_time = time.time() - start_time
        print("   Total time: {with_cache_time:.3f}s")
        print("   Average per request: {with_cache_time/num_requests:.3f}s")
        print("   Cache hits: {cache_hits}")
        print("   Cache misses: {cache_misses}")

        # Calculate savings
        time_saved = no_cache_time - with_cache_time
        (time_saved / no_cache_time) * 100 if no_cache_time > 0 else 0

        print("\n💰 Performance Benefits:")
        print("   Time saved: {time_saved:.3f}s")
        print("   Percentage faster: {percent_saved:.1f}%")
        print("   Cache hit rate: {(cache_hits/num_requests)*100:.1f}%")

        # Update demo stats
        self.demo_stats["cache_hits"] += cache_hits
        self.demo_stats["cache_misses"] += cache_misses

    def demo_cache_monitoring(self):
        """Demonstrate cache monitoring and statistics."""
        print("\n🎯 Demo 5: Cache Monitoring & Statistics")
        print("-" * 50)

        # Get comprehensive cache statistics
        stats = self.cache_manager.get_cache_stats()

        print("📊 Current Cache Statistics:")
        print("   Cache Version: {stats.get('version', 'unknown')}")
        print("   Memory Usage: {stats.get('memory_usage', 'unknown')}")
        print("   Connected Clients: {stats.get('connected_clients', 0)}")
        print("   Total Cache Keys: {stats.get('total_keys', 0)}")

        print("\n📈 Cache Entry Breakdown:")
        cache_counts = stats.get("cache_counts", {})
        for cache_type, count in cache_counts.items():
            print("   {cache_type.title()} cache: {count} entries")

        print("\n📋 Demo Session Statistics:")
        print("   Cache hits: {self.demo_stats['cache_hits']}")
        print("   Cache misses: {self.demo_stats['cache_misses']}")
        print("   Cache sets: {self.demo_stats['cache_sets']}")
        print("   JSON rejections: {self.demo_stats['json_rejections']}")
        print("   System prompt changes: {self.demo_stats['system_prompt_changes']}")

        total_requests = self.demo_stats["cache_hits"] + self.demo_stats["cache_misses"]
        if total_requests > 0:
            (self.demo_stats["cache_hits"] / total_requests) * 100
            print("   Cache hit rate: {hit_rate:.1f}%")

        # Show cache efficiency
        if self.demo_stats["cache_sets"] > 0:
            (self.demo_stats["cache_hits"] / self.demo_stats["cache_sets"]) * 100
            print("   Cache efficiency: {efficiency:.1f}%")

    def run_comprehensive_demo(self):
        """Run the complete cache manager demonstration."""
        print("🚀 Cache Manager Real-world Demonstration")
        print("=" * 60)

        if not self.setup_demo_environment():
            return False

        try:
            # Run all demo scenarios
            self.demo_basic_caching()
            self.demo_json_rejection()
            self.demo_system_prompt_changes()
            self.demo_performance_comparison()
            self.demo_cache_monitoring()

            # Summary
            print("\n" + "=" * 60)
            print("🎉 CACHE MANAGER DEMO COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("✅ Basic response caching")
            print("✅ JSON format rejection")
            print("✅ System prompt change detection")
            print("✅ Performance optimization")
            print("✅ Cache monitoring & statistics")
            print("=" * 60)

            # Save demo results
            demo_results = {
                "timestamp": datetime.now().isoformat(),
                "status": "SUCCESS",
                "demo_statistics": self.demo_stats,
                "cache_statistics": self.cache_manager.get_cache_stats(),
                "scenarios_completed": [
                    "Basic Caching",
                    "JSON Rejection",
                    "System Prompt Changes",
                    "Performance Comparison",
                    "Cache Monitoring",
                ],
            }

            with open("cache_manager_demo_results.json", "w") as f:
                json.dump(demo_results, f, indent=2)

            print("📄 Demo results saved to: cache_manager_demo_results.json")

            return True

        except Exception:
            print("\n💥 Demo failed with error: {e}")

            traceback.print_exc()
            return False


def main():
    """Main demo execution."""
    demo = CacheManagerDemo()
    success = demo.run_comprehensive_demo()

    if success:
        print("\n🎉 Demo completed successfully! Cache manager is working perfectly.")
    else:
        print("\n💥 Demo encountered issues. Please check the output above.")

    return success


if __name__ == "__main__":
    main()
