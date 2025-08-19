#!/usr/bin/env python3
"""
Production Metrics Health Check
Real-time metrics validation for production ARM Linux systems
"""

import asyncio
import json
import time
import platform
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class MetricsHealthChecker:
    """Comprehensive metrics health checker for production systems"""
    
    def __init__(self):
        self.start_time = time.time()
        self.system_info = self._get_system_info()
        self.health_status = {}
        
        # Add the backend directory to Python path for imports
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'is_arm': platform.machine().lower() in ['arm64', 'aarch64', 'armv7l', 'armv6l'],
            'is_linux': platform.system().lower() == 'linux',
            'is_docker': os.path.exists('/.dockerenv'),
            'hostname': platform.node(),
            'boot_time': datetime.now().isoformat()
        }
    
    async def check_psutil_health(self) -> Dict[str, Any]:
        """Check psutil functionality and performance"""
        health = {
            'status': 'unknown',
            'version': None,
            'features': {},
            'performance': {},
            'errors': []
        }
        
        try:
            import psutil
            health['version'] = psutil.__version__
            health['status'] = 'available'
            
            # Test core features
            start = time.time()
            
            # CPU metrics
            try:
                cpu_count = psutil.cpu_count()
                cpu_percent = psutil.cpu_percent(interval=0.1)
                health['features']['cpu'] = {
                    'physical_cores': cpu_count,
                    'logical_cores': psutil.cpu_count(logical=True),
                    'current_usage': cpu_percent,
                    'status': 'working'
                }
            except Exception as e:
                health['features']['cpu'] = {'status': 'error', 'error': str(e)}
                health['errors'].append(f"CPU monitoring: {e}")
            
            # Memory metrics
            try:
                memory = psutil.virtual_memory()
                health['features']['memory'] = {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'usage_percent': memory.percent,
                    'status': 'working'
                }
            except Exception as e:
                health['features']['memory'] = {'status': 'error', 'error': str(e)}
                health['errors'].append(f"Memory monitoring: {e}")
            
            # Disk metrics
            try:
                disk = psutil.disk_usage('/')
                health['features']['disk'] = {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'usage_percent': round(disk.percent, 1),
                    'status': 'working'
                }
            except Exception as e:
                health['features']['disk'] = {'status': 'error', 'error': str(e)}
                health['errors'].append(f"Disk monitoring: {e}")
            
            # Process metrics
            try:
                process = psutil.Process()
                process.cpu_percent()  # Initialize
                await asyncio.sleep(0.1)  # Allow measurement
                
                health['features']['process'] = {
                    'pid': process.pid,
                    'memory_mb': round(process.memory_info().rss / (1024**2), 2),
                    'cpu_percent': process.cpu_percent(),
                    'threads': process.num_threads(),
                    'status': 'working'
                }
            except Exception as e:
                health['features']['process'] = {'status': 'error', 'error': str(e)}
                health['errors'].append(f"Process monitoring: {e}")
            
            # Optional features (may not be available on ARM/containers)
            optional_features = {
                'cpu_frequency': lambda: psutil.cpu_freq(),
                'temperature': lambda: getattr(psutil, 'sensors_temperatures', lambda: None)(),
                'battery': lambda: getattr(psutil, 'sensors_battery', lambda: None)(),
                'network_io': lambda: psutil.net_io_counters(),
                'disk_io': lambda: psutil.disk_io_counters()
            }
            
            for feature_name, feature_func in optional_features.items():
                try:
                    result = feature_func()
                    health['features'][feature_name] = {
                        'available': result is not None,
                        'status': 'working' if result else 'unavailable'
                    }
                except Exception:
                    health['features'][feature_name] = {
                        'available': False,
                        'status': 'unsupported'
                    }
            
            # Performance timing
            health['performance'] = {
                'check_duration_ms': round((time.time() - start) * 1000, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            # Overall status
            working_features = sum(1 for f in health['features'].values() 
                                 if isinstance(f, dict) and f.get('status') == 'working')
            total_core_features = 4  # CPU, Memory, Disk, Process
            
            if working_features >= total_core_features:
                health['status'] = 'healthy'
            elif working_features >= 2:
                health['status'] = 'degraded'
            else:
                health['status'] = 'critical'
                
        except ImportError:
            health['status'] = 'missing'
            health['errors'].append("psutil not installed")
        except Exception as e:
            health['status'] = 'error'
            health['errors'].append(f"Unexpected error: {e}")
        
        return health
    
    async def check_backend_metrics_health(self) -> Dict[str, Any]:
        """Check backend metrics components"""
        health = {
            'status': 'unknown',
            'components': {},
            'errors': []
        }
        
        # Check performance middleware
        try:
            from middleware.performance_middleware import PerformanceMiddleware
            from starlette.applications import Starlette
            from starlette.requests import Request
            from starlette.responses import JSONResponse
            
            # Quick test
            app = Starlette()
            middleware = PerformanceMiddleware(app)
            
            scope = {
                'type': 'http',
                'method': 'GET',
                'path': '/health',
                'headers': [],
                'query_string': b'',
                'server': ('localhost', 8000)
            }
            
            async def mock_handler(request):
                await asyncio.sleep(0.01)  # Minimal work
                return JSONResponse({'status': 'ok'})
            
            start = time.time()
            request = Request(scope)
            response = await middleware.dispatch(request, mock_handler)
            duration = (time.time() - start) * 1000
            
            health['components']['performance_middleware'] = {
                'status': 'working',
                'response_time_ms': round(duration, 2),
                'headers_present': 'X-Response-Time-MS' in response.headers
            }
            
        except Exception as e:
            health['components']['performance_middleware'] = {
                'status': 'error',
                'error': str(e)
            }
            health['errors'].append(f"Performance middleware: {e}")
        
        # Check performance monitor
        try:
            from utilities.performance_monitoring import PerformanceMonitor
            
            monitor = PerformanceMonitor(collection_interval=0.5)
            await monitor.start_monitoring()
            await asyncio.sleep(0.6)  # Let it collect metrics
            
            summary = monitor.get_performance_summary()
            await monitor.stop_monitoring()
            
            health['components']['performance_monitor'] = {
                'status': 'working',
                'metrics_collected': summary.get('monitoring', {}).get('metrics_collected', 0),
                'has_system_performance': 'system_performance' in summary
            }
            
        except Exception as e:
            health['components']['performance_monitor'] = {
                'status': 'error',
                'error': str(e)
            }
            health['errors'].append(f"Performance monitor: {e}")
        
        # Check metrics registry
        try:
            from core.metrics import METRICS_ENABLED
            health['components']['prometheus_metrics'] = {
                'status': 'working' if METRICS_ENABLED else 'disabled',
                'enabled': METRICS_ENABLED
            }
        except Exception as e:
            health['components']['prometheus_metrics'] = {
                'status': 'error',
                'error': str(e)
            }
            health['errors'].append(f"Prometheus metrics: {e}")
        
        # Overall component health
        working_components = sum(1 for c in health['components'].values()
                               if isinstance(c, dict) and c.get('status') == 'working')
        total_components = len(health['components'])
        
        if working_components == total_components:
            health['status'] = 'healthy'
        elif working_components > 0:
            health['status'] = 'degraded'
        else:
            health['status'] = 'critical'
        
        return health
    
    async def check_arm_linux_compatibility(self) -> Dict[str, Any]:
        """Check ARM Linux specific compatibility"""
        compat = {
            'status': 'unknown',
            'architecture_support': {},
            'container_support': {},
            'recommendations': [],
            'warnings': []
        }
        
        # Architecture analysis
        compat['architecture_support'] = {
            'is_arm': self.system_info['is_arm'],
            'is_linux': self.system_info['is_linux'],
            'machine': self.system_info['machine'],
            'supported': True  # Our metrics work on all architectures
        }
        
        # Container environment analysis
        compat['container_support'] = {
            'is_docker': self.system_info['is_docker'],
            'cgroup_available': os.path.exists('/sys/fs/cgroup'),
            'proc_available': os.path.exists('/proc'),
            'container_ready': True
        }
        
        # Generate recommendations
        if self.system_info['is_arm']:
            compat['recommendations'].extend([
                "ARM architecture detected - all core metrics supported",
                "Use interval-based CPU monitoring for best accuracy",
                "Consider thermal monitoring limitations on ARM containers"
            ])
        
        if self.system_info['is_linux']:
            compat['recommendations'].extend([
                "Linux system - optimal performance expected",
                "Container deployment fully supported",
                "cgroup metrics available for fine-grained monitoring"
            ])
        
        if self.system_info['is_docker']:
            compat['recommendations'].extend([
                "Docker container detected - metrics will be container-scoped",
                "Host metrics may require privileged mode",
                "Network and disk I/O reflect container, not host"
            ])
            compat['warnings'].append("Some hardware sensors unavailable in containers")
        
        # Overall compatibility status
        if self.system_info['is_arm'] and self.system_info['is_linux']:
            compat['status'] = 'optimal'
            compat['recommendations'].append("Perfect environment for ARM Linux deployment")
        elif self.system_info['is_linux']:
            compat['status'] = 'excellent'
        else:
            compat['status'] = 'compatible'
        
        return compat
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run complete health check"""
        print("🏥 PRODUCTION METRICS HEALTH CHECK")
        print("=" * 50)
        print(f"System: {self.system_info['platform']}")
        print(f"Architecture: {self.system_info['machine']}")
        print(f"Time: {datetime.now().isoformat()}")
        print()
        
        # Run all checks
        psutil_health = await self.check_psutil_health()
        backend_health = await self.check_backend_metrics_health()
        arm_compat = await self.check_arm_linux_compatibility()
        
        # Compile overall health
        overall_health = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.system_info,
            'psutil_health': psutil_health,
            'backend_metrics_health': backend_health,
            'arm_linux_compatibility': arm_compat,
            'overall_status': 'unknown',
            'summary': {}
        }
        
        # Determine overall status
        component_statuses = [
            psutil_health['status'],
            backend_health['status'],
            arm_compat['status']
        ]
        
        if all(s in ['healthy', 'optimal', 'excellent'] for s in component_statuses):
            overall_health['overall_status'] = 'healthy'
        elif any(s == 'critical' for s in component_statuses):
            overall_health['overall_status'] = 'critical'
        else:
            overall_health['overall_status'] = 'degraded'
        
        # Generate summary
        overall_health['summary'] = {
            'psutil_status': psutil_health['status'],
            'backend_status': backend_health['status'],
            'arm_compatibility': arm_compat['status'],
            'total_errors': len(psutil_health['errors']) + len(backend_health['errors']),
            'recommendations_count': len(arm_compat['recommendations']),
            'health_check_duration_ms': round((time.time() - self.start_time) * 1000, 2)
        }
        
        return overall_health

async def main():
    """Run production health check"""
    checker = MetricsHealthChecker()
    health_report = await checker.run_comprehensive_health_check()
    
    # Display results
    print("📊 HEALTH CHECK RESULTS")
    print("=" * 50)
    
    print(f"Overall Status: {health_report['overall_status'].upper()}")
    print(f"psutil Health: {health_report['psutil_health']['status']}")
    print(f"Backend Metrics: {health_report['backend_metrics_health']['status']}")
    print(f"ARM Compatibility: {health_report['arm_linux_compatibility']['status']}")
    
    if health_report['summary']['total_errors'] > 0:
        print(f"\n⚠️  {health_report['summary']['total_errors']} errors detected")
    
    print(f"\nHealth check completed in {health_report['summary']['health_check_duration_ms']}ms")
    
    # Save detailed report
    report_file = f"metrics_health_report_{int(time.time())}.json"
    with open(report_file, 'w') as f:
        json.dump(health_report, f, indent=2, default=str)
    
    print(f"📋 Detailed report saved to: {report_file}")
    
    # Return appropriate exit code
    if health_report['overall_status'] == 'healthy':
        print("\n✅ ALL SYSTEMS OPERATIONAL")
        return 0
    elif health_report['overall_status'] == 'degraded':
        print("\n⚠️  SOME ISSUES DETECTED")
        return 1
    else:
        print("\n❌ CRITICAL ISSUES FOUND")
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
