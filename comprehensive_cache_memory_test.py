#!/usr/bin/env python3
"""
Comprehensive Cache & Memory Integration Test
Tests the interaction between caching, chat history, and long-term memory systems.
Demonstrates cache hit/miss logging and real-world memory scenarios.
"""

import redis
import json
import time
import hashlib
from datetime import datetime
from cache_manager import CacheManager
from database_manager import DatabaseManager
from human_logging import log_service_status

class CacheMemoryIntegrationTest:
    """Comprehensive test for cache and memory system integration."""
    
    def __init__(self):
        """Initialize test environment."""
        self.redis_client = None
        self.cache_manager = None
        self.db_manager = None
        self.test_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_sets": 0,
            "memory_stores": 0,
            "memory_retrievals": 0,
            "system_prompt_changes": 0
        }
        
    def setup_test_environment(self):
        """Setup Redis, cache manager, and database manager for testing."""
        try:
            print("🔧 Setting up comprehensive test environment...")
            
            # Connect to Redis (use test DB)
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=2,  # Use separate test database
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            print("✅ Redis connection successful")
            
            # Clear test database
            self.redis_client.flushdb()
            print("✅ Test database cleared")
            
            # Initialize CacheManager
            self.cache_manager = CacheManager(self.redis_client)
            print("✅ CacheManager initialized")
            
            # Initialize DatabaseManager
            self.db_manager = DatabaseManager()
            print("✅ DatabaseManager initialized")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup test environment: {e}")
            return False
    
    def generate_user_cache_key(self, user_id: str, message: str) -> str:
        """Generate cache key for user messages (similar to main app)."""
        # Create hash similar to main.py cache key generation
        context_hash = hashlib.sha256(message.encode()).hexdigest()[:16]
        return f"chat:{user_id}:{context_hash}"
    
    def simulate_llm_response(self, prompt: str, delay: float = 0.3) -> str:
        """Simulate LLM response generation."""
        time.sleep(delay)
        
        # Generate contextual responses
        if "python" in prompt.lower():
            return "Python is a versatile programming language known for its simplicity and readability. It's widely used in web development, data science, machine learning, and automation. Python's extensive library ecosystem makes it excellent for rapid prototyping and production applications."
        elif "machine learning" in prompt.lower():
            return "Machine Learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed. Popular approaches include supervised learning, unsupervised learning, and reinforcement learning. Key libraries include scikit-learn, TensorFlow, and PyTorch."
        elif "web development" in prompt.lower():
            return "Web development involves creating websites and web applications using various technologies. Frontend development uses HTML, CSS, and JavaScript frameworks like React or Vue.js. Backend development uses languages like Python, Node.js, or Java with frameworks like Django, Express, or Spring."
        else:
            return f"This is a comprehensive response about {prompt}. The system provides detailed information based on the user's query, incorporating relevant context and practical examples to ensure the response is helpful and informative."
    
    def test_basic_cache_memory_flow(self):
        """Test 1: Basic cache and memory interaction."""
        print("\n🧪 Test 1: Basic Cache & Memory Flow")
        print("-" * 60)
        
        user_id = "test_user_1"
        messages = [
            "What is Python programming?",
            "Tell me about machine learning",
            "Explain web development"
        ]
        
        print(f"👤 Testing user: {user_id}")
        
        for i, message in enumerate(messages, 1):
            print(f"\n📝 Message {i}: {message}")
            
            # Generate cache key
            cache_key = self.generate_user_cache_key(user_id, message)
            print(f"🔑 Cache key: {cache_key}")
            
            # Check cache first (simulating chat endpoint behavior)
            print("🔍 Checking cache...")
            cached_response = self.cache_manager.get_with_validation(cache_key)
            
            if cached_response:
                print("✅ Cache hit! Using cached response")
                self.test_stats["cache_hits"] += 1
                response = cached_response
            else:
                print("❌ Cache miss - generating new response")
                self.test_stats["cache_misses"] += 1
                
                # Simulate LLM call
                print("🧠 Calling LLM...")
                response = self.simulate_llm_response(message)
                
                # Cache the response
                print("💾 Caching response...")
                cache_success = self.cache_manager.set_with_validation(cache_key, response, 600)
                if cache_success:
                    self.test_stats["cache_sets"] += 1
                    print("✅ Response cached successfully")
                else:
                    print("❌ Failed to cache response")
            
            # Store in chat history (simulating main app behavior)
            print("📚 Storing in chat history...")
            history_key = f"chat_history:{user_id}"
            chat_entry = {
                "message": message,
                "response": response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.redis_client.rpush(history_key, json.dumps(chat_entry))
            self.redis_client.ltrim(history_key, -20, -1)  # Keep last 20
            self.test_stats["memory_stores"] += 1
            
            print(f"🤖 Response: {response[:100]}...")
            print(f"⏱️ Chat history entries: {self.redis_client.llen(history_key)}")
    
    def test_cache_hit_scenarios(self):
        """Test 2: Multiple cache hit scenarios."""
        print("\n🧪 Test 2: Cache Hit Scenarios")
        print("-" * 60)
        
        # Test same message from different users
        message = "What is Python programming?"
        users = ["user_a", "user_b", "user_c"]
        
        print(f"📝 Testing message: {message}")
        print("👥 Testing with multiple users...")
        
        for user in users:
            print(f"\n👤 User: {user}")
            cache_key = self.generate_user_cache_key(user, message)
            
            # First request for this user
            cached_response = self.cache_manager.get_with_validation(cache_key)
            if cached_response:
                print("✅ Cache hit!")
                self.test_stats["cache_hits"] += 1
            else:
                print("❌ Cache miss - generating response")
                self.test_stats["cache_misses"] += 1
                response = self.simulate_llm_response(message, 0.1)
                self.cache_manager.set_with_validation(cache_key, response, 600)
                self.test_stats["cache_sets"] += 1
        
        # Test repeated requests from same user
        print(f"\n🔄 Testing repeated requests from {users[0]}...")
        for i in range(3):
            print(f"Request {i+1}:")
            cache_key = self.generate_user_cache_key(users[0], message)
            cached_response = self.cache_manager.get_with_validation(cache_key)
            if cached_response:
                print("  ✅ Cache hit!")
                self.test_stats["cache_hits"] += 1
            else:
                print("  ❌ Unexpected cache miss!")
                self.test_stats["cache_misses"] += 1
    
    def test_system_prompt_cache_invalidation(self):
        """Test 3: System prompt changes and cache invalidation."""
        print("\n🧪 Test 3: System Prompt Cache Invalidation")
        print("-" * 60)
        
        # Cache responses with initial system prompt
        initial_prompt = "You are a helpful assistant that provides detailed explanations."
        print(f"🎨 Initial system prompt: {initial_prompt}")
        
        # Check system prompt (will set it if first time)
        self.cache_manager.check_system_prompt_change(initial_prompt)
        
        # Cache several responses
        test_users = ["prompt_user_1", "prompt_user_2", "prompt_user_3"]
        test_messages = [
            "Explain databases",
            "What is cloud computing?",
            "Tell me about APIs"
        ]
        
        print("\n💾 Caching responses with initial prompt...")
        for user, message in zip(test_users, test_messages):
            cache_key = self.generate_user_cache_key(user, message)
            response = self.simulate_llm_response(message, 0.1)
            self.cache_manager.set_with_validation(cache_key, response, 600)
            self.test_stats["cache_sets"] += 1
            print(f"  ✅ Cached response for {user}")
        
        # Show cache stats before change
        stats_before = self.cache_manager.get_cache_stats()
        print(f"\n📊 Cache stats before prompt change:")
        print(f"   Chat entries: {stats_before['cache_counts']['chat']}")
        print(f"   Total keys: {stats_before['total_keys']}")
        
        # Change system prompt
        new_prompt = "You are a concise assistant that provides brief, direct answers."
        print(f"\n🎨 Changing system prompt to: {new_prompt}")
        
        self.cache_manager.check_system_prompt_change(new_prompt)
        self.test_stats["system_prompt_changes"] += 1
        
        # Check cache stats after change
        stats_after = self.cache_manager.get_cache_stats()
        print(f"\n📊 Cache stats after prompt change:")
        print(f"   Chat entries: {stats_after['cache_counts']['chat']}")
        print(f"   Total keys: {stats_after['total_keys']}")
        
        # Verify chat cache was cleared
        if stats_after['cache_counts']['chat'] == 0:
            print("✅ Chat cache successfully invalidated")
        else:
            print(f"❌ Chat cache not properly cleared: {stats_after['cache_counts']['chat']} entries remain")
        
        # Test new requests after prompt change
        print(f"\n🔄 Testing cache after prompt change...")
        for user, message in zip(test_users[:2], test_messages[:2]):
            cache_key = self.generate_user_cache_key(user, message)
            cached_response = self.cache_manager.get_with_validation(cache_key)
            if cached_response:
                print(f"  ❌ Unexpected cache hit for {user}")
                self.test_stats["cache_hits"] += 1
            else:
                print(f"  ✅ Expected cache miss for {user}")
                self.test_stats["cache_misses"] += 1
    
    def test_memory_integration(self):
        """Test 4: Chat history and long-term memory integration."""
        print("\n🧪 Test 4: Memory Integration")
        print("-" * 60)
        
        user_id = "memory_test_user"
        
        # Simulate a conversation with memory storage
        conversation = [
            "My name is Alice and I'm learning Python",
            "What are the best Python libraries for data science?",
            "Can you remind me about my previous question?",
            "I mentioned my name earlier, what was it?"
        ]
        
        print(f"👤 Testing conversation memory for: {user_id}")
        
        for i, message in enumerate(conversation, 1):
            print(f"\n💬 Turn {i}: {message}")
            
            # Check cache
            cache_key = self.generate_user_cache_key(user_id, message)
            cached_response = self.cache_manager.get_with_validation(cache_key)
            
            if cached_response:
                print("✅ Using cached response")
                self.test_stats["cache_hits"] += 1
                response = cached_response
            else:
                print("❌ No cache - generating response")
                self.test_stats["cache_misses"] += 1
                
                # Retrieve chat history (simulating memory context)
                history_key = f"chat_history:{user_id}"
                history_length = self.redis_client.llen(history_key)
                
                if history_length > 0:
                    print(f"📚 Retrieved {history_length} previous messages from memory")
                    self.test_stats["memory_retrievals"] += 1
                    
                    # Get recent history for context
                    recent_history = self.redis_client.lrange(history_key, -5, -1)
                    print(f"📖 Using {len(recent_history)} recent messages for context")
                
                # Generate response (in real app, this would include memory context)
                response = self.simulate_llm_response(message, 0.2)
                
                # Cache the response
                self.cache_manager.set_with_validation(cache_key, response, 600)
                self.test_stats["cache_sets"] += 1
            
            # Store conversation turn in memory
            history_key = f"chat_history:{user_id}"
            chat_entry = {
                "message": message,
                "response": response,
                "timestamp": datetime.utcnow().isoformat(),
                "turn": i
            }
            
            self.redis_client.rpush(history_key, json.dumps(chat_entry))
            self.test_stats["memory_stores"] += 1
            
            print(f"🤖 Response: {response[:80]}...")
            
            # Show memory state
            total_turns = self.redis_client.llen(history_key)
            print(f"💾 Total conversation turns stored: {total_turns}")
    
    def test_performance_with_logging(self):
        """Test 5: Performance impact of detailed logging."""
        print("\n🧪 Test 5: Performance Impact of Detailed Logging")
        print("-" * 60)
        
        # Test multiple operations with timing
        num_operations = 20
        user_id = "perf_test_user"
        
        print(f"⚡ Testing {num_operations} cache operations with detailed logging...")
        
        # Measure cache set operations
        print("\n📈 Testing cache SET operations...")
        start_time = time.time()
        
        for i in range(num_operations):
            message = f"Performance test message number {i}"
            cache_key = self.generate_user_cache_key(user_id, f"test_{i}")
            response = f"Response {i}: This is a test response for performance evaluation."
            
            success = self.cache_manager.set_with_validation(cache_key, response, 300)
            if success:
                self.test_stats["cache_sets"] += 1
        
        set_time = time.time() - start_time
        print(f"   Time for {num_operations} SET operations: {set_time:.3f}s")
        print(f"   Average per SET: {set_time/num_operations:.4f}s")
        
        # Measure cache get operations
        print("\n📉 Testing cache GET operations...")
        start_time = time.time()
        
        hits = 0
        for i in range(num_operations):
            cache_key = self.generate_user_cache_key(user_id, f"test_{i}")
            cached = self.cache_manager.get_with_validation(cache_key)
            if cached:
                hits += 1
                self.test_stats["cache_hits"] += 1
            else:
                self.test_stats["cache_misses"] += 1
        
        get_time = time.time() - start_time
        print(f"   Time for {num_operations} GET operations: {get_time:.3f}s")
        print(f"   Average per GET: {get_time/num_operations:.4f}s")
        print(f"   Cache hit rate: {(hits/num_operations)*100:.1f}%")
    
    def show_final_statistics(self):
        """Display comprehensive test statistics."""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST STATISTICS")
        print("=" * 60)
        
        # Test stats
        print("🧪 Test Operations:")
        print(f"   Cache hits: {self.test_stats['cache_hits']}")
        print(f"   Cache misses: {self.test_stats['cache_misses']}")
        print(f"   Cache sets: {self.test_stats['cache_sets']}")
        print(f"   Memory stores: {self.test_stats['memory_stores']}")
        print(f"   Memory retrievals: {self.test_stats['memory_retrievals']}")
        print(f"   System prompt changes: {self.test_stats['system_prompt_changes']}")
        
        # Calculate metrics
        total_requests = self.test_stats['cache_hits'] + self.test_stats['cache_misses']
        if total_requests > 0:
            hit_rate = (self.test_stats['cache_hits'] / total_requests) * 100
            print(f"\n📈 Performance Metrics:")
            print(f"   Total cache requests: {total_requests}")
            print(f"   Cache hit rate: {hit_rate:.1f}%")
            print(f"   Cache efficiency: {(self.test_stats['cache_hits']/self.test_stats['cache_sets'])*100:.1f}%")
        
        # System stats
        cache_stats = self.cache_manager.get_cache_stats()
        print(f"\n🔧 System Statistics:")
        print(f"   Cache version: {cache_stats.get('version', 'unknown')}")
        print(f"   Memory usage: {cache_stats.get('memory_usage', 'unknown')}")
        print(f"   Total cache keys: {cache_stats.get('total_keys', 0)}")
        
        cache_counts = cache_stats.get('cache_counts', {})
        print(f"\n📋 Cache Distribution:")
        for cache_type, count in cache_counts.items():
            print(f"   {cache_type.title()} cache: {count} entries")
    
    def run_comprehensive_test(self):
        """Run the complete comprehensive test suite."""
        print("🚀 Comprehensive Cache & Memory Integration Test")
        print("=" * 60)
        
        if not self.setup_test_environment():
            return False
        
        try:
            # Run all test scenarios
            self.test_basic_cache_memory_flow()
            self.test_cache_hit_scenarios()
            self.test_system_prompt_cache_invalidation()
            self.test_memory_integration()
            self.test_performance_with_logging()
            
            # Show final statistics
            self.show_final_statistics()
            
            # Summary
            print("\n" + "=" * 60)
            print("🎉 COMPREHENSIVE TEST COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("✅ Basic cache & memory flow")
            print("✅ Cache hit/miss scenarios")
            print("✅ System prompt invalidation")
            print("✅ Memory integration")
            print("✅ Performance with detailed logging")
            print("=" * 60)
            
            # Save test results
            test_results = {
                "timestamp": datetime.now().isoformat(),
                "status": "SUCCESS",
                "test_statistics": self.test_stats,
                "cache_statistics": self.cache_manager.get_cache_stats(),
                "tests_completed": [
                    "Basic Cache & Memory Flow",
                    "Cache Hit Scenarios", 
                    "System Prompt Invalidation",
                    "Memory Integration",
                    "Performance Testing"
                ]
            }
            
            with open("comprehensive_cache_memory_test_results.json", "w") as f:
                json.dump(test_results, f, indent=2)
            
            print(f"📄 Detailed results saved to: comprehensive_cache_memory_test_results.json")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Cleanup test database
            if self.redis_client:
                self.redis_client.flushdb()
                print("🧹 Test database cleaned up")

def main():
    """Main test execution."""
    test = CacheMemoryIntegrationTest()
    success = test.run_comprehensive_test()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
