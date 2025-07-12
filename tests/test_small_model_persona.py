#!/usr/bin/env python3
"""
Test script to verify small model persona optimization
"""
import os
import sys
sys.path.append('/app')
sys.path.append('/app/pipelines')
sys.path.append('/app/pipelines/memory_system')

from pipelines.memory_system.processor import MemoryProcessor

def test_small_model_detection():
    """Test small model detection and persona loading"""
    print("Testing Small Model Persona Optimization")
    print("=" * 50)
    
    # Initialize processor
    processor = MemoryProcessor()
    
    # Test small model detection
    print("\n1. Testing Model Size Detection:")
    small_models = [
        "llama3.2:3b",
        "qwen2.5:3b", 
        "phi3:3.8b",
        "gemma2:2b"
    ]
    
    large_models = [
        "llama3.1:8b",
        "qwen2.5:7b",
        "codellama:13b",
        "llama3:70b"
    ]
    
    for model in small_models:
        is_small = processor.detect_model_size(model_name=model)
        print(f"   {model}: {'SMALL' if is_small else 'LARGE'} model")
    
    for model in large_models:
        is_small = processor.detect_model_size(model_name=model)
        print(f"   {model}: {'SMALL' if is_small else 'LARGE'} model")
    
    # Test persona loading
    print("\n2. Testing Persona Loading:")
    
    # Test small model persona
    small_persona = processor.get_small_model_persona()
    print(f"   Small model persona length: {len(small_persona)} characters")
    print(f"   Preview: {small_persona[:100]}...")
    
    # Test system message creation for small model
    print("\n3. Testing System Message Generation:")
    
    # Mock request body for small model
    mock_request_small = {
        "model": "llama3.2:3b",
        "messages": [{"role": "user", "content": "Hello, who are you?"}]
    }
    
    system_msg_small = processor.create_system_message(
        user_id="test_user",
        memory_context="",
        memory_quality_score=10,
        user_request_body=mock_request_small
    )
    
    print(f"   Small model system message length: {len(system_msg_small)} characters")
    print(f"   Using optimized persona: {'persona_small_model.json' in system_msg_small or len(system_msg_small) < 1000}")
    
    # Mock request body for large model
    mock_request_large = {
        "model": "llama3.1:8b",
        "messages": [{"role": "user", "content": "Hello, who are you?"}]
    }
    
    system_msg_large = processor.create_system_message(
        user_id="test_user",
        memory_context="",
        memory_quality_score=10,
        user_request_body=mock_request_large
    )
    
    print(f"   Large model system message length: {len(system_msg_large)} characters")
    print(f"   Using full persona: {len(system_msg_large) > 1000}")
    
    print("\n✅ Small Model Persona Optimization Test Complete!")

if __name__ == "__main__":
    test_small_model_detection()
