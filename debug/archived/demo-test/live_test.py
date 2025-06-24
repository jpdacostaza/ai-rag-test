#!/usr/bin/env python3
"""
Comprehensive Live System Test for Backend API
"""
import requests
import json
from datetime import datetime

def main():
    print('🧪 COMPREHENSIVE LIVE SYSTEM TEST')
    print('=' * 60)
    print(f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    base_url = 'http://localhost:8001'
    test_results = []

    def run_test(name, method, endpoint, data=None, expected_status=200, description=''):
        try:
            print(f'📝 {name}')
            if description:
                print(f'   {description}')
            
            headers = {'Content-Type': 'application/json'}
            
            if method == 'GET':
                response = requests.get(f'{base_url}{endpoint}', headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(f'{base_url}{endpoint}', json=data, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            status_icon = '✅' if success else '❌'
            
            print(f'   Status: {response.status_code} (expected {expected_status}) {status_icon}')
            
            if not success:
                print(f'   Response: {response.text[:150]}...')
            elif response.status_code == 200 and len(response.text) > 0:
                try:
                    json_resp = response.json()
                    if 'error' in json_resp:
                        print(f'   Response: Error - {json_resp["error"].get("message", "Unknown error")}')
                    else:
                        preview_keys = list(json_resp.keys())[:3] if isinstance(json_resp, dict) else str(json_resp)[:50]
                        print(f'   Response: Success - {preview_keys}')
                except:
                    print(f'   Response: {response.text[:50]}...')
            elif response.status_code == 400:
                try:
                    json_resp = response.json()
                    error_msg = json_resp.get('error', {}).get('message', 'Unknown error')
                    print(f'   Response: Error - {error_msg}')
                except:
                    print(f'   Response: {response.text[:100]}')
            
            test_results.append({
                'name': name,
                'status': response.status_code,
                'expected': expected_status,
                'success': success,
                'response_size': len(response.text)
            })
            
            print()
            return response, success
            
        except Exception as e:
            print(f'   ERROR: {str(e)} ❌')
            test_results.append({
                'name': name,
                'status': 'ERROR',
                'expected': expected_status,
                'success': False,
                'error': str(e)
            })
            print()
            return None, False

    # Test Suite
    print('🔍 STARTING TEST SUITE')
    print()

    # 1. Health Check
    run_test(
        'Health Check', 
        'GET', 
        '/health',
        description='Basic service health verification'
    )

    # 2. Valid Chat Completion
    run_test(
        'Valid Chat Completion', 
        'POST', 
        '/v1/chat/completions',
        {
            'model': 'test-model',
            'messages': [{'role': 'user', 'content': 'Hello, this is a test message.'}],
            'temperature': 0.7,
            'max_tokens': 100
        },
        description='Standard chat completion with all required fields'
    )

    # 3. Missing Model Field
    run_test(
        'Missing Model Field', 
        'POST', 
        '/v1/chat/completions',
        {
            'messages': [{'role': 'user', 'content': 'Hello'}]
        },
        400,
        description='Should return 400 when model field is missing'
    )

    # 4. Missing Messages Field
    run_test(
        'Missing Messages Field', 
        'POST', 
        '/v1/chat/completions',
        {
            'model': 'test-model'
        },
        400,
        description='Should return 400 when messages field is missing'
    )

    # 5. Empty Request Body
    run_test(
        'Empty Request Body', 
        'POST', 
        '/v1/chat/completions',
        {},
        400,
        description='Should return 400 when request body is empty'
    )

    # 6. Models Endpoint
    run_test(
        'Models List', 
        'GET', 
        '/v1/models',
        description='List available models'
    )    # 7. Upload Formats Endpoint
    run_test(
        'Upload Formats Endpoint', 
        'GET', 
        '/upload/formats',
        description='Get supported upload formats'
    )

    # 8. Invalid Endpoint (404 test)
    run_test(
        'Invalid Endpoint', 
        'GET', 
        '/invalid/endpoint',
        expected_status=404,
        description='Should return 404 for non-existent endpoints'
    )

    # Generate Summary
    print('=' * 60)
    print('📊 TEST SUMMARY')
    print('=' * 60)

    passed = sum(1 for r in test_results if r['success'])
    total = len(test_results)
    success_rate = (passed / total * 100) if total > 0 else 0

    print(f'Total Tests: {total}')
    print(f'Passed: {passed}')
    print(f'Failed: {total - passed}')
    print(f'Success Rate: {success_rate:.1f}%')
    print()

    if passed < total:
        print('❌ FAILED TESTS:')
        for r in test_results:
            if not r['success']:
                error_info = r.get('error', f'Status {r["status"]} (expected {r["expected"]})')
                print(f'   • {r["name"]}: {error_info}')
        print()

    print('✅ PASSED TESTS:')
    for r in test_results:
        if r['success']:
            print(f'   • {r["name"]} - Status {r["status"]}')

    print()
    print('🎯 KEY FINDINGS:')
    error_handling_tests = [r for r in test_results if r['expected'] == 400]
    error_handling_working = all(r['success'] for r in error_handling_tests)
    health_tests = [r for r in test_results if 'Health' in r['name']]
    health_working = all(r['success'] for r in health_tests)
    
    print(f'   • Error handling validation: {"✅" if error_handling_working else "❌"} Working correctly')
    print(f'   • Required field validation: {"✅" if error_handling_working else "❌"} Returns proper 400 errors')
    print(f'   • Health endpoints: {"✅" if health_working else "❌"} Responding normally')
    print(f'   • Overall system health: {"✅" if success_rate >= 85 else "❌"} {success_rate:.0f}% success rate')
    
    if success_rate >= 85:
        print()
        print('🎉 SYSTEM STATUS: HEALTHY')
        print('   The backend is functioning correctly with proper error handling.')
    else:
        print()
        print('⚠️  SYSTEM STATUS: NEEDS ATTENTION')
        print('   Some tests failed. Review the failed tests above.')

if __name__ == '__main__':
    main()
