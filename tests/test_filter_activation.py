#!/usr/bin/env python3
"""
Test script to check Filter activation for the exact query from screenshot
"""

import importlib.util
import asyncio

async def test_filter_activation():
    # Load the Filter
    spec = importlib.util.spec_from_file_location('auto_web_search_filter', '/app/backend/data/functions/auto_web_search_filter.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    print('🧪 TESTING FILTER ACTIVATION FOR SCREENSHOT QUERY')
    print('=' * 60)
    
    filter_instance = module.Filter()
    
    # Test queries from the screenshot
    test_queries = [
        'hello search the web for the weather tomorrow in netherlands.',
        'search the web for the latest news',
        'weather tomorrow in Netherlands',
        'what is the latest news today'
    ]
    
    for query in test_queries:
        print(f'\nQuery: "{query}"')
        
        # Check trigger conditions
        query_lower = query.lower()
        
        trigger_match = any(keyword in query_lower for keyword in filter_instance.valves.trigger_keywords)
        force_match = any(keyword in query_lower for keyword in filter_instance.valves.force_keywords)
        
        print(f'  Trigger Keywords Match: {trigger_match}')
        print(f'  Force Keywords Match: {force_match}')
        print(f'  Would Activate: {"[YES]" if (trigger_match or force_match) else "[NO]"}')
        
        if trigger_match:
            matching_triggers = [kw for kw in filter_instance.valves.trigger_keywords if kw in query_lower]
            print(f'  Matching Triggers: {matching_triggers}')
        
        if force_match:
            matching_force = [kw for kw in filter_instance.valves.force_keywords if kw in query_lower]
            print(f'  Matching Force: {matching_force}')

if __name__ == "__main__":
    asyncio.run(test_filter_activation())
