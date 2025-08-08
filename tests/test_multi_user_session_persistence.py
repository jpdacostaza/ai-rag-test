#!/usr/bin/env python3
"""
Multi-User Multi-Session Memory Persistence Test
===============================================

This test validates that the memory system correctly maintains persistence:
- Across multiple chat sessions for the same user
- Between different users with proper isolation
- Over time with session breaks
- With concurrent user interactions

Test Coverage:
- Multi-user memory isolation
- Cross-session memory persistence  
- Session lifecycle management
- Concurrent user memory operations
- Memory context preservation over time
- User-specific persona and preference persistence

Location: tests/ (following project organization standards)
"""

import sys
import os
import json
import time
import requests
import asyncio
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MultiUserSessionTester:
    def __init__(self):
        self.memory_api_url = "http://localhost:5001"
        self.openwebui_url = "http://localhost:8080"
        self.test_results = {}
        self.test_users = [
            {
                "id": "user_alice",
                "email": "alice@testcorp.com",
                "name": "Alice Johnson",
                "role": "Data Scientist",
                "preferences": "Technical discussions, Python, Machine Learning",
                "sessions": []
            },
            {
                "id": "user_bob", 
                "email": "bob@testcorp.com",
                "name": "Bob Smith",
                "role": "Product Manager",
                "preferences": "Business strategy, Market trends, User experience",
                "sessions": []
            },
            {
                "id": "user_carol",
                "email": "carol@testcorp.com", 
                "name": "Carol Davis",
                "role": "Software Engineer",
                "preferences": "Web development, APIs, System architecture",
                "sessions": []
            }
        ]
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] [MultiUserTest] {message}")
    
    def create_session_id(self, user_id: str, session_num: int) -> str:
        """Generate a unique session ID for testing."""
        return f"{user_id}_session_{session_num}_{int(time.time())}"
    
    def store_user_memory(self, user: Dict, content: str, context: str = "", session_id: str = "") -> bool:
        """Store a memory for a specific user."""
        try:
            memory_data = {
                "content": content,
                "user_id": user["id"],
                "context": f"{context} | Session: {session_id}" if session_id else context,
                "timestamp": "auto"
            }
            
            response = requests.post(
                f"{self.memory_api_url}/api/memory/store",
                json=memory_data,
                timeout=10
            )
            
            if response.status_code == 200:
                memory_id = response.json().get("memory_id", "unknown")
                self.log(f"✅ Stored memory for {user['name']}: {memory_id}")
                return True
            else:
                self.log(f"❌ Failed to store memory for {user['name']}: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Exception storing memory for {user['name']}: {e}", "ERROR")
            return False
    
    def retrieve_user_memories(self, user: Dict, query: str, max_results: int = 5) -> List[Dict]:
        """Retrieve memories for a specific user."""
        try:
            response = requests.post(
                f"{self.memory_api_url}/api/memory/retrieve",
                json={
                    "query": query,
                    "user_id": user["id"],
                    "max_results": max_results
                },
                timeout=10
            )
            
            if response.status_code == 200:
                memories = response.json().get("memories", [])
                self.log(f"✅ Retrieved {len(memories)} memories for {user['name']}")
                return memories
            else:
                self.log(f"❌ Failed to retrieve memories for {user['name']}: {response.status_code}", "ERROR")
                return []
                
        except Exception as e:
            self.log(f"❌ Exception retrieving memories for {user['name']}: {e}", "ERROR")
            return []
    
    def test_user_setup_and_isolation(self) -> bool:
        """Test 1: Set up users and verify memory isolation."""
        self.log("👥 Testing User Setup and Memory Isolation...")
        
        try:
            isolation_results = {}
            
            # Store initial memories for each user
            for user in self.test_users:
                user_memories = [
                    f"My name is {user['name']} and I work as a {user['role']}",
                    f"I'm interested in {user['preferences']}",
                    f"My email is {user['email']} for contact purposes"
                ]
                
                stored_count = 0
                for memory_content in user_memories:
                    if self.store_user_memory(user, memory_content, "User Setup"):
                        stored_count += 1
                
                # Verify user can retrieve their own memories
                user_specific_memories = self.retrieve_user_memories(user, user["name"])
                own_memories = [m for m in user_specific_memories if user["name"].lower() in m.get("content", "").lower()]
                
                # Verify user cannot see other users' memories
                other_user_memories = []
                for other_user in self.test_users:
                    if other_user["id"] != user["id"]:
                        cross_memories = self.retrieve_user_memories(user, other_user["name"])
                        other_user_memories.extend([m for m in cross_memories if other_user["name"].lower() in m.get("content", "").lower()])
                
                isolation_results[user["id"]] = {
                    "stored_memories": stored_count,
                    "own_memories_retrieved": len(own_memories),
                    "other_memories_leaked": len(other_user_memories),
                    "properly_isolated": len(other_user_memories) == 0
                }
                
                self.log(f"   {user['name']}: {stored_count} stored, {len(own_memories)} own retrieved, {len(other_user_memories)} leaked")
            
            all_isolated = all(result["properly_isolated"] for result in isolation_results.values())
            
            self.test_results["user_isolation"] = {
                "status": "PASS" if all_isolated else "FAIL",
                "users_tested": len(self.test_users),
                "all_properly_isolated": all_isolated,
                "isolation_details": isolation_results
            }
            
            return all_isolated
            
        except Exception as e:
            self.log(f"❌ User Setup Exception: {e}", "ERROR")
            self.test_results["user_isolation"] = {"status": "FAIL", "error": str(e)}
            return False
    
    def test_multi_session_persistence(self) -> bool:
        """Test 2: Test memory persistence across multiple sessions for each user."""
        self.log("🔄 Testing Multi-Session Memory Persistence...")
        
        try:
            session_results = {}
            
            for user in self.test_users:
                self.log(f"   Testing sessions for {user['name']}...")
                
                user_session_results = {}
                
                # Simulate 3 different chat sessions
                for session_num in range(1, 4):
                    session_id = self.create_session_id(user["id"], session_num)
                    
                    # Store session-specific memories
                    session_memories = [
                        f"In session {session_num}, I discussed {user['preferences']} topics",
                        f"Session {session_num} timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        f"This is my conversation session {session_num} with the AI assistant"
                    ]
                    
                    stored_in_session = 0
                    for memory in session_memories:
                        if self.store_user_memory(user, memory, f"Session {session_num}", session_id):
                            stored_in_session += 1
                    
                    # Small delay between sessions
                    time.sleep(0.5)
                    
                    # Retrieve memories from all previous sessions
                    all_session_memories = self.retrieve_user_memories(user, f"session discussion {user['preferences']}", 10)
                    session_specific_memories = [m for m in all_session_memories if f"session {session_num}" in m.get("content", "").lower()]
                    
                    user_session_results[f"session_{session_num}"] = {
                        "session_id": session_id,
                        "memories_stored": stored_in_session,
                        "session_memories_retrieved": len(session_specific_memories),
                        "total_memories_accessible": len(all_session_memories)
                    }
                    
                    self.log(f"     Session {session_num}: {stored_in_session} stored, {len(session_specific_memories)} retrieved")
                
                # Test cross-session memory retrieval
                all_user_memories = self.retrieve_user_memories(user, user["name"], 20)
                cross_session_memories = [m for m in all_user_memories if "session" in m.get("content", "").lower()]
                
                session_results[user["id"]] = {
                    "sessions_tested": 3,
                    "session_details": user_session_results,
                    "cross_session_memories": len(cross_session_memories),
                    "total_user_memories": len(all_user_memories)
                }
                
                self.log(f"   {user['name']} total: {len(cross_session_memories)} cross-session memories, {len(all_user_memories)} total")
            
            # Verify persistence across all users and sessions
            total_cross_session_memories = sum(result["cross_session_memories"] for result in session_results.values())
            persistence_successful = total_cross_session_memories > 0
            
            self.test_results["multi_session_persistence"] = {
                "status": "PASS" if persistence_successful else "FAIL",
                "users_tested": len(self.test_users),
                "total_cross_session_memories": total_cross_session_memories,
                "session_results": session_results
            }
            
            return persistence_successful
            
        except Exception as e:
            self.log(f"❌ Multi-Session Persistence Exception: {e}", "ERROR")
            self.test_results["multi_session_persistence"] = {"status": "FAIL", "error": str(e)}
            return False
    
    def test_concurrent_user_operations(self) -> bool:
        """Test 3: Test concurrent memory operations from multiple users."""
        self.log("⚡ Testing Concurrent User Operations...")
        
        try:
            def user_memory_operations(user, operation_count=5):
                """Perform memory operations for a single user concurrently."""
                operations_results = {"stored": 0, "retrieved": 0, "errors": 0}
                
                for i in range(operation_count):
                    try:
                        # Store a memory
                        content = f"Concurrent operation {i+1} by {user['name']} at {datetime.now().strftime('%H:%M:%S.%f')}"
                        if self.store_user_memory(user, content, "Concurrent Test"):
                            operations_results["stored"] += 1
                        
                        # Retrieve memories
                        memories = self.retrieve_user_memories(user, "concurrent", 3)
                        if memories:
                            operations_results["retrieved"] += 1
                        
                        # Small delay to simulate real usage
                        time.sleep(0.1)
                        
                    except Exception as e:
                        operations_results["errors"] += 1
                        self.log(f"   Concurrent operation error for {user['name']}: {e}", "WARN")
                
                return operations_results
            
            # Run concurrent operations for all users
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.test_users)) as executor:
                # Submit concurrent tasks for each user
                future_to_user = {executor.submit(user_memory_operations, user): user for user in self.test_users}
                
                concurrent_results = {}
                for future in concurrent.futures.as_completed(future_to_user):
                    user = future_to_user[future]
                    try:
                        result = future.result()
                        concurrent_results[user["id"]] = result
                        self.log(f"   {user['name']}: {result['stored']} stored, {result['retrieved']} retrieved, {result['errors']} errors")
                    except Exception as e:
                        self.log(f"   {user['name']} concurrent test failed: {e}", "ERROR")
                        concurrent_results[user["id"]] = {"stored": 0, "retrieved": 0, "errors": 1}
            
            # Analyze results
            total_operations = sum(r["stored"] + r["retrieved"] for r in concurrent_results.values())
            total_errors = sum(r["errors"] for r in concurrent_results.values())
            success_rate = (total_operations / (total_operations + total_errors)) * 100 if (total_operations + total_errors) > 0 else 0
            
            concurrent_success = success_rate >= 90  # 90% success rate threshold
            
            self.test_results["concurrent_operations"] = {
                "status": "PASS" if concurrent_success else "FAIL",
                "total_operations": total_operations,
                "total_errors": total_errors,
                "success_rate": round(success_rate, 2),
                "user_results": concurrent_results
            }
            
            self.log(f"   Concurrent operations: {total_operations} successful, {total_errors} errors ({success_rate:.1f}% success rate)")
            
            return concurrent_success
            
        except Exception as e:
            self.log(f"❌ Concurrent Operations Exception: {e}", "ERROR")
            self.test_results["concurrent_operations"] = {"status": "FAIL", "error": str(e)}
            return False
    
    def test_temporal_memory_persistence(self) -> bool:
        """Test 4: Test memory persistence over time with delays."""
        self.log("⏰ Testing Temporal Memory Persistence...")
        
        try:
            temporal_results = {}
            
            for user in self.test_users:
                self.log(f"   Testing temporal persistence for {user['name']}...")
                
                # Store a memory with timestamp
                timestamp = datetime.now()
                temporal_memory = f"Temporal test memory for {user['name']} stored at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                
                if self.store_user_memory(user, temporal_memory, "Temporal Test"):
                    # Wait a few seconds to simulate time passage
                    time.sleep(2)
                    
                    # Retrieve the memory after time delay
                    retrieved_memories = self.retrieve_user_memories(user, "temporal test", 5)
                    temporal_memories = [m for m in retrieved_memories if "temporal test" in m.get("content", "").lower()]
                    
                    # Check if memory persisted over time
                    memory_persisted = len(temporal_memories) > 0
                    
                    temporal_results[user["id"]] = {
                        "memory_stored": True,
                        "memory_persisted": memory_persisted,
                        "retrieval_delay_seconds": 2,
                        "temporal_memories_found": len(temporal_memories)
                    }
                    
                    self.log(f"     {user['name']}: Memory persisted after 2s delay: {memory_persisted}")
                else:
                    temporal_results[user["id"]] = {
                        "memory_stored": False,
                        "memory_persisted": False,
                        "error": "Failed to store temporal memory"
                    }
            
            # Check overall temporal persistence
            all_persisted = all(result.get("memory_persisted", False) for result in temporal_results.values())
            
            self.test_results["temporal_persistence"] = {
                "status": "PASS" if all_persisted else "FAIL",
                "users_tested": len(self.test_users),
                "all_memories_persisted": all_persisted,
                "temporal_results": temporal_results
            }
            
            return all_persisted
            
        except Exception as e:
            self.log(f"❌ Temporal Persistence Exception: {e}", "ERROR")
            self.test_results["temporal_persistence"] = {"status": "FAIL", "error": str(e)}
            return False
    
    def test_persona_preference_persistence(self) -> bool:
        """Test 5: Test persistence of user personas and preferences across sessions."""
        self.log("🎭 Testing Persona & Preference Persistence...")
        
        try:
            persona_results = {}
            
            for user in self.test_users:
                self.log(f"   Testing persona persistence for {user['name']}...")
                
                # Store persona-specific memories across multiple "sessions"
                persona_memories = [
                    f"{user['name']} prefers {user['preferences']} in technical discussions",
                    f"As a {user['role']}, {user['name']} focuses on domain-specific topics",
                    f"{user['name']}'s communication style is professional and {user['role'].lower()}-oriented"
                ]
                
                stored_personas = 0
                for memory in persona_memories:
                    if self.store_user_memory(user, memory, "Persona Profile"):
                        stored_personas += 1
                
                # Simulate session break
                time.sleep(1)
                
                # Test retrieval of persona information
                persona_query_results = {}
                persona_queries = [
                    ("preferences", user["preferences"].split(",")[0].strip()),
                    ("role", user["role"]),
                    ("communication", "professional")
                ]
                
                for query_type, query_term in persona_queries:
                    memories = self.retrieve_user_memories(user, query_term, 5)
                    relevant_memories = [m for m in memories if query_term.lower() in m.get("content", "").lower()]
                    
                    persona_query_results[query_type] = {
                        "query_term": query_term,
                        "memories_found": len(memories),
                        "relevant_memories": len(relevant_memories)
                    }
                
                # Check if persona information is retrievable
                total_persona_memories = sum(r["relevant_memories"] for r in persona_query_results.values())
                persona_persisted = total_persona_memories > 0
                
                persona_results[user["id"]] = {
                    "persona_memories_stored": stored_personas,
                    "persona_persisted": persona_persisted,
                    "query_results": persona_query_results,
                    "total_persona_memories": total_persona_memories
                }
                
                self.log(f"     {user['name']}: {stored_personas} stored, {total_persona_memories} persona memories retrievable")
            
            # Check overall persona persistence
            all_personas_persisted = all(result["persona_persisted"] for result in persona_results.values())
            
            self.test_results["persona_persistence"] = {
                "status": "PASS" if all_personas_persisted else "FAIL",
                "users_tested": len(self.test_users),
                "all_personas_persisted": all_personas_persisted,
                "persona_results": persona_results
            }
            
            return all_personas_persisted
            
        except Exception as e:
            self.log(f"❌ Persona Persistence Exception: {e}", "ERROR")
            self.test_results["persona_persistence"] = {"status": "FAIL", "error": str(e)}
            return False
    
    def test_cross_session_context_retrieval(self) -> bool:
        """Test 6: Test retrieval of context from previous sessions."""
        self.log("🔍 Testing Cross-Session Context Retrieval...")
        
        try:
            context_results = {}
            
            for user in self.test_users:
                self.log(f"   Testing context retrieval for {user['name']}...")
                
                # Create memories in "session 1"
                session1_id = self.create_session_id(user["id"], 1)
                session1_memories = [
                    f"In our last conversation, {user['name']} mentioned working on a machine learning project",
                    f"Previous session: {user['name']} asked about best practices for {user['role'].lower()} workflows",
                    f"Context from session 1: {user['name']} showed interest in advanced {user['preferences'].split(',')[0].strip()} topics"
                ]
                
                session1_stored = 0
                for memory in session1_memories:
                    if self.store_user_memory(user, memory, "Session 1 Context", session1_id):
                        session1_stored += 1
                
                # Simulate time gap between sessions
                time.sleep(1)
                
                # Simulate "session 2" trying to retrieve context from session 1
                session2_id = self.create_session_id(user["id"], 2)
                
                # Test context retrieval queries
                context_queries = [
                    "previous conversation",
                    "last session",
                    user["role"].lower(),
                    "mentioned working"
                ]
                
                session2_context = {}
                for query in context_queries:
                    retrieved_memories = self.retrieve_user_memories(user, query, 5)
                    session1_context = [m for m in retrieved_memories if "session 1" in m.get("context", "").lower() or "previous" in m.get("content", "").lower()]
                    
                    session2_context[query] = {
                        "total_retrieved": len(retrieved_memories),
                        "session1_context": len(session1_context)
                    }
                
                # Check if context from previous session is accessible
                total_context_retrieved = sum(r["session1_context"] for r in session2_context.values())
                context_accessible = total_context_retrieved > 0
                
                context_results[user["id"]] = {
                    "session1_memories_stored": session1_stored,
                    "context_accessible_in_session2": context_accessible,
                    "context_queries": session2_context,
                    "total_context_retrieved": total_context_retrieved
                }
                
                self.log(f"     {user['name']}: {session1_stored} session1 memories, {total_context_retrieved} context memories retrieved in session2")
            
            # Check overall cross-session context retrieval
            all_context_accessible = all(result["context_accessible_in_session2"] for result in context_results.values())
            
            self.test_results["cross_session_context"] = {
                "status": "PASS" if all_context_accessible else "FAIL",
                "users_tested": len(self.test_users),
                "all_context_accessible": all_context_accessible,
                "context_results": context_results
            }
            
            return all_context_accessible
            
        except Exception as e:
            self.log(f"❌ Cross-Session Context Exception: {e}", "ERROR")
            self.test_results["cross_session_context"] = {"status": "FAIL", "error": str(e)}
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all multi-user multi-session tests and return results."""
        self.log("🚀 Starting Multi-User Multi-Session Memory Persistence Tests...")
        self.log("=" * 80)
        
        tests = [
            ("User Setup & Isolation", self.test_user_setup_and_isolation),
            ("Multi-Session Persistence", self.test_multi_session_persistence),
            ("Concurrent User Operations", self.test_concurrent_user_operations),
            ("Temporal Memory Persistence", self.test_temporal_memory_persistence),
            ("Persona & Preference Persistence", self.test_persona_preference_persistence),
            ("Cross-Session Context Retrieval", self.test_cross_session_context_retrieval)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n📋 Running Test: {test_name}")
            try:
                if test_func():
                    passed_tests += 1
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.log(f"❌ {test_name}: EXCEPTION - {e}", "ERROR")
        
        # Summary
        self.log("\n" + "=" * 80)
        self.log(f"🎯 Multi-User Multi-Session Test Summary: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL MULTI-USER MULTI-SESSION TESTS PASSED!")
            overall_status = "PASS"
        elif passed_tests >= total_tests * 0.8:  # 80% pass rate
            self.log(f"✅ MULTI-USER TESTS MOSTLY PASSED - {total_tests - passed_tests} tests need attention", "WARN")
            overall_status = "PARTIAL"
        else:
            self.log(f"⚠️ MULTI-USER TESTS NEED WORK - {total_tests - passed_tests} tests failed", "WARN")
            overall_status = "FAIL"
        
        # Save detailed results
        final_results = {
            "overall_status": overall_status,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "test_results": self.test_results,
            "test_users": [{"id": u["id"], "name": u["name"], "role": u["role"]} for u in self.test_users],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return final_results

def main():
    """Main test execution function."""
    print("Multi-User Multi-Session Memory Persistence Test")
    print("Location: tests/ directory (organized file structure)")
    print("Purpose: Verify memory persistence across users and sessions")
    print("=" * 80)
    
    tester = MultiUserSessionTester()
    results = tester.run_all_tests()
    
    # Save results to file in tests directory
    results_file = os.path.join(os.path.dirname(__file__), "multi_user_session_test_results.json")
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Multi-user session test results saved to: {results_file}")
    except Exception as e:
        print(f"⚠️ Could not save multi-user session results: {e}")
    
    return results

if __name__ == "__main__":
    main()
