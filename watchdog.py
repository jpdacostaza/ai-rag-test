"""
Watchdog service for monitoring subsystem health (Redis, ChromaDB, Ollama).
Provides continuous monitoring, health checks, and alerting for critical services.
"""

import asyncio
import logging
import time
import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
import redis.asyncio as redis
import chromadb
from chromadb.config import Settings
from dataclasses import dataclass, asdict
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceHealth:
    service: str
    status: HealthStatus
    last_check: datetime
    response_time_ms: float
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class WatchdogConfig:
    """Configuration for the watchdog system."""
    check_interval: int = 30  # seconds between health checks
    timeout: int = 5  # seconds
    startup_delay: int = 10  # seconds to wait before starting monitoring
    max_retries: int = 3
    alert_threshold: int = 3  # consecutive failures before alert
    enable_logging: bool = True
    log_level: str = "INFO"
    stable_mode_interval: int = 60  # Use longer intervals when all services are healthy
    
    def __post_init__(self):
        """Parse environment variables with error handling."""
        try:
            self.check_interval = int(os.getenv("WATCHDOG_CHECK_INTERVAL", "30"))
        except (ValueError, TypeError):
            self.check_interval = 30
            
        try:
            self.timeout = int(os.getenv("WATCHDOG_TIMEOUT", "5"))
        except (ValueError, TypeError):
            self.timeout = 5
            
        try:
            self.startup_delay = int(os.getenv("WATCHDOG_STARTUP_DELAY", "10"))
        except (ValueError, TypeError):
            self.startup_delay = 10
            
        try:
            self.max_retries = int(os.getenv("WATCHDOG_MAX_RETRIES", "3"))
        except (ValueError, TypeError):
            self.max_retries = 3
            
        try:
            self.alert_threshold = int(os.getenv("WATCHDOG_ALERT_THRESHOLD", "3"))
        except (ValueError, TypeError):
            self.alert_threshold = 3
            
        try:
            self.enable_logging = os.getenv("WATCHDOG_ENABLE_LOGGING", "true").lower() == "true"
        except (ValueError, TypeError):
            self.enable_logging = True
            
        try:
            self.log_level = os.getenv("WATCHDOG_LOG_LEVEL", "INFO").strip()
        except (ValueError, TypeError):
            self.log_level = "INFO"
            
        try:
            stable_interval_str = os.getenv("WATCHDOG_STABLE_INTERVAL", "60").strip()
            # Handle cases where the env var might be malformed
            stable_interval_str = stable_interval_str.split()[0] if stable_interval_str else "60"
            self.stable_mode_interval = int(stable_interval_str)
        except (ValueError, TypeError):
            self.stable_mode_interval = 60

class SubsystemMonitor:
    """Base class for monitoring individual subsystems."""
    
    def __init__(self, name: str, config: WatchdogConfig):
        self.name = name
        self.config = config
        self.consecutive_failures = 0
        self.last_success = None
        self.alert_sent = False
        
    async def check_health(self) -> ServiceHealth:
        """Check the health of this subsystem. To be implemented by subclasses."""
        raise NotImplementedError
    
    def _record_success(self):
        """Record a successful health check."""
        self.consecutive_failures = 0
        self.last_success = datetime.now()
        self.alert_sent = False
    
    def _record_failure(self):
        """Record a failed health check."""
        self.consecutive_failures += 1
    
    def should_alert(self) -> bool:
        """Check if we should send an alert."""
        return (self.consecutive_failures >= self.config.alert_threshold and 
                not self.alert_sent)

class RedisMonitor(SubsystemMonitor):
    """Monitor Redis connectivity and performance."""
    
    def __init__(self, config: WatchdogConfig):
        super().__init__("Redis", config)
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
    
    async def check_health(self) -> ServiceHealth:
        start_time = time.time()
        
        try:
            # Create async Redis client with timeout
            client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                socket_connect_timeout=self.config.timeout,
                socket_timeout=self.config.timeout,
                decode_responses=True
            )
            
            # Test basic operations asynchronously
            await client.ping()
            await client.set("watchdog:health_check", "ok", ex=60)
            result = await client.get("watchdog:health_check")
            await client.close() # Close the connection
            
            response_time = (time.time() - start_time) * 1000
            
            if result == "ok":
                self._record_success()
                
                # Simple metadata to avoid type issues
                metadata = {
                    "host": self.redis_host,
                    "port": self.redis_port,
                    "connection_status": "connected"
                }
                
                return ServiceHealth(
                    service=self.name,
                    status=HealthStatus.HEALTHY,
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    metadata=metadata
                )
            else:
                raise Exception("Health check key mismatch")
                
        except Exception as e:
            self._record_failure()
            response_time = (time.time() - start_time) * 1000
            
            return ServiceHealth(
                service=self.name,
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )

class ChromaDBMonitor(SubsystemMonitor):
    """Monitor ChromaDB connectivity and performance."""
    
    def __init__(self, config: WatchdogConfig):
        super().__init__("ChromaDB", config)
        self.chroma_dir = os.getenv("CHROMA_DB_DIR", "./storage/chroma")
        self.use_http_chroma = os.getenv("USE_HTTP_CHROMA", "false").lower() == "true"
        self.chroma_host = os.getenv("CHROMA_HOST", "localhost")
        self.chroma_port = int(os.getenv("CHROMA_PORT", 8000))
    
    async def check_health(self) -> ServiceHealth:
        start_time = time.time()
        
        try:
            # Create ChromaDB client based on configuration
            if self.use_http_chroma:
                # HTTP-based ChromaDB client (for Docker)
                try:
                    client = chromadb.HttpClient(
                        host=self.chroma_host,
                        port=self.chroma_port
                    )
                except AttributeError:
                    # Fallback for older versions
                    client = chromadb.Client(Settings(
                        chroma_api_impl="rest",
                        chroma_server_host=self.chroma_host,
                        chroma_server_http_port=self.chroma_port
                    ))
            else:
                # File-based ChromaDB client (for local development)
                client = chromadb.Client(Settings(
                    persist_directory=self.chroma_dir
                ))
            
            # Test basic operations
            collection_name = "watchdog_health_check"
            collection = await asyncio.to_thread(
                client.get_or_create_collection, 
                collection_name
            )
            
            # Test add and query operations
            test_id = f"health_check_{int(time.time())}"
            await asyncio.to_thread(
                collection.add,
                documents=["Health check document"],
                ids=[test_id],
                metadatas=[{"type": "health_check", "timestamp": time.time()}]
            )
            
            # Query to verify
            results = await asyncio.to_thread(
                collection.query,
                query_texts=["Health check"],
                n_results=1
            )
            
            # Clean up
            await asyncio.to_thread(collection.delete, ids=[test_id])
            
            response_time = (time.time() - start_time) * 1000
            
            if results and len(results.get("ids", [[]])[0]) > 0:
                self._record_success()
                
                # Get collection count
                try:
                    collections = await asyncio.to_thread(client.list_collections)
                    collection_count = len(collections)
                except:
                    collection_count = "unknown"
                
                metadata = {
                    "collection_count": collection_count,
                    "test_collection": collection_name
                }
                
                if self.use_http_chroma:
                    metadata.update({
                        "mode": "http",
                        "host": self.chroma_host,
                        "port": self.chroma_port,
                        "url": f"http://{self.chroma_host}:{self.chroma_port}"
                    })
                else:
                    metadata.update({
                        "mode": "file",
                        "persist_directory": self.chroma_dir
                    })
                
                return ServiceHealth(
                    service=self.name,
                    status=HealthStatus.HEALTHY,
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    metadata=metadata
                )
            else:
                raise Exception("Query returned no results")
                
        except Exception as e:
            self._record_failure()
            response_time = (time.time() - start_time) * 1000
            
            return ServiceHealth(
                service=self.name,
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )

class OllamaMonitor(SubsystemMonitor):
    """Monitor Ollama API connectivity and performance."""
    
    def __init__(self, config: WatchdogConfig):
        super().__init__("Ollama", config)
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.api_key = os.getenv("LLM_API_KEY")
        self.client = httpx.AsyncClient(timeout=self.config.timeout)
    
    async def check_health(self) -> ServiceHealth:
        start_time = time.time()
        
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            health_url = f"{self.ollama_url.rstrip('/')}/api/tags"
            
            response = await self.client.get(health_url, headers=headers)
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                self._record_success()
                
                try:
                    data = response.json()
                    models = data.get("models", [])
                    model_names = [model.get("name", "unknown") for model in models]
                except json.JSONDecodeError:
                    models = []
                    model_names = []
                
                return ServiceHealth(
                    service=self.name,
                    status=HealthStatus.HEALTHY,
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    metadata={
                        "endpoint": health_url,
                        "available_models": model_names[:5],  # Limit to first 5
                        "total_models": len(models),
                        "status_code": response.status_code
                    }
                )
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self._record_failure()
            response_time = (time.time() - start_time) * 1000
            
            return ServiceHealth(
                service=self.name,
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )

class EmbeddingMonitor(SubsystemMonitor):
    """Monitor embedding model availability and performance."""
    
    def __init__(self, config: WatchdogConfig):
        super().__init__("Embeddings", config)
        
    async def check_health(self) -> ServiceHealth:
        start_time = time.time()
        
        try:
            # Import here to avoid circular imports
            from database import db_manager
            
            # Check if embedding model is loaded
            if not db_manager.is_embeddings_available() or db_manager.embedding_model is None:
                raise Exception("Embedding model not loaded")
            
            # Test embedding generation with a simple text
            test_text = "health check test"
            embedding_model = db_manager.embedding_model
            test_embedding = await asyncio.to_thread(
                embedding_model.encode, 
                [test_text]
            )
            
            # Verify embedding was generated successfully
            if test_embedding is None or len(test_embedding) == 0:
                raise Exception("Failed to generate test embedding")
            
            # Check embedding dimensions (should be > 0)
            embedding_dim = len(test_embedding[0]) if len(test_embedding) > 0 else 0
            if embedding_dim == 0:
                raise Exception("Generated embedding has invalid dimensions")
            
            self._record_success()
            response_time = (time.time() - start_time) * 1000
            
            metadata = {
                "model_name": getattr(embedding_model, 'model_name', 'Unknown'),
                "embedding_dimensions": embedding_dim,
                "test_embedding_size": len(test_embedding)
            }
            
            return ServiceHealth(
                service=self.name,
                status=HealthStatus.HEALTHY,
                last_check=datetime.now(),
                response_time_ms=response_time,
                metadata=metadata
            )
                
        except Exception as e:
            self._record_failure()
            response_time = (time.time() - start_time) * 1000
            
            return ServiceHealth(
                service=self.name,
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )

class SystemWatchdog:
    """Main watchdog service that orchestrates monitoring of all subsystems."""
    
    def __init__(self, config: Optional[WatchdogConfig] = None):
        self.config = config or WatchdogConfig()
        self.monitors: List[SubsystemMonitor] = []
        self.health_history: Dict[str, List[ServiceHealth]] = {}
        self.running = False
        self.loop = None
        
        # Setup logging
        if self.config.enable_logging:
            logging.basicConfig(
                level=getattr(logging, self.config.log_level),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            self.logger = logging.getLogger("SystemWatchdog")
        else:
            self.logger = logging.getLogger("SystemWatchdog")
        
        # Initialize monitors
        self._initialize_monitors()
    
    def _initialize_monitors(self):
        """Initialize all subsystem monitors."""
        self.monitors = [
            RedisMonitor(self.config),
            ChromaDBMonitor(self.config),
            EmbeddingMonitor(self.config),
            OllamaMonitor(self.config)
        ]
        
        # Initialize health history
        for monitor in self.monitors:
            self.health_history[monitor.name] = []
    
    async def check_all_systems(self) -> Dict[str, ServiceHealth]:
        """Check health of all monitored systems."""
        results = {}
        
        # Run all health checks concurrently
        tasks = []
        for monitor in self.monitors:
            tasks.append(monitor.check_health())
        
        health_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for monitor, result in zip(self.monitors, health_results):
            if isinstance(result, Exception):
                # Handle unexpected errors
                results[monitor.name] = ServiceHealth(
                    service=monitor.name,
                    status=HealthStatus.UNKNOWN,
                    last_check=datetime.now(),
                    response_time_ms=0,
                    error_message=f"Unexpected error: {str(result)}"
                )
            else:
                results[monitor.name] = result
            
            # Store in history (keep last 100 checks)
            self.health_history[monitor.name].append(results[monitor.name])
            if len(self.health_history[monitor.name]) > 100:
                self.health_history[monitor.name].pop(0)
            
            # Log alerts if needed
            if monitor.should_alert():
                self.logger.error(
                    f"ALERT: {monitor.name} has failed {monitor.consecutive_failures} "
                    f"consecutive health checks. Last error: {results[monitor.name].error_message}"
                )
                monitor.alert_sent = True
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status and statistics."""
        if not self.health_history:
            return {"status": "no_data", "message": "No health checks performed yet"}
        
        overall_status = HealthStatus.HEALTHY
        unhealthy_services = []
        degraded_services = []
        
        latest_results = {}
        for service_name in self.health_history:
            if self.health_history[service_name]:
                latest = self.health_history[service_name][-1]
                latest_results[service_name] = latest
                
                if latest.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                    unhealthy_services.append(service_name)
                elif latest.status == HealthStatus.DEGRADED:
                    if overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED
                    degraded_services.append(service_name)
        
        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "services": {name: asdict(health) for name, health in latest_results.items()},
            "unhealthy_services": unhealthy_services,
            "degraded_services": degraded_services,
            "monitoring_config": asdict(self.config)
        }
    
    def get_service_history(self, service_name: str, hours: int = 24) -> List[ServiceHealth]:
        """Get health history for a specific service."""
        if service_name not in self.health_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            health for health in self.health_history[service_name]
            if health.last_check >= cutoff_time        ]
    
    def _get_adaptive_check_interval(self) -> int:
        """Get adaptive check interval based on current system health."""
        # If all services are healthy, use longer intervals to reduce overhead
        if not self.health_history:
            return self.config.check_interval
        
        # Check recent health status of all services
        all_healthy = True
        for service_name, history in self.health_history.items():
            if history and history[-1].status != HealthStatus.HEALTHY:
                all_healthy = False
                break
        
        if all_healthy:
            # Use stable mode interval for healthy systems
            return self.config.stable_mode_interval
        else:
            # Use normal interval when issues are detected
            return self.config.check_interval

    async def start_monitoring(self):
        """Start the watchdog monitoring loop with adaptive frequency."""
        self.running = True
        
        # Initial startup delay to let services initialize
        if self.config.startup_delay > 0:
            self.logger.info(f"Waiting {self.config.startup_delay} seconds for services to initialize...")
            await asyncio.sleep(self.config.startup_delay)
        
        self.logger.info("Starting system watchdog monitoring")
        
        while self.running:
            try:
                start_time = time.time()
                results = await self.check_all_systems()
                
                # Log summary
                healthy_count = sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY)
                total_count = len(results)
                check_duration = time.time() - start_time
                
                # Get adaptive interval
                next_interval = self._get_adaptive_check_interval()
                
                self.logger.info(
                    f"Health check completed: {healthy_count}/{total_count} services healthy "
                    f"(took {check_duration:.2f}s, next check in {next_interval}s)"
                )
                
                # Store metrics for monitoring
                self._store_watchdog_metrics(check_duration, healthy_count, total_count)
                
                # Adaptive sleep based on system health
                await asyncio.sleep(next_interval)
                
            except Exception as e:
                self.logger.error(f"Error during monitoring cycle: {e}")
                await asyncio.sleep(self.config.check_interval)  # Fallback to normal interval on error
    
    def _store_watchdog_metrics(self, check_duration: float, healthy_count: int, total_count: int):
        """Store watchdog performance metrics."""
        metrics = {
            "timestamp": time.time(),
            "check_duration": check_duration,
            "healthy_count": healthy_count,
            "total_count": total_count,
            "health_ratio": healthy_count / total_count if total_count > 0 else 0
        }
        
        # Store in health history for analysis
        if not hasattr(self, 'watchdog_metrics'):
            self.watchdog_metrics = []
        
        self.watchdog_metrics.append(metrics)
        
        # Keep only last 24 hours of metrics
        cutoff_time = time.time() - (24 * 60 * 60)
        self.watchdog_metrics = [m for m in self.watchdog_metrics if m["timestamp"] > cutoff_time]

    def start_background_monitoring(self):
        """Start monitoring in a background thread."""
        def run_monitoring():
            asyncio.run(self.start_monitoring())
        
        monitoring_thread = threading.Thread(target=run_monitoring, daemon=True)
        monitoring_thread.start()
        return monitoring_thread

# Global watchdog instance
_watchdog_instance = None

def get_watchdog() -> SystemWatchdog:
    """Get or create the global watchdog instance."""
    global _watchdog_instance
    if _watchdog_instance is None:
        _watchdog_instance = SystemWatchdog()
    return _watchdog_instance

def start_watchdog_service():
    """Start the watchdog service in the background."""
    watchdog = get_watchdog()
    return watchdog.start_background_monitoring()

# Health check endpoint helpers
async def get_health_status():
    """Get current health status for API endpoints."""
    watchdog = get_watchdog()
    return await watchdog.check_all_systems()

def get_system_overview():
    """Get system overview for API endpoints."""
    watchdog = get_watchdog()
    return watchdog.get_system_status()

if __name__ == "__main__":
    # CLI mode for testing
    import sys
    
    async def main():
        config = WatchdogConfig(check_interval=10, enable_logging=True, log_level="DEBUG")
        watchdog = SystemWatchdog(config)
        
        if len(sys.argv) > 1 and sys.argv[1] == "monitor":
            # Continuous monitoring
            await watchdog.start_monitoring()
        else:
            # Single health check
            print("Performing single health check...")
            results = await watchdog.check_all_systems()
            
            print("\n=== SYSTEM HEALTH REPORT ===")
            for service_name, health in results.items():
                status_emoji = "✅" if health.status == HealthStatus.HEALTHY else "❌"
                print(f"{status_emoji} {service_name}: {health.status.value}")
                print(f"   Response time: {health.response_time_ms:.2f}ms")
                if health.error_message:
                    print(f"   Error: {health.error_message}")
                if health.metadata:
                    print(f"   Metadata: {health.metadata}")
                print()
            
            # Overall status
            status = watchdog.get_system_status()
            print(f"Overall Status: {status['overall_status']}")
    
    asyncio.run(main())
