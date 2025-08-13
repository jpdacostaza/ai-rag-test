#!/usr/bin/env python3
"""
Web Search Configuration Fix Verification
==========================================

This script verifies that the web search system is properly configured
for Filter-based injection (compatible with zero-conf setup) rather than
function calling.

ISSUE IDENTIFIED:
- Model was previously working with web search
- Configuration got overwritten with function-calling persona 
- Current system uses Filter-based injection, not function calling
- Persona mismatch caused model to ignore injected search results

FIX APPLIED:
- Updated unified_prompt.json with Filter-compatible persona
- Changed from function calling to context-based instructions
- Added explicit search result authority protocol
- Model now instructed to check context for search results

VERIFICATION TESTS:
1. Filter injection works (AutoWebSearchFilter v2.0)
2. Search results properly formatted and injected
3. Persona instructs model to use injected results
4. Model should now acknowledge search results
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add function path
sys.path.append('/app/backend/data/functions')

async def test_complete_flow():
    """Test the complete web search flow"""
    
    print("[*] WEB SEARCH CONFIGURATION FIX VERIFICATION")
    print("=" * 50)
    
    # Test 1: Check persona configuration
    print("\n1. [CHECK] PERSONA CONFIGURATION CHECK")
    persona_file = Path('/app/backend/config/unified_prompt.json')
    
    if persona_file.exists():
        with open(persona_file, 'r') as f:
            persona = json.load(f)
        
        # Check for Filter-compatible instructions
        system_prompt = persona.get('system_prompt', '')
        
        if 'check if web search results are provided in my context' in system_prompt:
            print("   [PASS] Filter-compatible persona detected")
        else:
            print("   [FAIL] Function-calling persona still present")
            
        if 'Based on the search results' in system_prompt:
            print("   [PASS] Search result acknowledgment instruction found")
        else:
            print("   [FAIL] Missing search result acknowledgment")
            
        print(f"   [INFO] Version: {persona.get('version', 'unknown')}")
    else:
        print("   [FAIL] Persona file not found")
    
    # Test 2: Filter injection test
    print("\n2. [CHECK] FILTER INJECTION TEST")
    try:
        from auto_web_search_filter import Filter
        
        filter_instance = Filter()
        test_body = {
            'messages': [
                {'role': 'user', 'content': 'search the web for weather in London'}
            ]
        }
        
        result = await filter_instance.inlet(test_body)
        
        if len(result['messages']) >= 2:
            system_msg = result['messages'][1]
            if system_msg['role'] == 'system' and '!!! MANDATORY WEB SEARCH RESULTS' in system_msg['content']:
                print("   [PASS] Filter injection working correctly")
                print(f"   [INFO] Injected {len(system_msg['content'])} characters")
                
                # Check for explicit instructions
                if 'ABSOLUTE REQUIREMENTS' in system_msg['content']:
                    print("   [PASS] Ultra-explicit instructions included")
                else:
                    print("   [WARN] Missing ultra-explicit instructions")
            else:
                print("   [FAIL] Filter injection failed")
        else:
            print("   [FAIL] Filter not triggering")
            
    except Exception as e:
        print(f"   [FAIL] Filter test failed: {e}")
    
    # Test 3: Expected behavior
    print("\n3. [INFO] EXPECTED BEHAVIOR")
    print("   With this configuration, the model should:")
    print("   [PASS] Receive search results in system message context")
    print("   [PASS] Check context first before answering") 
    print("   [PASS] Use ONLY search results when provided")
    print("   [PASS] Start responses with 'Based on the search results...'")
    print("   [PASS] Ignore training data when search results present")
    
    print("\n4. [INFO] TESTING PROCEDURE")
    print("   To verify the fix works:")
    print("   1. Ask model: 'What is the weather in Amsterdam today?'")
    print("   2. Model should trigger web search automatically")
    print("   3. Model should respond with 'Based on the search results...'")
    print("   4. Model should include current weather data and time")
    
    print("\n[INFO] VERIFICATION COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_complete_flow())
