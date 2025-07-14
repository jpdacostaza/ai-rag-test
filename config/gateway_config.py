#!/usr/bin/env python3
"""
Enhanced API Gateway Configuration
Comprehensive configuration management for the API Gateway.
"""

import os
import json
import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path

@dataclass
class SecuritySettings:
    """Security configuration settings"""
    # JWT Settings
    jwt_secret: str = "your-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_seconds: int = 3600
    jwt_issuer: str = "api-gateway"
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst_limit: int = 10
    rate_limit_block_duration_seconds: int = 60
    
    # IP Filtering
    ip_filtering_enabled: bool = False
    blocked_ips: List[str] = field(default_factory=list)
    allowed_ips: List[str] = field(default_factory=list)  # Empty means all allowed
    
    # Security Headers
    enable_hsts: bool = True
    enable_csp: bool = True
    enable_xss_protection: bool = True
    enable_frame_options: bool = True
    
    # Input Validation
    max_request_body_size: int = 10 * 1024 * 1024  # 10MB
    max_header_size: int = 8192  # 8KB
    max_url_length: int = 2048
    
    # SSL/TLS
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    ssl_verify_peer: bool = True

@dataclass
class CircuitBreakerSettings:
    """Circuit breaker configuration"""
    enabled: bool = True
    failure_threshold: int = 5
    timeout_seconds: int = 60
    half_open_max_calls: int = 3
    failure_rate_threshold: float = 0.5  # 50% failure rate
    minimum_request_threshold: int = 10

@dataclass
class ServiceInstanceConfig:
    """Individual service instance configuration"""
    id: str
    host: str
    port: int
    weight: int = 100
    health_check_path: str = "/health"
    health_check_interval_seconds: int = 30
    timeout_seconds: int = 30
    max_retries: int = 3
    ssl_enabled: bool = False

@dataclass
class ServiceConfig:
    """Service configuration"""
    name: str
    instances: List[ServiceInstanceConfig]
    load_balancer_strategy: str = "round_robin"  # round_robin, weighted, least_connections, random
    circuit_breaker: CircuitBreakerSettings = field(default_factory=CircuitBreakerSettings)
    request_timeout_seconds: int = 30
    retry_policy: Dict[str, Any] = field(default_factory=lambda: {
        "max_retries": 3,
        "backoff_factor": 0.5,
        "retry_status_codes": [502, 503, 504, 408]
    })
    rate_limit: Optional[Dict[str, int]] = None  # Service-specific rate limits

@dataclass
class RouteConfig:
    """Route configuration"""
    path_pattern: str
    service_name: str
    target_path: Optional[str] = None
    methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH"])
    auth_required: bool = True
    auth_scopes: List[str] = field(default_factory=list)
    rate_limit_override: Optional[Dict[str, int]] = None
    cache_enabled: bool = False
    cache_ttl_seconds: Optional[int] = None
    timeout_override_seconds: Optional[int] = None
    request_size_limit: Optional[int] = None
    
    # Request/Response transformation
    request_transform: Optional[Dict[str, Any]] = None
    response_transform: Optional[Dict[str, Any]] = None
    
    # Headers
    add_headers: Dict[str, str] = field(default_factory=dict)
    remove_headers: List[str] = field(default_factory=list)

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    metrics_enabled: bool = True
    metrics_export_interval_seconds: int = 60
    metrics_retention_days: int = 7
    
    health_check_enabled: bool = True
    health_check_interval_seconds: int = 30
    
    logging_level: str = "INFO"
    log_requests: bool = True
    log_responses: bool = False  # Be careful with sensitive data
    log_request_body: bool = False
    log_response_body: bool = False
    
    # Distributed tracing
    tracing_enabled: bool = False
    tracing_endpoint: Optional[str] = None
    tracing_service_name: str = "api-gateway"

@dataclass
class CacheConfig:
    """Caching configuration"""
    enabled: bool = True
    provider: str = "memory"  # memory, redis
    default_ttl_seconds: int = 300  # 5 minutes
    max_cache_size: int = 1000
    
    # Redis cache settings (if provider is redis)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

@dataclass
class GatewayConfig:
    """Main gateway configuration"""
    # Basic settings
    host: str = "0.0.0.0"
    port: int = 8888
    workers: int = 1
    environment: str = "development"  # development, staging, production
    
    # Security
    security: SecuritySettings = field(default_factory=SecuritySettings)
    
    # Services and routing
    services: Dict[str, ServiceConfig] = field(default_factory=dict)
    routes: Dict[str, RouteConfig] = field(default_factory=dict)
    
    # Features
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    
    # External integrations
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_headers: List[str] = field(default_factory=lambda: ["*"])

class ConfigManager:
    """Configuration manager for the API Gateway"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config: GatewayConfig = GatewayConfig()
        
        # Load configuration
        if config_path and Path(config_path).exists():
            self.load_from_file(config_path)
        else:
            self._load_from_environment()
            self._setup_default_services()
    
    def load_from_file(self, config_path: str):
        """Load configuration from file (JSON or YAML)"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            if config_file.suffix.lower() in ['.yml', '.yaml']:
                config_data = yaml.safe_load(f)
            else:
                config_data = json.load(f)
        
        self._load_from_dict(config_data)
    
    def _load_from_dict(self, config_data: Dict[str, Any]):
        """Load configuration from dictionary"""
        # This is a simplified version - in production, use proper serialization
        if 'host' in config_data:
            self.config.host = config_data['host']
        if 'port' in config_data:
            self.config.port = config_data['port']
        if 'environment' in config_data:
            self.config.environment = config_data['environment']
        
        # Load security settings
        if 'security' in config_data:
            security_data = config_data['security']
            if 'jwt_secret' in security_data:
                self.config.security.jwt_secret = security_data['jwt_secret']
            if 'rate_limit_requests_per_minute' in security_data:
                self.config.security.rate_limit_requests_per_minute = security_data['rate_limit_requests_per_minute']
        
        # Load services
        if 'services' in config_data:
            self._load_services(config_data['services'])
        
        # Load routes
        if 'routes' in config_data:
            self._load_routes(config_data['routes'])
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        # Basic settings
        self.config.host = os.getenv('GATEWAY_HOST', '0.0.0.0')
        self.config.port = int(os.getenv('GATEWAY_PORT', '8888'))
        self.config.environment = os.getenv('ENVIRONMENT', 'development')
        
        # Security settings
        self.config.security.jwt_secret = os.getenv('JWT_SECRET', 'your-jwt-secret-change-in-production')
        self.config.security.rate_limit_requests_per_minute = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
        
        # SSL settings
        self.config.security.ssl_enabled = os.getenv('SSL_ENABLED', 'false').lower() == 'true'
        self.config.security.ssl_cert_path = os.getenv('SSL_CERT_PATH')
        self.config.security.ssl_key_path = os.getenv('SSL_KEY_PATH')
        
        # Cache settings
        self.config.cache.provider = os.getenv('CACHE_PROVIDER', 'memory')
        self.config.cache.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.config.cache.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        
        # Monitoring
        self.config.monitoring.logging_level = os.getenv('LOG_LEVEL', 'INFO')
        self.config.monitoring.tracing_enabled = os.getenv('TRACING_ENABLED', 'false').lower() == 'true'
        
        # CORS
        cors_origins = os.getenv('CORS_ORIGINS', '*')
        if cors_origins != '*':
            self.config.cors_origins = cors_origins.split(',')
    
    def _setup_default_services(self):
        """Setup default service configurations"""
        # Memory API Service
        memory_instance = ServiceInstanceConfig(
            id="memory-1",
            host=os.getenv('MEMORY_API_HOST', 'backend-memory-api'),
            port=int(os.getenv('MEMORY_API_PORT', '5001')),
            health_check_path='/health'
        )
        
        self.config.services['memory'] = ServiceConfig(
            name='Memory API',
            instances=[memory_instance],
            load_balancer_strategy='round_robin'
        )
        
        # Ollama Service
        ollama_instance = ServiceInstanceConfig(
            id="ollama-1",
            host=os.getenv('OLLAMA_HOST', 'backend-ollama'),
            port=int(os.getenv('OLLAMA_PORT', '11434')),
            health_check_path='/api/tags',
            timeout_seconds=60  # LLM requests can be slow
        )
        
        self.config.services['ollama'] = ServiceConfig(
            name='Ollama',
            instances=[ollama_instance],
            request_timeout_seconds=60
        )
        
        # OpenWebUI Service
        openwebui_instance = ServiceInstanceConfig(
            id="openwebui-1",
            host=os.getenv('OPENWEBUI_HOST', 'backend-openwebui'),
            port=int(os.getenv('OPENWEBUI_PORT', '8080')),
            health_check_path='/health'
        )
        
        self.config.services['openwebui'] = ServiceConfig(
            name='OpenWebUI',
            instances=[openwebui_instance]
        )
        
        # Pipelines Service
        pipelines_instance = ServiceInstanceConfig(
            id="pipelines-1",
            host=os.getenv('PIPELINES_HOST', 'backend-pipelines'),
            port=int(os.getenv('PIPELINES_PORT', '9099')),
            health_check_path='/'
        )
        
        self.config.services['pipelines'] = ServiceConfig(
            name='Pipelines',
            instances=[pipelines_instance]
        )
        
        # ChromaDB Service
        chroma_instance = ServiceInstanceConfig(
            id="chroma-1",
            host=os.getenv('CHROMA_HOST', 'backend-chroma'),
            port=int(os.getenv('CHROMA_PORT', '8000')),
            health_check_path='/api/v1/heartbeat'
        )
        
        self.config.services['chroma'] = ServiceConfig(
            name='ChromaDB',
            instances=[chroma_instance]
        )
        
        # Setup default routes
        self._setup_default_routes()
    
    def _setup_default_routes(self):
        """Setup default route configurations"""
        # Memory API routes
        self.config.routes['/api/memory/store'] = RouteConfig(
            path_pattern='/api/memory/store',
            service_name='memory',
            target_path='/store',
            methods=['POST'],
            cache_enabled=False
        )
        
        self.config.routes['/api/memory/retrieve/{user_id}'] = RouteConfig(
            path_pattern='/api/memory/retrieve/{user_id}',
            service_name='memory',
            target_path='/retrieve/{user_id}',
            methods=['GET'],
            cache_enabled=True,
            cache_ttl_seconds=300
        )
        
        # Ollama routes
        self.config.routes['/api/ollama/chat'] = RouteConfig(
            path_pattern='/api/ollama/chat',
            service_name='ollama',
            target_path='/api/chat',
            methods=['POST'],
            timeout_override_seconds=120,
            cache_enabled=False
        )
        
        self.config.routes['/api/ollama/generate'] = RouteConfig(
            path_pattern='/api/ollama/generate',
            service_name='ollama',
            target_path='/api/generate',
            methods=['POST'],
            timeout_override_seconds=120,
            cache_enabled=False
        )
        
        self.config.routes['/api/ollama/tags'] = RouteConfig(
            path_pattern='/api/ollama/tags',
            service_name='ollama',
            target_path='/api/tags',
            methods=['GET'],
            cache_enabled=True,
            cache_ttl_seconds=600  # Cache model list for 10 minutes
        )
        
        # OpenWebUI routes
        self.config.routes['/api/webui/{path:.*}'] = RouteConfig(
            path_pattern='/api/webui/{path:.*}',
            service_name='openwebui',
            target_path='/{path}',
            methods=['GET', 'POST', 'PUT', 'DELETE'],
            auth_required=True
        )
        
        # ChromaDB routes
        self.config.routes['/api/vector/{path:.*}'] = RouteConfig(
            path_pattern='/api/vector/{path:.*}',
            service_name='chroma',
            target_path='/api/v1/{path}',
            methods=['GET', 'POST'],
            cache_enabled=True,
            cache_ttl_seconds=300
        )
        
        # Health check routes (no auth required)
        self.config.routes['/health'] = RouteConfig(
            path_pattern='/health',
            service_name='gateway',
            auth_required=False
        )
        
        self.config.routes['/api/health/{service}'] = RouteConfig(
            path_pattern='/api/health/{service}',
            service_name='{service}',
            target_path='/health',
            methods=['GET'],
            auth_required=False,
            cache_enabled=True,
            cache_ttl_seconds=30
        )
    
    def _load_services(self, services_data: Dict[str, Any]):
        """Load services from configuration data"""
        for service_name, service_data in services_data.items():
            instances = []
            for instance_data in service_data.get('instances', []):
                instance = ServiceInstanceConfig(
                    id=instance_data['id'],
                    host=instance_data['host'],
                    port=instance_data['port'],
                    weight=instance_data.get('weight', 100),
                    health_check_path=instance_data.get('health_check_path', '/health'),
                    timeout_seconds=instance_data.get('timeout_seconds', 30)
                )
                instances.append(instance)
            
            circuit_breaker = CircuitBreakerSettings()
            if 'circuit_breaker' in service_data:
                cb_data = service_data['circuit_breaker']
                circuit_breaker.enabled = cb_data.get('enabled', True)
                circuit_breaker.failure_threshold = cb_data.get('failure_threshold', 5)
                circuit_breaker.timeout_seconds = cb_data.get('timeout_seconds', 60)
            
            service_config = ServiceConfig(
                name=service_data['name'],
                instances=instances,
                load_balancer_strategy=service_data.get('load_balancer_strategy', 'round_robin'),
                circuit_breaker=circuit_breaker,
                request_timeout_seconds=service_data.get('request_timeout_seconds', 30)
            )
            
            self.config.services[service_name] = service_config
    
    def _load_routes(self, routes_data: Dict[str, Any]):
        """Load routes from configuration data"""
        for path_pattern, route_data in routes_data.items():
            route_config = RouteConfig(
                path_pattern=path_pattern,
                service_name=route_data['service_name'],
                target_path=route_data.get('target_path'),
                methods=route_data.get('methods', ['GET', 'POST']),
                auth_required=route_data.get('auth_required', True),
                cache_enabled=route_data.get('cache_enabled', False),
                cache_ttl_seconds=route_data.get('cache_ttl_seconds'),
                timeout_override_seconds=route_data.get('timeout_override_seconds')
            )
            
            self.config.routes[path_pattern] = route_config
    
    def save_to_file(self, config_path: str, format: str = 'yaml'):
        """Save configuration to file"""
        config_dict = asdict(self.config)
        
        with open(config_path, 'w') as f:
            if format.lower() == 'yaml':
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_dict, f, indent=2)
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate basic settings
        if not self.config.host:
            issues.append("Host not configured")
        
        if not (1 <= self.config.port <= 65535):
            issues.append(f"Invalid port: {self.config.port}")
        
        # Validate security settings
        if self.config.environment == 'production':
            if self.config.security.jwt_secret == 'your-jwt-secret-change-in-production':
                issues.append("JWT secret must be changed in production")
            
            if not self.config.security.ssl_enabled:
                issues.append("SSL should be enabled in production")
        
        # Validate services
        for service_name, service_config in self.config.services.items():
            if not service_config.instances:
                issues.append(f"Service '{service_name}' has no instances configured")
            
            for instance in service_config.instances:
                if not instance.host:
                    issues.append(f"Instance '{instance.id}' has no host configured")
                
                if not (1 <= instance.port <= 65535):
                    issues.append(f"Instance '{instance.id}' has invalid port: {instance.port}")
        
        # Validate routes
        for path_pattern, route_config in self.config.routes.items():
            if route_config.service_name not in self.config.services and route_config.service_name != 'gateway':
                issues.append(f"Route '{path_pattern}' references unknown service: {route_config.service_name}")
        
        return issues
    
    def get_config(self) -> GatewayConfig:
        """Get the current configuration"""
        return self.config

def load_config(config_path: Optional[str] = None) -> GatewayConfig:
    """Load configuration from file or environment"""
    manager = ConfigManager(config_path)
    return manager.get_config()

# Example configuration file template
EXAMPLE_CONFIG = """
# API Gateway Configuration
host: "0.0.0.0"
port: 8888
environment: "production"

security:
  jwt_secret: "your-super-secret-jwt-key-here"
  rate_limit_enabled: true
  rate_limit_requests_per_minute: 100
  ssl_enabled: true
  ssl_cert_path: "/path/to/cert.pem"
  ssl_key_path: "/path/to/key.pem"

services:
  memory:
    name: "Memory API"
    instances:
      - id: "memory-1"
        host: "memory-api-1.internal"
        port: 5001
      - id: "memory-2"
        host: "memory-api-2.internal"
        port: 5001
    load_balancer_strategy: "round_robin"
    circuit_breaker:
      enabled: true
      failure_threshold: 5
      timeout_seconds: 60

routes:
  "/api/memory/store":
    service_name: "memory"
    target_path: "/store"
    methods: ["POST"]
    auth_required: true
    cache_enabled: false
  
  "/api/memory/retrieve/{user_id}":
    service_name: "memory"
    target_path: "/retrieve/{user_id}"
    methods: ["GET"]
    auth_required: true
    cache_enabled: true
    cache_ttl_seconds: 300

monitoring:
  metrics_enabled: true
  logging_level: "INFO"
  tracing_enabled: true

cache:
  enabled: true
  provider: "redis"
  redis_host: "redis.internal"
  redis_port: 6379
"""

if __name__ == "__main__":
    # Example usage
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Validate configuration
    issues = config_manager.validate_config()
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration is valid")
    
    # Save example configuration
    with open("gateway_config_example.yaml", "w") as f:
        f.write(EXAMPLE_CONFIG)
