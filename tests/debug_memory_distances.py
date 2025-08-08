#!/usr/bin/env python3
"""
Debug Memory Distances
Check actual distance values to optimize thresholds
"""

import requests
import json

def debug_memory_retrieval():
    memory_api_url = "http://localhost:5001"
    
    # Test query
    response = requests.post(
        f"{memory_api_url}/api/memory/retrieve",
        json={
            "user_id": "test_user",
            "query": "Docker optimization", 
            "limit": 10,
            "threshold": 2.0  # Very high threshold to see all results
        }
    )
    
    if response.status_code == 200:
        results = response.json()
        print("[SEARCH] Memory Retrieval Debug Results:")
        print(f"Found {len(results.get('memories', []))} memories")
        
        for i, memory in enumerate(results.get('memories', [])):
            distance = memory.get('distance', 'unknown')
            similarity_score = memory.get('similarity_score', 'unknown') 
            content = memory.get('content', '')[:80] + "..."
            
            print(f"\n{i+1}. Distance: {distance}")
            print(f"   Similarity: {similarity_score}")
            print(f"   Content: {content}")
            
        # Test with different queries
        test_queries = [
            "Alex software engineer",
            "Python JavaScript preference", 
            "smart memory system",
            "containerization virtualization"
        ]
        
        print("\n" + "="*50)
        print(" Testing Different Queries:")
        
        for query in test_queries:
            resp = requests.post(
                f"{memory_api_url}/api/memory/retrieve",
                json={
                    "user_id": "test_user",
                    "query": query,
                    "limit": 3,
                    "threshold": 2.0
                }
            )
            
            if resp.status_code == 200:
                res = resp.json()
                memories = res.get('memories', [])
                print(f"\nQuery: '{query}'")
                if memories:
                    best_match = memories[0]
                    print(f"  Best match distance: {best_match.get('distance', 'unknown')}")
                    print(f"  Best match similarity: {best_match.get('similarity_score', 'unknown')}")
                else:
                    print("  No matches found")
    else:
        print(f"Request failed: {response.status_code}")

if __name__ == "__main__":
    debug_memory_retrieval()
