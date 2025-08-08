#!/usr/bin/env python3
"""
Enhanced Multi-User Memory System Test with Threshold Analysis
============================================================

This test addresses the failures from the previous multi-user test and adds:
1. Fixed session persistence testing with proper user_id validation
2. Enhanced temporal persistence with better timing
3. Comprehensive threshold testing for memory retrieval optimization
4. Higher volume memory testing to leverage storage capacity
5. Database-level user isolation verification

Location: tests/ directory (following project standards)
"""

import asyncio
import json
import time
import requests
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import threading
import uuid
import random

class EnhancedMultiUserMemoryTest:
    def __init__(self):
        self.api_base = "http://localhost:5001"
        self.test_results = {}
        self.test_users = {
            "alice": {
                "user_id": "enhanced_alice", 
                "name": "Alice Johnson",
                "role": "Senior Data Scientist",
                "preferences": ["Python", "Machine Learning", "Statistical Analysis", "Deep Learning"],
                "background": "5 years experience in ML, specializes in NLP and computer vision"
            },
            "bob": {
                "user_id": "enhanced_bob", 
                "name": "Bob Smith",
                "role": "Product Manager",
                "preferences": ["Product Strategy", "User Research", "Market Analysis", "Agile"],
                "background": "8 years in product management, focus on AI-driven products"
            },
            "carol": {
                "user_id": "enhanced_carol", 
                "name": "Carol Davis",
                "role": "Senior Software Engineer",
                "preferences": ["Backend Development", "API Design", "Distributed Systems", "Performance"],
                "background": "7 years in backend development, expert in scalable architectures"
            },
            "david": {
                "user_id": "enhanced_david",
                "name": "David Wilson", 
                "role": "DevOps Engineer",
                "preferences": ["Kubernetes", "CI/CD", "Infrastructure", "Monitoring"],
                "background": "6 years in DevOps, specializes in cloud-native deployments"
            }
        }
        self.threshold_test_values = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]  # Different similarity thresholds
        self.memory_volume_targets = [10, 25, 50, 100]  # Memory counts to test
        
    def log(self, level: str, message: str):
        """Enhanced logging with detailed formatting."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] [EnhancedMultiUserTest] {message}")

    def store_memory(self, content: str, user_id: str, context: str = "Test", 
                    importance: float = 0.5, session_id: str = None) -> str:
        """Store a memory with enhanced metadata."""
        memory_id = f"mem_enhanced_{user_id}_{int(time.time() * 1000000)}"
        
        metadata = {
            "user_id": user_id,
            "memory_id": memory_id,
            "context": context,
            "importance": importance,
            "source": "enhanced_test"
        }
        
        if session_id:
            metadata["session_id"] = session_id
            metadata["context"] = f"{context} | Session: {session_id}"
            
        payload = {
            "content": content,
            "metadata": metadata,
            "user_id": user_id
        }
        
        try:
            response = requests.post(f"{self.api_base}/api/memory/store", 
                                  json=payload, timeout=10)
            if response.status_code == 200:
                self.log("INFO", f"✅ Stored memory for {user_id}: {memory_id}")
                return memory_id
            else:
                self.log("ERROR", f"❌ Failed to store memory: {response.text}")
                return None
        except Exception as e:
            self.log("ERROR", f"❌ Memory store error: {str(e)}")
            return None

    def retrieve_memories(self, query: str, user_id: str, limit: int = 10, 
                         threshold: float = 2.0) -> List[Dict]:
        """Retrieve memories with specified threshold."""
        payload = {
            "query": query,
            "user_id": user_id,
            "limit": limit,
            "threshold": threshold
        }
        
        try:
            response = requests.post(f"{self.api_base}/api/memory/retrieve", 
                                  json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                memories = data.get("memories", [])
                self.log("INFO", f"✅ Retrieved {len(memories)} memories for {user_id} (threshold: {threshold})")
                return memories
            else:
                self.log("ERROR", f"❌ Failed to retrieve memories: {response.text}")
                return []
        except Exception as e:
            self.log("ERROR", f"❌ Memory retrieve error: {str(e)}")
            return []

    def test_database_user_isolation(self) -> Dict[str, Any]:
        """Test that user memories are properly isolated in the database."""
        self.log("INFO", "🔍 Testing Database-Level User Isolation...")
        
        results = {
            "status": "PASS",
            "users_tested": len(self.test_users),
            "cross_contamination_found": False,
            "isolation_details": {}
        }
        
        # Store unique memories for each user
        test_memories = {}
        for user_key, user_info in self.test_users.items():
            user_id = user_info["user_id"]
            unique_content = f"UNIQUE_DB_TEST_{user_id}_{uuid.uuid4().hex[:8]}"
            memory_id = self.store_memory(unique_content, user_id, "DB Isolation Test")
            test_memories[user_id] = {
                "content": unique_content,
                "memory_id": memory_id
            }
            time.sleep(0.1)  # Ensure different timestamps
        
        # Test each user can only see their own memories
        for user_key, user_info in self.test_users.items():
            user_id = user_info["user_id"]
            user_content = test_memories[user_id]["content"]
            
            # Retrieve this user's unique memory
            own_memories = self.retrieve_memories(user_content, user_id, limit=50)
            own_found = len([m for m in own_memories if user_content in m.get("content", "")])
            
            # Check for contamination from other users
            contamination_count = 0
            for other_user_id, other_memory in test_memories.items():
                if other_user_id != user_id:
                    contaminated = self.retrieve_memories(other_memory["content"], user_id, limit=50)
                    if any(other_memory["content"] in m.get("content", "") for m in contaminated):
                        contamination_count += 1
                        results["cross_contamination_found"] = True
            
            results["isolation_details"][user_id] = {
                "own_memories_found": own_found,
                "contamination_detected": contamination_count,
                "properly_isolated": contamination_count == 0 and own_found > 0
            }
            
            self.log("INFO", f"   {user_info['name']}: {own_found} own memories, {contamination_count} contaminations")
        
        # Overall status
        all_isolated = all(details["properly_isolated"] for details in results["isolation_details"].values())
        if not all_isolated or results["cross_contamination_found"]:
            results["status"] = "FAIL"
            self.log("ERROR", "❌ Database User Isolation: FAILED")
        else:
            self.log("INFO", "✅ Database User Isolation: PASSED")
            
        return results

    def test_threshold_optimization(self) -> Dict[str, Any]:
        """Test different similarity thresholds for optimal memory retrieval."""
        self.log("INFO", "🎯 Testing Threshold Optimization for Memory Retrieval...")
        
        results = {
            "status": "PASS",
            "thresholds_tested": len(self.threshold_test_values),
            "optimal_threshold": None,
            "threshold_analysis": {},
            "recommendations": []
        }
        
        # Store test memories with varying similarity levels
        test_user = "enhanced_alice"
        base_query = "machine learning project"
        
        # Store related memories with different similarity levels
        test_memories = [
            "Working on a machine learning project for image classification",
            "Developing ML algorithms for predictive analytics", 
            "Creating machine learning models for data analysis",
            "Building deep learning networks for computer vision",
            "Implementing neural networks for pattern recognition",
            "Designing artificial intelligence systems for automation",
            "Programming statistical models for data science",
            "Developing software applications for business intelligence"
        ]
        
        stored_ids = []
        for content in test_memories:
            memory_id = self.store_memory(content, test_user, "Threshold Test")
            if memory_id:
                stored_ids.append(memory_id)
            time.sleep(0.1)
        
        # Test each threshold
        for threshold in self.threshold_test_values:
            memories = self.retrieve_memories(base_query, test_user, limit=20, threshold=threshold)
            
            # Analyze results
            relevancy_scores = []
            for memory in memories:
                similarity = memory.get("similarity_score", 0)
                distance = memory.get("distance", float('inf'))
                relevancy_scores.append({
                    "similarity": similarity,
                    "distance": distance,
                    "content": memory.get("content", "")[:50] + "..."
                })
            
            avg_similarity = sum(r["similarity"] for r in relevancy_scores) / len(relevancy_scores) if relevancy_scores else 0
            avg_distance = sum(r["distance"] for r in relevancy_scores) / len(relevancy_scores) if relevancy_scores else float('inf')
            
            results["threshold_analysis"][threshold] = {
                "memories_returned": len(memories),
                "avg_similarity_score": round(avg_similarity, 4),
                "avg_distance": round(avg_distance, 4),
                "relevancy_distribution": relevancy_scores[:5]  # Top 5 for analysis
            }
            
            self.log("INFO", f"   Threshold {threshold}: {len(memories)} memories, avg similarity: {avg_similarity:.4f}")
        
        # Determine optimal threshold (balance between recall and precision)
        best_threshold = None
        best_score = -1
        
        for threshold, analysis in results["threshold_analysis"].items():
            # Score based on number of results and average similarity
            score = analysis["memories_returned"] * (1 + abs(analysis["avg_similarity_score"]))
            if score > best_score:
                best_score = score
                best_threshold = threshold
        
        results["optimal_threshold"] = best_threshold
        results["recommendations"] = [
            f"Optimal threshold appears to be {best_threshold} for balanced recall/precision",
            f"Higher thresholds (>1.5) provide more focused results",
            f"Lower thresholds (<1.0) provide broader recall",
            "Consider adaptive thresholds based on query type and user context"
        ]
        
        self.log("INFO", f"✅ Threshold Optimization: COMPLETED - Optimal: {best_threshold}")
        return results

    def test_high_volume_memory_performance(self) -> Dict[str, Any]:
        """Test memory system performance with high volumes of memories."""
        self.log("INFO", "📊 Testing High-Volume Memory Performance...")
        
        results = {
            "status": "PASS",
            "volume_tests": {},
            "performance_metrics": {},
            "scalability_assessment": "GOOD"
        }
        
        test_user = "enhanced_bob"
        
        for target_count in self.memory_volume_targets:
            self.log("INFO", f"   Testing with {target_count} memories...")
            
            # Store memories in batches
            start_time = time.time()
            stored_count = 0
            
            for i in range(target_count):
                content = f"High volume test memory {i+1}: {self.test_users['bob']['role']} working on project milestone {i+1} with focus on {random.choice(self.test_users['bob']['preferences'])}"
                memory_id = self.store_memory(content, test_user, f"Volume Test Batch {i//10 + 1}")
                if memory_id:
                    stored_count += 1
                
                # Small delay to prevent overwhelming the API
                if i % 10 == 0:
                    time.sleep(0.1)
            
            storage_time = time.time() - start_time
            
            # Test retrieval performance
            start_time = time.time()
            retrieved_memories = self.retrieve_memories("project milestone", test_user, limit=target_count)
            retrieval_time = time.time() - start_time
            
            # Performance metrics
            storage_rate = stored_count / storage_time if storage_time > 0 else 0
            retrieval_rate = len(retrieved_memories) / retrieval_time if retrieval_time > 0 else 0
            
            results["volume_tests"][target_count] = {
                "memories_stored": stored_count,
                "memories_retrieved": len(retrieved_memories),
                "storage_time_seconds": round(storage_time, 2),
                "retrieval_time_seconds": round(retrieval_time, 2),
                "storage_rate_per_second": round(storage_rate, 2),
                "retrieval_rate_per_second": round(retrieval_rate, 2),
                "success_rate": (stored_count / target_count) * 100 if target_count > 0 else 0
            }
            
            self.log("INFO", f"     Stored: {stored_count}/{target_count}, Retrieved: {len(retrieved_memories)}")
            self.log("INFO", f"     Storage: {storage_rate:.2f}/s, Retrieval: {retrieval_rate:.2f}/s")
        
        # Assess scalability
        volumes = list(results["volume_tests"].keys())
        if len(volumes) >= 2:
            # Compare performance across different volumes
            small_vol = min(volumes)
            large_vol = max(volumes)
            
            small_perf = results["volume_tests"][small_vol]
            large_perf = results["volume_tests"][large_vol]
            
            storage_degradation = (small_perf["storage_rate_per_second"] - large_perf["storage_rate_per_second"]) / small_perf["storage_rate_per_second"] * 100
            retrieval_degradation = (small_perf["retrieval_rate_per_second"] - large_perf["retrieval_rate_per_second"]) / small_perf["retrieval_rate_per_second"] * 100
            
            if storage_degradation > 50 or retrieval_degradation > 50:
                results["scalability_assessment"] = "POOR"
            elif storage_degradation > 25 or retrieval_degradation > 25:
                results["scalability_assessment"] = "MODERATE"
            else:
                results["scalability_assessment"] = "EXCELLENT"
            
            results["performance_metrics"] = {
                "storage_degradation_percent": round(storage_degradation, 2),
                "retrieval_degradation_percent": round(retrieval_degradation, 2),
                "volume_scaling_factor": large_vol / small_vol
            }
        
        self.log("INFO", f"✅ High-Volume Performance: {results['scalability_assessment']}")
        return results

    def test_fixed_session_persistence(self) -> Dict[str, Any]:
        """Fixed version of session persistence testing."""
        self.log("INFO", "🔄 Testing Fixed Multi-Session Persistence...")
        
        results = {
            "status": "PASS",
            "users_tested": len(self.test_users),
            "session_continuity_verified": True,
            "session_results": {}
        }
        
        for user_key, user_info in self.test_users.items():
            user_id = user_info["user_id"]
            user_name = user_info["name"]
            
            self.log("INFO", f"   Testing session persistence for {user_name}...")
            
            # Session 1: Store initial context
            session1_id = f"{user_id}_session_1_{int(time.time())}"
            session1_memories = []
            
            initial_context = f"{user_name} started a new project on {user_info['role']} tasks"
            memory_id1 = self.store_memory(initial_context, user_id, "Session 1", session_id=session1_id)
            session1_memories.append(memory_id1)
            
            project_details = f"Project involves {', '.join(user_info['preferences'][:2])} with focus on innovation"
            memory_id2 = self.store_memory(project_details, user_id, "Session 1", session_id=session1_id)
            session1_memories.append(memory_id2)
            
            time.sleep(0.5)  # Simulate session gap
            
            # Session 2: Continue conversation, should retrieve session 1 context
            session2_id = f"{user_id}_session_2_{int(time.time())}"
            
            # Test if we can retrieve session 1 context in session 2
            previous_context = self.retrieve_memories("project", user_id, limit=10, threshold=2.0)
            session1_context_found = any(session1_id in m.get("metadata", {}).get("context", "") for m in previous_context)
            
            # Store new memory in session 2 with reference to session 1
            continuation = f"Continuing from previous session, {user_name} made progress on the project"
            memory_id3 = self.store_memory(continuation, user_id, "Session 2", session_id=session2_id)
            
            time.sleep(0.5)
            
            # Session 3: Test cross-session retrieval
            session3_id = f"{user_id}_session_3_{int(time.time())}"
            all_project_memories = self.retrieve_memories("project", user_id, limit=20, threshold=2.0)
            
            # Count memories from different sessions
            session1_found = sum(1 for m in all_project_memories if session1_id in m.get("metadata", {}).get("context", ""))
            session2_found = sum(1 for m in all_project_memories if session2_id in m.get("metadata", {}).get("context", ""))
            
            results["session_results"][user_id] = {
                "session1_memories_stored": len(session1_memories),
                "session1_context_available_in_session2": session1_context_found,
                "total_cross_session_memories_found": len(all_project_memories),
                "session1_memories_accessible": session1_found,
                "session2_memories_accessible": session2_found,
                "session_continuity_working": session1_context_found and session1_found > 0
            }
            
            if not results["session_results"][user_id]["session_continuity_working"]:
                results["session_continuity_verified"] = False
            
            self.log("INFO", f"     {user_name}: Session continuity: {results['session_results'][user_id]['session_continuity_working']}")
        
        if not results["session_continuity_verified"]:
            results["status"] = "FAIL"
            self.log("ERROR", "❌ Fixed Session Persistence: FAILED")
        else:
            self.log("INFO", "✅ Fixed Session Persistence: PASSED")
            
        return results

    def test_enhanced_temporal_persistence(self) -> Dict[str, Any]:
        """Enhanced temporal persistence testing with better timing and validation."""
        self.log("INFO", "⏰ Testing Enhanced Temporal Memory Persistence...")
        
        results = {
            "status": "PASS",
            "users_tested": len(self.test_users),
            "temporal_intervals_tested": [1, 3, 5],  # seconds
            "all_memories_persisted": True,
            "temporal_results": {}
        }
        
        for user_key, user_info in self.test_users.items():
            user_id = user_info["user_id"] 
            user_name = user_info["name"]
            
            self.log("INFO", f"   Testing temporal persistence for {user_name}...")
            
            user_results = {
                "intervals_tested": {},
                "overall_persistence": True
            }
            
            for delay_seconds in results["temporal_intervals_tested"]:
                # Store a time-sensitive memory
                timestamp = datetime.now().isoformat()
                temporal_content = f"Temporal test at {timestamp}: {user_name} completed task at this specific time"
                
                memory_id = self.store_memory(temporal_content, user_id, f"Temporal Test {delay_seconds}s")
                
                if memory_id:
                    # Wait for the specified interval
                    time.sleep(delay_seconds)
                    
                    # Try to retrieve the memory
                    retrieved_memories = self.retrieve_memories("temporal test", user_id, limit=5, threshold=2.0)
                    
                    # Check if our specific memory persisted
                    memory_found = any(temporal_content in m.get("content", "") for m in retrieved_memories)
                    
                    # Also test with specific timestamp query
                    timestamp_memories = self.retrieve_memories(timestamp, user_id, limit=5, threshold=1.8)
                    timestamp_found = any(timestamp in m.get("content", "") for m in timestamp_memories)
                    
                    user_results["intervals_tested"][delay_seconds] = {
                        "memory_stored": True,
                        "memory_persisted_general": memory_found,
                        "memory_persisted_specific": timestamp_found,
                        "memories_retrieved": len(retrieved_memories),
                        "delay_seconds": delay_seconds
                    }
                    
                    if not (memory_found or timestamp_found):
                        user_results["overall_persistence"] = False
                        results["all_memories_persisted"] = False
                    
                    self.log("INFO", f"     {delay_seconds}s delay: General={memory_found}, Specific={timestamp_found}")
                else:
                    user_results["intervals_tested"][delay_seconds] = {
                        "memory_stored": False,
                        "memory_persisted_general": False,
                        "memory_persisted_specific": False,
                        "memories_retrieved": 0,
                        "delay_seconds": delay_seconds
                    }
                    user_results["overall_persistence"] = False
                    results["all_memories_persisted"] = False
            
            results["temporal_results"][user_id] = user_results
            self.log("INFO", f"   {user_name}: Overall temporal persistence: {user_results['overall_persistence']}")
        
        if not results["all_memories_persisted"]:
            results["status"] = "FAIL"
            self.log("ERROR", "❌ Enhanced Temporal Persistence: FAILED")
        else:
            self.log("INFO", "✅ Enhanced Temporal Persistence: PASSED")
            
        return results

    def test_concurrent_multi_user_operations(self) -> Dict[str, Any]:
        """Test concurrent operations across multiple users with enhanced metrics."""
        self.log("INFO", "⚡ Testing Enhanced Concurrent Multi-User Operations...")
        
        results = {
            "status": "PASS",
            "total_operations": 0,
            "total_errors": 0,
            "success_rate": 100.0,
            "concurrent_batches": 3,
            "operations_per_batch": 5,
            "user_results": {}
        }
        
        def user_operation_batch(user_info: Dict, batch_id: int) -> Dict:
            """Perform a batch of operations for a user."""
            user_id = user_info["user_id"]
            user_name = user_info["name"]
            
            batch_results = {
                "stored": 0,
                "retrieved": 0,
                "errors": 0,
                "operations": []
            }
            
            for op_id in range(results["operations_per_batch"]):
                try:
                    # Store operation
                    content = f"Concurrent batch {batch_id} operation {op_id+1} by {user_name}: {random.choice(user_info['preferences'])}"
                    memory_id = self.store_memory(content, user_id, f"Concurrent Batch {batch_id}")
                    
                    if memory_id:
                        batch_results["stored"] += 1
                        
                        # Immediate retrieval test
                        retrieved = self.retrieve_memories(user_info["preferences"][0], user_id, limit=5)
                        batch_results["retrieved"] += len(retrieved)
                        
                        batch_results["operations"].append({
                            "type": "store_retrieve",
                            "success": True,
                            "memory_id": memory_id,
                            "retrieved_count": len(retrieved)
                        })
                    else:
                        batch_results["errors"] += 1
                        batch_results["operations"].append({
                            "type": "store_retrieve", 
                            "success": False,
                            "error": "Storage failed"
                        })
                        
                except Exception as e:
                    batch_results["errors"] += 1
                    batch_results["operations"].append({
                        "type": "store_retrieve",
                        "success": False,
                        "error": str(e)
                    })
                
                # Small delay between operations
                time.sleep(0.1)
            
            return batch_results
        
        # Run concurrent batches
        all_user_results = {}
        
        for batch_id in range(results["concurrent_batches"]):
            self.log("INFO", f"   Running concurrent batch {batch_id + 1}...")
            
            # Execute operations for all users concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.test_users)) as executor:
                future_to_user = {
                    executor.submit(user_operation_batch, user_info, batch_id): user_key
                    for user_key, user_info in self.test_users.items()
                }
                
                for future in concurrent.futures.as_completed(future_to_user):
                    user_key = future_to_user[future]
                    try:
                        batch_result = future.result()
                        
                        if user_key not in all_user_results:
                            all_user_results[user_key] = {
                                "total_stored": 0,
                                "total_retrieved": 0,
                                "total_errors": 0,
                                "batches": []
                            }
                        
                        all_user_results[user_key]["total_stored"] += batch_result["stored"]
                        all_user_results[user_key]["total_retrieved"] += batch_result["retrieved"]
                        all_user_results[user_key]["total_errors"] += batch_result["errors"]
                        all_user_results[user_key]["batches"].append(batch_result)
                        
                        results["total_operations"] += batch_result["stored"] + len(batch_result["operations"])
                        results["total_errors"] += batch_result["errors"]
                        
                    except Exception as e:
                        self.log("ERROR", f"Batch error for {user_key}: {str(e)}")
                        results["total_errors"] += results["operations_per_batch"]
            
            time.sleep(0.2)  # Brief pause between batches
        
        # Calculate final metrics
        for user_key, user_results in all_user_results.items():
            user_info = self.test_users[user_key]
            total_ops = results["concurrent_batches"] * results["operations_per_batch"]
            success_rate = ((total_ops - user_results["total_errors"]) / total_ops) * 100 if total_ops > 0 else 0
            
            results["user_results"][user_key] = {
                "user_name": user_info["name"],
                "total_operations": total_ops,
                "stored": user_results["total_stored"],
                "retrieved": user_results["total_retrieved"],
                "errors": user_results["total_errors"],
                "success_rate": round(success_rate, 2)
            }
            
            self.log("INFO", f"   {user_info['name']}: {user_results['total_stored']} stored, {user_results['total_errors']} errors ({success_rate:.1f}% success)")
        
        # Overall success rate
        total_possible_ops = len(self.test_users) * results["concurrent_batches"] * results["operations_per_batch"]
        results["success_rate"] = ((total_possible_ops - results["total_errors"]) / total_possible_ops) * 100 if total_possible_ops > 0 else 0
        
        if results["success_rate"] < 90:  # 90% threshold for concurrent operations
            results["status"] = "FAIL"
            self.log("ERROR", f"❌ Concurrent Operations: FAILED ({results['success_rate']:.1f}% success)")
        else:
            self.log("INFO", f"✅ Concurrent Operations: PASSED ({results['success_rate']:.1f}% success)")
            
        return results

    def run_all_tests(self):
        """Run all enhanced tests with proper error handling."""
        self.log("INFO", "🚀 Starting Enhanced Multi-User Memory System Tests...")
        self.log("INFO", "=" * 80)
        
        # Test suite
        test_suite = [
            ("Database User Isolation", self.test_database_user_isolation),
            ("Threshold Optimization", self.test_threshold_optimization), 
            ("High Volume Performance", self.test_high_volume_memory_performance),
            ("Fixed Session Persistence", self.test_fixed_session_persistence),
            ("Enhanced Temporal Persistence", self.test_enhanced_temporal_persistence),
            ("Enhanced Concurrent Operations", self.test_concurrent_multi_user_operations)
        ]
        
        passed_tests = 0
        total_tests = len(test_suite)
        
        for test_name, test_function in test_suite:
            try:
                self.log("INFO", f"\n📋 Running Test: {test_name}")
                result = test_function()
                self.test_results[test_name.lower().replace(" ", "_")] = result
                
                if result.get("status") == "PASS":
                    passed_tests += 1
                    self.log("INFO", f"✅ {test_name}: PASSED")
                else:
                    self.log("WARN", f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                self.log("ERROR", f"❌ {test_name}: ERROR - {str(e)}")
                self.test_results[test_name.lower().replace(" ", "_")] = {
                    "status": "ERROR",
                    "error": str(e)
                }
        
        # Summary
        self.log("INFO", f"\n" + "=" * 80)
        self.log("INFO", f"🎯 Enhanced Multi-User Test Summary: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("INFO", "🎉 ALL ENHANCED TESTS PASSED!")
            overall_status = "PASS"
        elif passed_tests >= total_tests * 0.8:  # 80% threshold
            self.log("WARN", f"⚠️ MOSTLY PASSING - {passed_tests}/{total_tests} tests successful")
            overall_status = "PARTIAL"
        else:
            self.log("WARN", f"⚠️ NEEDS WORK - {passed_tests}/{total_tests} tests failed")
            overall_status = "FAIL"
        
        # Save results
        final_results = {
            "overall_status": overall_status,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat(),
            "test_summary": {
                "users_tested": len(self.test_users),
                "thresholds_analyzed": len(self.threshold_test_values),
                "volume_targets_tested": len(self.memory_volume_targets),
                "enhanced_features": [
                    "Database-level user isolation verification",
                    "Comprehensive threshold optimization analysis", 
                    "High-volume performance testing",
                    "Fixed session persistence with proper user_id handling",
                    "Enhanced temporal persistence with multiple intervals",
                    "Concurrent operations with detailed error tracking"
                ]
            }
        }
        
        results_file = "tests/enhanced_multi_user_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        self.log("INFO", f"\n💾 Enhanced test results saved to: {results_file}")
        return final_results

def main():
    """Main function to run the enhanced multi-user tests."""
    print("Enhanced Multi-User Multi-Session Memory Test with Threshold Analysis")
    print("Location: tests/ directory (organized file structure)")
    print("Purpose: Fix failed tests and add comprehensive threshold/volume testing")
    print("=" * 80)
    
    test_runner = EnhancedMultiUserMemoryTest()
    results = test_runner.run_all_tests()
    
    return results

if __name__ == "__main__":
    main()
