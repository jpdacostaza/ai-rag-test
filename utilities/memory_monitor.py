"""
Memory pressure monitoring and management system.
"""
import os
import psutil
import asyncio
from typing import Callable, List, Optional
from datetime import datetime
import json
from pathlib import Path

from human_logging import log_service_status

class MemoryPressureMonitor:
    """Monitor and manage system memory pressure."""
    
    def __init__(
        self,
        warning_threshold: float = 75.0,  # 75% memory usage
        critical_threshold: float = 90.0,  # 90% memory usage
        check_interval: int = 30  # 30 seconds
    ):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.check_interval = check_interval
        self.cleanup_callbacks: List[Callable] = []
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._last_state = "normal"
        self._pressure_history = []
        
    async def start(self):
        """Start memory pressure monitoring."""
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        log_service_status(
            "memory_monitor",
            "info",
            "Memory pressure monitoring started"
        )
        
    async def stop(self):
        """Stop memory pressure monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
                
        log_service_status(
            "memory_monitor",
            "info",
            "Memory pressure monitoring stopped"
        )
        
    def register_cleanup_callback(self, callback: Callable):
        """Register a callback to be called when memory pressure is high."""
        self.cleanup_callbacks.append(callback)
        
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                memory_info = self._get_memory_info()
                await self._check_memory_pressure(memory_info)
                await self._save_metrics(memory_info)
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_service_status(
                    "memory_monitor",
                    "error",
                    f"Error in memory monitor: {str(e)}"
                )
                await asyncio.sleep(self.check_interval)
                
    def _get_memory_info(self):
        """Get current memory usage information."""
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'memory_percent': vm.percent,
            'memory_available': vm.available,
            'memory_used': vm.used,
            'memory_total': vm.total,
            'swap_percent': swap.percent,
            'swap_used': swap.used,
            'swap_total': swap.total
        }
        
    async def _check_memory_pressure(self, memory_info: dict):
        """Check memory pressure and take action if needed."""
        memory_percent = memory_info['memory_percent']
        
        if memory_percent >= self.critical_threshold:
            if self._last_state != "critical":
                log_service_status(
                    "memory_monitor",
                    "error",
                    f"Critical memory pressure: {memory_percent:.1f}%"
                )
                await self._handle_critical_pressure()
            self._last_state = "critical"
            
        elif memory_percent >= self.warning_threshold:
            if self._last_state != "warning":
                log_service_status(
                    "memory_monitor",
                    "warning",
                    f"High memory pressure: {memory_percent:.1f}%"
                )
                await self._handle_warning_pressure()
            self._last_state = "warning"
            
        else:
            if self._last_state != "normal":
                log_service_status(
                    "memory_monitor",
                    "info",
                    f"Memory pressure normal: {memory_percent:.1f}%"
                )
            self._last_state = "normal"
            
    async def _handle_warning_pressure(self):
        """Handle warning level memory pressure."""
        # Call cleanup callbacks in parallel
        tasks = []
        for callback in self.cleanup_callbacks:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(asyncio.create_task(callback()))
            else:
                tasks.append(asyncio.to_thread(callback))
                
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def _handle_critical_pressure(self):
        """Handle critical level memory pressure."""
        # More aggressive cleanup
        await self._handle_warning_pressure()
        
        # Additional emergency measures
        if hasattr(self, 'emergency_cleanup'):
            await self.emergency_cleanup()
            
    async def _save_metrics(self, memory_info: dict):
        """Save memory metrics to file."""
        self._pressure_history.append(memory_info)
        
        # Keep only last 24 hours of data
        while len(self._pressure_history) > (24 * 3600 / self.check_interval):
            self._pressure_history.pop(0)
            
        # Save to file periodically
        if len(self._pressure_history) % 60 == 0:  # Every ~30 minutes
            metrics_dir = Path("metrics")
            metrics_dir.mkdir(exist_ok=True)
            
            metrics_file = metrics_dir / "memory_pressure.json"
            with open(metrics_file, "w") as f:
                json.dump({
                    'current_state': self._last_state,
                    'thresholds': {
                        'warning': self.warning_threshold,
                        'critical': self.critical_threshold
                    },
                    'history': self._pressure_history[-120:]  # Last hour
                }, f, indent=2)
                
    async def get_pressure_stats(self):
        """Get memory pressure statistics."""
        if not self._pressure_history:
            return None
            
        recent = self._pressure_history[-60:]  # Last 30 minutes
        memory_percentages = [entry['memory_percent'] for entry in recent]
        
        return {
            'current_state': self._last_state,
            'current_pressure': memory_percentages[-1] if memory_percentages else None,
            'avg_pressure_30m': sum(memory_percentages) / len(memory_percentages) if memory_percentages else None,
            'peak_pressure_30m': max(memory_percentages) if memory_percentages else None,
            'pressure_trends': self._analyze_trends(memory_percentages)
        }
        
    def _analyze_trends(self, percentages: List[float]):
        """Analyze memory pressure trends."""
        if len(percentages) < 2:
            return 'insufficient_data'
            
        # Calculate trend
        start_avg = sum(percentages[:10]) / 10 if len(percentages) >= 10 else percentages[0]
        end_avg = sum(percentages[-10:]) / 10 if len(percentages) >= 10 else percentages[-1]
        
        diff = end_avg - start_avg
        if abs(diff) < 1.0:
            return 'stable'
        elif diff > 0:
            return 'increasing'
        else:
            return 'decreasing'
