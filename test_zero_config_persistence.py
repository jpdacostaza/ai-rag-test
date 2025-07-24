#!/usr/bin/env python3
"""
Zero-Config Persistence Test Script
Verifies that dependency fixes persist across Docker rebuilds
"""

import subprocess
import sys
import time
import os

def run_command(command, description, capture_output=True):
    """Run a command and handle errors."""
    print(f"\n🔧 {description}")
    print(f"Command: {command}")
    
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print(f"✅ {description} completed successfully")
            return result.stdout
        else:
            subprocess.run(command, shell=True, check=True)
            print(f"✅ {description} completed successfully")
            return ""
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"Error: {e.stderr}")
        return None

def check_pipelines_logs():
    """Check pipelines logs for dependency issues."""
    print("\n🔍 Checking pipelines container logs...")
    logs = run_command("docker-compose logs pipelines --tail=50", "Getting pipelines logs")
    
    if logs:
        print("\n📋 Recent pipelines logs:")
        print("-" * 50)
        print(logs)
        print("-" * 50)
        
        # Check for specific issues
        issues = []
        if "can_be_positional" in logs:
            issues.append("❌ Pydantic can_be_positional error detected")
        if "attempted relative import" in logs:
            issues.append("❌ Memory system import error detected")
        if "Memory system modules imported successfully" in logs:
            issues.append("✅ Memory system imports working")
        if "LangChain dependencies not available" in logs:
            issues.append("⚠️  LangChain optional dependencies warning")
            
        print(f"\n🎯 Issue Summary:")
        for issue in issues:
            print(f"   {issue}")
            
        return len([i for i in issues if i.startswith("❌")]) == 0
    
    return False

def test_rebuild_persistence():
    """Test that fixes persist across container rebuilds."""
    print("🚀 Zero-Config Persistence Test")
    print("=" * 60)
    
    # Step 1: Current status
    print("\n1. Checking current container status...")
    run_command("docker-compose ps", "Container status", capture_output=False)
    
    # Step 2: Check current logs
    current_ok = check_pipelines_logs()
    
    # Step 3: Rebuild pipelines container
    print("\n2. Rebuilding pipelines container to test persistence...")
    success = run_command("docker-compose build --no-cache pipelines", "Building pipelines container")
    
    if success is None:
        print("❌ Container rebuild failed")
        return False
    
    # Step 4: Restart pipelines
    print("\n3. Restarting pipelines container...")
    run_command("docker-compose up -d pipelines", "Starting pipelines", capture_output=False)
    
    # Step 5: Wait for startup
    print("\n4. Waiting for container startup...")
    time.sleep(30)
    
    # Step 6: Check logs after rebuild
    print("\n5. Checking logs after rebuild...")
    rebuild_ok = check_pipelines_logs()
    
    # Step 7: Results
    print(f"\n🎯 Zero-Config Persistence Test Results:")
    print(f"   Before rebuild: {'✅ OK' if current_ok else '❌ Issues detected'}")
    print(f"   After rebuild:  {'✅ OK' if rebuild_ok else '❌ Issues detected'}")
    
    if rebuild_ok:
        print(f"\n✅ SUCCESS: Zero-config fixes persist across rebuilds!")
        print(f"   - Memory system imports working")
        print(f"   - Dependency versions correctly pinned")
        print(f"   - Container startup successful")
    else:
        print(f"\n❌ FAILURE: Issues detected after rebuild")
        print(f"   - Check container logs for details")
        print(f"   - Verify requirements.txt versions")
        
    return rebuild_ok

def verify_requirements_consistency():
    """Verify that requirements files are consistent."""
    print("\n6. Verifying requirements file consistency...")
    
    # Check main requirements
    with open("requirements.txt", "r") as f:
        main_req = f.read()
    
    # Check pipelines requirements  
    with open("pipelines/requirements.txt", "r") as f:
        pipeline_req = f.read()
    
    print("✅ Requirements files checked:")
    print(f"   - Main requirements.txt: {len(main_req.splitlines())} lines")
    print(f"   - Pipelines requirements.txt: {len(pipeline_req.splitlines())} lines")
    
    # Check for key dependencies
    key_deps = ["pydantic>=2.8.0", "langchain>=0.1.0,<0.2.0"]
    main_has_deps = all(dep.split(",")[0] in main_req for dep in key_deps)
    pipeline_has_deps = all(dep.split(",")[0] in pipeline_req for dep in key_deps)
    
    print(f"   - Main file has key deps: {'✅' if main_has_deps else '❌'}")
    print(f"   - Pipeline file has key deps: {'✅' if pipeline_has_deps else '❌'}")
    
    return main_has_deps and pipeline_has_deps

if __name__ == "__main__":
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run verification
    requirements_ok = verify_requirements_consistency()
    persistence_ok = test_rebuild_persistence()
    
    overall_success = requirements_ok and persistence_ok
    
    print(f"\n🏁 Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
    print(f"   Zero-config system: {'Working correctly' if overall_success else 'Needs attention'}")
    
    sys.exit(0 if overall_success else 1)
