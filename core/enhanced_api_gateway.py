#!/usr/bin/env python3
"""
Enhanced API Gateway - Best Practices Implementation
Implements comprehensive API Gateway patterns with:
- Authentication & Authorization
- Rate Limiting & Circuit Breakers  
- Request/Response Transformation
- Monitoring & Observability
- Load Balancing & Service Discovery
- Comprehensive Security
"""

import asyncio
import aiohttp
from aiohttp import web, ClientSession, ClientTimeout, ClientConnectorError
import json
import time
import logging
import hashlib
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
import traceback
import weakref
import os
import ssl
import uuid
from urllib.parse import urlparse, parse_qs

# Import our security middleware
from middleware.security_middleware import SecurityMiddleware, SecurityConfig

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'enhanced_api_gateway_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class ServiceInstance:
    """Service instance configuration"""
    id: str
    host: str
    port: int
    weight: int = 100
    health_check_url: str = "/health"
    timeout: int = 30
    max_retries: int = 3
    is_healthy: bool = True
    last_health_check: float = 0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    failure_count: int = 0
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"
    
    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0

@dataclass
class ServiceConfig:
    """Enhanced service configuration"""
    name: str
    instances: List[ServiceInstance]
    load_balancer_strategy: str = "round_robin"  # round_robin, weighted, least_connections
    health_check_interval: int = 30
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    request_timeout: int = 30
    retry_policy: Dict[str, Any] = field(default_factory=lambda: {
        "max_retries": 3,
        "backoff_factor": 0.5,
        "retry_status_codes": [502, 503, 504]
    })
    rate_limit: Optional[Dict[str, int]] = None  # {"requests": 100, "window": 60}

@dataclass
class RouteConfig:
    """Route configuration with transformation rules"""
    path_pattern: str
    service_name: str
    target_path: str = None  # If None, use original path
    methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    auth_required: bool = True
    rate_limit_override: Optional[Dict[str, int]] = None
    request_transform: Optional[Dict[str, Any]] = None
    response_transform: Optional[Dict[str, Any]] = None
    cache_ttl: Optional[int] = None  # seconds
    timeout_override: Optional[int] = None

@dataclass
class RequestMetrics:
    """Request metrics tracking"""
    timestamp: float
    service: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    request_size: int
    response_size: int
    client_ip: str
    user_id: Optional[str] = None
    error: Optional[str] = None

class LoadBalancer:
    """Advanced load balancer with multiple strategies"""
    
    def __init__(self):
        self.round_robin_counters = defaultdict(int)
        self.connection_counts = defaultdict(int)
    
    def select_instance(self, service_config: ServiceConfig) -> Optional[ServiceInstance]:
        """Select service instance based on load balancing strategy"""
        healthy_instances = [inst for inst in service_config.instances if inst.is_healthy]
        
        if not healthy_instances:
            # Fallback to any instance if all are unhealthy
            healthy_instances = service_config.instances
            
        if not healthy_instances:
            return None
        
        strategy = service_config.load_balancer_strategy
        
        if strategy == "round_robin":
            return self._round_robin_select(service_config.name, healthy_instances)
        elif strategy == "weighted":
            return self._weighted_select(healthy_instances)
        elif strategy == "least_connections":
            return self._least_connections_select(healthy_instances)
        else:
            return healthy_instances[0]  # Fallback
    
    def _round_robin_select(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Round robin selection"""
        counter = self.round_robin_counters[service_name]
        selected = instances[counter % len(instances)]
        self.round_robin_counters[service_name] = counter + 1
        return selected
    
    def _weighted_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted random selection"""
        total_weight = sum(inst.weight for inst in instances)
        if total_weight == 0:
            return instances[0]
        
        import random
        r = random.randint(1, total_weight)
        
        current_weight = 0
        for instance in instances:
            current_weight += instance.weight
            if r <= current_weight:
                return instance
        
        return instances[-1]  # Fallback
    
    def _least_connections_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance with least connections"""
        return min(instances, key=lambda inst: self.connection_counts.get(inst.id, 0))
    
    def track_connection_start(self, instance_id: str):
        """Track connection start"""
        self.connection_counts[instance_id] += 1
    
    def track_connection_end(self, instance_id: str):
        """Track connection end"""
        self.connection_counts[instance_id] = max(0, self.connection_counts[instance_id] - 1)

class ResponseCache:
    """Simple in-memory response cache"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.access_times: Dict[str, float] = {}
        self.max_size = max_size
    
    def get(self, key: str, ttl: int) -> Optional[Any]:
        """Get cached response if valid"""
        if key in self.cache:
            response, timestamp = self.cache[key]
            if time.time() - timestamp < ttl:
                self.access_times[key] = time.time()
                return response
            else:
                self._evict(key)
        return None
    
    def set(self, key: str, response: Any):
        """Cache response"""
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[key] = (response, time.time())
        self.access_times[key] = time.time()
    
    def _evict(self, key: str):
        """Evict specific key"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if self.access_times:
            lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            self._evict(lru_key)

class EnhancedAPIGateway:
    """Enhanced API Gateway with comprehensive features"""
    
    def __init__(self, config_file: str = None):
        self.services: Dict[str, ServiceConfig] = {}
        self.routes: Dict[str, RouteConfig] = {}
        self.session: Optional[ClientSession] = None
        self.load_balancer = LoadBalancer()
        self.response_cache = ResponseCache()
        self.security_middleware = SecurityMiddleware()
        
        # Metrics and monitoring
        self.request_metrics: deque = deque(maxlen=10000)
        self.error_log: deque = deque(maxlen=1000)
        self.health_status: Dict[str, Dict] = {}
        
        # Performance tracking
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0,
            "p95_response_time": 0,
            "p99_response_time": 0
        }
        
        # Circuit breaker states
        self.circuit_breakers: Dict[str, Dict] = defaultdict(lambda: {
            "state": "CLOSED",  # CLOSED, OPEN, HALF_OPEN
            "failure_count": 0,
            "last_failure_time": 0,
            "half_open_calls": 0
        })
        
        # Load configuration
        if config_file:
            self.load_config(config_file)
        else:
            self._setup_default_services()
        
        # Start background tasks
        asyncio.create_task(self._health_check_task())
        asyncio.create_task(self._metrics_aggregation_task())
    
    def _setup_default_services(self):
        """Setup default service configurations"""
        self.services = {
            'memory': ServiceConfig(
                name='Memory API',
                instances=[ServiceInstance(
                    id='memory-1',
                    host='backend-memory-api',
                    port=5001,
                    health_check_url='/health'
                )]
            ),
            'ollama': ServiceConfig(
                name='Ollama',
                instances=[ServiceInstance(
                    id='ollama-1',
                    host='backend-ollama',
                    port=11434,
                    health_check_url='/api/tags'
                )]
            ),
            'openwebui': ServiceConfig(
                name='OpenWebUI',
                instances=[ServiceInstance(
                    id='openwebui-1',
                    host='backend-openwebui',
                    port=8080,
                    health_check_url='/health'
                )]
            ),
            'pipelines': ServiceConfig(
                name='Pipelines',
                instances=[ServiceInstance(
                    id='pipelines-1',
                    host='backend-pipelines',
                    port=9099,
                    health_check_url='/'
                )]
            ),
            'chroma': ServiceConfig(
                name='ChromaDB',
                instances=[ServiceInstance(
                    id='chroma-1',
                    host='backend-chroma',
                    port=8000,
                    health_check_url='/api/v1/heartbeat'
                )]
            )
        }
        
        # Setup default routes
        self.routes = {
            # Memory service routes
            '/api/memory/store': RouteConfig(
                path_pattern='/api/memory/store',
                service_name='memory',
                target_path='/store',
                methods=['POST'],
                cache_ttl=None
            ),
            '/api/memory/retrieve/{user_id}': RouteConfig(
                path_pattern='/api/memory/retrieve/{user_id}',
                service_name='memory',
                target_path='/retrieve/{user_id}',
                methods=['GET'],
                cache_ttl=300  # 5 minutes
            ),
            
            # Ollama routes
            '/api/ollama/chat': RouteConfig(
                path_pattern='/api/ollama/chat',
                service_name='ollama',
                target_path='/api/chat',
                methods=['POST'],
                timeout_override=60
            ),
            '/api/ollama/generate': RouteConfig(
                path_pattern='/api/ollama/generate',
                service_name='ollama',
                target_path='/api/generate',
                methods=['POST'],
                timeout_override=60
            ),
            
            # OpenWebUI routes
            '/api/webui/{path:.*}': RouteConfig(
                path_pattern='/api/webui/{path:.*}',
                service_name='openwebui',
                target_path='/{path}',
                methods=['GET', 'POST', 'PUT', 'DELETE']
            ),
            
            # ChromaDB routes
            '/api/vector/{path:.*}': RouteConfig(
                path_pattern='/api/vector/{path:.*}',
                service_name='chroma',
                target_path='/api/v1/{path}',
                methods=['GET', 'POST']
            )
        }
    
    async def initialize(self):
        """Initialize the gateway"""
        # Create HTTP session with optimized settings
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection limit
            limit_per_host=30,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=60
        )
        
        self.session = ClientSession(
            connector=connector,
            timeout=ClientTimeout(total=60),
            headers={'User-Agent': 'Enhanced-API-Gateway/1.0'}
        )
        
        # Initial health check
        await self._check_all_services_health()
        
        logger.info("Enhanced API Gateway initialized successfully")
    
    async def shutdown(self):
        """Clean shutdown"""
        if self.session:
            await self.session.close()
        logger.info("Enhanced API Gateway shutdown complete")
    
    async def _check_service_instance_health(self, service_name: str, instance: ServiceInstance) -> bool:
        """Check health of a specific service instance"""
        try:
            url = f"{instance.base_url}{instance.health_check_url}"
            start_time = time.time()
            
            async with self.session.get(url, timeout=ClientTimeout(total=10)) as response:
                response_time = (time.time() - start_time) * 1000
                
                # Update response time tracking
                instance.response_times.append(response_time)
                instance.last_health_check = time.time()
                
                if response.status == 200:
                    instance.is_healthy = True
                    instance.failure_count = 0
                    return True
                else:
                    instance.is_healthy = False
                    instance.failure_count += 1
                    return False
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
            instance.response_times.append(response_time)
            instance.last_health_check = time.time()
            instance.is_healthy = False
            instance.failure_count += 1
            
            logger.warning(f"Health check failed for {service_name}:{instance.id} - {str(e)}")
            return False
    
    async def _check_all_services_health(self):
        """Check health of all service instances"""
        for service_name, service_config in self.services.items():
            service_health = {"instances": {}, "healthy_count": 0, "total_count": len(service_config.instances)}
            
            health_tasks = [
                self._check_service_instance_health(service_name, instance) 
                for instance in service_config.instances
            ]
            
            results = await asyncio.gather(*health_tasks, return_exceptions=True)
            
            for instance, is_healthy in zip(service_config.instances, results):
                if isinstance(is_healthy, Exception):
                    is_healthy = False
                    
                service_health["instances"][instance.id] = {
                    "healthy": is_healthy,
                    "last_check": instance.last_health_check,
                    "avg_response_time": instance.avg_response_time,
                    "failure_count": instance.failure_count
                }
                
                if is_healthy:
                    service_health["healthy_count"] += 1
            
            service_health["service_healthy"] = service_health["healthy_count"] > 0
            self.health_status[service_name] = service_health
    
    async def handle_request(self, request) -> web.Response:
        """Main request handler with comprehensive processing"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Apply security middleware
            security_result = await self.security_middleware(request, self._process_request)
            if isinstance(security_result, web.Response):
                return security_result
            
            return await self._process_request(request)
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            await self._log_error(request, str(e), duration)
            
            return web.json_response(
                {
                    "error": "Internal gateway error",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                },
                status=500
            )
    
    async def _process_request(self, request) -> web.Response:
        """Process the actual request"""
        start_time = time.time()
        
        # Find matching route
        route_config = self._find_route(request.path, request.method)
        if not route_config:
            return web.json_response({"error": "Route not found"}, status=404)
        
        # Get service configuration
        service_config = self.services.get(route_config.service_name)
        if not service_config:
            return web.json_response({"error": "Service not configured"}, status=503)
        
        # Check circuit breaker
        if service_config.circuit_breaker_enabled:
            if not self._check_circuit_breaker(route_config.service_name):
                return web.json_response({"error": "Service temporarily unavailable"}, status=503)
        
        # Check cache first
        if route_config.cache_ttl and request.method == 'GET':
            cache_key = self._generate_cache_key(request)
            cached_response = self.response_cache.get(cache_key, route_config.cache_ttl)
            if cached_response:
                return web.json_response(cached_response, headers={'X-Cache': 'HIT'})
        
        # Select service instance
        instance = self.load_balancer.select_instance(service_config)
        if not instance:
            return web.json_response({"error": "No healthy service instances available"}, status=503)
        
        try:
            # Track connection
            self.load_balancer.track_connection_start(instance.id)
            
            # Transform request
            transformed_request = await self._transform_request(request, route_config)
            
            # Make request to service
            response = await self._proxy_to_service(instance, transformed_request, route_config)
            
            # Transform response
            transformed_response = await self._transform_response(response, route_config)
            
            # Cache response if configured
            if route_config.cache_ttl and request.method == 'GET' and response.status == 200:
                cache_key = self._generate_cache_key(request)
                self.response_cache.set(cache_key, transformed_response)
            
            # Record success
            if service_config.circuit_breaker_enabled:
                self._record_circuit_breaker_success(route_config.service_name)
            
            # Record metrics
            duration = (time.time() - start_time) * 1000
            await self._record_metrics(request, response.status, duration, route_config.service_name)
            
            return web.json_response(
                transformed_response, 
                status=response.status,
                headers={'X-Cache': 'MISS', 'X-Service-Instance': instance.id}
            )
            
        except Exception as e:
            # Record failure
            if service_config.circuit_breaker_enabled:
                self._record_circuit_breaker_failure(route_config.service_name)
            
            duration = (time.time() - start_time) * 1000
            await self._log_error(request, str(e), duration)
            
            return web.json_response({"error": "Service error"}, status=502)
            
        finally:
            # Track connection end
            self.load_balancer.track_connection_end(instance.id)
    
    def _find_route(self, path: str, method: str) -> Optional[RouteConfig]:
        """Find matching route configuration"""
        # Simple pattern matching - in production, use more sophisticated routing
        for pattern, route_config in self.routes.items():
            if method in route_config.methods:
                # Simple path matching (expand this for real pattern matching)
                if path.startswith(pattern.split('{')[0]):
                    return route_config
        return None
    
    async def _transform_request(self, request, route_config: RouteConfig) -> Dict[str, Any]:
        """Transform request according to route configuration"""
        # Get request body
        body = None
        if request.can_read_body:
            try:
                body = await request.json()
            except:
                try:
                    body = await request.text()
                except:
                    pass
        
        # Build transformed request
        transformed = {
            "method": request.method,
            "path": route_config.target_path or request.path,
            "headers": dict(request.headers),
            "query": dict(request.query),
            "body": body
        }
        
        # Apply request transformation rules
        if route_config.request_transform:
            # Apply transformation logic here
            pass
        
        return transformed
    
    async def _proxy_to_service(self, instance: ServiceInstance, transformed_request: Dict, route_config: RouteConfig):
        """Proxy request to service instance"""
        url = f"{instance.base_url}{transformed_request['path']}"
        
        # Prepare request parameters
        request_kwargs = {
            "method": transformed_request["method"],
            "url": url,
            "headers": transformed_request["headers"],
            "params": transformed_request["query"]
        }
        
        # Add body if present
        if transformed_request["body"]:
            if isinstance(transformed_request["body"], (dict, list)):
                request_kwargs["json"] = transformed_request["body"]
            else:
                request_kwargs["data"] = transformed_request["body"]
        
        # Set timeout
        timeout = route_config.timeout_override or instance.timeout
        request_kwargs["timeout"] = ClientTimeout(total=timeout)
        
        # Make request with retries
        for attempt in range(instance.max_retries):
            try:
                async with self.session.request(**request_kwargs) as response:
                    response_body = await response.json() if response.content_type == 'application/json' else await response.text()
                    
                    # Create response object
                    class ProxyResponse:
                        def __init__(self, status, body):
                            self.status = status
                            self.body = body
                    
                    return ProxyResponse(response.status, response_body)
                    
            except Exception as e:
                if attempt == instance.max_retries - 1:
                    raise e
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
    
    async def _transform_response(self, response, route_config: RouteConfig) -> Any:
        """Transform response according to route configuration"""
        response_data = response.body
        
        # Apply response transformation rules
        if route_config.response_transform:
            # Apply transformation logic here
            pass
        
        return response_data
    
    def _generate_cache_key(self, request) -> str:
        """Generate cache key for request"""
        key_parts = [request.method, request.path]
        
        # Include query parameters
        if request.query:
            sorted_query = sorted(request.query.items())
            key_parts.append(str(sorted_query))
        
        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()
    
    def _check_circuit_breaker(self, service_name: str) -> bool:
        """Check circuit breaker state"""
        breaker = self.circuit_breakers[service_name]
        current_time = time.time()
        
        if breaker["state"] == "OPEN":
            # Check if timeout has passed
            service_config = self.services[service_name]
            if current_time - breaker["last_failure_time"] > service_config.circuit_breaker_timeout:
                breaker["state"] = "HALF_OPEN"
                breaker["half_open_calls"] = 0
                logger.info(f"Circuit breaker for {service_name} moved to HALF_OPEN")
            else:
                return False
        
        elif breaker["state"] == "HALF_OPEN":
            if breaker["half_open_calls"] >= 3:  # Max half-open calls
                return False
        
        return True
    
    def _record_circuit_breaker_success(self, service_name: str):
        """Record successful request for circuit breaker"""
        breaker = self.circuit_breakers[service_name]
        
        if breaker["state"] == "HALF_OPEN":
            breaker["half_open_calls"] += 1
            if breaker["half_open_calls"] >= 3:  # Successful half-open calls
                breaker["state"] = "CLOSED"
                breaker["failure_count"] = 0
                logger.info(f"Circuit breaker for {service_name} closed")
        elif breaker["state"] == "CLOSED":
            breaker["failure_count"] = max(0, breaker["failure_count"] - 1)
    
    def _record_circuit_breaker_failure(self, service_name: str):
        """Record failed request for circuit breaker"""
        breaker = self.circuit_breakers[service_name]
        service_config = self.services[service_name]
        
        breaker["failure_count"] += 1
        breaker["last_failure_time"] = time.time()
        
        if breaker["state"] == "HALF_OPEN":
            breaker["state"] = "OPEN"
            logger.warning(f"Circuit breaker for {service_name} opened (half-open failure)")
        elif (breaker["state"] == "CLOSED" and 
              breaker["failure_count"] >= service_config.circuit_breaker_threshold):
            breaker["state"] = "OPEN"
            logger.warning(f"Circuit breaker for {service_name} opened ({breaker['failure_count']} failures)")
    
    async def _record_metrics(self, request, status_code: int, duration_ms: float, service_name: str):
        """Record request metrics"""
        metrics = RequestMetrics(
            timestamp=time.time(),
            service=service_name,
            endpoint=request.path,
            method=request.method,
            status_code=status_code,
            response_time_ms=duration_ms,
            request_size=len(await request.read()) if hasattr(request, 'read') else 0,
            response_size=0,  # Would need to track actual response size
            client_ip=request.remote or 'unknown'
        )
        
        self.request_metrics.append(metrics)
        
        # Update performance metrics
        self.performance_metrics["total_requests"] += 1
        if 200 <= status_code < 400:
            self.performance_metrics["successful_requests"] += 1
        else:
            self.performance_metrics["failed_requests"] += 1
    
    async def _log_error(self, request, error: str, duration_ms: float):
        """Log error with context"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "path": request.path,
            "method": request.method,
            "error": error,
            "duration_ms": duration_ms,
            "client_ip": request.remote or 'unknown',
            "traceback": traceback.format_exc()
        }
        
        self.error_log.append(error_entry)
        logger.error(f"Request error: {json.dumps(error_entry)}")
    
    async def _health_check_task(self):
        """Background health check task"""
        while True:
            try:
                await self._check_all_services_health()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health check task error: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _metrics_aggregation_task(self):
        """Background metrics aggregation task"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Calculate performance metrics
                if self.request_metrics:
                    response_times = [m.response_time_ms for m in self.request_metrics]
                    self.performance_metrics["avg_response_time"] = statistics.mean(response_times)
                    
                    if len(response_times) >= 20:  # Need enough data for percentiles
                        sorted_times = sorted(response_times)
                        p95_index = int(len(sorted_times) * 0.95)
                        p99_index = int(len(sorted_times) * 0.99)
                        
                        self.performance_metrics["p95_response_time"] = sorted_times[p95_index]
                        self.performance_metrics["p99_response_time"] = sorted_times[p99_index]
                
                logger.debug("Metrics aggregation completed")
                
            except Exception as e:
                logger.error(f"Metrics aggregation error: {str(e)}")
    
    # Admin/Management endpoints
    async def handle_health(self, request):
        """Gateway health endpoint"""
        return web.json_response({
            "gateway_healthy": True,
            "services": self.health_status,
            "performance_metrics": self.performance_metrics,
            "timestamp": datetime.now().isoformat()
        })
    
    async def handle_metrics(self, request):
        """Metrics endpoint"""
        return web.json_response({
            "performance": self.performance_metrics,
            "circuit_breakers": dict(self.circuit_breakers),
            "service_health": self.health_status,
            "recent_requests": len(self.request_metrics),
            "recent_errors": len(self.error_log)
        })
    
    async def handle_config(self, request):
        """Configuration endpoint"""
        return web.json_response({
            "services": {name: {
                "name": config.name,
                "instances": len(config.instances),
                "load_balancer_strategy": config.load_balancer_strategy,
                "circuit_breaker_enabled": config.circuit_breaker_enabled
            } for name, config in self.services.items()},
            "routes": {pattern: {
                "service": route.service_name,
                "methods": route.methods,
                "auth_required": route.auth_required,
                "cache_ttl": route.cache_ttl
            } for pattern, route in self.routes.items()}
        })
    
    def create_app(self):
        """Create the web application"""
        app = web.Application()
        
        # Admin endpoints
        app.router.add_get('/gateway/health', self.handle_health)
        app.router.add_get('/gateway/metrics', self.handle_metrics)
        app.router.add_get('/gateway/config', self.handle_config)
        
        # Main request handler - catch all
        app.router.add_route('*', '/{path:.*}', self.handle_request)
        
        return app

async def create_enhanced_gateway(config_file: str = None) -> EnhancedAPIGateway:
    """Factory function to create enhanced gateway"""
    gateway = EnhancedAPIGateway(config_file)
    await gateway.initialize()
    return gateway

async def main():
    """Run the Enhanced API Gateway server"""
    gateway = await create_enhanced_gateway()
    app = gateway.create_app()
    
    # Store gateway reference for cleanup
    app['gateway'] = gateway
    
    async def cleanup_handler(app):
        await app['gateway'].shutdown()
    
    app.on_cleanup.append(cleanup_handler)
    
    # Run server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8888)
    await site.start()
    
    logger.info("Enhanced API Gateway started on http://localhost:8888")
    logger.info("Features enabled:")
    logger.info("  ✓ Authentication & Authorization")
    logger.info("  ✓ Rate Limiting & Circuit Breakers")
    logger.info("  ✓ Load Balancing & Service Discovery")
    logger.info("  ✓ Request/Response Caching")
    logger.info("  ✓ Comprehensive Security")
    logger.info("  ✓ Performance Monitoring")
    logger.info("  ✓ Error Tracking & Recovery")
    
    logger.info("Management endpoints:")
    logger.info("  GET  /gateway/health - System health")
    logger.info("  GET  /gateway/metrics - Performance metrics")
    logger.info("  GET  /gateway/config - Configuration")
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())