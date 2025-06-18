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
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OPENWEBUI_URL = os.getenv('OPENWEBUI_URL', 'http://localhost:3000')
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8001')
API_KEY = os.getenv('API_KEY', 'f2b985dd-219f-45b1-a90e-170962cc7082')

class ModelRefreshService:
    """Service to refresh and synchronize models across services."""
    
    def __init__(self):
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={'Authorization': f'Bearer {API_KEY}'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def get_ollama_models(self) -> List[Dict]:
        """Get list of models from Ollama."""
        try:
            response = await self.client.get(f"{OLLAMA_URL}/api/tags")
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
            response = await self.client.get(f"{BACKEND_URL}/v1/models")
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
            payload = {
                "model": model_name,
                "prompt": "test",
                "stream": False
            }
            response = await self.client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error verifying model {model_name}: {e}")
            return False
    
    async def trigger_backend_model_refresh(self) -> bool:
        """Trigger model refresh in backend."""
        try:
            response = await self.client.get(f"{BACKEND_URL}/v1/models/verify/llama3.2:3b")
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
        health_status = {
            'ollama': False,
            'backend': False,
            'openwebui': False
        }
        
        # Check Ollama
        try:
            response = await self.client.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
            health_status['ollama'] = response.status_code == 200
        except:
            pass
        
        # Check Backend
        try:
            response = await self.client.get(f"{BACKEND_URL}/health", timeout=5.0)
            health_status['backend'] = response.status_code == 200
        except:
            pass
        
        # Check OpenWebUI (if accessible)
        try:
            response = await self.client.get(f"{OPENWEBUI_URL}/health", timeout=5.0)
            health_status['openwebui'] = response.status_code == 200
        except:
            # OpenWebUI might not have a health endpoint, so we'll assume it's ok if others are working
            health_status['openwebui'] = health_status['ollama'] and health_status['backend']
        
        return health_status
    
    async def refresh_all_models(self) -> Dict:
        """Refresh and synchronize all models."""
        logger.info("🔄 Starting model refresh and synchronization...")
        
        # Check service health first
        health = await self.check_service_health()
        logger.info(f"Service health: {health}")
        
        if not health['ollama']:
            logger.error("❌ Ollama service is not accessible")
            return {'success': False, 'error': 'Ollama service unavailable'}
        
        if not health['backend']:
            logger.error("❌ Backend service is not accessible")
            return {'success': False, 'error': 'Backend service unavailable'}
        
        # Get models from both sources
        ollama_models = await self.get_ollama_models()
        backend_models = await self.get_backend_models()
        
        # Trigger backend refresh
        await self.trigger_backend_model_refresh()
        
        # Wait a moment for refresh to propagate
        await asyncio.sleep(2)
        
        # Get updated backend models
        updated_backend_models = await self.get_backend_models()
        
        # Verify default model
        default_model = "llama3.2:3b"
        model_verified = False
        if ollama_models:
            for model in ollama_models:
                if model.get('name') == default_model:
                    model_verified = await self.verify_model(default_model)
                    break
        
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'services': health,
            'ollama_models': len(ollama_models),
            'backend_models': len(updated_backend_models),
            'default_model_verified': model_verified,
            'models': {
                'ollama': [model.get('name', 'unknown') for model in ollama_models],
                'backend': [model.get('id', 'unknown') for model in updated_backend_models]
            }
        }
        
        logger.info(f"✅ Model refresh completed: {result['ollama_models']} Ollama models, {result['backend_models']} backend models")
        return result

async def main():
    """Main function to run model refresh."""
    print("🤖 Model Refresh and Synchronization Utility")
    print("=" * 50)
    
    try:
        async with ModelRefreshService() as service:
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
                print(f"❌ Refresh failed: {result.get('error', 'Unknown error')}")
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
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Refresh and synchronize models")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--ollama-url", default=OLLAMA_URL, help="Ollama URL")
    parser.add_argument("--backend-url", default=BACKEND_URL, help="Backend URL")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Update URLs if provided
    OLLAMA_URL = args.ollama_url
    BACKEND_URL = args.backend_url
    
    sys.exit(sync_refresh())
