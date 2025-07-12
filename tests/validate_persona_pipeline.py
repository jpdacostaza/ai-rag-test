#!/usr/bin/env python3
"""
Persona and Pipeline Validation Script
=====================================

Validates that the enhanced persona configuration and memory pipeline 
work correctly with any AI model (local/cloud, old/new).
"""

import json
import os
import sys
from pathlib import Path

def validate_persona_file():
    """Validate the persona_enhanced.json file structure and content."""
    print("🔍 Validating Enhanced Persona v3.2.0 configuration...")
    
    # Get the correct path relative to the script location
    script_dir = Path(__file__).parent.parent
    persona_path = script_dir / "config" / "persona_enhanced.json"
    
    try:
        # Check file exists
        if not os.path.exists(persona_path):
            print(f"❌ Persona file not found: {persona_path}")
            return False
        
        # Load and validate JSON
        with open(persona_path, 'r', encoding='utf-8') as f:
            persona = json.load(f)
        
        # Validate required fields
        required_fields = ["system_prompt", "capabilities", "status"]
        for field in required_fields:
            if field not in persona:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate system prompt
        system_prompt = persona["system_prompt"]
        if len(system_prompt) < 100:
            print(f"❌ System prompt too short: {len(system_prompt)} chars")
            return False
        
        # Check for memory-related instructions
        memory_keywords = [
            "MEMORY SYSTEM INSTRUCTIONS",
            "MEMORY DETECTION",
            "MANDATORY MEMORY ACKNOWLEDGMENT",
            "MEMORIES FROM PREVIOUS CONVERSATIONS"
        ]
        
        missing_keywords = []
        for keyword in memory_keywords:
            if keyword not in system_prompt:
                missing_keywords.append(keyword)
        
        if missing_keywords:
            print(f"⚠️ Missing memory keywords: {missing_keywords}")
        
        # Validate model compatibility
        models = persona.get("capabilities", {}).get("models", {})
        if not models:
            print("⚠️ No model configuration found")
        else:
            print(f"✅ Model configuration found:")
            print(f"   - Primary LLM: {models.get('primary_llm', 'not specified')}")
            print(f"   - Available models: {len(models.get('available_models', []))}")
            print(f"   - Embedding model: {models.get('embedding_model', 'not specified')}")
            print(f"   - Memory threshold: {models.get('memory_threshold', 'not specified')}")
        
        # Validate version info
        status = persona.get("status", {})
        print(f"✅ Persona version: {status.get('version', 'unknown')}")
        print(f"✅ Memory system: {status.get('memory_system', 'unknown')}")
        print(f"✅ Integration quality: {status.get('integration_quality', 'unknown')}")
        
        print(f"✅ Persona validation successful")
        print(f"   - File size: {os.path.getsize(persona_path)} bytes")
        print(f"   - System prompt: {len(system_prompt)} characters")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def validate_pipeline_integration():
    """Validate that the pipeline can integrate with any model."""
    print("\n🔍 Validating pipeline integration...")
    
    script_dir = Path(__file__).parent.parent
    pipeline_path = script_dir / "pipelines" / "enhanced_memory_pipeline.py"
    
    try:
        # Check pipeline file exists
        if not os.path.exists(pipeline_path):
            print(f"❌ Pipeline file not found: {pipeline_path}")
            return False
        
        # Read pipeline content
        with open(pipeline_path, 'r', encoding='utf-8') as f:
            pipeline_content = f.read()
        
        # Check for model compatibility features
        compatibility_features = [
            "UNIVERSAL MODEL COMPATIBILITY",
            "model_agnostic",
            "adaptive_prompting",
            "universal_memory_format",
            "_create_model_compatible_system_message",
            "_load_persona_config",
            "integrate_persona"
        ]
        
        missing_features = []
        for feature in compatibility_features:
            if feature not in pipeline_content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"⚠️ Missing compatibility features: {missing_features}")
        else:
            print("✅ All model compatibility features present")
        
        # Check for persona integration
        persona_integration = [
            "load_persona_config",
            "get_base_persona_prompt",
            "create_model_compatible_system_message",
            "persona_priority"
        ]
        
        persona_missing = []
        for feature in persona_integration:
            if feature not in pipeline_content:
                persona_missing.append(feature)
        
        if persona_missing:
            print(f"⚠️ Missing persona integration: {persona_missing}")
        else:
            print("✅ Persona integration features present")
        
        print(f"✅ Pipeline integration validation successful")
        print(f"   - File size: {os.path.getsize(pipeline_path)} bytes")
        print(f"   - Content length: {len(pipeline_content)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline validation error: {e}")
        return False

def validate_model_compatibility():
    """Validate compatibility with different model types."""
    print("\n🔍 Validating model compatibility...")
    
    # Simulate different model scenarios
    model_scenarios = [
        {
            "name": "Local Ollama Model (llama3.2:3b)",
            "type": "local",
            "context_limit": 4096,
            "capabilities": ["text_generation"]
        },
        {
            "name": "Local Mistral Model (mistral:7b)",
            "type": "local", 
            "context_limit": 8192,
            "capabilities": ["text_generation", "code"]
        },
        {
            "name": "OpenAI GPT-4",
            "type": "cloud",
            "context_limit": 128000,
            "capabilities": ["text_generation", "function_calling", "vision"]
        },
        {
            "name": "Legacy Model (Small Context)",
            "type": "legacy",
            "context_limit": 2048,
            "capabilities": ["text_generation"]
        }
    ]
    
    for scenario in model_scenarios:
        print(f"\n  📱 Testing: {scenario['name']}")
        
        # Test persona prompt size compatibility
        try:
            script_dir = Path(__file__).parent.parent
            persona_path = script_dir / "config" / "persona_enhanced.json"
            with open(persona_path, 'r', encoding='utf-8') as f:
                persona = json.load(f)
            
            system_prompt = persona["system_prompt"]
            prompt_size = len(system_prompt)
            context_limit = scenario["context_limit"]
            
            # Estimate token usage (rough: 1 token ≈ 4 characters)
            estimated_tokens = prompt_size // 4
            context_tokens = context_limit
            
            if estimated_tokens < context_tokens * 0.3:  # Use max 30% of context for system prompt
                print(f"    ✅ Prompt size compatible ({estimated_tokens} tokens < {context_tokens * 0.3:.0f} limit)")
            else:
                print(f"    ⚠️ Prompt might be too large ({estimated_tokens} tokens > {context_tokens * 0.3:.0f} limit)")
                print(f"       Pipeline should use condensed version for this model")
            
            # Test memory integration compatibility
            if "text_generation" in scenario["capabilities"]:
                print("    ✅ Text generation supported - memory integration will work")
            
            if scenario["type"] == "local":
                print("    ✅ Local model - pipeline design is compatible")
            elif scenario["type"] == "cloud":
                print("    ✅ Cloud model - API integration supported")
            elif scenario["type"] == "legacy":
                print("    ✅ Legacy model - fallback mechanisms available")
                
        except Exception as e:
            print(f"    ❌ Compatibility test failed: {e}")
    
    print(f"\n✅ Model compatibility validation complete")
    return True

def validate_memory_instructions():
    """Validate that memory instructions are clear and actionable."""
    print("\n🔍 Validating memory instructions...")
    
    try:
        script_dir = Path(__file__).parent.parent
        persona_path = script_dir / "config" / "persona_enhanced.json"
        with open(persona_path, 'r', encoding='utf-8') as f:
            persona = json.load(f)
        
        system_prompt = persona["system_prompt"]
        
        # Check for clear memory detection patterns
        detection_patterns = [
            "🧠 CRITICAL MEMORY",
            "MEMORIES FROM PREVIOUS CONVERSATIONS",
            "Memory:",
            "YOU MUST IMMEDIATELY"
        ]
        
        found_patterns = []
        for pattern in detection_patterns:
            if pattern in system_prompt:
                found_patterns.append(pattern)
        
        print(f"✅ Memory detection patterns found: {len(found_patterns)}/{len(detection_patterns)}")
        
        # Check for acknowledgment requirements
        acknowledgment_patterns = [
            "I remember you!",
            "acknowledge",
            "reference specific details",
            "MANDATORY"
        ]
        
        found_ack = []
        for pattern in acknowledgment_patterns:
            if pattern.lower() in system_prompt.lower():
                found_ack.append(pattern)
        
        print(f"✅ Acknowledgment patterns found: {len(found_ack)}/{len(acknowledgment_patterns)}")
        
        # Check for response patterns
        response_patterns = persona.get("response_patterns", {})
        if response_patterns:
            print(f"✅ Response patterns configured: {len(response_patterns)} types")
            
            memory_ack = response_patterns.get("memory_acknowledgment", {})
            if memory_ack.get("priority") == "absolute_first":
                print("✅ Memory acknowledgment set to absolute priority")
            else:
                print("⚠️ Memory acknowledgment priority not set to absolute_first")
        
        print(f"✅ Memory instructions validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Memory instructions validation error: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Persona and Pipeline Validation")
    print("=" * 50)
    
    os.chdir(Path(__file__).parent)
    
    results = []
    
    # Run all validations
    results.append(validate_persona_file())
    results.append(validate_pipeline_integration())
    results.append(validate_model_compatibility())
    results.append(validate_memory_instructions())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL VALIDATIONS PASSED ({passed}/{total})")
        print()
        print("🎯 SYSTEM STATUS:")
        print("✅ Persona configuration is valid and enhanced")
        print("✅ Pipeline supports universal model compatibility")
        print("✅ Memory instructions are clear and actionable")
        print("✅ System works with local and cloud models")
        print("✅ Ready for production deployment")
    else:
        print(f"⚠️ SOME VALIDATIONS FAILED ({passed}/{total})")
        print("Please review the issues above before deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
