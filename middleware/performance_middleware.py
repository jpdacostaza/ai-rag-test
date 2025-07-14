"""
Performance Monitoring Middleware
================================

Provides comprehensive request timing and performance monitoring for the FastAPI application.
Tracks request durations, database query times, memory usage, and other performance metrics.

Features:
- Request/response timing with sub-millisecond precision
- Database query monitoring integration
- Memory usage tracking during requests
- Structured logging of performance metrics
- Minimal overhead design for production use
- Correlation ID integration for request tracing

Usage:
    from middleware.performance_middleware import PerformanceMiddleware
    app.add_middleware(PerformanceMiddleware)
"""

import time
import psutil
import asyncio
from typing import Optional, Dict, Any, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from core.logging_config import get_logger, get_correlation_id


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor request performance and resource usage.
    
    Tracks:
    - Request/response timing
    - Memory usage changes
    - Database query timing (when available)
    - CPU usage during request processing
    - Response size and status codes
    """
    
    def __init__(self, app, enable_memory_tracking: bool = True, enable_cpu_tracking: bool = True):
        super().__init__(app)
        self.logger = get_logger(__name__)
        self.enable_memory_tracking = enable_memory_tracking
        self.enable_cpu_tracking = enable_cpu_tracking
        self.process = psutil.Process() if (enable_memory_tracking or enable_cpu_tracking) else None
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance monitoring."""
        start_time = time.time()
        start_perf_counter = time.perf_counter()
        
        # Get initial resource measurements
        initial_memory = None
        initial_cpu_percent = None
        
        if self.enable_memory_tracking and self.process:
            try:
                memory_info = self.process.memory_info()
                initial_memory = {
                    'rss': memory_info.rss,  # Resident Set Size
                    'vms': memory_info.vms   # Virtual Memory Size
                }
            except Exception:
                pass
        
        if self.enable_cpu_tracking and self.process:
            try:
                initial_cpu_percent = self.process.cpu_percent()
            except Exception:
                pass
        
        # Store metrics in request state for potential use by route handlers
        request.state.performance_start_time = start_time
        request.state.performance_start_perf = start_perf_counter
        
        # Process the request
        try:
            response = await call_next(request)
            error = None
        except Exception as e:
            # Still measure performance even if request failed
            response = Response(content="Internal Server Error", status_code=500)
            error = str(e)
        
        # Calculate timing metrics
        end_time = time.time()
        end_perf_counter = time.perf_counter()
        
        total_time_ms = (end_time - start_time) * 1000
        precise_time_ms = (end_perf_counter - start_perf_counter) * 1000
        
        # Calculate resource usage changes
        memory_delta = None
        cpu_usage = None
        
        if self.enable_memory_tracking and self.process and initial_memory:
            try:
                final_memory_info = self.process.memory_info()
                memory_delta = {
                    'rss_delta': final_memory_info.rss - initial_memory['rss'],
                    'vms_delta': final_memory_info.vms - initial_memory['vms'],
                    'rss_mb': final_memory_info.rss / 1024 / 1024,
                    'vms_mb': final_memory_info.vms / 1024 / 1024
                }
            except Exception:
                pass
        
        if self.enable_cpu_tracking and self.process:
            try:
                cpu_usage = self.process.cpu_percent()
            except Exception:
                pass
        
        # Get response size
        response_size = 0
        if hasattr(response, 'headers') and 'content-length' in response.headers:
            try:
                response_size = int(response.headers['content-length'])
            except (ValueError, TypeError):
                pass
        
        # Prepare performance metrics
        performance_metrics = {
            'method': request.method,
            'path': str(request.url.path),
            'status_code': response.status_code,
            'total_time_ms': round(total_time_ms, 3),
            'precise_time_ms': round(precise_time_ms, 3),
            'response_size_bytes': response_size,
            'timestamp': start_time
        }
        
        # Add optional metrics
        if memory_delta:
            performance_metrics['memory'] = memory_delta
        
        if cpu_usage is not None:
            performance_metrics['cpu_percent'] = cpu_usage
        
        if error:
            performance_metrics['error'] = error
        
        # Add query timing if available from request state
        if hasattr(request.state, 'db_query_time_ms'):
            performance_metrics['db_query_time_ms'] = request.state.db_query_time_ms
        
        # Log performance metrics with appropriate level
        log_level = self._determine_log_level(total_time_ms, response.status_code, error)
        
        if log_level == 'warning':
            self.logger.warning("Request performance warning", **performance_metrics)
        elif log_level == 'error':
            self.logger.error("Request performance error", **performance_metrics)
        else:
            self.logger.info("Request completed", **performance_metrics)
        
        # Add performance headers to response (optional, for debugging)
        if hasattr(response, 'headers'):
            response.headers['X-Response-Time-MS'] = str(round(precise_time_ms, 3))
            
            # Add correlation ID header if available
            correlation_id = get_correlation_id()
            if correlation_id:
                response.headers['X-Correlation-ID'] = correlation_id
        
        return response
    
    def _determine_log_level(self, response_time_ms: float, status_code: int, error: Optional[str]) -> str:
        """Determine appropriate log level based on performance and status."""
        if error or status_code >= 500:
            return 'error'
        elif status_code >= 400:
            return 'warning'
        elif response_time_ms > 5000:  # 5 seconds
            return 'error'
        elif response_time_ms > 2000:  # 2 seconds
            return 'warning'
        else:
            return 'info'


class DatabaseQueryTracker:
    """
    Helper class to track database query performance within requests.
    Can be used by database services to report query timing to the performance middleware.
    """
    
    @staticmethod
    def start_query_timer() -> float:
        """Start timing a database query."""
        return time.perf_counter()
    
    @staticmethod
    def end_query_timer(start_time: float, query_type: str = "unknown", request: Optional[Request] = None):
        """End timing a database query and update request state."""
        end_time = time.perf_counter()
        query_time_ms = (end_time - start_time) * 1000
        
        if request and hasattr(request, 'state'):
            # Accumulate query time in request state
            if not hasattr(request.state, 'db_query_time_ms'):
                request.state.db_query_time_ms = 0
            
            request.state.db_query_time_ms += query_time_ms
            
            # Also track individual queries for detailed logging
            if not hasattr(request.state, 'db_queries'):
                request.state.db_queries = []
            
            request.state.db_queries.append({
                'type': query_type,
                'duration_ms': round(query_time_ms, 3)
            })
        
        return query_time_ms


# Performance metrics aggregator for advanced monitoring
class PerformanceMetrics:
    """
    Aggregates performance metrics for reporting and monitoring.
    Useful for creating dashboards or alerts based on performance trends.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.reset_metrics()
    
    def reset_metrics(self):
        """Reset all accumulated metrics."""
        self.request_count = 0
        self.total_response_time = 0.0
        self.slow_requests = 0
        self.error_requests = 0
        self.memory_peak = 0
        self.start_time = time.time()
    
    def record_request(self, response_time_ms: float, status_code: int, memory_mb: Optional[float] = None):
        """Record metrics for a completed request."""
        self.request_count += 1
        self.total_response_time += response_time_ms
        
        if response_time_ms > 2000:  # 2 seconds
            self.slow_requests += 1
        
        if status_code >= 400:
            self.error_requests += 1
        
        if memory_mb and memory_mb > self.memory_peak:
            self.memory_peak = memory_mb
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics."""
        duration = time.time() - self.start_time
        
        return {
            'duration_seconds': round(duration, 2),
            'total_requests': self.request_count,
            'average_response_time_ms': round(self.total_response_time / max(self.request_count, 1), 3),
            'requests_per_second': round(self.request_count / max(duration, 1), 2),
            'slow_request_percentage': round((self.slow_requests / max(self.request_count, 1)) * 100, 2),
            'error_percentage': round((self.error_requests / max(self.request_count, 1)) * 100, 2),
            'memory_peak_mb': self.memory_peak
        }
    
    def log_summary(self):
        """Log current performance summary."""
        summary = self.get_summary()
        self.logger.info("Performance metrics summary", **summary)


# Global instance for collecting metrics
performance_metrics = PerformanceMetrics()
