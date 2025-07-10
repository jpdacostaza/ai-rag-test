#!/usr/bin/env python3
"""
Comprehensive Memory System Test
===============================

This script performs a thorough test of the memory system to verify:
1. Memory persistence across sessions
2. User isolation (each user only sees their own memories)
3. Cross-session memory retrieval
4. Memory storage in both Redis and ChromaDB
5. Memory extraction from conversations
6. End-to-end chat API integration

Test Structure:
- Phase 1: Initial Memory Storage (multiple users introduce themselves)
- Phase 2: Session Break (simulate time passing/restart)
- Phase 3: Memory Recall Test (verify persistence)
- Phase 4: Cross-User Isolation Test (verify no data leakage)
- Phase 5: End-to-End Chat Integration Test
- Phase 6: Memory Management Tests (delete, clear)
"""

import asyncio
import httpx
import json
import time
import uuid
from datetime import datetime

# API URLs
MEMORY_API_URL = "http://localhost:8001"
BACKEND_API_URL = "http://localhost:3000"

class MemoryTestFramework:
    def __init__(self):
        self.test_users = [
            {
                "user_id": "alice.smith.test",
                "name": "Alice Smith",
                "job": "Senior Python Developer",
                "company": "TechCorp Industries",
                "location": "San Francisco",
                "interests": "machine learning and backend APIs",
                "intro_message": "Hello! My name is Alice Smith and I'm a Senior Python Developer at TechCorp Industries in San Francisco. I love working with machine learning and backend APIs.",
                "recall_query": "What do you know about my professional background and interests?"
            },
            {
                "user_id": "bob.jones.test",
                "name": "Bob Jones",
                "job": "Data Scientist",
                "company": "Analytics Pro LLC",
                "location": "New York",
                "interests": "statistical modeling and R programming",
                "intro_message": "Hi there! I'm Bob Jones, a Data Scientist at Analytics Pro LLC in New York. I specialize in statistical modeling and R programming, and I have a PhD in Statistics.",
                "recall_query": "Tell me about my work experience and academic background."
            },
            {
                "user_id": "carol.white.test",
                "name": "Carol White",
                "job": "Product Manager",
                "company": "StartupXYZ",
                "location": "Austin",
                "interests": "user experience design and product strategy",
                "intro_message": "Hey! I'm Carol White, a Product Manager at StartupXYZ in Austin. I focus on user experience design and product strategy, and I previously worked at Google for 4 years.",
                "recall_query": "What can you remember about my career and experience?"
            },
            {
                "user_id": "david.brown.test",
                "name": "David Brown",
                "job": "DevOps Engineer",
                "company": "CloudTech Solutions",
                "location": "Seattle",
                "interests": "containerization and cloud infrastructure",
                "intro_message": "Hello! My name is David Brown and I work as a DevOps Engineer at CloudTech Solutions in Seattle. I'm passionate about containerization and cloud infrastructure, especially Kubernetes.",
                "recall_query": "What do you remember about my technical expertise and role?"
            }
        ]
        self.results = {
            "phase1_storage": {},
            "phase2_session_break": {},
            "phase3_recall": {},
            "phase4_isolation": {},
            "phase5_e2e_chat": {},
            "phase6_management": {},
            "summary": {}
        }
    
    async def run_comprehensive_test(self):
        """Run the complete memory test suite."""
        print("🧪 COMPREHENSIVE MEMORY SYSTEM TEST")
        print("=" * 60)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing with {len(self.test_users)} users")
        print()
        
        try:
            # Phase 1: Initial Memory Storage
            await self.phase1_initial_storage()
            
            # Phase 2: Session Break Simulation
            await self.phase2_session_break()
            
            # Phase 3: Memory Recall Test
            await self.phase3_memory_recall()
            
            # Phase 4: Cross-User Isolation Test
            await self.phase4_cross_user_isolation()
            
            # Phase 5: End-to-End Chat Integration
            await self.phase5_e2e_chat_integration()
            
            # Phase 6: Memory Management Tests
            await self.phase6_memory_management()
            
            # Final Summary
            self.generate_final_summary()
            
        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    async def phase1_initial_storage(self):
        """Phase 1: Store initial memories for all users."""
        print("📝 PHASE 1: INITIAL MEMORY STORAGE")
        print("-" * 50)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for user in self.test_users:
                print(f"\n👤 Testing memory storage for {user['name']} ({user['user_id']})")
                
                # Method 1: Direct memory storage API
                save_request = {
                    "user_id": user["user_id"],
                    "content": user["intro_message"],
                    "metadata": {"test_phase": "phase1", "method": "direct_api"},
                    "category": "introduction"
                }
                
                try:
                    response = await client.post(
                        f"{MEMORY_API_URL}/api/memory/save",
                        json=save_request
                    )
                    
                    if response.status_code == 200:
                        print(f"  ✅ Direct API storage successful")
                        self.results["phase1_storage"][user["user_id"]] = {"direct_api": True}
                    else:
                        print(f"  ❌ Direct API storage failed: {response.status_code}")
                        self.results["phase1_storage"][user["user_id"]] = {"direct_api": False}
                        
                except Exception as e:
                    print(f"  ❌ Direct API storage error: {e}")
                    self.results["phase1_storage"][user["user_id"]] = {"direct_api": False}
                
                # Method 2: Learning interaction API (simulates conversation)
                interaction_request = {
                    "user_id": user["user_id"],
                    "conversation_id": f"test_session_{int(time.time())}",
                    "user_message": user["intro_message"],
                    "assistant_response": f"Nice to meet you, {user['name']}! I'll remember your background.",
                    "context": {"test_phase": "phase1", "method": "interaction_api"}
                }
                
                try:
                    response = await client.post(
                        f"{MEMORY_API_URL}/api/learning/process_interaction",
                        json=interaction_request
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        memories_stored = data.get("new_memories", 0)
                        print(f"  ✅ Interaction API storage successful: {memories_stored} memories extracted")
                        self.results["phase1_storage"][user["user_id"]]["interaction_api"] = True
                        self.results["phase1_storage"][user["user_id"]]["memories_extracted"] = memories_stored
                    else:
                        print(f"  ❌ Interaction API storage failed: {response.status_code}")
                        self.results["phase1_storage"][user["user_id"]]["interaction_api"] = False
                        
                except Exception as e:
                    print(f"  ❌ Interaction API storage error: {e}")
                    self.results["phase1_storage"][user["user_id"]]["interaction_api"] = False
                
                # Add some additional specific memories
                specific_memories = [
                    f"User's name is {user['name']}",
                    f"User works as {user['job']} at {user['company']}",
                    f"User lives in {user['location']}",
                    f"User is interested in {user['interests']}"
                ]
                
                for memory in specific_memories:
                    try:
                        save_request = {
                            "user_id": user["user_id"],
                            "content": memory,
                            "metadata": {"test_phase": "phase1", "method": "specific_facts"},
                            "category": "explicit"
                        }
                        
                        response = await client.post(
                            f"{MEMORY_API_URL}/api/memory/save",
                            json=save_request
                        )
                        
                        if response.status_code == 200:
                            print(f"    ✅ Stored: {memory[:40]}...")
                        else:
                            print(f"    ❌ Failed to store: {memory[:40]}...")
                            
                    except Exception as e:
                        print(f"    ❌ Error storing specific memory: {e}")
                
                # Small delay between users
                await asyncio.sleep(0.5)
        
        print(f"\n📊 Phase 1 Summary:")
        successful_users = sum(1 for user_id, results in self.results["phase1_storage"].items() 
                              if results.get("direct_api", False) or results.get("interaction_api", False))
        print(f"   Users with successful storage: {successful_users}/{len(self.test_users)}")
    
    async def phase2_session_break(self):
        """Phase 2: Simulate session break."""
        print(f"\n⏰ PHASE 2: SESSION BREAK SIMULATION")
        print("-" * 50)
        print("Simulating time passing and session restart...")
        print("In a real scenario, this would be:")
        print("  - User closes browser/app")
        print("  - Time passes (hours/days)")
        print("  - Backend services may restart")
        print("  - User starts new session")
        
        # Wait a few seconds to simulate time passing
        for i in range(3, 0, -1):
            print(f"  Waiting {i} seconds...")
            await asyncio.sleep(1)
        
        print("  ✅ Session break simulation complete")
        self.results["phase2_session_break"]["completed"] = True
    
    async def phase3_memory_recall(self):
        """Phase 3: Test memory recall across sessions."""
        print(f"\n🔍 PHASE 3: MEMORY RECALL TEST")
        print("-" * 50)
        print("Testing if memories persist across sessions...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for user in self.test_users:
                print(f"\n👤 Testing memory recall for {user['name']} ({user['user_id']})")
                
                # Test 1: General query
                retrieve_request = {
                    "user_id": user["user_id"],
                    "query": "professional background work experience",
                    "limit": 10,
                    "threshold": 0.01
                }
                
                try:
                    response = await client.post(
                        f"{MEMORY_API_URL}/api/memory/retrieve",
                        json=retrieve_request
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        memories = data.get("memories", [])
                        sources = data.get("sources", {})
                        
                        print(f"  📚 Retrieved {len(memories)} memories")
                        print(f"      Short-term (Redis): {sources.get('short_term', 0)}")
                        print(f"      Long-term (ChromaDB): {sources.get('long_term', 0)}")
                        
                        # Analyze memory content
                        user_specific_content = 0
                        contains_name = False
                        contains_job = False
                        contains_company = False
                        contains_location = False
                        
                        for memory in memories:
                            content = memory.get("content", "").lower()
                            memory_user_id = memory.get("user_id", "")
                            
                            if memory_user_id == user["user_id"]:
                                user_specific_content += 1
                                
                            if user["name"].lower() in content:
                                contains_name = True
                            if user["job"].lower() in content:
                                contains_job = True
                            if user["company"].lower() in content:
                                contains_company = True
                            if user["location"].lower() in content:
                                contains_location = True
                            
                            print(f"      - {content[:60]}...")
                        
                        recall_score = sum([contains_name, contains_job, contains_company, contains_location])
                        print(f"  📊 Recall Analysis:")
                        print(f"      User-specific memories: {user_specific_content}/{len(memories)}")
                        print(f"      Contains name: {contains_name}")
                        print(f"      Contains job: {contains_job}")
                        print(f"      Contains company: {contains_company}")
                        print(f"      Contains location: {contains_location}")
                        print(f"      Overall recall score: {recall_score}/4")
                        
                        self.results["phase3_recall"][user["user_id"]] = {
                            "success": True,
                            "total_memories": len(memories),
                            "user_specific": user_specific_content,
                            "recall_score": recall_score,
                            "sources": sources
                        }
                        
                        if recall_score >= 2:
                            print(f"  ✅ Memory recall successful")
                        else:
                            print(f"  ⚠️  Memory recall partial")
                            
                    else:
                        print(f"  ❌ Memory retrieval failed: {response.status_code}")
                        self.results["phase3_recall"][user["user_id"]] = {"success": False}
                        
                except Exception as e:
                    print(f"  ❌ Memory retrieval error: {e}")
                    self.results["phase3_recall"][user["user_id"]] = {"success": False}
                
                # Test 2: Specific name query
                name_query = {
                    "user_id": user["user_id"],
                    "query": f"name {user['name'].split()[0]}",
                    "limit": 5,
                    "threshold": 0.01
                }
                
                try:
                    response = await client.post(
                        f"{MEMORY_API_URL}/api/memory/retrieve",
                        json=name_query
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        name_memories = data.get("memories", [])
                        name_found = any(user["name"].lower() in mem.get("content", "").lower() 
                                       for mem in name_memories)
                        print(f"  👤 Name-specific query: {len(name_memories)} memories, name found: {name_found}")
                        self.results["phase3_recall"][user["user_id"]]["name_recall"] = name_found
                        
                except Exception as e:
                    print(f"  ❌ Name query error: {e}")
        
        print(f"\n📊 Phase 3 Summary:")
        successful_recalls = sum(1 for user_id, results in self.results["phase3_recall"].items() 
                               if results.get("success", False) and results.get("recall_score", 0) >= 2)
        print(f"   Users with successful recall: {successful_recalls}/{len(self.test_users)}")
    
    async def phase4_cross_user_isolation(self):
        """Phase 4: Test user isolation."""
        print(f"\n🔒 PHASE 4: CROSS-USER ISOLATION TEST")
        print("-" * 50)
        print("Testing that users cannot access each other's memories...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            isolation_violations = 0
            
            for i, user_a in enumerate(self.test_users):
                for j, user_b in enumerate(self.test_users):
                    if i >= j:  # Skip self and avoid duplicates
                        continue
                    
                    print(f"\n🔍 Testing: {user_a['name']} trying to access {user_b['name']}'s info")
                    
                    # User A tries to query for User B's specific information
                    cross_query = {
                        "user_id": user_a["user_id"],  # User A's session
                        "query": f"{user_b['name']} {user_b['company']} {user_b['job']}",  # User B's info
                        "limit": 10,
                        "threshold": 0.01
                    }
                    
                    try:
                        response = await client.post(
                            f"{MEMORY_API_URL}/api/memory/retrieve",
                            json=cross_query
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            memories = data.get("memories", [])
                            
                            # Check if any memories contain User B's information
                            leaked_info = []
                            for memory in memories:
                                content = memory.get("content", "").lower()
                                memory_user_id = memory.get("user_id", "")
                                
                                # Check for User B's specific info in User A's memories
                                if (user_b["name"].lower() in content or 
                                    user_b["company"].lower() in content or
                                    user_b["location"].lower() in content):
                                    # But make sure it's not User A's own memory mentioning User B
                                    if memory_user_id == user_a["user_id"]:
                                        leaked_info.append({
                                            "content": content,
                                            "user_id": memory_user_id
                                        })
                                        
                                # Critical: Check if we got memories that belong to User B
                                elif memory_user_id == user_b["user_id"]:
                                    leaked_info.append({
                                        "content": content,
                                        "user_id": memory_user_id,
                                        "critical": True
                                    })
                            
                            if leaked_info:
                                print(f"  ❌ ISOLATION VIOLATION DETECTED!")
                                isolation_violations += 1
                                for leak in leaked_info:
                                    if leak.get("critical"):
                                        print(f"      CRITICAL: Got memory from {leak['user_id']}: {leak['content'][:50]}...")
                                    else:
                                        print(f"      Info leak: {leak['content'][:50]}...")
                            else:
                                print(f"  ✅ No information leakage")
                            
                            # Store results
                            key = f"{user_a['user_id']}_vs_{user_b['user_id']}"
                            self.results["phase4_isolation"][key] = {
                                "violation": len(leaked_info) > 0,
                                "leaked_items": len(leaked_info),
                                "memories_returned": len(memories)
                            }
                            
                        else:
                            print(f"  ❌ Query failed: {response.status_code}")
                            
                    except Exception as e:
                        print(f"  ❌ Cross-user query error: {e}")
            
            print(f"\n📊 Phase 4 Summary:")
            print(f"   Total isolation violations: {isolation_violations}")
            if isolation_violations == 0:
                print(f"   ✅ Perfect user isolation maintained!")
            else:
                print(f"   ❌ User isolation compromised!")
    
    async def phase5_e2e_chat_integration(self):
        """Phase 5: Test end-to-end chat integration."""
        print(f"\n💬 PHASE 5: END-TO-END CHAT INTEGRATION TEST")
        print("-" * 50)
        print("Testing memory integration with chat API...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for user in self.test_users:
                print(f"\n👤 Testing chat integration for {user['name']} ({user['user_id']})")
                
                # Test chat with memory recall
                chat_request = {
                    "model": "llama3.2:3b",
                    "messages": [
                        {
                            "role": "user",
                            "content": user["recall_query"]
                        }
                    ],
                    "stream": False,
                    "user": user["user_id"]
                }
                
                try:
                    response = await client.post(
                        f"{BACKEND_API_URL}/v1/chat/completions",
                        json=chat_request
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        ai_response = data["choices"][0]["message"]["content"].lower()
                        
                        print(f"  📝 Chat response received ({len(ai_response)} chars)")
                        
                        # Analyze if the AI response contains user's information
                        contains_name = user["name"].lower() in ai_response
                        contains_job = user["job"].lower() in ai_response
                        contains_company = user["company"].lower() in ai_response
                        contains_location = user["location"].lower() in ai_response
                        
                        memory_integration_score = sum([contains_name, contains_job, contains_company, contains_location])
                        
                        print(f"  🧠 Memory integration analysis:")
                        print(f"      Contains name: {contains_name}")
                        print(f"      Contains job: {contains_job}")
                        print(f"      Contains company: {contains_company}")
                        print(f"      Contains location: {contains_location}")
                        print(f"      Integration score: {memory_integration_score}/4")
                        
                        # Show part of the response for verification
                        print(f"  💬 Response preview: {ai_response[:150]}...")
                        
                        self.results["phase5_e2e_chat"][user["user_id"]] = {
                            "success": True,
                            "integration_score": memory_integration_score,
                            "response_length": len(ai_response),
                            "contains_personal_info": memory_integration_score > 0
                        }
                        
                        if memory_integration_score >= 2:
                            print(f"  ✅ Excellent memory integration")
                        elif memory_integration_score >= 1:
                            print(f"  ⚠️  Partial memory integration")
                        else:
                            print(f"  ❌ No memory integration detected")
                            
                    else:
                        print(f"  ❌ Chat request failed: {response.status_code}")
                        print(f"      Response: {response.text}")
                        self.results["phase5_e2e_chat"][user["user_id"]] = {"success": False}
                        
                except Exception as e:
                    print(f"  ❌ Chat integration error: {e}")
                    self.results["phase5_e2e_chat"][user["user_id"]] = {"success": False}
        
        print(f"\n📊 Phase 5 Summary:")
        successful_integrations = sum(1 for user_id, results in self.results["phase5_e2e_chat"].items() 
                                    if results.get("success", False) and results.get("integration_score", 0) >= 1)
        print(f"   Users with successful chat integration: {successful_integrations}/{len(self.test_users)}")
    
    async def phase6_memory_management(self):
        """Phase 6: Test memory management operations."""
        print(f"\n🗂️ PHASE 6: MEMORY MANAGEMENT TEST")
        print("-" * 50)
        print("Testing memory management operations...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test with first user only to avoid affecting other tests
            test_user = self.test_users[0]
            print(f"\n👤 Testing memory management for {test_user['name']}")
            
            # Test 1: List all memories
            try:
                response = await client.get(f"{MEMORY_API_URL}/api/memory/list/{test_user['user_id']}")
                if response.status_code == 200:
                    data = response.json()
                    memory_count = data.get("count", 0)
                    print(f"  📋 Listed {memory_count} memories")
                    self.results["phase6_management"]["list_success"] = True
                    self.results["phase6_management"]["total_memories"] = memory_count
                else:
                    print(f"  ❌ Memory list failed: {response.status_code}")
                    self.results["phase6_management"]["list_success"] = False
            except Exception as e:
                print(f"  ❌ Memory list error: {e}")
                self.results["phase6_management"]["list_success"] = False
            
            # Test 2: Delete specific memory
            delete_request = {
                "user_id": test_user["user_id"],
                "query": "TechCorp",
                "exact_match": False
            }
            
            try:
                response = await client.post(
                    f"{MEMORY_API_URL}/api/memory/delete",
                    json=delete_request
                )
                
                if response.status_code == 200:
                    data = response.json()
                    deleted_count = data.get("deleted_count", 0)
                    print(f"  🗑️ Deleted {deleted_count} memories containing 'TechCorp'")
                    self.results["phase6_management"]["delete_success"] = True
                    self.results["phase6_management"]["deleted_count"] = deleted_count
                else:
                    print(f"  ❌ Memory deletion failed: {response.status_code}")
                    self.results["phase6_management"]["delete_success"] = False
            except Exception as e:
                print(f"  ❌ Memory deletion error: {e}")
                self.results["phase6_management"]["delete_success"] = False
            
            # Test 3: Verify deletion worked
            try:
                retrieve_request = {
                    "user_id": test_user["user_id"],
                    "query": "TechCorp",
                    "limit": 10,
                    "threshold": 0.01
                }
                
                response = await client.post(
                    f"{MEMORY_API_URL}/api/memory/retrieve",
                    json=retrieve_request
                )
                
                if response.status_code == 200:
                    data = response.json()
                    remaining_memories = data.get("memories", [])
                    techcorp_found = any("techcorp" in mem.get("content", "").lower() for mem in remaining_memories)
                    
                    print(f"  🔍 Verification: {len(remaining_memories)} memories found, TechCorp present: {techcorp_found}")
                    self.results["phase6_management"]["deletion_verified"] = not techcorp_found
                    
                    if not techcorp_found:
                        print(f"  ✅ Deletion verified successfully")
                    else:
                        print(f"  ⚠️  Some TechCorp memories still present")
                        
            except Exception as e:
                print(f"  ❌ Deletion verification error: {e}")
        
        print(f"\n📊 Phase 6 Summary:")
        management_operations = ["list_success", "delete_success", "deletion_verified"]
        successful_operations = sum(1 for op in management_operations 
                                  if self.results["phase6_management"].get(op, False))
        print(f"   Successful management operations: {successful_operations}/{len(management_operations)}")
    
    def generate_final_summary(self):
        """Generate comprehensive test summary."""
        print(f"\n🎯 FINAL TEST SUMMARY")
        print("=" * 60)
        
        # Phase 1: Storage
        phase1_success = sum(1 for user_id, results in self.results["phase1_storage"].items() 
                           if results.get("direct_api", False) or results.get("interaction_api", False))
        print(f"📝 Phase 1 - Initial Storage: {phase1_success}/{len(self.test_users)} users successful")
        
        # Phase 3: Recall
        phase3_success = sum(1 for user_id, results in self.results["phase3_recall"].items() 
                           if results.get("success", False) and results.get("recall_score", 0) >= 2)
        print(f"🔍 Phase 3 - Memory Recall: {phase3_success}/{len(self.test_users)} users successful")
        
        # Phase 4: Isolation
        isolation_violations = sum(1 for key, results in self.results["phase4_isolation"].items() 
                                 if results.get("violation", False))
        total_isolation_tests = len(self.results["phase4_isolation"])
        print(f"🔒 Phase 4 - User Isolation: {total_isolation_tests - isolation_violations}/{total_isolation_tests} tests passed")
        
        # Phase 5: E2E Integration
        phase5_success = sum(1 for user_id, results in self.results["phase5_e2e_chat"].items() 
                           if results.get("success", False) and results.get("integration_score", 0) >= 1)
        print(f"💬 Phase 5 - E2E Chat Integration: {phase5_success}/{len(self.test_users)} users successful")
        
        # Phase 6: Management
        management_operations = ["list_success", "delete_success", "deletion_verified"]
        phase6_success = sum(1 for op in management_operations 
                           if self.results["phase6_management"].get(op, False))
        print(f"🗂️ Phase 6 - Memory Management: {phase6_success}/{len(management_operations)} operations successful")
        
        # Overall Assessment
        print(f"\n🏆 OVERALL ASSESSMENT:")
        
        # Storage & Persistence
        storage_score = (phase1_success / len(self.test_users)) * 100
        recall_score = (phase3_success / len(self.test_users)) * 100
        persistence_health = (storage_score + recall_score) / 2
        
        print(f"   📊 Memory Persistence Health: {persistence_health:.1f}%")
        if persistence_health >= 90:
            print(f"      ✅ Excellent - Memories persist reliably across sessions")
        elif persistence_health >= 70:
            print(f"      ⚠️  Good - Most memories persist with minor issues")
        else:
            print(f"      ❌ Poor - Significant persistence problems detected")
        
        # User Isolation
        isolation_score = ((total_isolation_tests - isolation_violations) / total_isolation_tests) * 100 if total_isolation_tests > 0 else 0
        print(f"   🔐 User Isolation Score: {isolation_score:.1f}%")
        if isolation_score == 100:
            print(f"      ✅ Perfect - No cross-user data leakage detected")
        elif isolation_score >= 90:
            print(f"      ⚠️  Good - Minor isolation issues detected")
        else:
            print(f"      ❌ Critical - Significant user isolation problems")
        
        # Integration Quality
        integration_score = (phase5_success / len(self.test_users)) * 100
        print(f"   🔗 Integration Quality: {integration_score:.1f}%")
        if integration_score >= 80:
            print(f"      ✅ Excellent - Memory integrates well with chat API")
        elif integration_score >= 60:
            print(f"      ⚠️  Partial - Some memory integration issues")
        else:
            print(f"      ❌ Poor - Memory integration not working properly")
        
        # Final Verdict
        overall_score = (persistence_health + isolation_score + integration_score) / 3
        print(f"\n🎖️ FINAL VERDICT: {overall_score:.1f}%")
        
        if overall_score >= 90:
            print(f"   🌟 EXCELLENT - Memory system is working exceptionally well!")
            print(f"      ✅ Memories persist across sessions")
            print(f"      ✅ User isolation is maintained")
            print(f"      ✅ Integration with chat API is seamless")
        elif overall_score >= 75:
            print(f"   👍 GOOD - Memory system is working well with minor issues")
        elif overall_score >= 60:
            print(f"   ⚠️  FAIR - Memory system has some problems that need attention")
        else:
            print(f"   ❌ POOR - Memory system has significant issues requiring immediate attention")
        
        print(f"\n📋 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Store summary for reference
        self.results["summary"] = {
            "overall_score": overall_score,
            "persistence_health": persistence_health,
            "isolation_score": isolation_score,
            "integration_score": integration_score,
            "test_timestamp": datetime.now().isoformat()
        }

async def main():
    """Run the comprehensive memory test."""
    test_framework = MemoryTestFramework()
    await test_framework.run_comprehensive_test()
    
    # Ask if user wants to clean up test data
    cleanup = input("\n🧹 Clean up test data? (y/N): ").strip().lower()
    if cleanup in ['y', 'yes']:
        print("🧹 Cleaning up test data...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            for user in test_framework.test_users:
                try:
                    clear_request = {
                        "user_id": user["user_id"],
                        "confirm": True
                    }
                    
                    response = await client.post(
                        f"{MEMORY_API_URL}/api/memory/clear",
                        json=clear_request
                    )
                    
                    if response.status_code == 200:
                        print(f"  ✅ Cleared memories for {user['name']}")
                    else:
                        print(f"  ⚠️  Could not clear memories for {user['name']}")
                        
                except Exception as e:
                    print(f"  ❌ Error clearing memories for {user['name']}: {e}")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Memory System Test")
    asyncio.run(main())
    print("✅ Test suite completed!")
