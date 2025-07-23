#!/usr/bin/env python3
"""
Persona File Analysis and Cleanup Recommendations
=================================================

Analyzes persona file usage and provides cleanup recommendations for Orange Pi optimization.
"""

import json
import os
from pathlib import Path

def analyze_persona_files():
    """Analyze all persona files and recommend which to keep."""
    
    print("🔍 PERSONA FILE ANALYSIS FOR ORANGE PI OPTIMIZATION")
    print("=" * 60)
    
    persona_files = {
        "persona_unified_small.json": {
            "purpose": "Orange Pi <7B models, anti-fabrication",
            "size": 0,
            "recommendation": "KEEP - Primary for Orange Pi",
            "priority": 1
        },
        "persona_small_model.json": {
            "purpose": "Small models, recently fixed anti-fabrication", 
            "size": 0,
            "recommendation": "CONSIDER REMOVING - Redundant with unified",
            "priority": 3
        },
        "persona_new_user.json": {
            "purpose": "New user introduction, anti-fabrication",
            "size": 0, 
            "recommendation": "KEEP - Good for new user handling",
            "priority": 2
        },
        "persona_enhanced.json": {
            "purpose": "Large models, complex features, fabrication risk",
            "size": 0,
            "recommendation": "REMOVE - Not needed for Orange Pi <7B",
            "priority": 5
        },
        "persona.json": {
            "purpose": "Legacy general purpose, fabrication risk", 
            "size": 0,
            "recommendation": "REMOVE - Superseded by unified small",
            "priority": 4
        }
    }
    
    # Check which files exist and get their sizes
    config_dir = Path("config")
    for filename, info in persona_files.items():
        filepath = config_dir / filename
        if filepath.exists():
            info["size"] = filepath.stat().st_size
            info["exists"] = True
            
            # Quick safety check
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    has_fabrication_risk = any(risk in content.lower() for risk in [
                        "always acknowledge", "must acknowledge", "prove you remember"
                    ])
                    has_safety = any(safety in content.lower() for safety in [
                        "never fabricate", "anti-hallucination", "only when provided"
                    ])
                    
                    info["fabrication_risk"] = has_fabrication_risk
                    info["safety_measures"] = has_safety
                    
            except Exception as e:
                info["error"] = str(e)
        else:
            info["exists"] = False
    
    # Display analysis
    print("\n📊 PERSONA FILE STATUS:")
    for filename, info in sorted(persona_files.items(), key=lambda x: x[1]["priority"]):
        status = "✅ EXISTS" if info["exists"] else "❌ MISSING"
        size = f"{info['size']} bytes" if info["exists"] else "N/A"
        
        print(f"\n📄 {filename}")
        print(f"   Status: {status}")
        print(f"   Size: {size}")
        print(f"   Purpose: {info['purpose']}")
        print(f"   Recommendation: {info['recommendation']}")
        
        if info["exists"]:
            risk_indicator = "🚨 HIGH RISK" if info.get("fabrication_risk") else "✅ SAFE"
            safety_indicator = "🛡️ PROTECTED" if info.get("safety_measures") else "⚠️ NO PROTECTION"
            print(f"   Fabrication Risk: {risk_indicator}")
            print(f"   Safety Measures: {safety_indicator}")
    
    print(f"\n🎯 RECOMMENDATIONS FOR ORANGE PI (<7B MODELS):")
    print(f"")
    print(f"✅ KEEP THESE FILES:")
    print(f"   • persona_unified_small.json (PRIMARY - best for Orange Pi)")
    print(f"   • persona_new_user.json (for new user handling)")
    print(f"")
    print(f"🗑️ SAFE TO REMOVE:")
    print(f"   • persona_enhanced.json (too complex for small models)")
    print(f"   • persona.json (legacy, has fabrication risks)")
    print(f"   • persona_small_model.json (redundant with unified)")
    print(f"")
    print(f"🔧 SYSTEM UPDATES NEEDED:")
    print(f"   • Update memory processor to prioritize persona_unified_small.json")
    print(f"   • Update all config files to use unified persona first")
    print(f"   • Test with small models to ensure no fabrication")
    
    return persona_files

def generate_cleanup_commands():
    """Generate cleanup commands."""
    
    print(f"\n🧹 CLEANUP COMMANDS:")
    print(f"")
    print(f"# Backup existing files first:")
    print(f"mkdir -p config/backup")
    print(f"cp config/persona_enhanced.json config/backup/")
    print(f"cp config/persona.json config/backup/")
    print(f"cp config/persona_small_model.json config/backup/")
    print(f"")
    print(f"# Remove redundant files (after testing):")
    print(f"# rm config/persona_enhanced.json")
    print(f"# rm config/persona.json") 
    print(f"# rm config/persona_small_model.json")
    print(f"")
    print(f"# Keep only:")
    print(f"# config/persona_unified_small.json (PRIMARY)")
    print(f"# config/persona_new_user.json (FALLBACK)")

if __name__ == "__main__":
    analysis = analyze_persona_files()
    generate_cleanup_commands()
    
    print(f"\n✨ SUMMARY:")
    print(f"For optimal Orange Pi performance with <7B models:")
    print(f"1. Use persona_unified_small.json as primary persona")
    print(f"2. Keep persona_new_user.json for new user scenarios") 
    print(f"3. Remove large/complex personas that cause conflicts")
    print(f"4. Ensure anti-fabrication measures are working")
