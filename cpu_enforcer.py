"""
CPU Enforcer Module
===================

This module ensures that all machine learning libraries operate in CPU-only mode
and prevents any attempt to use GPU/CUDA resources.
"""

import os
import logging


def enforce_cpu_only_mode():
    """
    Enforce CPU-only mode for all ML libraries and prevent GPU usage.
    This should be called early in the application startup.
    """
    # Set environment variables to force CPU-only operation
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = ""
    os.environ["FORCE_CPU_ONLY"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["NUMBA_DISABLE_CUDA"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    
    logging.info("🔧 CPU-only mode enforced via environment variables")


def verify_cpu_only_setup():
    """
    Verify that all ML libraries are configured to use CPU only.
    Returns a dict with verification results.
    """
    results = {
        "torch_available": False,
        "torch_cuda_available": False,
        "torch_device": "unknown",
        "sentence_transformers_device": "unknown",
        "environment_vars": {},
        "warnings": [],
        "status": "unknown"
    }
    
    # Check environment variables
    cpu_env_vars = [
        "CUDA_VISIBLE_DEVICES",
        "FORCE_CPU_ONLY", 
        "TOKENIZERS_PARALLELISM",
        "NUMBA_DISABLE_CUDA"
    ]
    
    for var in cpu_env_vars:
        results["environment_vars"][var] = os.environ.get(var, "not_set")
    
    try:
        # Check PyTorch configuration
        import torch
        results["torch_available"] = True
        results["torch_cuda_available"] = torch.cuda.is_available()
        results["torch_device"] = str(torch.device('cpu'))
        
        if torch.cuda.is_available():
            results["warnings"].append("⚠️  PyTorch reports CUDA is available - this should be false in CPU-only mode")
            results["status"] = "warning"
        else:
            logging.info("✅ PyTorch CUDA is disabled")
            
    except ImportError:
        results["warnings"].append("PyTorch not available")
    except Exception as e:
        results["warnings"].append(f"Error checking PyTorch: {e}")
    
    try:
        # Check if sentence-transformers respects CPU-only mode
        from sentence_transformers import SentenceTransformer
        import tempfile
        import torch
        
        # Create a minimal test model to verify device usage
        test_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        
        # Check if the model is actually on CPU
        if hasattr(test_model, 'device') and 'cpu' in str(test_model.device):
            results["sentence_transformers_device"] = "cpu"
            logging.info("✅ SentenceTransformers is using CPU")
        elif hasattr(test_model, '_modules'):
            # Check the underlying modules
            for name, module in test_model._modules.items():
                if hasattr(module, 'device'):
                    device = str(module.device)
                    if 'cuda' in device.lower():
                        results["warnings"].append(f"⚠️  SentenceTransformers module {name} is on GPU: {device}")
                        results["status"] = "warning"
                        break
            else:
                results["sentence_transformers_device"] = "cpu"
                logging.info("✅ SentenceTransformers modules are on CPU")
                        
    except ImportError:
        results["warnings"].append("SentenceTransformers not available")
    except Exception as e:
        results["warnings"].append(f"Error checking SentenceTransformers: {e}")
    
    # Determine overall status
    if not results["warnings"]:
        results["status"] = "cpu_only_verified"
        logging.info("✅ CPU-only mode verified successfully")
    elif results["status"] != "warning":
        results["status"] = "verification_incomplete"
        
    return results


def log_cpu_verification_results(results):
    """Log the CPU verification results in a readable format."""
    logging.info("🔍 CPU-Only Mode Verification Results:")
    logging.info("=" * 50)
    
    # Environment variables
    logging.info("Environment Variables:")
    for var, value in results["environment_vars"].items():
        logging.info(f"  {var}: {value}")
    
    # Library status
    logging.info(f"PyTorch Available: {results['torch_available']}")
    if results["torch_available"]:
        logging.info(f"PyTorch CUDA Available: {results['torch_cuda_available']}")
        logging.info(f"PyTorch Device: {results['torch_device']}")
    
    logging.info(f"SentenceTransformers Device: {results['sentence_transformers_device']}")
    
    # Warnings
    if results["warnings"]:
        logging.warning("Warnings:")
        for warning in results["warnings"]:
            logging.warning(f"  {warning}")
    
    # Overall status
    status_emoji = {
        "cpu_only_verified": "✅",
        "warning": "⚠️",
        "verification_incomplete": "❓",
        "unknown": "❓"
    }
    
    emoji = status_emoji.get(results["status"], "❓")
    logging.info(f"Overall Status: {emoji} {results['status']}")
    logging.info("=" * 50)


if __name__ == "__main__":
    # Enable logging for testing
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Enforce CPU-only mode
    enforce_cpu_only_mode()
    
    # Verify setup
    results = verify_cpu_only_setup()
    log_cpu_verification_results(results)
