#!/usr/bin/env python3
"""
Additional Edge Case Tests for Backend API
"""
import requests
import json
from datetime import datetime

def main():
    print('🔬 EDGE CASE AND STRESS TESTING')
    print('=' * 60)
    print(f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    base_url = 'http://localhost:8001'
    test_results = []

    def run_test(name, method, endpoint, data=None, expected_status=200, description=''):
        try:
            print(f'🧪 {name}')
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
            elif response.status_code == 400:
                try:
                    json_resp = response.json()
                    error_msg = json_resp.get('error', {}).get('message', 'Unknown error')
                    print(f'   Response: Error - {error_msg}')
                except:
                    print(f'   Response: {response.text[:100]}')
            elif response.status_code == 200:
                try:
                    json_resp = response.json()
                    print(f'   Response: Success - {len(str(json_resp))} chars')
                except:
                    print(f'   Response: Success - {len(response.text)} chars')
            
            test_results.append({
                'name': name,
                'status': response.status_code,
                'expected': expected_status,
                'success': success
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

    print('🔍 EDGE CASE TESTS')
    print()    # 1. Empty model name
    run_test(
        'Empty Model Name', 
        'POST', 
        '/v1/chat/completions',
        {
            'model': '',
            'messages': [{'role': 'user', 'content': 'Hello'}]
        },
        400,
        description='Should reject empty model name'
    )

    # 2. Null model field
    run_test(
        'Null Model Field', 
        'POST', 
        '/v1/chat/completions',
        {
            'model': None,
            'messages': [{'role': 'user', 'content': 'Hello'}]
        },
        400,
        description='Should reject null model value'
    )    # 3. Empty messages array
    run_test(
        'Empty Messages Array', 
        'POST', 
        '/v1/chat/completions',
        {
            'model': 'llama3.2:3b',
            'messages': []
        },
        400,
        description='Should reject empty messages array'
    )    # 4. Invalid message format
    run_test(
        'Invalid Message Format', 
        'POST', 
        '/v1/chat/completions',
        {
            'model': 'llama3.2:3b',
            'messages': ['invalid_format']
        },
        description='Should handle invalid message format gracefully'
    )    # 5. Very long content
    long_content = 'A' * 10000  # 10K characters
    run_test(
        'Very Long Content', 
        'POST', 
        '/v1/chat/completions',
        {
            'model': 'llama3.2:3b',
            'messages': [{'role': 'user', 'content': long_content}]
        },
        description='Should handle very long content'
    )    # 6. Special characters in content
    run_test(
        'Special Characters', 
        'POST', 
        '/v1/chat/completions',
        {
            'model': 'llama3.2:3b',
            'messages': [{'role': 'user', 'content': '🚀💻🔥 Test with emojis and special chars: <>&"\''}]
        },
        description='Should handle special characters and emojis'
    )

    # 7. Invalid HTTP method
    run_test(
        'Invalid HTTP Method', 
        'GET', 
        '/v1/chat/completions',
        expected_status=405,
        description='Should return 405 for wrong HTTP method'
    )    # 8. Large JSON payload
    large_messages = [{'role': 'user', 'content': f'Message {i}: ' + 'X' * 100} for i in range(50)]
    run_test(
        'Large JSON Payload', 
        'POST', 
        '/v1/chat/completions',
        {
            'model': 'llama3.2:3b',
            'messages': large_messages
        },
        description='Should handle large JSON payloads'
    )

    # Generate Summary
    print('=' * 60)
    print('📊 EDGE CASE TEST SUMMARY')
    print('=' * 60)

    passed = sum(1 for r in test_results if r['success'])
    total = len(test_results)
    success_rate = (passed / total * 100) if total > 0 else 0

    print(f'Total Edge Case Tests: {total}')
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
    print('🎯 EDGE CASE FINDINGS:')
    validation_tests = [r for r in test_results if r['expected'] == 400]
    validation_working = all(r['success'] for r in validation_tests)
    
    print(f'   • Input validation: {"✅" if validation_working else "❌"} Handling edge cases properly')
    print(f'   • Error responses: {"✅" if validation_working else "❌"} Returning appropriate error codes')
    print(f'   • Robustness: {"✅" if success_rate >= 75 else "❌"} {success_rate:.0f}% success rate')
    
    if success_rate >= 75:
        print()
        print('🛡️  ROBUSTNESS STATUS: EXCELLENT')
        print('   The backend handles edge cases and stress scenarios well.')
    else:
        print()
        print('⚠️  ROBUSTNESS STATUS: NEEDS IMPROVEMENT')
        print('   Some edge cases may need additional handling.')

if __name__ == '__main__':
    main()
