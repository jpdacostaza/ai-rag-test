#!/usr/bin/env python3
"""
Direct Memory API Test
======================

Tests memory store and retrieve functionality directly through the Memory API.
This validates the co                # Search for specific information using the correct endpoint
                response = await client.get(
                    f"{MEMORY_API_URL}/retrieve/{self.test_user_id}",
                    params={"query": "What is my profession and where do I work?"}
                )nctionality that pipelines depend on.

Features tested:
- Memory storage via interaction processing
- Memory retrieval via search/query
- User-specific memory isolation
- Memory persistence and accuracy
- Memory content filtering and relevance
"""

import asyncio
import time
import json
import httpx
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configuration
MEMORY_API_URL = "http://localhost:5001"
OLLAMA_URL = "http://localhost:11434"

class DirectMemoryTest:
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.test_user_id = f"test_user_{int(time.time())}"
        self.conversation_id = f"test_conv_{int(time.time())}"
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        elapsed = time.time() - self.start_time
        emoji = {
            "INFO": "📝", "SUCCESS": "✅", "WARNING": "⚠️", 
            "ERROR": "❌", "DEBUG": "🔍", "TEST": "🧪", "MEMORY": "🧠"
        }.get(level, "📝")
        print(f"[{timestamp}] {emoji} [{level}] [{elapsed:.1f}s] {message}")
    
    async def check_memory_api_health(self) -> bool:
        """Check if Memory API is healthy."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{MEMORY_API_URL}/health")
                if response.status_code == 200:
                    self.log("Memory API: Healthy", "SUCCESS")
                    return True
                else:
                    self.log(f"Memory API: Unhealthy ({response.status_code})", "ERROR")
                    return False
        except Exception as e:
            self.log(f"Memory API: Connection failed - {e}", "ERROR")
            return False
    
    async def test_memory_storage(self) -> bool:
        """Test storing memories via interaction processing."""
        self.log("Testing memory storage...", "TEST")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create a rich interaction with personal information
                interaction = {
                    "user_id": self.test_user_id,
                    "conversation_id": self.conversation_id,
                    "user_message": (
                        "Hi! I'm Sarah Martinez, a 32-year-old data scientist at DataTech Solutions. "
                        "I live in Seattle and I'm passionate about machine learning and rock climbing. "
                        "I'm currently working on a project involving natural language processing for "
                        "customer sentiment analysis. I have two cats named Pixel and Vector."
                    ),
                    "assistant_response": (
                        "Hello Sarah! It's great to meet you. As a data scientist working on NLP "
                        "for sentiment analysis, you must find the intersection of language and "
                        "machine learning fascinating. And I love the names Pixel and Vector - "
                        "very fitting for a data scientist! How are you finding the rock climbing scene in Seattle?"
                    ),
                    "timestamp": time.time(),
                    "metadata": {
                        "model": "test_model",
                        "source": "direct_test",
                        "importance": "high"
                    }
                }
                
                # Store the interaction using the correct endpoint
                store_payload = {
                    "user_id": interaction["user_id"],
                    "content": f"User: {interaction['user_message']}\nAssistant: {interaction['assistant_response']}",
                    "metadata": interaction.get("metadata", {})
                }
                
                response = await client.post(
                    f"{MEMORY_API_URL}/store",
                    json=store_payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Handle boolean response from store endpoint
                    if result is True:
                        self.log("Memory storage successful", "SUCCESS")
                        self.log(f"Stored interaction: {result}", "DEBUG")
                        return True
                    else:
                        self.log(f"Memory storage returned: {result}", "WARNING")
                        return False
                else:
                    self.log(f"Memory storage failed: {response.status_code}", "ERROR")
                    self.log(f"Response: {response.text}", "DEBUG")
                    return False
                    
        except Exception as e:
            self.log(f"Memory storage error: {e}", "ERROR")
            return False
    
    async def test_memory_retrieval_by_query(self) -> bool:
        """Test retrieving memories by query."""
        self.log("Testing memory retrieval by query...", "TEST")
        
        # Wait a moment for memory processing
        await asyncio.sleep(2)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test various queries
                queries = [
                    "data scientist",
                    "Sarah Martinez", 
                    "Seattle",
                    "rock climbing",
                    "cats named Pixel and Vector",
                    "natural language processing"
                ]
                
                found_memories = 0
                for query in queries:
                    # Use the correct GET endpoint with query parameter
                    response = await client.get(
                        f"{MEMORY_API_URL}/retrieve/{self.test_user_id}",
                        params={"query": query}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        # The response structure might be different - check both formats
                        memories = data if isinstance(data, list) else data.get("memories", [])
                        
                        if memories:
                            found_memories += 1
                            self.log(f"Query '{query}': Found {len(memories)} memories", "MEMORY")
                            
                            # Show details of first memory
                            first_memory = memories[0]
                            content_preview = first_memory.get("content", "")[:100]
                            score = first_memory.get("relevance_score", 0)
                            self.log(f"  Top memory (score {score:.3f}): {content_preview}...", "DEBUG")
                        else:
                            self.log(f"Query '{query}': No memories found", "WARNING")
                    else:
                        self.log(f"Query '{query}' failed: {response.status_code}", "ERROR")
                
                # Success if we found memories for most queries
                success_rate = found_memories / len(queries)
                if success_rate >= 0.5:  # At least 50% of queries should return results
                    self.log(f"Memory retrieval PASSED - {found_memories}/{len(queries)} queries successful", "SUCCESS")
                    return True
                else:
                    self.log(f"Memory retrieval FAILED - Only {found_memories}/{len(queries)} queries successful", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"Memory retrieval error: {e}", "ERROR")
            return False
    
    async def test_memory_search_specific_info(self) -> bool:
        """Test searching for specific stored information."""
        self.log("Testing specific memory search...", "TEST")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Search for specific information we stored
                search_request = {
                    "user_id": self.test_user_id,
                    "query": "What is my profession and where do I work?",
                    "limit": 3,
                    "threshold": 0.2
                }
                
                response = await client.post(
                    f"{MEMORY_API_URL}/api/memory/retrieve",
                    json=search_request
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Handle different response formats
                    memories = data if isinstance(data, list) else data.get("memories", [])
                    
                    if memories:
                        # Check if the returned memories contain expected information
                        all_content = " ".join([m.get("content", "") if isinstance(m, dict) else str(m) for m in memories]).lower()
                        
                        expected_terms = [
                            "sarah martinez", "data scientist", "datatech solutions", 
                            "seattle", "machine learning", "rock climbing"
                        ]
                        
                        found_terms = [term for term in expected_terms if term.lower() in all_content]
                        
                        if len(found_terms) >= 3:  # At least half the terms should be found
                            self.log(f"Specific search PASSED - Found: {', '.join(found_terms)}", "SUCCESS")
                            self.log(f"Retrieved {len(memories)} relevant memories", "MEMORY")
                            return True
                        else:
                            self.log(f"Specific search FAILED - Only found: {', '.join(found_terms)}", "ERROR")
                            return False
                    else:
                        self.log("Specific search FAILED - No memories returned", "ERROR")
                        return False
                else:
                    self.log(f"Specific search failed: {response.status_code}", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"Specific search error: {e}", "ERROR")
            return False
    
    async def test_user_isolation(self) -> bool:
        """Test that memories are properly isolated by user."""
        self.log("Testing user memory isolation...", "TEST")
        
        try:
            # Create a second user and store different information
            other_user_id = f"other_user_{int(time.time())}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Store information for the other user
                other_interaction = {
                    "user_id": other_user_id,
                    "conversation_id": f"other_conv_{int(time.time())}",
                    "user_message": "I'm John Smith, a chef from New York who loves basketball.",
                    "assistant_response": "Nice to meet you, John! Cooking and basketball - great combination!",
                    "timestamp": time.time(),
                    "metadata": {"source": "isolation_test"}
                }
                
                # Store information for the other user using correct endpoint
                other_store_payload = {
                    "user_id": other_user_id,
                    "content": other_interaction["user_message"],
                    "metadata": other_interaction.get("metadata", {})
                }
                
                # Store other user's interaction
                await client.post(
                    f"{MEMORY_API_URL}/store",
                    json=other_store_payload
                )
                
                await asyncio.sleep(1)  # Wait for processing
                
                # Try to retrieve other user's information using original user's ID
                response = await client.get(
                    f"{MEMORY_API_URL}/retrieve/{self.test_user_id}",
                    params={"query": "John Smith chef basketball"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    memories = data.get("memories", [])
                    
                    # Check if any memories contain the other user's information
                    john_mentions = 0
                    for memory in memories:
                        content = memory.get("content", "") if isinstance(memory, dict) else str(memory)
                        content = content.lower()
                        if "john smith" in content or "chef" in content or "basketball" in content:
                            john_mentions += 1
                    
                    if john_mentions == 0:
                        self.log("User isolation PASSED - No cross-user memory leakage", "SUCCESS")
                        return True
                    else:
                        self.log(f"User isolation FAILED - Found {john_mentions} cross-user memories", "ERROR")
                        return False
                else:
                    self.log(f"User isolation test failed: {response.status_code}", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"User isolation test error: {e}", "ERROR")
            return False
    
    async def test_memory_persistence(self) -> bool:
        """Test that memories persist and remain accessible."""
        self.log("Testing memory persistence...", "TEST")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Wait a bit to ensure all processing is complete
                await asyncio.sleep(2)
                
                # Re-query for the original information to ensure it's still there
                response = await client.get(
                    f"{MEMORY_API_URL}/retrieve/{self.test_user_id}",
                    params={"query": "Sarah Martinez data scientist Seattle"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    memories = data.get("memories", [])
                    
                    if memories:
                        # Verify the content is still accurate
                        content = " ".join([m.get("content", "") if isinstance(m, dict) else str(m) for m in memories]).lower()
                        key_info_present = all(term in content for term in ["sarah", "data scientist"])
                        
                        if key_info_present:
                            self.log("Memory persistence PASSED - Information still accessible", "SUCCESS")
                            return True
                        else:
                            self.log("Memory persistence FAILED - Key information degraded", "ERROR")
                            return False
                    else:
                        self.log("Memory persistence FAILED - No memories found", "ERROR")
                        return False
                else:
                    self.log(f"Memory persistence test failed: {response.status_code}", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"Memory persistence error: {e}", "ERROR")
            return False
    
    async def run_full_test_suite(self) -> Dict[str, bool]:
        """Run the complete direct memory test suite."""
        self.log("Starting Direct Memory API Test", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Test User ID: {self.test_user_id}", "INFO")
        self.log(f"Conversation ID: {self.conversation_id}", "INFO")
        self.log("=" * 60, "INFO")
        
        # Check Memory API health first
        memory_healthy = await self.check_memory_api_health()
        if not memory_healthy:
            self.log("Aborting test - Memory API not healthy", "ERROR")
            return {"Memory API Health": False}
        
        # Run test sequence
        tests = [
            ("Memory API Health", True),  # Already checked
            ("Memory Storage", await self.test_memory_storage()),
            ("Memory Retrieval by Query", await self.test_memory_retrieval_by_query()),
            ("Specific Memory Search", await self.test_memory_search_specific_info()),
            ("User Memory Isolation", await self.test_user_isolation()),
            ("Memory Persistence", await self.test_memory_persistence()),
        ]
        
        results = {}
        for test_name, result in tests:
            results[test_name] = result
        
        # Print summary
        self.log("=" * 60, "INFO")
        self.log("DIRECT MEMORY API TEST SUMMARY", "INFO")
        self.log("=" * 60, "INFO")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        self.log(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)", "INFO")
        self.log("", "INFO")
        
        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            self.log(f"  [{status}] {test_name}", "SUCCESS" if result else "ERROR")
        
        self.log("=" * 60, "INFO")
        if success_rate == 100:
            self.log("🎉 ALL TESTS PASSED - Memory API fully functional!", "SUCCESS")
        elif success_rate >= 80:
            self.log("✅ MOSTLY SUCCESSFUL - Minor issues detected", "SUCCESS")
        elif success_rate >= 60:
            self.log("⚠️  PARTIAL SUCCESS - Some issues detected", "WARNING")
        else:
            self.log("❌ CRITICAL ISSUES - Memory API needs attention", "ERROR")
        
        total_time = time.time() - self.start_time
        self.log(f"Total test time: {total_time:.1f} seconds", "INFO")
        self.log("=" * 60, "INFO")
        
        return results

async def main():
    """Main test execution."""
    test_suite = DirectMemoryTest()
    results = await test_suite.run_full_test_suite()
    
    # Exit with appropriate code
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    asyncio.run(main())
