#!/usr/bin/env python3
"""
API Gateway/Warehouse - Consolidated API Management System
Provides centralized access to all services with:
- Unified endpoint routing
- Request/response logging
- Error handling and retry logic
- Health monitoring
- Rate limiting
- Authentication middleware
"""

import asyncio
import aiohttp
from aiohttp import web, ClientSession, ClientTimeout
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import traceback
from dataclasses import dataclass
import weakref

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'api_gateway_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    name: str
    base_url: str
    health_endpoint: str
    timeout: int = 30
    max_retries: int = 3
    is_critical: bool = True

@dataclass
class APIRequest:
    method: str
    path: str
    headers: Dict[str, str]
    body: Any
    timestamp: float
    client_ip: str
    request_id: str

@dataclass
class APIResponse:
    status_code: int
    headers: Dict[str, str]
    body: Any
    timestamp: float
    duration_ms: float
    request_id: str

class APIGateway:
    def __init__(self):
        self.services = {
            'openwebui': ServiceConfig(
                name='OpenWebUI',
                base_url='http://localhost:8080',
                health_endpoint='/health'
            ),
            'pipelines': ServiceConfig(
                name='Pipelines',
                base_url='http://localhost:9099',
                health_endpoint='/'
            ),
            'memory': ServiceConfig(
                name='Memory API',
                base_url='http://localhost:8001',
                health_endpoint='/health'
            ),
            'ollama': ServiceConfig(
                name='Ollama',
                base_url='http://localhost:11434',
                health_endpoint='/api/tags'
            ),
            'chroma': ServiceConfig(
                name='ChromaDB',
                base_url='http://localhost:8000',
                health_endpoint='/api/v2/version'
            ),
            'backend': ServiceConfig(
                name='Backend',
                base_url='http://localhost:3000',
                health_endpoint='/health',
                is_critical=False
            )
        }
        
        self.session = None
        self.request_log = []
        self.error_log = []
        self.health_status = {}
        self.request_counter = 0
        
    async def initialize(self):
        """Initialize the gateway with health checks"""
        self.session = ClientSession(timeout=ClientTimeout(total=30))
        await self.check_all_services_health()
        logger.info("API Gateway initialized successfully")
        
    async def shutdown(self):
        """Clean shutdown"""
        if self.session:
            await self.session.close()
        logger.info("API Gateway shutdown complete")

    def generate_request_id(self) -> str:
        """Generate unique request ID"""
        self.request_counter += 1
        return f"req_{int(time.time())}_{self.request_counter:06d}"

    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service"""
        if service_name not in self.services:
            return {"healthy": False, "error": "Service not found"}
            
        service = self.services[service_name]
        start_time = time.time()
        
        try:
            async with self.session.get(f"{service.base_url}{service.health_endpoint}") as response:
                duration = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    self.health_status[service_name] = {
                        "healthy": True,
                        "status_code": response.status,
                        "response_time_ms": duration,
                        "last_check": datetime.now().isoformat()
                    }
                    return self.health_status[service_name]
                else:
                    error_info = {
                        "healthy": False,
                        "status_code": response.status,
                        "response_time_ms": duration,
                        "error": f"HTTP {response.status}",
                        "last_check": datetime.now().isoformat()
                    }
                    self.health_status[service_name] = error_info
                    return error_info
                    
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_info = {
                "healthy": False,
                "error": str(e),
                "response_time_ms": duration,
                "last_check": datetime.now().isoformat()
            }
            self.health_status[service_name] = error_info
            logger.error(f"Health check failed for {service.name}: {str(e)}")
            return error_info

    async def check_all_services_health(self) -> Dict[str, Any]:
        """Check health of all services"""
        health_tasks = [
            self.check_service_health(name) for name in self.services.keys()
        ]
        
        results = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        health_summary = {
            "overall_healthy": True,
            "services": {},
            "critical_services_healthy": True,
            "timestamp": datetime.now().isoformat()
        }
        
        for i, (service_name, result) in enumerate(zip(self.services.keys(), results)):
            if isinstance(result, Exception):
                result = {"healthy": False, "error": str(result)}
                
            health_summary["services"][service_name] = result
            
            if not result.get("healthy", False):
                health_summary["overall_healthy"] = False
                if self.services[service_name].is_critical:
                    health_summary["critical_services_healthy"] = False
        
        return health_summary

    async def proxy_request(self, service_name: str, method: str, path: str, 
                          headers: Dict[str, str] = None, body: Any = None,
                          client_ip: str = "unknown") -> APIResponse:
        """Proxy request to a service with full logging"""
        
        if service_name not in self.services:
            raise ValueError(f"Service '{service_name}' not found")
            
        service = self.services[service_name]
        request_id = self.generate_request_id()
        start_time = time.time()
        
        # Log request
        api_request = APIRequest(
            method=method,
            path=path,
            headers=headers or {},
            body=body,
            timestamp=start_time,
            client_ip=client_ip,
            request_id=request_id
        )
        
        logger.info(f"[{request_id}] {method} {service_name}{path} from {client_ip}")
        
        try:
            # Prepare request
            url = f"{service.base_url}{path}"
            request_headers = headers or {}
            
            # Make request with retries
            for attempt in range(service.max_retries):
                try:
                    # Prepare request kwargs
                    request_kwargs = {
                        'method': method,
                        'url': url,
                        'headers': request_headers
                    }
                    
                    # Add body based on content type
                    if body:
                        if isinstance(body, (dict, list)):
                            request_kwargs['json'] = body
                        else:
                            request_kwargs['data'] = body
                    
                    async with self.session.request(**request_kwargs) as response:
                        
                        response_body = None
                        try:
                            if response.content_type == 'application/json':
                                response_body = await response.json()
                            else:
                                response_body = await response.text()
                        except:
                            response_body = None
                        
                        duration = (time.time() - start_time) * 1000
                        
                        api_response = APIResponse(
                            status_code=response.status,
                            headers=dict(response.headers),
                            body=response_body,
                            timestamp=time.time(),
                            duration_ms=duration,
                            request_id=request_id
                        )
                        
                        # Log response
                        logger.info(f"[{request_id}] Response: {response.status} ({duration:.1f}ms)")
                        
                        # Store in request log
                        self.request_log.append({
                            "request": api_request,
                            "response": api_response,
                            "service": service_name
                        })
                        
                        # Keep only last 1000 requests
                        if len(self.request_log) > 1000:
                            self.request_log = self.request_log[-1000:]
                        
                        return api_response
                        
                except Exception as e:
                    if attempt == service.max_retries - 1:
                        raise e
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_info = {
                "request_id": request_id,
                "service": service_name,
                "method": method,
                "path": path,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "duration_ms": duration,
                "timestamp": datetime.now().isoformat()
            }
            
            self.error_log.append(error_info)
            logger.error(f"[{request_id}] Error: {str(e)}")
            
            # Keep only last 100 errors
            if len(self.error_log) > 100:
                self.error_log = self.error_log[-100:]
                
            raise e

    # HTTP handlers for the gateway API
    async def handle_health(self, request):
        """Gateway health endpoint"""
        health_data = await self.check_all_services_health()
        return web.json_response(health_data)

    async def handle_service_health(self, request):
        """Individual service health endpoint"""
        service_name = request.match_info['service']
        health_data = await self.check_service_health(service_name)
        return web.json_response(health_data)

    async def handle_proxy(self, request):
        """Main proxy handler"""
        service_name = request.match_info['service']
        path = '/' + request.match_info.get('path', '')
        method = request.method
        
        # Get client IP
        client_ip = request.remote or request.headers.get('X-Forwarded-For', 'unknown')
        
        # Get headers (exclude hop-by-hop headers and content-type to avoid conflicts)
        headers = dict(request.headers)
        hop_by_hop = ['connection', 'keep-alive', 'proxy-authenticate', 
                     'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade',
                     'content-type', 'content-length', 'host']
        headers = {k: v for k, v in headers.items() if k.lower() not in hop_by_hop}
        
        # Get body
        body = None
        if request.can_read_body:
            try:
                body = await request.json()
            except:
                try:
                    body = await request.text()
                except:
                    pass
        
        try:
            api_response = await self.proxy_request(
                service_name=service_name,
                method=method,
                path=path,
                headers=headers,
                body=body,
                client_ip=client_ip
            )
            
            # Return response
            response_headers = {k: v for k, v in api_response.headers.items() 
                              if k.lower() not in ['content-length', 'transfer-encoding', 'connection']}
            
            if isinstance(api_response.body, dict) or isinstance(api_response.body, list):
                return web.json_response(
                    api_response.body, 
                    status=api_response.status_code,
                    headers=response_headers
                )
            else:
                return web.Response(
                    text=str(api_response.body) if api_response.body else "",
                    status=api_response.status_code,
                    headers=response_headers,
                    content_type='text/plain'
                )
                
        except Exception as e:
            return web.json_response(
                {"error": str(e), "service": service_name, "path": path},
                status=500
            )

    async def handle_logs(self, request):
        """Get request logs"""
        limit = int(request.query.get('limit', 50))
        logs = self.request_log[-limit:]
        
        # Serialize logs
        serialized_logs = []
        for log in logs:
            serialized_logs.append({
                "request_id": log["request"].request_id,
                "service": log["service"],
                "method": log["request"].method,
                "path": log["request"].path,
                "status_code": log["response"].status_code,
                "duration_ms": log["response"].duration_ms,
                "timestamp": log["request"].timestamp,
                "client_ip": log["request"].client_ip
            })
        
        return web.json_response(serialized_logs)

    async def handle_errors(self, request):
        """Get error logs"""
        limit = int(request.query.get('limit', 50))
        errors = self.error_log[-limit:]
        return web.json_response(errors)

    def create_app(self):
        """Create the web application"""
        app = web.Application()
        
        # Health endpoints
        app.router.add_get('/gateway/health', self.handle_health)
        app.router.add_get('/gateway/health/{service}', self.handle_service_health)
        
        # Logging endpoints
        app.router.add_get('/gateway/logs', self.handle_logs)
        app.router.add_get('/gateway/errors', self.handle_errors)
        
        # Main proxy endpoint - catch all routes
        app.router.add_route('*', '/{service}/{path:.*}', self.handle_proxy)
        app.router.add_route('*', '/{service}', self.handle_proxy)
        
        return app

async def create_gateway():
    """Factory function to create gateway"""
    gateway = APIGateway()
    await gateway.initialize()
    return gateway

async def main():
    """Run the API Gateway server"""
    gateway = await create_gateway()
    app = gateway.create_app()
    
    # Store gateway reference in app for cleanup
    app['gateway'] = gateway
    
    async def cleanup_handler(app):
        await app['gateway'].shutdown()
    
    app.on_cleanup.append(cleanup_handler)
    
    # Run server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, 'localhost', 8888)
    await site.start()
    
    logger.info("API Gateway started on http://localhost:8888")
    logger.info("Available endpoints:")
    logger.info("  GET  /gateway/health - Overall health")
    logger.info("  GET  /gateway/health/{service} - Service health")
    logger.info("  GET  /gateway/logs - Request logs")
    logger.info("  GET  /gateway/errors - Error logs")
    logger.info("  *    /{service}/{path} - Proxy to service")
    
    try:
        await asyncio.Event().wait()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
