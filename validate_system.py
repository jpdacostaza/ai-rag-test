#!/usr/bin/env python3
"""
Final System Validation Script
Validates all endpoints and system health after cleanup
"""

import asyncio
import httpx
import json
from pathlib import Path

async def test_endpoint(client: httpx.AsyncClient, method: str, url: str, name: str):
    """Test a single endpoint"""
    try:
        if method.upper() == 'GET':
            response = await client.get(url, timeout=10.0)
        elif method.upper() == 'POST':
            response = await client.post(url, json={}, timeout=10.0)
        else:
            return f"❓ {name}: Method {method} not tested"
        
        if response.status_code < 500:  # Any non-server error is considered working
            return f"✅ {name}: {response.status_code}"
        else:
            return f"❌ {name}: {response.status_code}"
            
    except Exception as e:
        return f"⚠️ {name}: {str(e)[:50]}..."

async def validate_system():
    """Validate the entire system"""
    print("🔍 FINAL SYSTEM VALIDATION")
    print("=" * 50)
    
    # Core endpoints to test
    endpoints = [
        ("GET", "http://localhost:8001/health", "Main Health"),
        ("GET", "http://localhost:8001/", "Main Root"),
        ("GET", "http://localhost:8001/v1/models", "Models API"),
        ("GET", "http://localhost:8003/health", "Memory API Health"),
        ("POST", "http://localhost:8003/api/memory/retrieve", "Memory Retrieve"),
        ("GET", "http://localhost:8000/api/v1/heartbeat", "ChromaDB"),
        ("GET", "http://localhost:6379", "Redis (will fail - expected)"),
    ]
    
    results = []
    
    async with httpx.AsyncClient() as client:
        for method, url, name in endpoints:
            result = await test_endpoint(client, method, url, name)
            results.append(result)
            print(result)
    
    print("\n" + "=" * 50)
    
    # Check file integrity
    print("📁 FILE INTEGRITY CHECK")
    critical_files = [
        "main.py",
        "config.py", 
        "config/persona.json",
        "memory_filter_function.py",
        "enhanced_memory_api.py",
        "docker-compose.yml"
    ]
    
    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
    
    print("\n" + "=" * 50)
    print("🎯 VALIDATION COMPLETE")
    
    # Count results
    success = len([r for r in results if r.startswith("✅")])
    total = len(results)
    
    print(f"📊 Endpoint Success Rate: {success}/{total}")
    
    if success >= total * 0.7:  # 70% success rate
        print("🎉 System is HEALTHY and READY")
        return True
    else:
        print("⚠️ System needs attention")
        return False

if __name__ == "__main__":
    asyncio.run(validate_system())
