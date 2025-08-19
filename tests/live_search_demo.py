#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('/app/utilities')

async def demonstrate_your_search():
    print("🔍 LIVE DEMONSTRATION: Your Search Query Processing")
    print("="*65)
    
    # Your original query from the screenshot
    your_query = "what are the latest headlines for today ion europe"
    print(f"📝 YOUR EXACT QUERY: '{your_query}'")
    print("-" * 65)
    
    # Step 1: Show trigger detection
    trigger_keywords = [
        "current", "today", "latest", "news", "headline",
        "date", "time", "update", "trending", "market", "stock", "price", "search the web",
        "web search", "lookup", "recent", "what is happening", "check online"
    ]
    
    detected = [kw for kw in trigger_keywords if kw.lower() in your_query.lower()]
    print(f"🎯 DETECTED TRIGGERS: {detected}")
    
    # Step 2: Show query processing
    print(f"\n🔧 QUERY PROCESSING:")
    
    # Import the actual search function
    from enhanced_web_search import search_web
    
    # Show the query that would be built
    import re
    
    content_lower = your_query.lower()
    
    # Check if it's a news query
    is_news = any(word in content_lower for word in ['news', 'latest', 'today', 'recent', 'current', 'headline'])
    print(f"   📰 News Query Detected: {is_news}")
    
    # Process the query (simplified version of _build_query)
    cleaned = re.sub(r"\b(please|can you|could you|search|find|look up|web search for|check|get|give me)\b", "", your_query, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    if len(cleaned) < 5:
        cleaned = your_query
    
    cleaned = re.sub(r"[?!]+$", "", cleaned)
    cleaned = re.sub(r"\b(the|a|an|what|when|where|how|why)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    final_query = cleaned or your_query
    
    # Add news context
    if is_news and 'news' not in final_query.lower():
        final_query += ' news'
    
    print(f"   📥 Original: '{your_query}'")
    print(f"   🧹 Cleaned: '{cleaned}'")
    print(f"   🎯 Final Query: '{final_query}'")
    
    # Step 3: Execute the actual search
    print(f"\n🌐 EXECUTING SEARCH...")
    try:
        result = await search_web(final_query, max_results=3)
        
        print(f"   ✅ Search completed successfully!")
        print(f"   📊 Results found: {len(result.get('results', []))}")
        print(f"   🌍 Search region: eu-en (European English)")
        print(f"   📅 Timestamp: {result.get('timestamp', 'Unknown')}")
        
        # Show the actual results
        print(f"\n📰 ACTUAL SEARCH RESULTS:")
        print("-" * 40)
        
        for i, item in enumerate(result.get('results', []), 1):
            title = item.get('title', 'No title')
            snippet = item.get('snippet', 'No snippet')
            link = item.get('link', 'No link')
            
            print(f"{i}. {title}")
            print(f"   {snippet[:100]}...")
            print(f"   🔗 {link}")
            print()
            
        # Step 4: Show how this gets injected
        print(f"💉 HOW THIS GETS INJECTED INTO CONVERSATION:")
        print("-" * 50)
        print("The AI model receives this additional message:")
        print()
        print("Role: user")
        print("Content:")
        print(f'''[SYSTEM CONTEXT - WEB SEARCH RESULTS]
Search Query: "{final_query}"
Search Completed: 2025-08-19 10:30:00 UTC

{result.get('summary', 'Results summary')}

IMPORTANT: The above are real web search results. Please use this information to answer the original question.''')
        
        print(f"\n🤖 AI MODEL PROCESS:")
        print("1. Receives your original question")
        print("2. Receives web search results")  
        print("3. Combines both to generate informed response")
        print("4. Responds with current, accurate information")
        
    except Exception as e:
        print(f"   ❌ Search failed: {e}")

if __name__ == "__main__":
    asyncio.run(demonstrate_your_search())
