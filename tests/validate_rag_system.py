#!/usr/bin/env python3
"""
RAG Dual-Database Memory System Validation Script
Comprehensive validation of the RAG architecture implementation
"""

import json
import time
import requests
import redis
import chromadb
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.rag_system_config import rag_config, validate_configuration, get_system_info

class RAGSystemValidator:
    """Comprehensive RAG system validation"""
    
    def __init__(self):
        self.redis_client = None
        self.chroma_client = None
        self.memory_api_url = f"http://localhost:{rag_config.api.api_port}"
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str, duration: float = 0.0):
        """Log a test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {test_name}: {message} ({duration:.2f}s)")
        
    def validate_configuration(self):
        """Validate RAG system configuration"""
        start_time = time.time()
        
        try:
            config_valid = validate_configuration()
            if config_valid:
                self.log_result(
                    "Configuration Validation",
                    True,
                    "RAG system configuration is valid",
                    time.time() - start_time
                )
                return True
            else:
                self.log_result(
                    "Configuration Validation",
                    False,
                    "RAG system configuration is invalid",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Configuration Validation",
                False,
                f"Configuration validation failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_redis_connection(self):
        """Test Redis connection"""
        start_time = time.time()
        
        try:
            self.redis_client = redis.Redis(
                host=rag_config.database.redis_host,
                port=rag_config.database.redis_port,
                decode_responses=rag_config.database.redis_decode_responses,
                socket_timeout=rag_config.database.redis_socket_timeout
            )
            
            # Test basic connection
            ping_result = self.redis_client.ping()
            if ping_result:
                # Test set/get operations
                test_key = "rag_test_key"
                test_value = "rag_test_value"
                
                self.redis_client.set(test_key, test_value)
                retrieved_value = self.redis_client.get(test_key)
                
                if retrieved_value == test_value:
                    self.redis_client.delete(test_key)
                    self.log_result(
                        "Redis Connection",
                        True,
                        "Redis connection and operations successful",
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_result(
                        "Redis Connection",
                        False,
                        "Redis set/get operations failed",
                        time.time() - start_time
                    )
                    return False
            else:
                self.log_result(
                    "Redis Connection",
                    False,
                    "Redis ping failed",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Redis Connection",
                False,
                f"Redis connection failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_chromadb_connection(self):
        """Test ChromaDB connection"""
        start_time = time.time()
        
        try:
            self.chroma_client = chromadb.HttpClient(
                host=rag_config.database.chroma_host,
                port=rag_config.database.chroma_port
            )
            
            # Test basic connection
            heartbeat = self.chroma_client.heartbeat()
            
            # Test collection operations
            test_collection_name = "rag_test_collection"
            
            # Create test collection
            try:
                test_collection = self.chroma_client.create_collection(
                    name=test_collection_name
                )
            except Exception:
                # Collection might already exist
                test_collection = self.chroma_client.get_collection(
                    name=test_collection_name
                )
            
            # Test add/query operations
            test_documents = ["This is a test document for RAG validation"]
            test_metadatas = [{"source": "rag_test", "timestamp": datetime.now().isoformat()}]
            test_ids = ["rag_test_doc_1"]
            
            test_collection.add(
                documents=test_documents,
                metadatas=test_metadatas,
                ids=test_ids
            )
            
            # Query the collection
            query_results = test_collection.query(
                query_texts=["test document"],
                n_results=1
            )
            
            if query_results and query_results['documents']:
                # Clean up
                self.chroma_client.delete_collection(name=test_collection_name)
                
                self.log_result(
                    "ChromaDB Connection",
                    True,
                    "ChromaDB connection and operations successful",
                    time.time() - start_time
                )
                return True
            else:
                self.log_result(
                    "ChromaDB Connection",
                    False,
                    "ChromaDB query operations failed",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ChromaDB Connection",
                False,
                f"ChromaDB connection failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_memory_api_health(self):
        """Test Memory API health endpoint"""
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.memory_api_url}/health",
                timeout=10
            )
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Check for RAG-specific health indicators
                if ("redis_status" in health_data and 
                    "chroma_status" in health_data and
                    "system_version" in health_data):
                    
                    self.log_result(
                        "Memory API Health",
                        True,
                        f"Memory API health check successful - v{health_data.get('system_version', 'unknown')}",
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_result(
                        "Memory API Health",
                        False,
                        "Memory API health check incomplete - missing RAG indicators",
                        time.time() - start_time
                    )
                    return False
            else:
                self.log_result(
                    "Memory API Health",
                    False,
                    f"Memory API health check failed - HTTP {response.status_code}",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Memory API Health",
                False,
                f"Memory API health check failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_rag_storage_strategies(self):
        """Test RAG storage strategies"""
        start_time = time.time()
        
        try:
            test_user_id = "rag_test_user"
            
            # Test short-term storage (Redis only)
            short_term_data = {
                "user_id": test_user_id,
                "content": "This is a temporary session message",
                "metadata": {"importance": 0.2, "type": "session"}
            }
            
            response = requests.post(
                f"{self.memory_api_url}/api/memory/store",
                json=short_term_data,
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_result(
                    "RAG Storage Strategies",
                    False,
                    f"Short-term storage failed - HTTP {response.status_code}",
                    time.time() - start_time
                )
                return False
            
            # Test long-term storage (ChromaDB priority)
            long_term_data = {
                "user_id": test_user_id,
                "content": "This is important personal information to remember",
                "metadata": {"importance": 0.9, "type": "personal"}
            }
            
            response = requests.post(
                f"{self.memory_api_url}/api/memory/store",
                json=long_term_data,
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_result(
                    "RAG Storage Strategies",
                    False,
                    f"Long-term storage failed - HTTP {response.status_code}",
                    time.time() - start_time
                )
                return False
            
            # Test retrieval
            response = requests.post(
                f"{self.memory_api_url}/api/memory/retrieve",
                json={
                    "user_id": test_user_id,
                    "query": "personal information",
                    "limit": 5
                },
                timeout=10
            )
            
            if response.status_code == 200:
                retrieval_data = response.json()
                if retrieval_data.get("memories"):
                    self.log_result(
                        "RAG Storage Strategies",
                        True,
                        f"RAG storage strategies working - retrieved {len(retrieval_data['memories'])} memories",
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_result(
                        "RAG Storage Strategies",
                        False,
                        "RAG storage strategies failed - no memories retrieved",
                        time.time() - start_time
                    )
                    return False
            else:
                self.log_result(
                    "RAG Storage Strategies",
                    False,
                    f"RAG retrieval failed - HTTP {response.status_code}",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "RAG Storage Strategies",
                False,
                f"RAG storage strategies test failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_explicit_memory_processing(self):
        """Test explicit memory processing"""
        start_time = time.time()
        
        try:
            test_user_id = "rag_test_user"
            
            # Test explicit memory command
            explicit_memory_data = {
                "user_id": test_user_id,
                "content": "Remember that I prefer dark mode and work at TechCorp as a software engineer",
                "metadata": {"type": "explicit_command"}
            }
            
            response = requests.post(
                f"{self.memory_api_url}/api/memory/store_explicit",
                json=explicit_memory_data,
                timeout=10
            )
            
            if response.status_code == 200:
                explicit_data = response.json()
                
                if (explicit_data.get("processed") and 
                    explicit_data.get("extracted_content") and
                    explicit_data.get("importance_score")):
                    
                    self.log_result(
                        "Explicit Memory Processing",
                        True,
                        f"Explicit memory processing successful - importance: {explicit_data.get('importance_score', 0):.2f}",
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_result(
                        "Explicit Memory Processing",
                        False,
                        "Explicit memory processing incomplete - missing required fields",
                        time.time() - start_time
                    )
                    return False
            else:
                self.log_result(
                    "Explicit Memory Processing",
                    False,
                    f"Explicit memory processing failed - HTTP {response.status_code}",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Explicit Memory Processing",
                False,
                f"Explicit memory processing test failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_semantic_search(self):
        """Test semantic search functionality"""
        start_time = time.time()
        
        try:
            test_user_id = "rag_test_user"
            
            # Test semantic search
            response = requests.get(
                f"{self.memory_api_url}/api/memory/search/{test_user_id}",
                params={
                    "query": "work preferences",
                    "limit": 5
                },
                timeout=10
            )
            
            if response.status_code == 200:
                search_data = response.json()
                
                if search_data.get("results"):
                    self.log_result(
                        "Semantic Search",
                        True,
                        f"Semantic search successful - found {len(search_data['results'])} results",
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_result(
                        "Semantic Search",
                        False,
                        "Semantic search failed - no results found",
                        time.time() - start_time
                    )
                    return False
            else:
                self.log_result(
                    "Semantic Search",
                    False,
                    f"Semantic search failed - HTTP {response.status_code}",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Semantic Search",
                False,
                f"Semantic search test failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_memory_statistics(self):
        """Test memory statistics endpoint"""
        start_time = time.time()
        
        try:
            test_user_id = "rag_test_user"
            
            response = requests.get(
                f"{self.memory_api_url}/api/memory/stats/{test_user_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                stats_data = response.json()
                
                if ("redis_memory_count" in stats_data and 
                    "chroma_memory_count" in stats_data and
                    "total_memory_count" in stats_data):
                    
                    self.log_result(
                        "Memory Statistics",
                        True,
                        f"Memory statistics successful - Total: {stats_data.get('total_memory_count', 0)}",
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_result(
                        "Memory Statistics",
                        False,
                        "Memory statistics incomplete - missing required fields",
                        time.time() - start_time
                    )
                    return False
            else:
                self.log_result(
                    "Memory Statistics",
                    False,
                    f"Memory statistics failed - HTTP {response.status_code}",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Memory Statistics",
                False,
                f"Memory statistics test failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def run_full_validation(self):
        """Run complete RAG system validation"""
        print("=" * 60)
        print("RAG DUAL-DATABASE MEMORY SYSTEM VALIDATION")
        print("=" * 60)
        print()
        
        # System information
        system_info = get_system_info()
        print(f"System Version: {system_info['system_status']['version']}")
        print(f"Architecture: {system_info['system_status']['architecture']}")
        print(f"Deployment Date: {system_info['system_status']['deployment_date']}")
        print()
        
        validation_start = time.time()
        
        # Run validation tests
        tests = [
            self.validate_configuration,
            self.test_redis_connection,
            self.test_chromadb_connection,
            self.test_memory_api_health,
            self.test_rag_storage_strategies,
            self.test_explicit_memory_processing,
            self.test_semantic_search,
            self.test_memory_statistics
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            if test():
                passed_tests += 1
            print()
        
        validation_duration = time.time() - validation_start
        
        print("=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Total Duration: {validation_duration:.2f}s")
        print()
        
        if passed_tests == total_tests:
            print("[OK] RAG DUAL-DATABASE MEMORY SYSTEM VALIDATION PASSED")
            return True
        else:
            print("[FAIL] RAG DUAL-DATABASE MEMORY SYSTEM VALIDATION FAILED")
            return False
    
    def generate_report(self):
        """Generate detailed validation report"""
        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "system_info": get_system_info(),
            "test_results": self.test_results,
            "summary": {
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r["success"]),
                "failed_tests": sum(1 for r in self.test_results if not r["success"]),
                "success_rate": (sum(1 for r in self.test_results if r["success"]) / len(self.test_results)) * 100 if self.test_results else 0
            }
        }
        
        report_path = "logs/rag_validation_report.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Detailed validation report saved to: {report_path}")
        return report


def main():
    """Main validation function"""
    validator = RAGSystemValidator()
    
    try:
        success = validator.run_full_validation()
        validator.generate_report()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n[FAIL] Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Validation failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
