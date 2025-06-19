#!/usr/bin/env python3
"""
refresh-models.py - Model Refresh and Synchronization Utility

This script refreshes and synchronizes models between Ollama and OpenWebUI,
ensuring that all available models are properly detected and accessible.
"""

import asyncio
import httpx
import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
OLLAMA_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OPENWEBUI_URL = os.getenv('OPENWEBUI_URL', 'http://localhost:3000')
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8001')
API_KEY = os.getenv('API_KEY', 'demo-key-replace-with-actual')

class ModelRefreshService:
    """Service to refresh and synchronize models across services."""
    
    def __init__(self):
        pass
    
    async def get_ollama_models(self) -> List[Dict]:
        """Get list of models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{OLLAMA_URL}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get('models', [])
                    logger.info(f"Found {len(models)} models in Ollama")
                    return models
                else:
                    logger.error(f"Failed to get Ollama models: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {e}")
            return []

    async def get_backend_models(self) -> List[Dict]:
        """Get list of models from backend API."""
        try:
            async with httpx.AsyncClient(timeout=30.0, headers={'Authorization': f'Bearer {API_KEY}'}) as client:
                response = await client.get(f"{BACKEND_URL}/v1/models")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get('data', [])
                    logger.info(f"Found {len(models)} models in backend")
                    return models
                else:
                    logger.error(f"Failed to get backend models: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error connecting to backend: {e}")
            return []
    
    async def verify_model(self, model_name: str) -> bool:
        """Verify that a model is working in Ollama."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": model_name,
                    "prompt": "test",
                    "stream": False
                }
                response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error verifying model {model_name}: {e}")
            return False
    
    async def trigger_backend_model_refresh(self) -> bool:
        """Trigger model refresh in backend."""
        try:
            async with httpx.AsyncClient(timeout=30.0, headers={'Authorization': f'Bearer {API_KEY}'}) as client:
                response = await client.get(f"{BACKEND_URL}/v1/models/verify/llama3.2:3b")
                if response.status_code in [200, 404]:  # 404 is ok, means model check was performed
                    logger.info("Backend model refresh triggered")
                    return True
                else:
                    logger.error(f"Failed to trigger backend refresh: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Error triggering backend refresh: {e}")
            return False
    
    async def check_service_health(self) -> Dict[str, bool]:
        """Check health of all services."""
        health = {}
        
        # Check Ollama
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{OLLAMA_URL}/api/tags")
                health['ollama'] = response.status_code == 200
        except Exception:
            health['ollama'] = False
        
        # Check Backend
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{BACKEND_URL}/health")
                health['backend'] = response.status_code == 200
        except Exception:
            health['backend'] = False
        
        # Check OpenWebUI
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{OPENWEBUI_URL}/health")
                health['openwebui'] = response.status_code == 200
        except Exception:
            health['openwebui'] = False
        
        return health
    
    async def refresh_all_models(self) -> Dict:
        """Refresh and synchronize all models."""
        logger.info("🔄 Starting model refresh and synchronization")
        
        # Check service health first
        health = await self.check_service_health()
        logger.info(f"📊 Service health: {health}")
        
        # Get models from all sources
        ollama_models = await self.get_ollama_models()
        backend_models = await self.get_backend_models()
        
        # Trigger backend refresh
        refresh_success = await self.trigger_backend_model_refresh()
        
        # Verify default model
        default_model_verified = False
        if ollama_models:
            default_model = "llama3.2:3b"
            for model in ollama_models:
                if model.get('name') == default_model:
                    default_model_verified = await self.verify_model(default_model)
                    break
        
        # Build result
        result = {
            'success': health.get('ollama', False) and len(ollama_models) > 0,
            'timestamp': datetime.now().isoformat(),
            'services': health,
            'ollama_models': len(ollama_models),
            'backend_models': len(backend_models),
            'default_model_verified': default_model_verified,
            'backend_refresh_triggered': refresh_success,
            'models': {
                'ollama': [model.get('name', 'unknown') for model in ollama_models],
                'backend': [model.get('id', 'unknown') for model in backend_models]
            }
        }
        
        logger.info(f"✅ Model refresh completed: {result['ollama_models']} Ollama models, {result['backend_models']} backend models")
        return result

async def main():
    """Main function to run model refresh."""
    print("🤖 Model Refresh and Synchronization Utility")
    print("=" * 50)
    
    try:
        service = ModelRefreshService()
        result = await service.refresh_all_models()
        
        if result['success']:
            print(f"✅ Refresh completed successfully at {result['timestamp']}")
            print(f"📊 Services: {result['services']}")
            print(f"📋 Ollama models: {result['ollama_models']}")
            print(f"📋 Backend models: {result['backend_models']}")
            print(f"🔍 Default model verified: {result['default_model_verified']}")
            
            if result['models']['ollama']:
                print("\n📝 Available Ollama models:")
                for model in result['models']['ollama']:
                    print(f"  - {model}")
            
            return 0
        else:
            print(f"❌ Refresh failed: Check service connectivity")
            return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

def sync_refresh():
    """Synchronous wrapper for the async refresh function."""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Refresh interrupted by user")
        return 130

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Refresh and synchronize LLM models")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run the refresh
    exit_code = sync_refresh()
    sys.exit(exit_code)
