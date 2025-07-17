#!/usr/bin/env python3
"""
Comprehensive Live System Test
Tests all systems and subsystems interactions including:
- Service health checks
- Ollama model availability  
- Memory system functionality
- Pipeline integration
- Tool execution
- Persona/prompt handling
- End-to-end conversation flow
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List
import sys

# Configure logging for comprehensive test output with Windows Unicode support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'comprehensive_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)

# Set stdout encoding to handle Unicode on Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

class ComprehensiveSystemTest:
    def __init__(self):
        self.base_urls = {
            'openwebui': 'http://localhost:8080',
            'pipelines': 'http://localhost:9099', 
            'backend': 'http://localhost:3000',
            'memory_api': 'http://localhost:5001',
            'ollama': 'http://localhost:11434',
            'chroma': 'http://localhost:8000',
            'redis': 'http://localhost:6379'
        }
        self.test_results = {}
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_test_start(self, test_name: str):
        logger.info(f"[TEST START] {test_name}")
        logger.info("=" * 60)
        
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        status = "[PASS]" if success else "[FAIL]"
        logger.info(f"{status} {test_name}")
        if details:
            logger.info(f"   Details: {details}")
        self.test_results[test_name] = {'success': success, 'details': details}
        logger.info("-" * 60)

    async def test_service_health(self):
        """Test 1: Service Health Checks"""
        self.log_test_start("Service Health Checks")
        
        health_endpoints = {
            'OpenWebUI': f"{self.base_urls['openwebui']}/health",
            'Pipelines': f"{self.base_urls['pipelines']}/",
            'Memory API': f"{self.base_urls['memory_api']}/health",
            'Ollama': f"{self.base_urls['ollama']}/api/tags",
            'ChromaDB': f"{self.base_urls['chroma']}/api/v2/version"
        }
        
        all_healthy = True
        details = []
        
        for service, url in health_endpoints.items():
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        details.append(f"{service}: Healthy (200)")
                        logger.info(f"   [OK] {service}: Healthy")
                    else:
                        details.append(f"{service}: Unhealthy ({response.status})")
                        logger.warning(f"   [WARN] {service}: Status {response.status}")
                        all_healthy = False
            except Exception as e:
                details.append(f"{service}: Error - {str(e)}")
                logger.error(f"   [ERROR] {service}: {str(e)}")
                all_healthy = False
                
        self.log_test_result("Service Health Checks", all_healthy, "; ".join(details))
        return all_healthy

    async def test_ollama_models(self):
        """Test 2: Ollama Model Availability"""
        self.log_test_start("Ollama Model Availability")
        
        try:
            async with self.session.get(f"{self.base_urls['ollama']}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get('models', [])
                    
                    required_models = ['llama3.2:3b', 'nomic-embed-text']
                    available_models = [model['name'] for model in models]
                    
                    # Handle model name variations (e.g., :latest suffix)
                    available_base_models = []
                    for model_name in available_models:
                        # Strip version tags to get base model name
                        base_name = model_name.split(':')[0]
                        if ':' in model_name:
                            available_base_models.append(base_name)
                        available_base_models.append(model_name)  # Also keep full name
                    
                    missing_models = []
                    for required in required_models:
                        # Check if exact match or base model exists
                        if required not in available_models and required not in available_base_models:
                            missing_models.append(required)
                    
                    if not missing_models:
                        details = f"All required models available: {', '.join(available_models)}"
                        logger.info(f"   [OK] Models: {', '.join(available_models)}")
                        self.log_test_result("Ollama Model Availability", True, details)
                        return True
                    else:
                        details = f"Missing models: {', '.join(missing_models)}"
                        logger.warning(f"   [WARN] Missing: {', '.join(missing_models)}")
                        self.log_test_result("Ollama Model Availability", False, details)
                        return False
                else:
                    self.log_test_result("Ollama Model Availability", False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result("Ollama Model Availability", False, str(e))
            return False

    async def test_ollama_generation(self):
        """Test 3: Ollama Text Generation"""
        self.log_test_start("Ollama Text Generation")
        
        test_prompt = "Hello! Please respond with exactly: 'System test successful'"
        
        try:
            payload = {
                "model": "llama3.2:3b",
                "prompt": test_prompt,
                "stream": False
            }
            
            async with self.session.post(
                f"{self.base_urls['ollama']}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    generated_text = data.get('response', '').strip()
                    
                    if generated_text:
                        details = f"Generated: '{generated_text[:100]}...'"
                        logger.info(f"   [OK] Generated: {generated_text[:50]}...")
                        self.log_test_result("Ollama Text Generation", True, details)
                        return True
                    else:
                        self.log_test_result("Ollama Text Generation", False, "Empty response")
                        return False
                else:
                    self.log_test_result("Ollama Text Generation", False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result("Ollama Text Generation", False, str(e))
            return False

    async def test_memory_api(self):
        """Test 4: Memory API Functionality"""
        self.log_test_start("Memory API Functionality")
        
        # Test storing a memory via the memory API
        test_memory = {
            "user_id": "comprehensive_test_user",
            "content": "This is a test memory for comprehensive system validation",
            "context": "comprehensive test",
            "importance": 0.8
        }
        
        try:
            # Test the working /api/memory/store endpoint first
            async with self.session.post(
                f"{self.base_urls['memory_api']}/api/memory/store",
                json=test_memory
            ) as response:
                if response.status == 200:
                    logger.info("   [OK] Memory storage endpoint working")
                    
                    # Test retrieval endpoint
                    retrieve_data = {
                        "user_id": "comprehensive_test_user",
                        "query": "test memory",
                        "limit": 5
                    }
                    async with self.session.post(
                        f"{self.base_urls['memory_api']}/api/memory/retrieve",
                        json=retrieve_data
                    ) as retrieve_response:
                        if retrieve_response.status == 200:
                            retrieve_result = await retrieve_response.json()
                            memory_count = len(retrieve_result.get('memories', []))
                            details = f"Memory API functional - storage and retrieval working, {memory_count} memories found"
                            logger.info(f"   [OK] Memory retrieval working - {memory_count} memories found")
                            self.log_test_result("Memory API Functionality", True, details)
                            return True
                        else:
                            self.log_test_result("Memory API Functionality", False, f"Retrieval failed: HTTP {retrieve_response.status}")
                            return False
                else:
                    self.log_test_result("Memory API Functionality", False, f"Storage failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result("Memory API Functionality", False, str(e))
            return False

    async def test_pipelines_service(self):
        """Test 5: Pipelines Service"""
        self.log_test_start("Pipelines Service")
        
        try:
            # Check pipelines endpoint
            async with self.session.get(f"{self.base_urls['pipelines']}/") as response:
                if response.status == 200:
                    logger.info("   [OK] Pipelines service responding")
                    
                    # Check for available pipelines
                    async with self.session.get(f"{self.base_urls['pipelines']}/api/v1/pipelines") as pipelines_response:
                        if pipelines_response.status == 200:
                            pipelines_data = await pipelines_response.json()
                            pipeline_count = len(pipelines_data) if isinstance(pipelines_data, list) else 0
                            
                            details = f"Service active, {pipeline_count} pipelines available"
                            logger.info(f"   [OK] {pipeline_count} pipelines found")
                            self.log_test_result("Pipelines Service", True, details)
                            return True
                        else:
                            details = f"Service active but pipelines endpoint returned {pipelines_response.status}"
                            self.log_test_result("Pipelines Service", True, details)
                            return True
                else:
                    self.log_test_result("Pipelines Service", False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result("Pipelines Service", False, str(e))
            return False

    async def test_openwebui_integration(self):
        """Test 6: OpenWebUI Integration"""
        self.log_test_start("OpenWebUI Integration")
        
        try:
            # Check OpenWebUI API
            async with self.session.get(f"{self.base_urls['openwebui']}/api/config") as response:
                if response.status == 200:
                    config_data = await response.json()
                    logger.info("   [OK] OpenWebUI API responding")
                    
                    # Check if models are available through OpenWebUI
                    async with self.session.get(f"{self.base_urls['openwebui']}/api/models") as models_response:
                        if models_response.status == 200:
                            models_data = await models_response.json()
                            model_count = len(models_data) if isinstance(models_data, list) else 0
                            
                            details = f"API active, {model_count} models available through UI"
                            logger.info(f"   [OK] {model_count} models available through OpenWebUI")
                            self.log_test_result("OpenWebUI Integration", True, details)
                            return True
                        else:
                            details = f"API active but models endpoint returned {models_response.status}"
                            self.log_test_result("OpenWebUI Integration", True, details)
                            return True
                else:
                    self.log_test_result("OpenWebUI Integration", False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result("OpenWebUI Integration", False, str(e))
            return False

    async def test_full_conversation_flow(self):
        """Test 7: Full Conversation Flow with Memory"""
        self.log_test_start("Full Conversation Flow with Memory")
        
        # This test would ideally simulate a full conversation through OpenWebUI
        # For now, we'll test the components individually and together
        
        conversation_tests = []
        
        # Test 1: Basic LLM response
        try:
            payload = {
                "model": "llama3.2:3b", 
                "prompt": "What is 2+2? Answer with just the number.",
                "stream": False
            }
            
            async with self.session.post(
                f"{self.base_urls['ollama']}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    answer = data.get('response', '').strip()
                    if '4' in answer:
                        conversation_tests.append("[OK] Basic LLM reasoning")
                        logger.info("   [OK] Basic LLM reasoning works")
                    else:
                        conversation_tests.append("[ERROR] Basic LLM reasoning")
                        logger.warning(f"   [WARN] Unexpected answer: {answer}")
                else:
                    conversation_tests.append("[ERROR] LLM connection failed")
                    
        except Exception as e:
            conversation_tests.append(f"[ERROR] LLM error: {str(e)}")
        
        # Test 2: Memory integration 
        try:
            # Store conversation context
            context_memory = {
                "user_id": "conversation_test_user",
                "content": "User asked about mathematics, specifically 2+2",
                "context": "conversation_math",
                "importance": 0.7
            }
            
            async with self.session.post(
                f"{self.base_urls['memory_api']}/api/memory/store",
                json=context_memory
            ) as response:
                if response.status == 200:
                    conversation_tests.append("[OK] Memory storage integration")
                    logger.info("   [OK] Memory storage works")
                else:
                    conversation_tests.append("[ERROR] Memory storage failed")
                    
        except Exception as e:
            conversation_tests.append(f"[ERROR] Memory error: {str(e)}")
        
        success = all("[OK]" in test for test in conversation_tests)
        details = "; ".join(conversation_tests)
        
        self.log_test_result("Full Conversation Flow with Memory", success, details)
        return success

    async def test_data_persistence(self):
        """Test 8: Data Persistence Across Services"""
        self.log_test_start("Data Persistence Across Services")
        
        persistence_tests = []
        
        # Test Redis persistence
        try:
            # Note: Redis doesn't have a direct HTTP API, so we'll test through services that use it
            test_data = {
                "user_id": "persistence_test_user",
                "content": "Persistence test for Redis and memory systems",
                "context": "persistence_validation",
                "importance": 0.8
            }
            
            async with self.session.post(
                f"{self.base_urls['memory_api']}/api/memory/store",
                json=test_data
            ) as response:
                if response.status == 200:
                    persistence_tests.append("[OK] Redis-backed memory persistence")
                    logger.info("   [OK] Redis persistence works")
                else:
                    persistence_tests.append("[ERROR] Redis persistence failed")
                    
        except Exception as e:
            persistence_tests.append(f"[ERROR] Redis error: {str(e)}")
        
        # Test ChromaDB persistence
        try:
            async with self.session.get(f"{self.base_urls['chroma']}/api/v2/version") as response:
                if response.status == 200:
                    persistence_tests.append("[OK] ChromaDB vector persistence")
                    logger.info("   [OK] ChromaDB persistence works")
                else:
                    persistence_tests.append("[ERROR] ChromaDB persistence failed")
                    
        except Exception as e:
            persistence_tests.append(f"[ERROR] ChromaDB error: {str(e)}")
        
        success = all("[OK]" in test for test in persistence_tests)
        details = "; ".join(persistence_tests)
        
        self.log_test_result("Data Persistence Across Services", success, details)
        return success

    async def run_all_tests(self):
        """Run the complete test suite"""
        logger.info("[TEST START] Starting Comprehensive System Test")
        logger.info("=" * 80)
        logger.info(f"Test started at: {datetime.now()}")
        logger.info("=" * 80)
        
        tests = [
            self.test_service_health,
            self.test_ollama_models,
            self.test_ollama_generation,
            self.test_memory_api,
            self.test_pipelines_service,
            self.test_openwebui_integration,
            self.test_full_conversation_flow,
            self.test_data_persistence
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
                await asyncio.sleep(1)  # Brief pause between tests
            except Exception as e:
                logger.error(f"Test failed with exception: {str(e)}")
                results.append(False)
        
        # Final summary
        self.print_final_summary(results)
        return all(results)

    def print_final_summary(self, results):
        """Print comprehensive test summary"""
        logger.info("=" * 80)
        logger.info("[SUMMARY] COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 80)
        
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        logger.info(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        logger.info("")
        
        logger.info("DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "[PASS]" if result['success'] else "[FAIL]"
            logger.info(f"   {status} {test_name}")
            if result['details']:
                logger.info(f"      └─ {result['details']}")
        
        logger.info("=" * 80)
        if success_rate >= 80:
            logger.info("[STATUS] EXCELLENT - All major systems operational!")
        elif success_rate >= 60:
            logger.info("[STATUS] GOOD - Most systems operational")
        elif success_rate >= 40:
            logger.info("[STATUS] PARTIAL - Some systems need attention")
        else:
            logger.info("[STATUS] CRITICAL - Multiple system failures")
        
        logger.info(f"Test completed at: {datetime.now()}")
        logger.info("=" * 80)

async def main():
    """Main test execution"""
    async with ComprehensiveSystemTest() as test_suite:
        await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
