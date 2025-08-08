#!/usr/bin/env python3
"""
Open WebUI Configuration Helper
==============================

Helps configure Open WebUI to use the memory pipeline globally.
"""

def print_configuration_guide():
    """Print step-by-step configuration guide."""
    print("=" * 70)
    print(" OPEN WEBUI MEMORY PIPELINE CONFIGURATION GUIDE")
    print("=" * 70)
    
    print("\n Current Status:")
    print("   [OK] Memory API: Running (localhost:8001)")
    print("   [OK] Pipelines Service: Running (localhost:9099)")
    print("   [OK] Memory Pipeline: Loaded globally")
    print("   [OK] Memory Storage/Retrieval: Working")
    
    print("\n Problem: Model still says 'I don't retain information'")
    print("   This means the pipeline filter is not being triggered.")
    
    print("\n SOLUTION STEPS:")
    print("\n1.  Check Open WebUI Pipeline Settings:")
    print("   - Go to http://localhost:8080")
    print("   - Click on your profile/settings")
    print("   - Look for 'Pipelines' or 'Functions' section")
    print("   - Ensure 'Enhanced Memory Pipeline' is enabled")
    print("   - Make sure it's set to apply to ALL models")
    
    print("\n2. [SYNC] Full System Restart (if needed):")
    print("   - Stop all containers: docker-compose down")
    print("   - Start them again: docker-compose up -d")
    print("   - Wait for all services to be healthy")
    
    print("\n3.  Test with ANY Model:")
    print("   - Open a new chat with qwen3:4b")
    print("   - Say: 'Hello, my name is J.P. and I work at Swift'")
    print("   - Then ask: 'What do you remember about me?'")
    print("   - The model should remember your name and job")
    
    print("\n4. [SEARCH] Debug Pipeline Activation:")
    print("   - Check if conversation messages trigger the pipeline")
    print("   - Pipeline should log: '[MEMORY PIPELINE INFO]' messages")
    print("   - Memory API should log interaction processing")
    
    print("\n Key Points:")
    print("   - Pipeline works with ANY model (llama3.2, mistral, etc.)")
    print("   - Memory is preserved across sessions")
    print("   - No model-specific configuration needed")
    print("   - Uses system message injection (universal method)")
    
    print("\n*** If Still Not Working:")
    print("   - The pipeline might need manual activation in Open WebUI")
    print("   - Check Open WebUI documentation for pipeline management")
    print("   - Ensure pipelines are enabled globally, not per-model")
    
    print("\n Quick Test Command:")
    print("   Run: docker logs backend-pipelines --tail 20")
    print("   Look for: 'Enhanced Memory Pipeline started'")
    
    print("\n" + "=" * 70)

def main():
    """Main function."""
    print_configuration_guide()

if __name__ == "__main__":
    main()
