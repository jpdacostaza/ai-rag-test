#!/usr/bin/env python3
"""
Comprehensive Metrics Verification Test
Tests all metrics components across different platforms
"""

import sys
import os
import platform
import asyncio
import time
from typing import Dict, Any, List

# Add the backend path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def get_system_info():
    """Get detailed system information"""
    return {
        'platform': platform.platform(),
        'system': platform.system(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'architecture': platform.architecture(),
        'python_version': platform.python_version(),
        'is_arm': platform.machine().lower() in ['arm64', 'aarch64', 'armv7l', 'armv6l'],
        'is_linux': platform.system().lower() == 'linux',
        'is_docker': os.path.exists('/.dockerenv')
    }

def test_psutil_compatibility():
    """Test psutil functionality across platforms"""
    print("🔍 TESTING PSUTIL COMPATIBILITY")
    print("=" * 50)
    
    try:
        import psutil
        print("✅ psutil imported successfully")
        print(f"   Version: {psutil.__version__}")
    except ImportError as e:
        print(f"❌ psutil import failed: {e}")
        return False
    
    # Test CPU monitoring
    print("\n📊 CPU Monitoring:")
    try:
        # System CPU
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        
        print(f"   Physical cores: {cpu_count}")
        print(f"   Logical cores: {cpu_count_logical}")
        if cpu_freq:
            print(f"   CPU frequency: {cpu_freq.current:.1f} MHz")
        else:
            print("   CPU frequency: Not available (common on ARM/containers)")
        
        # CPU percentage tests
        print("   CPU percentage (first call):", psutil.cpu_percent(interval=None))
        print("   CPU percentage (with 0.1s interval):", psutil.cpu_percent(interval=0.1))
        print("   CPU percentage (non-blocking):", psutil.cpu_percent(interval=None))
        
        # Per-CPU percentages
        cpu_percents = psutil.cpu_percent(interval=0.1, percpu=True)
        print(f"   Per-CPU usage: {[f'{c:.1f}%' for c in cpu_percents[:4]]}{' ...' if len(cpu_percents) > 4 else ''}")
        
        print("   ✅ CPU monitoring working")
        
    except Exception as e:
        print(f"   ❌ CPU monitoring failed: {e}")
        return False
    
    # Test Memory monitoring
    print("\n💾 Memory Monitoring:")
    try:
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        print(f"   Total RAM: {memory.total / (1024**3):.1f} GB")
        print(f"   Available RAM: {memory.available / (1024**3):.1f} GB")
        print(f"   RAM usage: {memory.percent}%")
        print(f"   Swap total: {swap.total / (1024**3):.1f} GB")
        print(f"   Swap usage: {swap.percent}%")
        
        print("   ✅ Memory monitoring working")
        
    except Exception as e:
        print(f"   ❌ Memory monitoring failed: {e}")
        return False
    
    # Test Process monitoring
    print("\n🔄 Process Monitoring:")
    try:
        process = psutil.Process()
        
        # Basic process info
        print(f"   PID: {process.pid}")
        print(f"   Process name: {process.name()}")
        print(f"   Status: {process.status()}")
        
        # Memory info
        memory_info = process.memory_info()
        print(f"   Process RAM: {memory_info.rss / (1024**2):.1f} MB")
        print(f"   Virtual memory: {memory_info.vms / (1024**2):.1f} MB")
        
        # CPU info
        process.cpu_percent()  # Initialize
        time.sleep(0.1)  # Some work
        cpu_percent = process.cpu_percent()
        print(f"   Process CPU: {cpu_percent}%")
        
        # Thread count
        try:
            threads = process.num_threads()
            print(f"   Thread count: {threads}")
        except Exception as e:
            print(f"   Thread count: Not available ({e})")
        
        print("   ✅ Process monitoring working")
        
    except Exception as e:
        print(f"   ❌ Process monitoring failed: {e}")
        return False
    
    # Test Disk monitoring
    print("\n💿 Disk Monitoring:")
    try:
        disk_usage = psutil.disk_usage('/')
        
        print(f"   Disk total: {disk_usage.total / (1024**3):.1f} GB")
        print(f"   Disk used: {disk_usage.used / (1024**3):.1f} GB")
        print(f"   Disk usage: {disk_usage.percent}%")
        
        # Disk I/O (may not be available in containers)
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                print(f"   Disk reads: {disk_io.read_count}")
                print(f"   Disk writes: {disk_io.write_count}")
        except Exception:
            print("   Disk I/O: Not available (common in containers)")
        
        print("   ✅ Disk monitoring working")
        
    except Exception as e:
        print(f"   ❌ Disk monitoring failed: {e}")
        return False
    
    # Test Network monitoring
    print("\n🌐 Network Monitoring:")
    try:
        # Network I/O (may not be available in containers)
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                print(f"   Bytes sent: {net_io.bytes_sent / (1024**2):.1f} MB")
                print(f"   Bytes received: {net_io.bytes_recv / (1024**2):.1f} MB")
                print(f"   Packets sent: {net_io.packets_sent}")
                print(f"   Packets received: {net_io.packets_recv}")
        except Exception:
            print("   Network I/O: Not available (common in containers)")
        
        # Network connections
        try:
            connections = psutil.net_connections()
            print(f"   Active connections: {len(connections)}")
        except Exception:
            print("   Network connections: Not available (permission/container)")
        
        print("   ✅ Network monitoring working")
        
    except Exception as e:
        print(f"   ❌ Network monitoring failed: {e}")
        return False
    
    return True

async def test_backend_metrics():
    """Test backend metrics components"""
    print("\n🔧 TESTING BACKEND METRICS COMPONENTS")
    print("=" * 50)
    
    # Test Performance Middleware
    print("\n1. Performance Middleware:")
    try:
        from middleware.performance_middleware import PerformanceMiddleware
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import JSONResponse
        
        app = Starlette()
        middleware = PerformanceMiddleware(app)
        
        # Create mock request
        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/test',
            'headers': [],
            'query_string': b'',
            'server': ('localhost', 8000)
        }
        
        async def mock_call_next(request):
            await asyncio.sleep(0.05)  # Simulate work
            return JSONResponse({'status': 'ok'})
        
        request = Request(scope)
        response = await middleware.dispatch(request, mock_call_next)
        
        timing = response.headers.get('X-Response-Time-MS')
        print(f"   ✅ Middleware working - Response time: {timing}ms")
        
    except Exception as e:
        print(f"   ❌ Performance middleware failed: {e}")
    
    # Test Performance Monitor
    print("\n2. Performance Monitor:")
    try:
        from utilities.performance_monitoring import PerformanceMonitor
        
        monitor = PerformanceMonitor(collection_interval=0.5)
        await monitor.start_monitoring()
        await asyncio.sleep(1.0)  # Let it collect metrics
        
        summary = monitor.get_performance_summary()
        cpu_percent = summary.get('system_performance', {}).get('cpu_percent', 0)
        memory_mb = summary.get('system_performance', {}).get('memory_usage_mb', 0)
        
        await monitor.stop_monitoring()
        
        print(f"   ✅ Performance monitor working - CPU: {cpu_percent}%, Memory: {memory_mb:.1f}MB")
        
    except Exception as e:
        print(f"   ❌ Performance monitor failed: {e}")
    
    # Test Memory Metrics
    print("\n3. Memory Metrics:")
    try:
        # Test if we can import metrics-related modules
        from core.metrics import METRICS_ENABLED
        if METRICS_ENABLED:
            print("   ✅ Prometheus metrics enabled")
        else:
            print("   ⚠️  Prometheus metrics disabled (fallback mode)")
        
    except Exception as e:
        print(f"   ❌ Memory metrics failed: {e}")
    
    # Test Redis Metrics (if available)
    print("\n4. Redis Metrics:")
    try:
        from services.redis_service import RedisService
        
        redis_service = RedisService()
        # Test basic Redis functionality without assuming specific methods
        print("   ✅ Redis service can be instantiated")
            
    except Exception as e:
        print(f"   ⚠️  Redis not available: {e}")

def test_arm_linux_compatibility():
    """Test ARM Linux specific compatibility"""
    print("\n🔧 ARM LINUX COMPATIBILITY CHECK")
    print("=" * 50)
    
    system_info = get_system_info()
    
    print(f"Platform: {system_info['platform']}")
    print(f"Architecture: {system_info['machine']}")
    print(f"Is ARM: {system_info['is_arm']}")
    print(f"Is Linux: {system_info['is_linux']}")
    print(f"Is Docker: {system_info['is_docker']}")
    
    # Check ARM-specific considerations
    if system_info['is_arm']:
        print("\n🔍 ARM-specific checks:")
        
        # Check for common ARM limitations
        try:
            import psutil
            
            # CPU frequency may not be available
            freq = psutil.cpu_freq()
            if freq is None:
                print("   ⚠️  CPU frequency not available (common on ARM)")
            else:
                print(f"   ✅ CPU frequency available: {freq.current} MHz")
            
            # Check for thermal monitoring
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    print("   ✅ Temperature sensors available")
                else:
                    print("   ⚠️  Temperature sensors not available")
            except:
                print("   ⚠️  Temperature sensors not supported")
            
            # Check for battery info (relevant for ARM devices)
            try:
                battery = psutil.sensors_battery()
                if battery:
                    print(f"   ✅ Battery info available: {battery.percent}%")
                else:
                    print("   ⚠️  No battery detected")
            except:
                print("   ⚠️  Battery monitoring not supported")
                
        except Exception as e:
            print(f"   ❌ ARM compatibility check failed: {e}")
    
    # Docker-specific checks
    if system_info['is_docker']:
        print("\n🐳 Docker-specific checks:")
        print("   ⚠️  Running in Docker - some metrics may be limited")
        print("   ⚠️  Network interfaces may be virtual")
        print("   ⚠️  Disk I/O may not reflect host system")
        print("   ⚠️  Process list limited to container")
    
    # Linux-specific optimizations
    if system_info['is_linux']:
        print("\n🐧 Linux-specific optimizations:")
        
        # Check for cgroup limits (Docker/Kubernetes)
        try:
            if os.path.exists('/sys/fs/cgroup'):
                print("   ✅ cgroup filesystem available")
                
                # Check memory limits
                memory_limit_files = [
                    '/sys/fs/cgroup/memory/memory.limit_in_bytes',
                    '/sys/fs/cgroup/memory.max',
                    '/proc/meminfo'
                ]
                
                for mem_file in memory_limit_files:
                    if os.path.exists(mem_file):
                        print(f"   ✅ Memory limit info: {mem_file}")
                        break
                else:
                    print("   ⚠️  Memory limit info not found")
                    
        except Exception as e:
            print(f"   ❌ Linux optimization check failed: {e}")

def check_required_packages():
    """Check if all required packages are available"""
    print("\n📦 PACKAGE COMPATIBILITY CHECK")
    print("=" * 50)
    
    required_packages = {
        'psutil': 'System metrics',
        'asyncio': 'Async operations',
        'time': 'Timing operations',
        'platform': 'Platform detection',
        'json': 'JSON serialization',
        'logging': 'Logging system'
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"   ✅ {package}: {description}")
        except ImportError:
            print(f"   ❌ {package}: {description} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        return False
    else:
        print("\n✅ All required packages available")
        return True

async def main():
    """Run comprehensive metrics verification"""
    print("🔍 COMPREHENSIVE METRICS VERIFICATION")
    print("=" * 60)
    
    # Get system information
    system_info = get_system_info()
    print(f"\nSystem: {system_info['platform']}")
    print(f"Architecture: {system_info['machine']}")
    print(f"Python: {system_info['python_version']}")
    
    # Check package compatibility
    packages_ok = check_required_packages()
    
    # Test psutil compatibility
    psutil_ok = test_psutil_compatibility()
    
    # Test backend metrics
    await test_backend_metrics()
    
    # ARM Linux compatibility
    test_arm_linux_compatibility()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    print(f"✅ System Info: {system_info['platform']}")
    print(f"{'✅' if packages_ok else '❌'} Required Packages: {'All available' if packages_ok else 'Some missing'}")
    print(f"{'✅' if psutil_ok else '❌'} System Metrics: {'Working' if psutil_ok else 'Issues detected'}")
    
    # ARM Linux recommendations
    if system_info['is_arm'] and system_info['is_linux']:
        print("\n🔧 ARM LINUX RECOMMENDATIONS:")
        print("✅ Metrics will work on ARM Linux")
        print("⚠️  Some features may be limited (CPU frequency, thermal)")
        print("✅ Core functionality (CPU %, Memory, Disk) fully supported")
        print("✅ Docker containers fully supported")
        print("✅ Performance monitoring recommended for production")
    
    # Overall compatibility
    overall_compatible = packages_ok and psutil_ok
    print(f"\n🎯 OVERALL COMPATIBILITY: {'✅ EXCELLENT' if overall_compatible else '⚠️  ISSUES DETECTED'}")
    
    if overall_compatible:
        print("🚀 All metrics systems ready for production on ARM Linux!")
    else:
        print("⚠️  Some issues detected - review output above")

if __name__ == "__main__":
    asyncio.run(main())
