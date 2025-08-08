#!/usr/bin/env python3
"""
Update Enhanced Memory Pipeline to Enable Memory Functionality
"""

import requests
import json

def update_pipeline_valves():
    """Update the enhanced memory pipeline valves to enable memory"""
    print("🔧 Updating Enhanced Memory Pipeline Configuration")
    print("=" * 50)
    
    pipelines_url = "http://localhost:9099"
    
    # Get current valves
    try:
        response = requests.get(f"{pipelines_url}/enhanced_memory_pipeline/valves")
        if response.status_code == 200:
            current_valves = response.json()
            print("📊 Current valves:")
            for key, value in current_valves.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ Failed to get current valves: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting valves: {e}")
        return False
    
    # Update valves to enable memory
    updated_valves = {
        **current_valves,
        "MEMORY_ENABLED": True,
        "DEBUG_LOGGING": True,  # Enable debug logging to see what's happening
        "INTELLIGENT_CONTEXT": True,
        "ENABLE_GLOBAL_CONTEXT": True
    }
    
    print(f"\n🔄 Updating valves to enable memory...")
    
    try:
        response = requests.post(
            f"{pipelines_url}/enhanced_memory_pipeline/valves/update",
            json=updated_valves,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Pipeline valves updated successfully!")
            print("📊 New valves:")
            for key, value in updated_valves.items():
                print(f"   {key}: {value}")
            return True
        else:
            print(f"❌ Failed to update valves: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error updating valves: {e}")
        return False

def test_memory_functionality_again():
    """Test memory functionality after enabling it"""
    print("\n🧠 Testing Memory Functionality After Enabling")
    print("=" * 50)
    
    # Import our real pipeline tester
    import sys
    sys.path.append('.')
    
    from test_real_pipeline_memory import RealPipelineMemoryTester
    
    tester = RealPipelineMemoryTester()
    
    # Just test the inlet filter again
    memories_stored = tester.setup_test_memories()
    if memories_stored > 0:
        success, enhanced_message = tester.test_pipeline_inlet_filter()
        return success
    return False

def main():
    """Main function to update and test pipeline"""
    print("🚀 Enhanced Memory Pipeline Update and Test")
    print("=" * 60)
    
    # Step 1: Update pipeline valves
    valves_updated = update_pipeline_valves()
    
    if not valves_updated:
        print("❌ Failed to update pipeline valves")
        return
    
    # Step 2: Test memory functionality
    print("\n⏳ Waiting for pipeline to reload...")
    import time
    time.sleep(3)
    
    memory_working = test_memory_functionality_again()
    
    print("\n" + "=" * 60)
    if memory_working:
        print("✅ Memory functionality is now working through the pipeline!")
    else:
        print("ℹ️ Pipeline updated but memory implementation may need code changes")
    
    print("\n📝 Note: If memory is still not working, the pipeline code itself")
    print("   needs to be updated to actually call the memory API when MEMORY_ENABLED is True")

if __name__ == "__main__":
    main()
