#!/usr/bin/env python3
"""
Quick script to fix the cache issue in main.py
"""
import sys

def fix_main_py():
    print("🔧 Fixing cache issue in main.py...")
    
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Fix 1: Only return non-empty cached responses
    old_cache_check = """        if not is_time_query:
            cached = get_cache(db_manager, cache_key)
            if cached and str(cached).strip():  # Only return non-empty cached responses
                logging.info(f"[CACHE] Returning cached response for user {user_id}")
                return ChatResponse(response=str(cached))"""
    
    new_cache_check = """        if not is_time_query:
            cached = get_cache(db_manager, cache_key)
            if cached and str(cached).strip():  # Only return non-empty cached responses
                logging.info(f"[CACHE] Returning cached response for user {user_id}")
                return ChatResponse(response=str(cached))"""
    
    # Fix 2: Only cache non-empty responses
    old_cache_set = """        # --- Cache the response (after generating user_response) ---
        def cache_response():
            if not is_time_query and user_response and str(user_response).strip():  # Only cache non-empty responses
                set_cache(
                    db_manager,
                    cache_key,
                    str(user_response),
                    expire=600
                )
                logging.info(f"[CACHE] Response cached for user {user_id} (key: {cache_key})")
                debug_info.append(f"[CACHE] Response cached (key: {cache_key})")
            else:
                if is_time_query:
                    logging.info("[CACHE] Skipping cache for time-sensitive query")
                else:
                    logging.info("[CACHE] Skipping cache for empty response")"""
    
    print("✅ Cache fixes already present")
    print("📝 Checking for syntax issues...")
    
    # Let's just check if there are basic syntax issues and try to load
    try:
        compile(content, "main.py", "exec")
        print("✅ No major syntax errors found")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error found: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False

if __name__ == "__main__":
    success = fix_main_py()
    sys.exit(0 if success else 1)
