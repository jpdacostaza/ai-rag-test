#!/usr/bin/env python3
"""
Anti-Fabrication Memory Test
============================

Tests the memory system to ensure it doesn't fabricate memories for new users.
"""

import json
import sys
import os

def test_persona_anti_fabrication():
    """Test all persona files for anti-fabrication measures."""
    
    print(" ANTI-FABRICATION MEMORY SYSTEM TEST")
    print("=" * 50)
    
    # Test persona files
    persona_files = [
        "/opt/backend/config/persona_unified_small.json",
        "/opt/backend/config/persona_new_user.json",
        "/opt/backend/config/persona_enhanced.json",
        "/opt/backend/config/persona_small_model.json",
        "/opt/backend/config/persona.json"
    ]
    
    fabrication_indicators = [
        "ALWAYS acknowledge",
        "MUST acknowledge", 
        "prove you remember",
        "Last time we",
        "I remember you",
        "Hello again"
    ]
    
    safe_indicators = [
        "only when provided",
        "never fabricate",
        "anti-hallucination", 
        "don't make up",
        "transparent about"
    ]
    
    for file_path in persona_files:
        if os.path.exists(file_path):
            print(f"\n Testing {os.path.basename(file_path)}:")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for fabrication indicators
                fabrication_count = sum(1 for indicator in fabrication_indicators 
                                      if indicator.lower() in content.lower())
                
                # Check for safety indicators  
                safety_count = sum(1 for indicator in safe_indicators
                                 if indicator.lower() in content.lower())
                
                if fabrication_count > 0:
                    print(f"  [FAIL] FABRICATION RISK: Found {fabrication_count} risky patterns")
                    print(f"   Safety measures: {safety_count}")
                    
                    if safety_count == 0:
                        print(f"  *** HIGH RISK: No anti-fabrication measures found!")
                    else:
                        print(f"  [WARN] MODERATE RISK: Some safety measures present")
                else:
                    print(f"  [OK] SAFE: No fabrication indicators found")
                    print(f"   Safety measures: {safety_count}")
                    
            except Exception as e:
                print(f"  [FAIL] Error reading file: {e}")
        else:
            print(f"\n {os.path.basename(file_path)}: Not found")
    
    print(f"\n RECOMMENDATIONS:")
    print(f"  - Use persona_unified_small.json for Orange Pi (small models)")
    print(f"  - Remove old persona files to prevent conflicts")
    print(f"  - Ensure memory system only acknowledges when memories are provided")
    print(f"  - Test with new user conversations to verify no fabrication")

def test_memory_processor():
    """Test if memory processor loads the right personas."""
    
    print(f"\n MEMORY PROCESSOR TEST")
    print("=" * 30)
    
    try:
        # Import the memory processor
        sys.path.append('/opt/backend')
        from pipelines.memory_system.processor import MemoryProcessor
        
        processor = MemoryProcessor(debug=True)
        
        # Test small model persona
        small_persona = processor.get_small_model_persona()
        if "never fabricate" in small_persona.lower():
            print("[OK] Small model persona has anti-fabrication measures")
        else:
            print("[FAIL] Small model persona lacks anti-fabrication measures")
            
        # Test new user persona  
        new_user_persona = processor.get_new_user_persona_prompt()
        if "only when provided" in new_user_persona.lower():
            print("[OK] New user persona has proper memory handling")
        else:
            print("[FAIL] New user persona may cause fabrication")
            
    except Exception as e:
        print(f"[FAIL] Error testing memory processor: {e}")

if __name__ == "__main__":
    test_persona_anti_fabrication()
    test_memory_processor()
    
    print(f"\n TEST COMPLETE")
    print(f"For Orange Pi with small models, ensure:")
    print(f"  1. Only persona_unified_small.json is used")
    print(f"  2. Memory system doesn't fabricate when no memories exist")
    print(f"  3. Remove conflicting persona files")
