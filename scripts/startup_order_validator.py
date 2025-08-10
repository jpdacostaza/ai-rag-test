#!/usr/bin/env python3
"""
Startup Order Validator
======================

Validates and monitors the correct startup order of services according to dependency hierarchy:

1. Redis (Foundation - Cache & Storage)
2. ChromaDB (Data Foundation - Vector Database) 
3. Ollama (AI Foundation - Language Models)
4. Backend (Core Services - Main API)
5. Memory API (Enhanced Memory System)
6. Pipelines (Advanced Functionality)
7. OpenWebUI (User Interface Layer)
8. Memory Installer (Setup/Configuration)
9. API Gateway (Monitoring Layer)
10. Watchtower (Maintenance Layer)
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configure logging
try:
    from core.unified_logging import setup_logging, get_logger
    setup_logging()
    logger = get_logger(__name__)
except ImportError:
    # Minimal fallback for standalone usage - no basicConfig to avoid conflicts
    logger = logging.getLogger(__name__)

class ServiceConfig:
    def __init__(self, name: str, url: str, health_endpoint: str, port: int, 
                 dependencies: List[str] = None, critical: bool = True,
                 startup_order: int = 0, max_startup_time: int = 60):
        self.name = name
        self.url = url
        self.health_endpoint = health_endpoint
        self.port = port
        self.dependencies = dependencies or []
        self.critical = critical
        self.startup_order = startup_order
        self.max_startup_time = max_startup_time
        self.startup_time = None
        self.healthy = False

# Service definitions in correct startup order
SERVICES = [
    ServiceConfig("redis", "http://localhost:6379", "/", 6379, [], True, 1, 30),
    ServiceConfig("chroma", "http://localhost:8000", "/api/v1/version", 8000, ["redis"], True, 2, 45),
    ServiceConfig("ollama", "http://localhost:11434", "/api/tags", 11434, ["redis", "chroma"], True, 3, 60),
    ServiceConfig("backend", "http://localhost:3000", "/health/simple", 3000, ["redis", "chroma", "ollama"], True, 4, 120),
    ServiceConfig("memory_api", "http://localhost:8001", "/health", 8001, ["redis", "chroma", "ollama", "backend"], True, 5, 90),
    ServiceConfig("pipelines", "http://localhost:9099", "/", 9099, ["redis", "chroma", "ollama", "backend", "memory_api"], True, 6, 75),
    ServiceConfig("openwebui", "http://localhost:8080", "/health", 8080, ["redis", "chroma", "ollama", "backend", "memory_api", "pipelines"], True, 7, 90),
    ServiceConfig("memory_installer", "http://localhost:0", "", 0, ["openwebui", "pipelines"], False, 8, 60),  # One-time container
    ServiceConfig("api_gateway", "http://localhost:8888", "/gateway/health", 8888, ["openwebui", "pipelines", "memory_api", "backend"], False, 9, 45),
    ServiceConfig("watchtower", "http://localhost:0", "", 0, ["openwebui", "pipelines"], False, 10, 30),  # No health endpoint
]

class StartupOrderValidator:
    def __init__(self):
        self.services = {svc.name: svc for svc in SERVICES}
        self.startup_log = []
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def check_service_health(self, service: ServiceConfig) -> bool:
        """Check if a service is healthy"""
        if not service.health_endpoint:
            return True  # Services without health endpoints are assumed healthy
        
        try:
            url = f"{service.url}{service.health_endpoint}"
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception as e:
            logger.debug(f"Health check failed for {service.name}: {e}")
            return False
    
    async def wait_for_service(self, service: ServiceConfig, timeout: int = None) -> bool:
        """Wait for a service to become healthy"""
        timeout = timeout or service.max_startup_time
        start_time = time.time()
        
        logger.info(f"[{service.startup_order}] Waiting for {service.name} (max {timeout}s)...")
        
        while time.time() - start_time < timeout:
            if await self.check_service_health(service):
                elapsed = time.time() - start_time
                service.startup_time = elapsed
                service.healthy = True
                logger.info(f"[{service.startup_order}] [OK] {service.name} healthy after {elapsed:.1f}s")
                return True
            
            await asyncio.sleep(1)
        
        elapsed = time.time() - start_time
        logger.warning(f"[{service.startup_order}] [FAIL] {service.name} timeout after {elapsed:.1f}s")
        return False
    
    async def validate_dependencies(self, service: ServiceConfig) -> bool:
        """Validate that all dependencies are healthy"""
        for dep_name in service.dependencies:
            dep_service = self.services.get(dep_name)
            if not dep_service:
                logger.error(f"Dependency {dep_name} not found for {service.name}")
                return False
            
            if not dep_service.healthy:
                logger.warning(f"Dependency {dep_name} not healthy for {service.name}")
                return False
        
        return True
    
    async def validate_startup_order(self) -> Dict:
        """Validate the entire startup order"""
        logger.info("====================================================================================================")
        logger.info("[STARTUP ORDER VALIDATION] Starting comprehensive startup order validation")
        logger.info("====================================================================================================")
        
        results = {
            "validation_start": datetime.now().isoformat(),
            "services": {},
            "order_violations": [],
            "dependency_failures": [],
            "critical_failures": [],
            "total_startup_time": 0,
            "success": False
        }
        
        overall_start = time.time()
        
        # Sort services by startup order
        ordered_services = sorted(SERVICES, key=lambda x: x.startup_order)
        
        for service in ordered_services:
            service_start = time.time()
            
            # Skip non-critical services that don't have health endpoints
            if not service.critical and not service.health_endpoint:
                logger.info(f"[{service.startup_order}]   Skipping {service.name} (no health endpoint)")
                results["services"][service.name] = {
                    "status": "skipped",
                    "startup_time": 0,
                    "healthy": True,
                    "dependencies_met": True
                }
                continue
            
            # Check dependencies
            deps_met = await self.validate_dependencies(service)
            if not deps_met:
                results["dependency_failures"].append(service.name)
                if service.critical:
                    results["critical_failures"].append(service.name)
                
                results["services"][service.name] = {
                    "status": "dependency_failure",
                    "startup_time": 0,
                    "healthy": False,
                    "dependencies_met": False
                }
                continue
            
            # Wait for service to become healthy
            healthy = await self.wait_for_service(service)
            
            results["services"][service.name] = {
                "status": "healthy" if healthy else "timeout",
                "startup_time": service.startup_time or 0,
                "healthy": healthy,
                "dependencies_met": deps_met,
                "startup_order": service.startup_order
            }
            
            if not healthy and service.critical:
                results["critical_failures"].append(service.name)
        
        results["total_startup_time"] = time.time() - overall_start
        results["validation_end"] = datetime.now().isoformat()
        
        # Determine overall success
        results["success"] = len(results["critical_failures"]) == 0
        
        return results
    
    def generate_startup_report(self, results: Dict):
        """Generate a comprehensive startup report"""
        logger.info("====================================================================================================")
        logger.info("[STARTUP ORDER REPORT] Validation Results")
        logger.info("====================================================================================================")
        
        # Overall status
        status = "SUCCESS" if results["success"] else "FAILURE"
        logger.info(f"Overall Status: {status}")
        logger.info(f"Total Validation Time: {results['total_startup_time']:.1f}s")
        logger.info(f"Critical Failures: {len(results['critical_failures'])}")
        logger.info(f"Dependency Failures: {len(results['dependency_failures'])}")
        logger.info("")
        
        # Service details
        logger.info("SERVICE STARTUP DETAILS:")
        for service_name, service_data in results["services"].items():
            status_icon = "[OK]" if service_data["healthy"] else "[FAIL]" if service_data["status"] != "skipped" else ""
            startup_time = service_data["startup_time"]
            order = service_data.get("startup_order", 0)
            
            logger.info(f"   [{order:2d}] {status_icon} {service_name:<15} {startup_time:6.1f}s   {service_data['status']}")
        
        logger.info("")
        
        # Failures
        if results["critical_failures"]:
            logger.error("CRITICAL FAILURES:")
            for failure in results["critical_failures"]:
                logger.error(f"   [FAIL] {failure}")
            logger.info("")
        
        if results["dependency_failures"]:
            logger.warning("DEPENDENCY FAILURES:")
            for failure in results["dependency_failures"]:
                logger.warning(f"   [WARN]  {failure}")
            logger.info("")
        
        # Recommendations
        logger.info("STARTUP ORDER ANALYSIS:")
        logger.info("   1. [OK] Redis (Foundation) - Should start first")
        logger.info("   2. [OK] ChromaDB (Data) - Depends on Redis")
        logger.info("   3. [OK] Ollama (AI) - Depends on Redis + ChromaDB")
        logger.info("   4. [OK] Backend (Core) - Depends on all foundation services")
        logger.info("   5. [OK] Memory API (Enhanced) - Depends on core services")
        logger.info("   6. [OK] Pipelines (Advanced) - Depends on enhanced services")
        logger.info("   7. [OK] OpenWebUI (UI) - Depends on all backend services")
        logger.info("   8. [OK] Installer (Setup) - Runs after UI is ready")
        logger.info("   9. [OK] API Gateway (Monitor) - Last core service")
        logger.info("  10. [OK] Watchtower (Maintenance) - Background monitoring")
        
        logger.info("====================================================================================================")
    
    async def quick_health_check(self) -> Dict:
        """Quick health check of all running services"""
        logger.info("[QUICK HEALTH CHECK] Checking all services...")
        
        results = {}
        tasks = []
        
        for service in SERVICES:
            if service.health_endpoint:
                task = asyncio.create_task(self.check_service_health(service))
                tasks.append((service.name, task))
        
        for name, task in tasks:
            try:
                healthy = await task
                results[name] = healthy
                status = "[OK]" if healthy else "[FAIL]"
                logger.info(f"   {status} {name}")
            except Exception as e:
                results[name] = False
                logger.error(f"   [FAIL] {name} - Error: {e}")
        
        return results

async def main():
    """Main validation function"""
    async with StartupOrderValidator() as validator:
        # Quick health check first
        logger.info("Starting startup order validation...")
        
        # Quick check
        health_results = await validator.quick_health_check()
        healthy_count = sum(1 for v in health_results.values() if v)
        total_count = len(health_results)
        
        logger.info(f"Quick health check: {healthy_count}/{total_count} services healthy")
        logger.info("")
        
        # Full validation
        results = await validator.validate_startup_order()
        
        # Generate report
        validator.generate_startup_report(results)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"startup_order_validation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Validation results saved to: {filename}")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())
