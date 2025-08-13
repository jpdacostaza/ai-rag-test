#!/usr/bin/env python3
"""
Comprehensive Web Search Testing Script
Tests various query types and analyzes performance metrics
"""

import importlib.util
import asyncio
import time
import sys
import os

# Add the backend path to sys.path for imports
sys.path.insert(0, '/app/backend/data')

async def comprehensive_test():
    # Load the web search tool
    spec = importlib.util.spec_from_file_location('web_search_tool', '/app/backend/data/tools/web_search_tool.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    action = module.Action()
    
    test_queries = [
        ('News Query', 'latest AI breakthroughs August 2025'),
        ('Technical Query', 'Python 3.12 new features performance benchmarks'),
        ('Date-Specific', 'OpenAI announcements August 13 2025'),
        ('Product Query', 'iPhone 16 release date specifications'),
        ('Academic Query', 'machine learning research papers 2025'),
        ('Local Query', 'weather forecast New York today'),
        ('Stock/Finance', 'NVIDIA stock price August 2025'),
        ('Health Query', 'COVID vaccines 2025 updates')
    ]
    
    print('=== COMPREHENSIVE QUERY TYPE TESTING ===')
    print(f'Date: August 13, 2025')
    print(f'Testing {len(test_queries)} different query types')
    print('='*50)
    
    total_success = 0
    total_time = 0
    performance_metrics = []
    
    for query_type, query in test_queries:
        print(f'\n[{query_type}] Testing: "{query}"')
        start_time = time.time()
        
        try:
            result = await action.run(query=query, max_results=3)
            elapsed = time.time() - start_time
            total_time += elapsed
            total_success += 1
            
            print(f'✅ Success - {len(result)} chars in {elapsed:.2f}s')
            
            # Extract key metrics
            lines = result.split('\n')
            results_count = 0
            dates_found = 0
            snippets_found = 0
            
            for line in lines:
                if line.startswith('**') and '. ' in line:
                    results_count += 1
                elif 'Date:' in line and line.strip() != 'Date:':
                    dates_found += 1
                elif 'Content:' in line and 'No preview available' not in line:
                    snippets_found += 1
            
            print(f'   📊 Results: {results_count}, Dates: {dates_found}, Snippets: {snippets_found}')
            
            performance_metrics.append({
                'type': query_type,
                'query': query,
                'time': elapsed,
                'chars': len(result),
                'results': results_count,
                'dates': dates_found,
                'snippets': snippets_found
            })
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f'❌ Error in {elapsed:.2f}s: {e}')
        
        await asyncio.sleep(1)  # Rate limiting
    
    # Summary statistics
    print('\n' + '='*50)
    print('📈 PERFORMANCE SUMMARY')
    print('='*50)
    print(f'Success Rate: {total_success}/{len(test_queries)} ({total_success/len(test_queries)*100:.1f}%)')
    print(f'Average Response Time: {total_time/total_success:.2f}s')
    
    if performance_metrics:
        avg_results = sum(m['results'] for m in performance_metrics) / len(performance_metrics)
        avg_dates = sum(m['dates'] for m in performance_metrics) / len(performance_metrics)
        avg_snippets = sum(m['snippets'] for m in performance_metrics) / len(performance_metrics)
        avg_chars = sum(m['chars'] for m in performance_metrics) / len(performance_metrics)
        
        print(f'Average Results per Query: {avg_results:.1f}')
        print(f'Average Dates Found: {avg_dates:.1f}')
        print(f'Average Snippets Found: {avg_snippets:.1f}')
        print(f'Average Response Length: {avg_chars:.0f} characters')
        
        # Identify best and worst performers
        fastest = min(performance_metrics, key=lambda x: x['time'])
        slowest = max(performance_metrics, key=lambda x: x['time'])
        
        print(f'\n🚀 Fastest Query: {fastest["type"]} ({fastest["time"]:.2f}s)')
        print(f'🐌 Slowest Query: {slowest["type"]} ({slowest["time"]:.2f}s)')

if __name__ == "__main__":
    asyncio.run(comprehensive_test())
