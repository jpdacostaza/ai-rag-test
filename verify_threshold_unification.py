#!/usr/bin/env python3
"""
Verify all thresholds are properly unified and no conflicts remain
"""

import os
import re

def scan_threshold_unified():
    """Scan codebase to verify threshold unification"""
    
    print("🔍 THRESHOLD UNIFICATION VERIFICATION")
    print("=" * 45)
    
    # Define what should be the ONLY active threshold
    target_threshold = "-0.5"
    function_file = "enhanced_memory_function_filter_v5_1_final.py"
    
    print(f"✅ TARGET: Single source of truth = {target_threshold} in {function_file}")
    print()
    
    # Files to check for conflicts
    critical_files = [
        "docker-compose.yml",
        ".env", 
        "config/settings.py",
        "config/config_unified.py",
        # "core/config.py",  # REMOVED - deprecated file deleted
        "config/memory_functions.json",
        "services/memory_service.py",
        "memory/api/main.py"
    ]
    
    conflicts_found = []
    unified_correctly = []
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"📋 Checking: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for active threshold settings (not commented)
            active_thresholds = []
            commented_thresholds = []
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Check for threshold patterns
                threshold_patterns = [
                    r'MEMORY_RETRIEVAL_THRESHOLD\s*=\s*([0-9.-]+)',
                    r'MEMORY_THRESHOLD\s*=\s*([0-9.-]+)',
                    r'similarity_threshold.*default\s*=\s*([0-9.-]+)',
                    r'retrieval_threshold.*=\s*([0-9.-]+)',
                    r'memory_threshold.*default\s*=\s*([0-9.-]+)',
                    r'"default":\s*([0-9.-]+)',
                    r'threshold.*=\s*([0-9.-]+)'
                ]
                
                for pattern in threshold_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        threshold_value = match.group(1)
                        
                        # Check if line is commented
                        if line.strip().startswith('#') or line.strip().startswith('//'):
                            commented_thresholds.append(f"  Line {i}: {line.strip()}")
                        else:
                            active_thresholds.append(f"  Line {i}: {line.strip()} → Value: {threshold_value}")
            
            # Report findings
            if active_thresholds:
                if file_path == function_file and target_threshold in str(active_thresholds):
                    print(f"   ✅ Correct active threshold found")
                    unified_correctly.append(file_path)
                else:
                    print(f"   ❌ CONFLICT: Active thresholds found:")
                    for threshold in active_thresholds:
                        print(f"      {threshold}")
                    conflicts_found.append(file_path)
            else:
                if file_path == function_file:
                    print(f"   ❌ NO THRESHOLD: Expected active threshold in function file")
                    conflicts_found.append(file_path)
                else:
                    print(f"   ✅ No active thresholds (correctly disabled)")
                    unified_correctly.append(file_path)
            
            if commented_thresholds:
                print(f"   📝 Commented thresholds (good):")
                for threshold in commented_thresholds[:3]:  # Show first 3
                    print(f"      {threshold}")
                if len(commented_thresholds) > 3:
                    print(f"      ... and {len(commented_thresholds) - 3} more")
            
            print()
        else:
            print(f"❌ Missing file: {file_path}")
            print()
    
    # Summary
    print("🎯 UNIFICATION SUMMARY")
    print("=" * 25)
    
    if conflicts_found:
        print(f"❌ CONFLICTS FOUND in {len(conflicts_found)} files:")
        for file in conflicts_found:
            print(f"   • {file}")
        print()
        print("🔧 ACTION NEEDED:")
        print("   1. Comment out or remove active thresholds in conflict files")
        print("   2. Ensure only the OpenWebUI function has active threshold")
        print("   3. Re-test memory system")
    else:
        print(f"✅ ALL UNIFIED CORRECTLY!")
        print(f"   • {len(unified_correctly)} files properly configured")
        print(f"   • Single source of truth: {function_file}")
        print()
        print("🚀 READY FOR TESTING:")
        print("   1. Restart containers: docker restart memory-api backend-openwebui")
        print("   2. Import function in OpenWebUI")
        print("   3. Test memory persistence")
    
    return len(conflicts_found) == 0

if __name__ == "__main__":
    unified = scan_threshold_unified()
    exit(0 if unified else 1)
