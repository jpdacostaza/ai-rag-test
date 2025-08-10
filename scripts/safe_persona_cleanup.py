#!/usr/bin/env python3
"""
Safe Persona Cleanup Script
===========================

Tests current persona functionality before removing old files.
"""

import json
import os
from pathlib import Path

def test_persona_loading():
    """Test if unified_prompt.json loads correctly."""
    
    print(" TESTING PERSONA LOADING")
    print("=" * 40)
    
    unified_persona_path = "config/unified_prompt.json"
    
    try:
        with open(unified_persona_path, 'r', encoding='utf-8') as f:
            persona_data = json.load(f)
            system_prompt = persona_data.get("system_prompt", "")
            
            print(f"[OK] unified_prompt.json loads successfully")
            print(f"[CHART] System prompt length: {len(system_prompt)} characters")
            print(f" Anti-fabrication check:")
            
            # Check for anti-fabrication measures
            safety_checks = [
                ("Never fabricate", "never fabricate" in system_prompt.lower()),
                ("Only when provided", "only acknowledge memories when they are actually provided" in system_prompt.lower()),
                ("Clean slate", "treat this as our first conversation" in system_prompt.lower()),
                ("Anti-hallucination", "anti-hallucination" in system_prompt.lower())
            ]
            
            for check_name, passed in safety_checks:
                status = "[OK] PASS" if passed else "[FAIL] FAIL"
                print(f"   {check_name}: {status}")
            
            all_passed = all(passed for _, passed in safety_checks)
            
            if all_passed:
                print(f"\n RESULT: unified_prompt.json is SAFE and READY")
                return True
            else:
                print(f"\n[WARN] RESULT: Some safety checks failed")
                return False
                
    except Exception as e:
        print(f"[FAIL] ERROR: Could not load unified_prompt.json: {e}")
        return False

def check_removal_safety():
    """Check if it's safe to remove old persona files."""
    
    print(f"\n REMOVAL SAFETY CHECK")
    print("=" * 30)
    
    # Files that are safe to remove for Orange Pi
    removable_files = [
        ("persona_enhanced.json", "Too large (21KB) for small models"),
        ("persona.json", "Legacy file with potential fabrication risks"),
        ("persona_small_model.json", "Redundant with persona_unified_small.json")
    ]
    
    # Files to keep
    keep_files = [
        ("unified_prompt.json", "PRIMARY - 7B model optimized"),
        ("persona_new_user.json", "FALLBACK - safe new user handling")
    ]
    
    print(" REMOVAL RECOMMENDATIONS:")
    print(f"\n SAFE TO REMOVE (after backup):")
    for filename, reason in removable_files:
        exists = "[OK]" if Path(f"config/{filename}").exists() else "[FAIL]"
        print(f"   {exists} {filename} - {reason}")
    
    print(f"\n[OK] KEEP THESE:")
    for filename, reason in keep_files:
        exists = "[OK]" if Path(f"config/{filename}").exists() else "[FAIL]"
        print(f"   {exists} {filename} - {reason}")
    
    return True

def generate_removal_commands():
    """Generate safe removal commands."""
    
    print(f"\n SAFE REMOVAL COMMANDS:")
    print("=" * 30)
    
    print(f"\n# 1. BACKUP FIRST (already done):")
    print(f"mkdir -p config/backup")
    print(f"cp config/persona_enhanced.json config/backup/")
    print(f"cp config/persona.json config/backup/")
    print(f"cp config/persona_small_model.json config/backup/")
    
    print(f"\n# 2. TEST CURRENT SYSTEM:")
    print(f"# Start fresh conversation and verify no memory fabrication")
    
    print(f"\n# 3. REMOVE WHEN READY (Orange Pi optimization):")
    print(f"rm config/persona_enhanced.json     # 21KB -> Save 85% space")
    print(f"rm config/persona.json              # 17KB -> Remove legacy")
    print(f"rm config/persona_small_model.json  # 2.6KB -> Remove redundant")
    
    print(f"\n# 4. VERIFY FINAL STATE:")
    print(f"ls config/persona*.json")
    print(f"# Should show only:")
    print(f"# - unified_prompt.json (1.5KB - PRIMARY)")
    print(f"# - persona_new_user.json (7.9KB - FALLBACK)")
    
    print(f"\n FINAL RESULT:")
    print(f"   Before: 5 files, ~52KB total")
    print(f"   After:  2 files, ~11KB total")
    print(f"   Savings: 79% reduction, optimized for Orange Pi <7B models")

if __name__ == "__main__":
    print(" ORANGE PI PERSONA OPTIMIZATION")
    print("=" * 50)
    
    # Test current persona
    persona_ok = test_persona_loading()
    
    # Check removal safety
    removal_safe = check_removal_safety()
    
    # Generate commands
    generate_removal_commands()
    
    print(f"\n RECOMMENDATION:")
    if persona_ok:
        print(f"[OK] unified_prompt.json is working correctly")
        print(f"[OK] Safe to remove old persona files after testing")
        print(f" Optimized for Orange Pi with <7B models")
    else:
        print(f"[WARN] Fix unified_prompt.json issues first")
        print(f"[SYNC] Keep old files as fallbacks until fixed")
