"""
Performance Monitoring Utilities
===============================

This module provides comprehensive performance monitoring for the enhanced
connection pooling and error handling improvements (Issues #3 and #5).

Key metrics:
1. Connection pool performance and utilization
2. Error handling reduction and standardization
3. Memory pressure detection and response
4. Response time improvements
5. System resource utilization
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque

from core.unified_logging import get_logger, log_service_status
from utilities.enhanced_connection_pooling import pool_manager

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    timestamp: float = field(default_factory=time.time)
    operation_name: str = ""
    response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    connection_pool_stats: Dict[str, Any] = field(default_factory=dict)
    error_count: int = 0
    success_count: int = 0


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.
    """
    
    def __init__(self, collection_interval: float = 60.0):
        self.collection_interval = collection_interval
        self.metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 data points
        self.operation_stats: Dict[str, List[float]] = defaultdict(list)
        self.error_patterns: Dict[str, int] = defaultdict(int)
        self.memory_pressure_events: List[Dict[str, Any]] = []
        
        # Performance baseline tracking
        self.baseline_metrics: Optional[PerformanceMetrics] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self._started = False

    async def start_monitoring(self):
        """Start the performance monitoring system."""
        if not self._started:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self._started = True
            log_service_status("performance_monitor", "info", "Performance monitoring started")

    async def stop_monitoring(self):
        """Stop the performance monitoring system."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            self._started = False
            log_service_status("performance_monitor", "info", "Performance monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.collection_interval)
                await self._collect_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

    async def _collect_metrics(self):
        """Collect performance metrics."""
        try:
            # System metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Connection pool metrics
            pool_stats = pool_manager.get_all_stats()
            
            # Create metrics snapshot
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                operation_name="system_snapshot",
                memory_usage_mb=memory.used / (1024 * 1024),
                cpu_percent=cpu_percent,
                connection_pool_stats=pool_stats
            )
            
            self.metrics_history.append(metrics)
            
            # Check for memory pressure
            if memory.percent > 80.0:
                await self._handle_memory_pressure_event(memory.percent)
                
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

    async def _handle_memory_pressure_event(self, memory_percent: float):
        """Handle memory pressure events."""
        event = {
            "timestamp": time.time(),
            "memory_percent": memory_percent,
            "action": "monitoring_detected"
        }
        
        self.memory_pressure_events.append(event)
        
        # Keep only last 100 events
        if len(self.memory_pressure_events) > 100:
            self.memory_pressure_events = self.memory_pressure_events[-100:]
        
        log_service_status("performance_monitor", "warning", 
                         f"Memory pressure detected: {memory_percent:.1f}%")

    def record_operation(
        self, 
        operation_name: str, 
        response_time_ms: float, 
        success: bool = True,
        error_type: Optional[str] = None
    ):
        """Record an operation's performance metrics."""
        # Track response times
        self.operation_stats[operation_name].append(response_time_ms)
        
        # Keep only last 1000 measurements per operation
        if len(self.operation_stats[operation_name]) > 1000:
            self.operation_stats[operation_name] = self.operation_stats[operation_name][-1000:]
        
        # Track errors
        if not success and error_type:
            self.error_patterns[f"{operation_name}:{error_type}"] += 1

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a comprehensive performance summary."""
        if not self.metrics_history:
            return {"status": "no_data", "message": "No metrics collected yet"}
        
        latest_metrics = self.metrics_history[-1]
        
        # Calculate averages over last 10 minutes
        ten_minutes_ago = time.time() - 600
        recent_metrics = [m for m in self.metrics_history if m.timestamp > ten_minutes_ago]
        
        if recent_metrics:
            avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        else:
            avg_memory = latest_metrics.memory_usage_mb
            avg_cpu = latest_metrics.cpu_percent
        
        # Operation performance analysis
        operation_summary = {}
        for op_name, times in self.operation_stats.items():
            if times:
                operation_summary[op_name] = {
                    "avg_response_time_ms": sum(times) / len(times),
                    "min_response_time_ms": min(times),
                    "max_response_time_ms": max(times),
                    "total_operations": len(times),
                    "p95_response_time_ms": self._calculate_percentile(times, 95),
                    "p99_response_time_ms": self._calculate_percentile(times, 99)
                }
        
        # Error analysis
        total_errors = sum(self.error_patterns.values())
        error_summary = dict(self.error_patterns) if total_errors > 0 else {}
        
        return {
            "timestamp": latest_metrics.timestamp,
            "system_performance": {
                "memory_usage_mb": round(avg_memory, 2),
                "memory_percent": round((avg_memory / (psutil.virtual_memory().total / (1024 * 1024))) * 100, 1),
                "cpu_percent": round(avg_cpu, 1),
                "memory_pressure_events": len(self.memory_pressure_events)
            },
            "connection_pools": latest_metrics.connection_pool_stats,
            "operations": operation_summary,
            "errors": {
                "total_errors": total_errors,
                "error_patterns": error_summary
            },
            "monitoring": {
                "metrics_collected": len(self.metrics_history),
                "monitoring_duration_hours": round((time.time() - self.metrics_history[0].timestamp) / 3600, 2) if self.metrics_history else 0,
                "collection_interval_seconds": self.collection_interval
            }
        }

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate the specified percentile of a list of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_improvement_metrics(self) -> Dict[str, Any]:
        """
        Get metrics showing improvements from enhanced pooling and error handling.
        """
        summary = self.get_performance_summary()
        
        improvements = {
            "connection_pooling": {},
            "error_handling": {},
            "memory_management": {}
        }
        
        # Connection pooling improvements
        pool_stats = summary.get("connection_pools", {})
        if pool_stats:
            total_pools = pool_stats.get("global", {}).get("total_pools", 0)
            total_connections = pool_stats.get("global", {}).get("total_connections", 0)
            total_errors = pool_stats.get("global", {}).get("total_errors", 0)
            
            improvements["connection_pooling"] = {
                "active_pools": total_pools,
                "total_connections": total_connections,
                "connection_errors": total_errors,
                "error_rate": round((total_errors / max(total_connections, 1)) * 100, 2),
                "status": "enhanced" if total_pools > 0 else "legacy"
            }
        
        # Error handling improvements
        operations = summary.get("operations", {})
        if operations:
            total_ops = sum(op["total_operations"] for op in operations.values())
            avg_response_time = sum(op["avg_response_time_ms"] for op in operations.values()) / len(operations)
            
            improvements["error_handling"] = {
                "standardized_operations": len(operations),
                "total_operations_tracked": total_ops,
                "avg_response_time_ms": round(avg_response_time, 2),
                "operations_with_metrics": list(operations.keys())
            }
        
        # Memory management improvements
        sys_perf = summary.get("system_performance", {})
        improvements["memory_management"] = {
            "memory_usage_mb": sys_perf.get("memory_usage_mb", 0),
            "memory_percent": sys_perf.get("memory_percent", 0),
            "pressure_events": sys_perf.get("memory_pressure_events", 0),
            "automatic_scaling": pool_stats.get("global", {}).get("total_pools", 0) > 0
        }
        
        return improvements

    async def generate_performance_report(self) -> str:
        """Generate a detailed performance report."""
        summary = self.get_performance_summary()
        improvements = self.get_improvement_metrics()
        
        report = []
        report.append("# Enhanced Connection Pooling & Error Handling - Performance Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # System Performance
        sys_perf = summary.get("system_performance", {})
        report.append("## System Performance")
        report.append(f"- Memory Usage: {sys_perf.get('memory_usage_mb', 0):.1f} MB ({sys_perf.get('memory_percent', 0):.1f}%)")
        report.append(f"- CPU Usage: {sys_perf.get('cpu_percent', 0):.1f}%")
        report.append(f"- Memory Pressure Events: {sys_perf.get('memory_pressure_events', 0)}")
        report.append("")
        
        # Connection Pooling
        pool_improvements = improvements.get("connection_pooling", {})
        report.append("## Connection Pooling Improvements")
        report.append(f"- Status: {pool_improvements.get('status', 'unknown').upper()}")
        report.append(f"- Active Pools: {pool_improvements.get('active_pools', 0)}")
        report.append(f"- Total Connections: {pool_improvements.get('total_connections', 0)}")
        report.append(f"- Connection Error Rate: {pool_improvements.get('error_rate', 0):.2f}%")
        report.append("")
        
        # Error Handling
        error_improvements = improvements.get("error_handling", {})
        report.append("## Error Handling Standardization")
        report.append(f"- Standardized Operations: {error_improvements.get('standardized_operations', 0)}")
        report.append(f"- Total Operations Tracked: {error_improvements.get('total_operations_tracked', 0)}")
        report.append(f"- Average Response Time: {error_improvements.get('avg_response_time_ms', 0):.2f} ms")
        report.append("")
        
        # Operation Details
        operations = summary.get("operations", {})
        if operations:
            report.append("## Operation Performance Details")
            for op_name, stats in operations.items():
                report.append(f"### {op_name}")
                report.append(f"- Average: {stats['avg_response_time_ms']:.2f} ms")
                report.append(f"- P95: {stats['p95_response_time_ms']:.2f} ms")
                report.append(f"- P99: {stats['p99_response_time_ms']:.2f} ms")
                report.append(f"- Total Operations: {stats['total_operations']}")
                report.append("")
        
        # Error Patterns
        errors = summary.get("errors", {})
        if errors.get("total_errors", 0) > 0:
            report.append("## Error Patterns")
            for error_pattern, count in errors.get("error_patterns", {}).items():
                report.append(f"- {error_pattern}: {count}")
            report.append("")
        
        # Monitoring Info
        monitoring = summary.get("monitoring", {})
        report.append("## Monitoring Statistics")
        report.append(f"- Metrics Collected: {monitoring.get('metrics_collected', 0)}")
        report.append(f"- Monitoring Duration: {monitoring.get('monitoring_duration_hours', 0):.2f} hours")
        report.append(f"- Collection Interval: {monitoring.get('collection_interval_seconds', 0)} seconds")
        
        return "\n".join(report)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def record_operation_performance(operation_name: str, response_time_ms: float, success: bool = True, error_type: Optional[str] = None):
    """Convenience function to record operation performance."""
    performance_monitor.record_operation(operation_name, response_time_ms, success, error_type)


async def start_performance_monitoring():
    """Start the global performance monitoring."""
    await performance_monitor.start_monitoring()


async def stop_performance_monitoring():
    """Stop the global performance monitoring."""
    await performance_monitor.stop_monitoring()


async def get_performance_report() -> str:
    """Get the current performance report."""
    return await performance_monitor.generate_performance_report()
