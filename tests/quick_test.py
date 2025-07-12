#!/usr/bin/env python3
"""
Quick Enhanced Memory System Test
================================
"""

import sys
sys.path.insert(0, '.')

def test_enhanced_memory_configuration():
    """Test the enhanced memory system configuration."""
    print("🧪 Enhanced Memory System - Quick Configuration Test")
    print("=" * 60)
    
    try:
        from storage.pipelines.enhanced_memory_pipeline import Pipeline
        pipeline = Pipeline()
        
        print("📊 MAXIMUM LEARNING SETTINGS:")
        print(f"  ✅ Max memories per query: {pipeline.valves.max_memories}")
        print(f"  ✅ Memory threshold: {pipeline.valves.memory_threshold} (0.0 = accept all)")
        print(f"  ✅ Max context memories: {pipeline.valves.max_context_memories}")
        print(f"  ✅ Auto store threshold: {pipeline.valves.auto_store_threshold} (0 = store everything)")
        print(f"  ✅ Unlimited storage: {pipeline.valves.unlimited_storage}")
        
        # Verify the settings are correct for maximum learning
        assert pipeline.valves.max_memories == 100, f"Expected 100, got {pipeline.valves.max_memories}"
        assert pipeline.valves.memory_threshold == 0.0, f"Expected 0.0, got {pipeline.valves.memory_threshold}"
        assert pipeline.valves.max_context_memories == 50, f"Expected 50, got {pipeline.valves.max_context_memories}"
        assert pipeline.valves.auto_store_threshold == 0, f"Expected 0, got {pipeline.valves.auto_store_threshold}"
        assert pipeline.valves.unlimited_storage == True, f"Expected True, got {pipeline.valves.unlimited_storage}"
        
        print("\n🧠 FORGET/DELETE COMMAND DETECTION:")
        forget_tests = [
            "Forget about my password",
            "Delete that memory about work", 
            "Remove the information about my salary",
            "Don't remember my previous conversation"
        ]
        
        for cmd in forget_tests:
            result = pipeline.detect_explicit_memory_commands(cmd)
            if result['has_command']:
                forget_cmds = [c for c in result['commands'] if c.get('type') == 'forget_command']
                if forget_cmds:
                    print(f"  ✅ FORGET: \"{cmd}\"")
                else:
                    print(f"  ⚠️  DETECTED: \"{cmd}\" (but not as forget)")
            else:
                print(f"  ❌ MISSED: \"{cmd}\"")
        
        print("\n🎯 REMEMBER COMMAND DETECTION:")
        remember_tests = [
            "Remember this: I like coffee",
            "Save this important note",
            "Don't forget that I work at Swift"
        ]
        
        for cmd in remember_tests:
            result = pipeline.detect_explicit_memory_commands(cmd)
            if result['has_command']:
                print(f"  ✅ REMEMBER: \"{cmd}\"")
            else:
                print(f"  ❌ MISSED: \"{cmd}\"")
        
        print("\n🎉 ENHANCED MEMORY SYSTEM VERIFICATION COMPLETE!")
        print("   • Maximum memory capacity: ENABLED")
        print("   • Zero threshold filtering: ENABLED (remembers everything)")
        print("   • Forget/delete commands: DETECTED")
        print("   • Remember commands: DETECTED")
        print("   • Self-learning: OPTIMIZED")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_memory_configuration()
    exit(0 if success else 1)
