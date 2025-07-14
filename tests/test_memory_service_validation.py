#!/usr/bin/env python3
"""
Memory Service Validation Test
=============================

This test focuses on validating the memory service components and working around
the identified issues:

1. Pipeline memory retrieval method not available
2. Memory API connection failures 
3. Backend timeout issues

FINDINGS TO ADDRESS:
- Direct memory API storage works
- Pipeline endpoints return 404 (expected for enhanced_memory_pipeline)
- Backend /v1/chat/completions endpoint times out
- Memory service warnings about pipeline retrieval methods
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, Any
import sys
import uuid
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'memory_validation_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

logger = logging.getLogger(__name__)

class MemoryServiceValidationTest:
    """Focused test for memory service validation and issue resolution"""
    
    def __init__(self):
        self.base_urls = {
            'backend': 'http://localhost:3000',
            'memory_api': 'http://localhost:5001',
            'pipelines': 'http://localhost:9099'
        }
        self.test_results = {}
        self.session = None
        self.test_user_id = "4e5fc3e1-a7a8-40b8-af00-92482fe23c05"
        self.test_email = "admin@theroot.za.net"
        self.conversation_id = f"memory_test_{uuid.uuid4().hex[:8]}"
        
    async def __aenter__(self):
        # Conservative timeout settings
        timeout = aiohttp.ClientTimeout(total=10, connect=3, sock_read=7)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_test_start(self, test_name: str):
        logger.info(f"\n{'='*60}")
        logger.info(f"[TEST] {test_name}")
        logger.info(f"{'='*60}")
        
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        status = "[✅ PASS]" if success else "[❌ FAIL]"
        logger.info(f"\n{status} {test_name}")
        if details:
            logger.info(f"Details: {details}")
        self.test_results[test_name] = {'success': success, 'details': details}

    async def test_memory_api_direct_access(self):
        """Test 1: Validate direct memory API functionality"""
        self.log_test_start("Memory API Direct Access")
        
        results = []
        
        # Test health endpoint
        try:
            async with self.session.get(f"{self.base_urls['memory_api']}/health") as response:
                if response.status == 200:
                    results.append("✅ Health endpoint operational")
                else:
                    results.append(f"❌ Health endpoint failed: HTTP {response.status}")
        except Exception as e:
            results.append(f"❌ Health endpoint error: {str(e)}")
        
        # Test direct storage
        test_memory = {
            "user_id": self.test_user_id,
            "content": f"Memory service validation test - {self.conversation_id}",
            "metadata": {
                "type": "test",
                "timestamp": datetime.now().isoformat(),
                "source": "validation_test"
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_urls['memory_api']}/store",
                json=test_memory,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    results.append("✅ Direct storage operational")
                    data = await response.json()
                    logger.info(f"   Storage response: {data}")
                else:
                    text = await response.text()
                    results.append(f"❌ Direct storage failed: HTTP {response.status} - {text}")
        except Exception as e:
            results.append(f"❌ Direct storage error: {str(e)}")
        
        # Test retrieval endpoints
        retrieval_endpoints = [
            f"/retrieve/{self.test_user_id}",
            f"/memories/{self.test_user_id}",
            f"/search?user_id={self.test_user_id}"
        ]
        
        retrieval_working = False
        for endpoint in retrieval_endpoints:
            try:
                async with self.session.get(f"{self.base_urls['memory_api']}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        results.append(f"✅ Retrieval endpoint {endpoint} working - {len(data)} items")
                        retrieval_working = True
                        break
                    else:
                        logger.info(f"   Endpoint {endpoint}: HTTP {response.status}")
            except Exception as e:
                logger.info(f"   Endpoint {endpoint} error: {str(e)}")
        
        if not retrieval_working:
            results.append("⚠️ No working retrieval endpoints found")
        
        success = any("✅" in result for result in results)
        details = "; ".join(results)
        self.log_test_result("Memory API Direct Access", success, details)
        return success

    async def test_backend_health_and_endpoints(self):
        """Test 2: Check backend service health and available endpoints"""
        self.log_test_start("Backend Service Health Check")
        
        results = []
        
        # Test basic health
        try:
            async with self.session.get(f"{self.base_urls['backend']}/health/simple") as response:
                if response.status == 200:
                    results.append("✅ Backend health endpoint operational")
                else:
                    results.append(f"❌ Backend health failed: HTTP {response.status}")
        except Exception as e:
            results.append(f"❌ Backend health error: {str(e)}")
        
        # Test alternative endpoints that might work better
        test_endpoints = [
            "/health",
            "/api/health", 
            "/v1/health",
            "/status"
        ]
        
        working_endpoints = []
        for endpoint in test_endpoints:
            try:
                async with self.session.get(f"{self.base_urls['backend']}{endpoint}") as response:
                    if response.status == 200:
                        working_endpoints.append(endpoint)
                        logger.info(f"   Working endpoint: {endpoint}")
            except Exception as e:
                logger.info(f"   Endpoint {endpoint} error: {str(e)}")
        
        if working_endpoints:
            results.append(f"✅ Additional working endpoints: {', '.join(working_endpoints)}")
        
        # Check if chat endpoint is available without timeout
        try:
            # Very short timeout to avoid hanging
            short_timeout = aiohttp.ClientTimeout(total=3, connect=1, sock_read=2)
            async with aiohttp.ClientSession(timeout=short_timeout) as short_session:
                test_payload = {
                    "model": "llama3.2:3b",
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                    "stream": False
                }
                
                async with short_session.post(
                    f"{self.base_urls['backend']}/v1/chat/completions",
                    json=test_payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    results.append(f"✅ Chat endpoint responsive: HTTP {response.status}")
                    
        except asyncio.TimeoutError:
            results.append("❌ Chat endpoint timeout (performance issue)")
        except Exception as e:
            results.append(f"⚠️ Chat endpoint issue: {str(e)[:50]}")
        
        success = any("✅" in result for result in results)
        details = "; ".join(results)
        self.log_test_result("Backend Service Health Check", success, details)
        return success

    async def test_pipeline_service_integration(self):
        """Test 3: Check pipeline service and memory integration points"""
        self.log_test_start("Pipeline Service Integration")
        
        results = []
        
        # Test basic pipeline health
        try:
            async with self.session.get(f"{self.base_urls['pipelines']}/") as response:
                if response.status == 200:
                    data = await response.json()
                    results.append("✅ Pipeline service operational")
                    logger.info(f"   Pipeline status: {data}")
                else:
                    results.append(f"❌ Pipeline service failed: HTTP {response.status}")
        except Exception as e:
            results.append(f"❌ Pipeline service error: {str(e)}")
        
        # Check what pipelines are actually available
        pipeline_discovery_endpoints = [
            "/pipelines",
            "/api/pipelines", 
            "/v1/pipelines",
            "/list",
            "/api/list"
        ]
        
        found_pipelines = []
        for endpoint in pipeline_discovery_endpoints:
            try:
                async with self.session.get(f"{self.base_urls['pipelines']}{endpoint}") as response:
                    logger.info(f"   Discovery endpoint {endpoint}: HTTP {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        found_pipelines.append(f"{endpoint}: {data}")
                    elif response.status == 403:
                        found_pipelines.append(f"{endpoint}: Access restricted (pipelines exist)")
            except Exception as e:
                logger.info(f"   Discovery endpoint {endpoint} error: {str(e)}")
        
        if found_pipelines:
            results.append(f"✅ Pipeline discovery: {'; '.join(found_pipelines[:2])}")  # Limit output
        else:
            results.append("⚠️ No accessible pipeline discovery endpoints")
        
        # Check memory pipeline specific functionality
        # Based on the error logs, the issue seems to be that the pipeline doesn't have
        # the expected memory_manager or _get_relevant_memories methods
        try:
            # Try to call the pipeline in a way that might trigger memory functionality
            # but with a short timeout
            memory_test_payload = {
                "action": "test_memory_integration",
                "user_id": self.test_user_id,
                "content": "test memory functionality"
            }
            
            async with self.session.post(
                f"{self.base_urls['pipelines']}/",
                json=memory_test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status in [200, 400, 405]:  # Any reasonable response
                    results.append(f"✅ Pipeline memory test responded: HTTP {response.status}")
                else:
                    results.append(f"⚠️ Pipeline memory test: HTTP {response.status}")
        except asyncio.TimeoutError:
            results.append("⚠️ Pipeline memory test timeout")
        except Exception as e:
            results.append(f"⚠️ Pipeline memory test error: {str(e)[:50]}")
        
        success = any("✅" in result for result in results)
        details = "; ".join(results)
        self.log_test_result("Pipeline Service Integration", success, details)
        return success

    async def test_memory_service_diagnostics(self):
        """Test 4: Diagnose the specific memory service issues"""
        self.log_test_start("Memory Service Diagnostics")
        
        results = []
        
        # Check if we can import and inspect the memory service
        try:
            import sys
            import os
            
            # Add the project root to the path
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            # Try to import the memory service
            from services.memory_service import get_memory_service, MemoryProviderType
            
            results.append("✅ Memory service module importable")
            
            # Check available provider types
            providers = [provider.value for provider in MemoryProviderType]
            results.append(f"✅ Available memory providers: {', '.join(providers)}")
            
            # Try to get a memory service instance (get_memory_service is not async)
            memory_service = get_memory_service()
            if memory_service:
                results.append("✅ Memory service instance created")
                
                # Check what type of provider is being used
                provider_type = getattr(memory_service, 'provider_type', 'unknown')
                results.append(f"✅ Active provider type: {provider_type}")
                
            else:
                results.append("❌ Failed to create memory service instance")
            
        except ImportError as e:
            results.append(f"❌ Memory service import failed: {str(e)}")
        except Exception as e:
            results.append(f"❌ Memory service diagnostic error: {str(e)}")
        
        # Check pipeline memory integration specifically
        try:
            # Import the Pipeline class (not EnhancedMemoryPipeline)
            from pipelines.enhanced_memory_pipeline import Pipeline
            
            results.append("✅ Enhanced memory pipeline importable")
            
            # Check if the pipeline has the expected memory methods
            pipeline_methods = dir(Pipeline)
            memory_methods = [method for method in pipeline_methods if 'memory' in method.lower()]
            
            if memory_methods:
                results.append(f"✅ Pipeline memory methods: {', '.join(memory_methods[:3])}")
            else:
                results.append("⚠️ No memory methods found in pipeline")
                
        except ImportError as e:
            results.append(f"⚠️ Enhanced memory pipeline import failed: {str(e)}")
        except Exception as e:
            results.append(f"⚠️ Pipeline diagnostic error: {str(e)}")
        
        success = any("✅" in result for result in results)
        details = "; ".join(results)
        self.log_test_result("Memory Service Diagnostics", success, details)
        return success

    async def test_connection_troubleshooting(self):
        """Test 5: Troubleshoot the connection issues"""
        self.log_test_start("Connection Troubleshooting")
        
        results = []
        
        # Check Docker container status
        try:
            if sys.platform.startswith('win'):
                result = subprocess.run(
                    ["powershell", "-Command", "docker ps --format 'table {{.Names}}\\t{{.Status}}' --filter name=backend"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8'
                )
            else:
                result = subprocess.run(
                    ["docker", "ps", "--format", "table {{.Names}}\\t{{.Status}}", "--filter", "name=backend"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            if result.returncode == 0 and result.stdout:
                container_count = len([line for line in result.stdout.split('\n') if 'backend' in line])
                results.append(f"✅ Docker containers running: {container_count} backend containers")
                logger.info(f"   Container status:\n{result.stdout}")
            else:
                results.append("⚠️ Could not check Docker container status")
                
        except Exception as e:
            results.append(f"⚠️ Docker status check failed: {str(e)}")
        
        # Test network connectivity to each service
        services_to_test = [
            ("Memory API", self.base_urls['memory_api']),
            ("Pipeline Service", self.base_urls['pipelines']),
            ("Backend Service", self.base_urls['backend'])
        ]
        
        for service_name, base_url in services_to_test:
            try:
                # Use a very short timeout just to test connectivity
                quick_timeout = aiohttp.ClientTimeout(total=2, connect=1, sock_read=1)
                async with aiohttp.ClientSession(timeout=quick_timeout) as quick_session:
                    async with quick_session.get(f"{base_url}/") as response:
                        results.append(f"✅ {service_name} connectivity: HTTP {response.status}")
            except asyncio.TimeoutError:
                results.append(f"⚠️ {service_name} connectivity: Timeout")
            except Exception as e:
                results.append(f"❌ {service_name} connectivity: {str(e)[:30]}")
        
        # Check if there are any environment/configuration issues
        try:
            # Check if required environment variables or config files exist
            config_files = [
                "config/config.py",
                "config/persona_enhanced.json", 
                "docker-compose.yml"
            ]
            
            project_root = Path(__file__).parent.parent
            found_configs = []
            
            for config_file in config_files:
                config_path = project_root / config_file
                if config_path.exists():
                    found_configs.append(config_file)
            
            if found_configs:
                results.append(f"✅ Configuration files present: {len(found_configs)}/3")
            else:
                results.append("⚠️ Configuration files missing")
                
        except Exception as e:
            results.append(f"⚠️ Configuration check failed: {str(e)}")
        
        success = any("✅" in result for result in results)
        details = "; ".join(results)
        self.log_test_result("Connection Troubleshooting", success, details)
        return success

    async def run_validation_suite(self):
        """Run the complete memory service validation suite"""
        logger.info(f"\n{'='*80}")
        logger.info(f"[MEMORY SERVICE VALIDATION] Diagnosing and Testing Issues")
        logger.info(f"{'='*80}")
        logger.info(f"Started: {datetime.now()}")
        logger.info(f"User ID: {self.test_user_id}")
        logger.info(f"Conversation ID: {self.conversation_id}")
        logger.info(f"{'='*80}")
        
        tests = [
            ("Memory API Direct Access", self.test_memory_api_direct_access),
            ("Backend Service Health", self.test_backend_health_and_endpoints),
            ("Pipeline Service Integration", self.test_pipeline_service_integration),
            ("Memory Service Diagnostics", self.test_memory_service_diagnostics),
            ("Connection Troubleshooting", self.test_connection_troubleshooting)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n🔄 Running: {test_name}")
                result = await test_func()
                results.append(result)
                await asyncio.sleep(1)  # Brief pause
            except Exception as e:
                logger.error(f"❌ Test '{test_name}' failed: {str(e)}")
                results.append(False)
                self.test_results[test_name] = {'success': False, 'details': f"Exception: {str(e)}"}
        
        # Summary
        self.print_summary(results)
        return all(results)

    def print_summary(self, results):
        """Print test summary with recommendations"""
        logger.info(f"\n{'='*80}")
        logger.info(f"[VALIDATION SUMMARY] Memory Service Issue Analysis")
        logger.info(f"{'='*80}")
        
        passed = sum(results)
        total = len(results)
        
        logger.info(f"\n📊 RESULTS: {passed}/{total} tests passed")
        
        logger.info(f"\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            logger.info(f"   {status} | {test_name}")
            if result['details']:
                logger.info(f"      └─ {result['details'][:100]}{'...' if len(result['details']) > 100 else ''}")
        
        logger.info(f"\n🔧 ISSUE ANALYSIS:")
        logger.info("   Based on the warning messages you provided:")
        logger.info("   1. 'Pipeline memory retrieval method not available'")
        logger.info("      → Enhanced memory pipeline missing expected methods")
        logger.info("   2. 'All connection attempts failed'") 
        logger.info("      → Memory API client connection issues")
        logger.info("   3. 'Failed to save conversation'")
        logger.info("      → Pipeline memory storage integration broken")
        
        logger.info(f"\n💡 RECOMMENDATIONS:")
        if any("Memory API" in test and result['success'] for test, result in self.test_results.items()):
            logger.info("   ✅ Memory API is working - focus on pipeline integration")
        if any("Backend" in test and result['success'] for test, result in self.test_results.items()):
            logger.info("   ✅ Backend is healthy - focus on timeout optimization")
        if any("Pipeline" in test and result['success'] for test, result in self.test_results.items()):
            logger.info("   ✅ Pipeline service running - check memory method implementation")
        
        logger.info(f"\n{'='*80}")

async def main():
    """Main validation execution"""
    async with MemoryServiceValidationTest() as validator:
        success = await validator.run_validation_suite()
        return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
