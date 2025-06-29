#!/usr/bin/env python3
"""
Pipeline Debug Tool
==================

A simple tool to test and debug pipeline connectivity between OpenWebUI and the pipelines server.
"""

import requests
import json
import sys

# Configuration
PIPELINES_URL = "http://localhost:9098"
PIPELINES_API_KEY = "0p3n-w3bu!"

def test_endpoint(endpoint, use_auth=True):
    """Test a pipeline endpoint."""
    url = f"{PIPELINES_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if use_auth:
        headers["Authorization"] = f"Bearer {PIPELINES_API_KEY}"
    
    try:
        print(f"\n🔍 Testing: {url}")
        print(f"   Auth: {'Yes' if use_auth else 'No'}")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   Error: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"   Exception: {e}")
        return False

def main():
    """Test all pipeline endpoints."""
    print("🧪 Pipeline Connectivity Test")
    print("=" * 40)
    
    # Test various endpoints that OpenWebUI might use
    endpoints = [
        "/",
        "/v1/pipelines",
        "/pipelines",
        "/api/v1/pipelines",
        "/api/v1/pipelines/list", 
        "/api/pipelines",
    ]
    
    for endpoint in endpoints:
        # Test without auth
        success_no_auth = test_endpoint(endpoint, use_auth=False)
        
        # Test with auth
        success_with_auth = test_endpoint(endpoint, use_auth=True)
        
        if success_with_auth:
            print(f"   ✅ {endpoint} works with auth")
        elif success_no_auth:
            print(f"   ⚠️  {endpoint} works without auth")
        else:
            print(f"   ❌ {endpoint} doesn't work")

if __name__ == "__main__":
    main()
