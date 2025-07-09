#!/usr/bin/env python3
"""
Test script to verify the call_llm_stream function works
"""
import asyncio
import sys
import os
sys.path.append('/app')

async def test_stream():
    from services.llm_service import call_llm_stream
    
    print("Testing call_llm_stream function...", flush=True)
    
    messages = [{"role": "user", "content": "Hello"}]
    model = "llama3.2:3b"
    session_id = "test_session"
    
    print(f"Calling call_llm_stream with model={model}, session_id={session_id}", flush=True)
    
    async for token in call_llm_stream(messages, model=model, session_id=session_id):
        print(f"Received token: '{token}'", flush=True)
    
    print("Stream completed", flush=True)

if __name__ == "__main__":
    asyncio.run(test_stream())
