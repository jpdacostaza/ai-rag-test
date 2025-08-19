#!/usr/bin/env python3
"""
CPU Monitoring Test Script
Test the fixed CPU percentage monitoring
"""

import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("❌ psutil not available - installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil
    PSUTIL_AVAILABLE = True

def test_cpu_monitoring():
    """Test different CPU monitoring approaches"""
    print("🔍 TESTING CPU MONITORING APPROACHES")
    print("=" * 50)
    
    if not PSUTIL_AVAILABLE:
        print("❌ psutil not available")
        return
    
    print("1. Testing psutil.cpu_percent() with different intervals:")
    
    # Test 1: First call (should return 0.0)
    print("   First call (baseline):", end=" ")
    cpu1 = psutil.cpu_percent(interval=None)
    print(f"{cpu1}% (expected: 0.0)")
    
    # Test 2: Immediate second call (should still be 0.0)
    print("   Immediate second call:", end=" ")
    cpu2 = psutil.cpu_percent(interval=None)
    print(f"{cpu2}% (expected: 0.0)")
    
    # Test 3: Call with small interval (should give actual reading)
    print("   With 0.1s interval:", end=" ")
    cpu3 = psutil.cpu_percent(interval=0.1)
    print(f"{cpu3}% (expected: > 0.0)")
    
    # Test 4: Non-blocking call after interval (should give actual reading)
    print("   Non-blocking after interval:", end=" ")
    cpu4 = psutil.cpu_percent(interval=None)
    print(f"{cpu4}% (expected: > 0.0)")
    
    print("\n2. Testing process-specific CPU monitoring:")
    
    try:
        process = psutil.Process()
        
        # Test 5: Process CPU first call
        print("   Process CPU first call:", end=" ")
        proc_cpu1 = process.cpu_percent()
        print(f"{proc_cpu1}% (expected: 0.0)")
        
        # Simulate some work
        print("   Simulating work for 0.5 seconds...")
        start_time = time.time()
        while time.time() - start_time < 0.5:
            # Simple CPU work
            sum(range(1000))
        
        # Test 6: Process CPU after work
        print("   Process CPU after work:", end=" ")
        proc_cpu2 = process.cpu_percent()
        print(f"{proc_cpu2}% (expected: > 0.0)")
        
    except Exception as e:
        print(f"   ❌ Process monitoring failed: {e}")
    
    print("\n3. Testing recommended approach:")
    
    # Recommended approach: Initialize first, then use interval or subsequent calls
    try:
        # Initialize
        psutil.cpu_percent(interval=None)
        print("   Initialized CPU monitoring baseline")
        
        # Wait a moment
        time.sleep(0.2)
        
        # Get reading
        cpu_reading = psutil.cpu_percent(interval=0.1)
        print(f"   CPU usage reading: {cpu_reading}%")
        
        # Subsequent non-blocking call
        cpu_reading2 = psutil.cpu_percent(interval=None)
        print(f"   Non-blocking follow-up: {cpu_reading2}%")
        
    except Exception as e:
        print(f"   ❌ Recommended approach failed: {e}")
    
    print("\n4. Testing memory monitoring (for comparison):")
    
    try:
        memory = psutil.virtual_memory()
        print(f"   Memory usage: {memory.percent}% ({memory.used / (1024**3):.1f} GB used)")
        
        process = psutil.Process()
        proc_memory = process.memory_info()
        print(f"   Process memory: {proc_memory.rss / (1024**2):.1f} MB RSS")
        
    except Exception as e:
        print(f"   ❌ Memory monitoring failed: {e}")

def test_middleware_scenario():
    """Test the middleware CPU monitoring scenario"""
    print("\n🔧 TESTING MIDDLEWARE SCENARIO")
    print("=" * 50)
    
    try:
        process = psutil.Process()
        
        # Simulate middleware initialization
        print("1. Middleware initialization:")
        process.cpu_percent()  # Baseline call
        print("   ✅ CPU baseline established")
        
        # Simulate request processing
        print("\n2. Simulating request processing:")
        
        # Start of request
        print("   Request start - CPU measurement:", end=" ")
        start_cpu = process.cpu_percent()
        print(f"{start_cpu}%")
        
        # Simulate request work
        print("   Processing request (0.3s work)...")
        start_time = time.time()
        while time.time() - start_time < 0.3:
            # Simulate request processing work
            [i**2 for i in range(1000)]
        
        # End of request
        print("   Request end - CPU measurement:", end=" ")
        end_cpu = process.cpu_percent()
        print(f"{end_cpu}%")
        
        # Fallback to system CPU if needed
        if end_cpu == 0.0:
            print("   Process CPU is 0.0, trying system CPU:", end=" ")
            sys_cpu = psutil.cpu_percent(interval=None)
            print(f"{sys_cpu}%")
        
    except Exception as e:
        print(f"❌ Middleware scenario test failed: {e}")

if __name__ == "__main__":
    test_cpu_monitoring()
    test_middleware_scenario()
    
    print("\n" + "=" * 50)
    print("✅ CPU MONITORING TEST COMPLETE")
    print("\nKey findings:")
    print("• First psutil.cpu_percent() call always returns 0.0")
    print("• Use interval parameter for accurate readings")
    print("• Process CPU needs baseline + interval or work between calls")
    print("• System CPU with interval=0.1 is most reliable")
    print("• Non-blocking calls work after interval-based calls")
