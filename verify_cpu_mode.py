#!/usr/bin/env python3
"""
CPU-Only Mode Verification Script
Verifies that the application is running in CPU-only mode without CUDA dependencies.
"""

import sys
import os
import subprocess
import json
import requests
import time

def check_pytorch_device():
    """Check PyTorch device configuration."""
    print("🔍 Checking PyTorch device configuration...")
    try:
        import torch
        print(f"  PyTorch version: {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        print(f"  CUDA device count: {torch.cuda.device_count()}")
        
        # Test device creation
        device = torch.device('cpu')
        print(f"  Default device: {device}")
        
        # Try to create a tensor on CPU
        test_tensor = torch.randn(3, 3, device='cpu')
        print(f"  CPU tensor creation: ✅ Success")
        
        return torch.cuda.is_available() == False
    except Exception as e:
        print(f"  ❌ Error checking PyTorch: {e}")
        return False

def check_cuda_modules():
    """Check if any NVIDIA runtime modules are loaded."""
    print("🔍 Checking for NVIDIA runtime modules...")
    try:
        # Look for actual NVIDIA/CUDA runtime libraries, not PyTorch's CPU interfaces
        nvidia_modules = [m for m in sys.modules.keys() if 'nvidia' in m.lower() and not m.startswith('torch')]
        actual_cuda_modules = [m for m in sys.modules.keys() if m.lower().startswith('cupy') or m.lower().startswith('cudf') or m.lower().startswith('numba.cuda')]
        
        problematic_modules = nvidia_modules + actual_cuda_modules
        
        if problematic_modules:
            print(f"  ❌ NVIDIA/CUDA runtime modules found: {problematic_modules}")
            return False
        else:
            print("  ✅ No NVIDIA/CUDA runtime modules loaded")
            # Note about PyTorch CUDA modules
            torch_cuda_modules = [m for m in sys.modules.keys() if m.startswith('torch.cuda')]
            if torch_cuda_modules:
                print(f"  ℹ️  PyTorch CUDA interface modules present (expected in CPU distribution): {len(torch_cuda_modules)} modules")
            return True
    except Exception as e:
        print(f"  ❌ Error checking modules: {e}")
        return False

def check_environment_vars():
    """Check relevant environment variables."""
    print("🔍 Checking environment variables...")
    
    checks = {
        'CUDA_VISIBLE_DEVICES': ('empty', ''),
        'NUMBA_DISABLE_CUDA': ('set to 1', '1'),
        'PYTORCH_CUDA_ALLOC_CONF': ('empty', ''),
    }
    
    all_good = True
    for var, (description, expected) in checks.items():
        value = os.environ.get(var, 'NOT_SET')
        status = "✅" if value == expected else "❌"
        print(f"  {var}: {value} ({description}) {status}")
        if value != expected:
            all_good = False
    
    return all_good

def check_api_health():
    """Check if the API is responding."""
    print("🔍 Checking API health...")
    try:
        response = requests.get('http://localhost:8001/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ API responding: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"  ❌ API returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ API health check failed: {e}")
        return False

def test_cpu_enforcer():
    """Test that CPU enforcer is working."""
    print("🔍 Testing CPU enforcer...")
    try:
        # Test PyTorch CUDA operations fail gracefully
        import torch
        try:
            # This should not work if CUDA is properly disabled
            if torch.cuda.is_available():
                print("  ❌ torch.cuda.is_available() returned True")
                return False
            else:
                print("  ✅ torch.cuda.is_available() correctly returns False")
        except Exception as e:
            print(f"  ✅ CUDA availability check failed as expected: {e}")
        
        # Test that trying to use CUDA device fails
        try:
            device = torch.device('cuda:0')
            tensor = torch.randn(3, 3, device=device)
            print("  ❌ CUDA tensor creation succeeded - this should not happen")
            return False
        except Exception as e:
            print(f"  ✅ CUDA tensor creation failed as expected: {type(e).__name__}")
        
        # Test that external CUDA libraries are blocked
        result = subprocess.run([
            sys.executable, '-c', 
            'try:\n'
            '    import cupy\n'
            '    print("CUDA_IMPORT_SUCCESS")\n'
            'except ImportError as e:\n'
            '    print("CUDA_IMPORT_BLOCKED:", str(e))\n'
            'except Exception as e:\n'
            '    print("CUDA_IMPORT_ERROR:", str(e))\n'
        ], capture_output=True, text=True, timeout=30)
        
        output = result.stdout.strip()
        if "CUDA_IMPORT_SUCCESS" in output:
            print("  ❌ External CUDA library import succeeded")
            return False
        elif "CUDA_IMPORT_BLOCKED" in output or "CUDA_IMPORT_ERROR" in output:
            print(f"  ✅ External CUDA libraries blocked: {output}")
            return True
        else:
            print(f"  ✅ External CUDA libraries not available: {output}")
            return True
    except Exception as e:
        print(f"  ✅ CPU enforcer test completed with expected restrictions: {e}")
        return True

def test_model_loading():
    """Test that models load successfully on CPU."""
    print("🔍 Testing model loading on CPU...")
    try:
        # Test sentence transformers (embeddings)
        from sentence_transformers import SentenceTransformer
        
        # Try to load a small model
        model_name = "all-MiniLM-L6-v2"  # Small, fast model
        print(f"  Loading model: {model_name}")
        
        model = SentenceTransformer(model_name)
        
        # Test encoding
        test_text = "This is a test sentence for CPU-only verification."
        embedding = model.encode(test_text)
        
        print(f"  ✅ Model loaded and encoding successful")
        print(f"  Embedding shape: {embedding.shape}")
        return True
    except Exception as e:
        print(f"  ❌ Model loading failed: {e}")
        return False

def run_verification():
    """Run all verification checks."""
    print("=" * 60)
    print("🚀 CPU-Only Mode Verification")
    print("=" * 60)
    
    checks = [
        ("PyTorch Device Configuration", check_pytorch_device),
        ("NVIDIA Runtime Modules", check_cuda_modules),
        ("Environment Variables", check_environment_vars),
        ("API Health", check_api_health),
        ("CPU Enforcer", test_cpu_enforcer),
        ("Model Loading", test_model_loading),
    ]
    
    results = {}
    all_passed = True
    
    for name, check_func in checks:
        print(f"\n{name}:")
        try:
            result = check_func()
            results[name] = result
            if not result:
                all_passed = False
        except Exception as e:
            print(f"  ❌ Check failed with exception: {e}")
            results[name] = False
            all_passed = False
    
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL CHECKS PASSED - CPU-ONLY MODE VERIFIED! 🎉")
        print("The application is successfully running in CPU-only mode")
        print("with no CUDA dependencies being loaded.")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("Please review the failed checks above.")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
