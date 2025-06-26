#!/usr/bin/env python3
"""
Comprehensive validation script for alert manager integration.
Tests cache monitoring, memory pressure alerts, and service downtime detection.
"""

import asyncio
import sys
import os
import time
from typing import Dict, Any

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from utilities.alert_manager import get_alert_manager, AlertSeverity, alert_cache_performance, alert_memory_pressure, alert_service_down
from utilities.cache_manager import CacheManager
from database_manager import initialize_database, get_database_health
from human_logging import log_service_status, init_logging

async def test_alert_manager_basic():
    """Test basic alert manager functionality."""
    print("🧪 Testing Alert Manager Basic Functionality...")
    
    try:
        alert_manager = get_alert_manager()
        
        # Test alert creation
        test_alert = await alert_manager.trigger_alert(
            alert_id="test_alert_001",
            title="Test Alert",
            message="This is a test alert to validate the system",
            severity=AlertSeverity.LOW,
            component="validation_script"
        )
        
        print(f"✅ Successfully created test alert: {test_alert.alert_id}")
        
        # Test alert statistics
        stats = alert_manager.get_alert_stats()
        print(f"📊 Alert statistics: {stats}")
        
        # Test alert resolution
        resolved = await alert_manager.resolve_alert("test_alert_001", "Test completed successfully")
        print(f"✅ Alert resolution: {'Success' if resolved else 'Failed'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Alert manager basic test failed: {e}")
        return False

async def test_cache_performance_monitoring():
    """Test cache performance monitoring and alerting."""
    print("\n🧪 Testing Cache Performance Monitoring...")
    
    try:
        # Create a cache manager with low alert threshold for testing
        cache = CacheManager[str](max_size=100, alert_threshold=80.0)
        
        # Simulate cache operations with poor hit rate
        print("📊 Simulating cache operations with poor hit rate...")
        
        for i in range(60):  # Generate enough requests to trigger monitoring
            if i % 10 == 0:  # Only 10% cache hits
                cache.set(f"key_{i}", f"value_{i}")
                cache.get(f"key_{i}")  # Hit
            else:
                cache.get(f"non_existent_key_{i}")  # Miss
        
        # Check cache stats
        stats = cache.get_stats()
        print(f"📈 Cache statistics: {stats}")
        
        # Manually trigger cache alert for testing
        hit_rate = stats['hit_rate_numeric']
        await alert_cache_performance(hit_rate, "test_cache")
        
        print(f"✅ Cache performance monitoring test completed (hit rate: {hit_rate:.1f}%)")
        return True
        
    except Exception as e:
        print(f"❌ Cache performance monitoring test failed: {e}")
        return False

async def test_memory_pressure_alerts():
    """Test memory pressure alerting."""
    print("\n🧪 Testing Memory Pressure Alerts...")
    
    try:
        # Test different severity levels
        test_scenarios = [
            (50.0, "low_pressure"),
            (80.0, "medium_pressure"),
            (90.0, "high_pressure"),
            (96.0, "critical_pressure")
        ]
        
        for memory_percentage, scenario in test_scenarios:
            await alert_memory_pressure(memory_percentage, f"test_component_{scenario}")
            print(f"📊 Triggered memory alert for {memory_percentage}% usage")
            
        print("✅ Memory pressure alert test completed")
        return True
        
    except Exception as e:
        print(f"❌ Memory pressure alert test failed: {e}")
        return False

async def test_service_downtime_alerts():
    """Test service downtime alerting."""
    print("\n🧪 Testing Service Downtime Alerts...")
    
    try:
        # Test different downtime durations
        test_scenarios = [
            (30.0, "short_outage"),
            (180.0, "medium_outage"),
            (600.0, "long_outage"),
            (1800.0, "critical_outage")
        ]
        
        for duration, scenario in test_scenarios:
            await alert_service_down(f"test_service_{scenario}", duration)
            print(f"🚨 Triggered service downtime alert for {duration} seconds")
            
        print("✅ Service downtime alert test completed")
        return True
        
    except Exception as e:
        print(f"❌ Service downtime alert test failed: {e}")
        return False

async def test_health_endpoint_integration():
    """Test health endpoint integration with alert statistics."""
    print("\n🧪 Testing Health Endpoint Integration...")
    
    try:
        # Initialize database for health endpoint
        await initialize_database()
        
        # Get health status including alert statistics
        health_status = await get_database_health()
        
        print("📊 Health Status:")
        for component, status in health_status.items():
            if isinstance(status, dict):
                component_status = status.get('status', 'unknown')
                print(f"  {component}: {component_status}")
                if 'stats' in status:
                    print(f"    Stats: {status['stats']}")
            else:
                print(f"  {component}: {status}")
        
        # Check if alerts component is included
        if 'alerts' in health_status:
            print("✅ Alert manager successfully integrated into health endpoint")
            return True
        else:
            print("❌ Alert manager not found in health endpoint")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint integration test failed: {e}")
        return False

async def test_alert_notification_channels():
    """Test different notification channels."""
    print("\n🧪 Testing Alert Notification Channels...")
    
    try:
        alert_manager = get_alert_manager()
        
        # Test different severity levels to trigger different channels
        test_alerts = [
            ("low_severity_test", AlertSeverity.LOW, "Low severity alert test"),
            ("medium_severity_test", AlertSeverity.MEDIUM, "Medium severity alert test"),
            ("high_severity_test", AlertSeverity.HIGH, "High severity alert test"),
            ("critical_severity_test", AlertSeverity.CRITICAL, "Critical severity alert test")
        ]
        
        for alert_id, severity, message in test_alerts:
            await alert_manager.trigger_alert(
                alert_id=alert_id,
                title=f"Test Alert - {severity.value.upper()}",
                message=message,
                severity=severity,
                component="notification_test"
            )
            print(f"📡 Triggered {severity.value} severity alert")
            await asyncio.sleep(0.1)  # Small delay between alerts
            
        print("✅ Notification channels test completed")
        return True
        
    except Exception as e:
        print(f"❌ Notification channels test failed: {e}")
        return False

async def generate_final_report():
    """Generate a final validation report."""
    print("\n📋 Generating Final Validation Report...")
    
    try:
        alert_manager = get_alert_manager()
        
        # Get comprehensive statistics
        stats = alert_manager.get_alert_stats()
        active_alerts = alert_manager.get_active_alerts()
        alert_history = alert_manager.get_alert_history(hours=24)
        
        print("=" * 60)
        print("🏁 ALERT SYSTEM VALIDATION REPORT")
        print("=" * 60)
        print(f"📊 Total Alerts Triggered: {stats['total_alerts']}")
        print(f"📊 Active Alerts: {stats['active_alerts']}")
        print(f"📊 Resolved Alerts: {stats['resolved_alerts']}")
        print(f"📊 Average Resolution Time: {stats['avg_resolution_time']}")
        print(f"📊 Alerts by Severity: {stats['alerts_by_severity']}")
        print(f"📊 Alerts by Component: {stats['alerts_by_component']}")
        
        print(f"\n🔥 Active Alerts ({len(active_alerts)}):")
        for alert in active_alerts:
            print(f"  - {alert.alert_id}: {alert.title} ({alert.severity.value})")
            
        print(f"\n📚 Recent Alert History ({len(alert_history)} alerts in last 24h):")
        for alert in alert_history[-5:]:  # Show last 5 alerts
            status = "RESOLVED" if alert.resolved else "ACTIVE"
            print(f"  - {alert.timestamp.strftime('%H:%M:%S')}: {alert.title} [{status}]")
        
        print("\n✅ Alert system validation completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Final report generation failed: {e}")
        return False

async def main():
    """Run comprehensive validation tests."""
    print("🚀 Starting Alert Manager Integration Validation")
    print("=" * 60)
    
    # Initialize logging
    init_logging("INFO")
    
    # Run all tests
    test_results = []
    
    tests = [
        ("Alert Manager Basic", test_alert_manager_basic),
        ("Cache Performance Monitoring", test_cache_performance_monitoring),
        ("Memory Pressure Alerts", test_memory_pressure_alerts),
        ("Service Downtime Alerts", test_service_downtime_alerts),
        ("Health Endpoint Integration", test_health_endpoint_integration),
        ("Notification Channels", test_alert_notification_channels)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            test_results.append((test_name, False))
            print(f"❌ {test_name}: ERROR - {e}")
        
        # Small delay between tests
        await asyncio.sleep(0.5)
    
    # Generate final report
    await generate_final_report()
    
    # Summary
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    print(f"\n🏁 VALIDATION SUMMARY: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Alert system is fully integrated and functional.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        sys.exit(1)
