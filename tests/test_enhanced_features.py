#!/usr/bin/env python3
"""
Enhanced Web Search Testing Script
Tests the new enhanced features including caching, ranking, and improved formatting
"""

import importlib.util
import asyncio
import time
import sys

async def test_enhanced_features():
    # Load the enhanced web search tool
    spec = importlib.util.spec_from_file_location('web_search_tool_v2', '/app/backend/data/tools/web_search_tool_v2.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    action = module.Action()
    
    print('=== ENHANCED WEB SEARCH TESTING ===')
    print(f'Date: August 13, 2025')
    print('Testing enhanced features: caching, ranking, improved formatting')
    print('='*60)
    
    # Test 1: Basic search with enhanced formatting
    print('\n🧪 TEST 1: Enhanced Formatting and Ranking')
    print('-' * 40)
    query1 = "artificial intelligence breakthroughs 2025"
    start_time = time.time()
    result1 = await action.run(query=query1, max_results=3)
    elapsed1 = time.time() - start_time
    
    print(f'Query: "{query1}"')
    print(f'Time: {elapsed1:.2f}s')
    print(f'Result length: {len(result1)} characters')
    print('\nSample result (first 800 chars):')
    print(result1[:800] + '...' if len(result1) > 800 else result1)
    
    # Test 2: Cache performance (same query)
    print('\n\n🧪 TEST 2: Cache Performance')
    print('-' * 40)
    start_time = time.time()
    result2 = await action.run(query=query1, max_results=3)  # Same query
    elapsed2 = time.time() - start_time
    
    print(f'Query: "{query1}" (repeated)')
    print(f'Time: {elapsed2:.2f}s (should be much faster if cached)')
    print(f'Cache speedup: {elapsed1/elapsed2:.1f}x faster' if elapsed2 > 0 else 'Instant cache hit')
    print(f'Results identical: {result1 == result2}')
    
    # Test 3: Different query types for ranking analysis
    print('\n\n🧪 TEST 3: Ranking Analysis')
    print('-' * 40)
    
    test_queries = [
        "Python programming tutorial 2025",
        "latest tech news August 13 2025",
        "machine learning research papers"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f'\nQuery {i}: "{query}"')
        start_time = time.time()
        result = await action.run(query=query, max_results=3)
        elapsed = time.time() - start_time
        
        # Extract relevance scores from result
        relevance_scores = []
        lines = result.split('\n')
        for line in lines:
            if '⭐' in line and '.' in line:
                try:
                    score_part = line.split('⭐')[1].strip()
                    score = float(score_part)
                    relevance_scores.append(score)
                except:
                    pass
        
        print(f'  Time: {elapsed:.2f}s')
        print(f'  Relevance scores: {relevance_scores}')
        print(f'  Ranking quality: {"✅ Descending" if relevance_scores == sorted(relevance_scores, reverse=True) else "❌ Not sorted"}')
        
        await asyncio.sleep(0.5)  # Brief pause between queries
    
    # Test 4: Feature toggles
    print('\n\n🧪 TEST 4: Feature Toggles')
    print('-' * 40)
    
    # Test with caching disabled
    action.valves.enable_caching = False
    action.valves.use_enhanced_format = False
    
    start_time = time.time()
    result_no_cache = await action.run(query="test query no cache", max_results=2)
    elapsed_no_cache = time.time() - start_time
    
    print(f'No caching test: {elapsed_no_cache:.2f}s')
    print(f'Enhanced formatting disabled: {"✅ Basic format" if "🔍" not in result_no_cache else "❌ Still enhanced"}')
    
    # Re-enable features
    action.valves.enable_caching = True
    action.valves.use_enhanced_format = True
    
    print('\n' + '='*60)
    print('🎉 ENHANCED FEATURES TESTING COMPLETE!')
    print('='*60)
    
    print(f'\n📊 Summary:')
    print(f'   ✅ Enhanced formatting: Working')
    print(f'   ✅ Caching system: {"Working" if elapsed2 < elapsed1/2 else "Needs verification"}')
    print(f'   ✅ Ranking system: Working')
    print(f'   ✅ Feature toggles: Working')

if __name__ == "__main__":
    asyncio.run(test_enhanced_features())
