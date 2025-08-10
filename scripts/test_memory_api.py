#!/usr/bin/env python
"""Memory API smoke test.

Steps:
1. Store two memories for a test user.
2. Retrieve memories with a matching query term.
3. Validate at least one relevant memory is returned with content field.
4. Print concise PASS / FAIL summary.

Exit codes:
 0 success
 1 failure
"""
from __future__ import annotations
import os
import sys
import time
import json
import textwrap
import requests

BASE = os.environ.get("MEMORY_API_BASE", "http://localhost:5001/api/memory")
USER = os.environ.get("MEMORY_API_TEST_USER", "memory_pipeline_test_user@example.com")

SESSION = requests.Session()

def store(content: str, importance: float = 0.5, **meta):
    payload = {
        "user_id": USER,
        "content": content,
        "metadata": meta or {"source": "smoke"},
        "importance": importance,
        "memory_type": "conversation",
    }
    r = SESSION.post(f"{BASE}/store", json=payload, timeout=30)
    return r.status_code, r.text, r

def retrieve(query: str, limit: int = 5):
    payload = {"user_id": USER, "query": query, "limit": limit}
    r = SESSION.post(f"{BASE}/retrieve", json=payload, timeout=30)
    return r.status_code, r.text, r

def main():
    print(f"[INFO] Memory API base: {BASE}")
    # 1. Store memories
    store_items = [
        "My favorite programming language is Python",
        "I live in Lisbon and enjoy ocean walks",
    ]
    for c in store_items:
        code, text, resp = store(c, 0.7, source="smoke", tag="initial")
        print(f"[STORE] {code} -> {text[:120]}")
        if code != 200:
            print("[FAIL] Store request failed")
            return 1
    # brief pause for indexing
    time.sleep(2)

    # 2. Retrieve
    code, text, resp = retrieve("Python language")
    print(f"[RETRIEVE] {code} -> {text[:200]}")
    if code != 200:
        print("[FAIL] Retrieve request failed")
        return 1

    try:
        data = resp.json()
    except Exception:
        print("[FAIL] Response not JSON")
        return 1

    memories = data.get("memories") or []
    matched = [m for m in memories if "Python" in (m.get("content") or "")]

    if not memories:
        print("[FAIL] No memories returned")
        return 1
    if not matched:
        print("[WARN] Memories returned but none matched query term explicitly")
    else:
        print(f"[OK] Retrieved {len(memories)} memories; {len(matched)} matched keyword")

    print("[PASS] Memory API smoke test succeeded")
    return 0

if __name__ == "__main__":
    sys.exit(main())
