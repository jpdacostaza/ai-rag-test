#!/usr/bin/env python3
"""
Auto-installer for OpenWebUI Pipelines
=====================================

This script automatically installs the Enhanced Memory Pipeline into OpenWebUI's Pipelines system.
It waits for the Pipelines service to be ready, then uploads the pipeline.
"""

import requests
import time
import os
import json
import sys
from pathlib import Path

# Configuration
PIPELINES_URL = os.getenv("PIPELINES_URL", "http://pipelines:9099")
PIPELINE_FILE = os.getenv("PIPELINE_FILE", "/app/memory_pipeline.py")
MAX_RETRIES = 30
RETRY_DELAY = 10

def log(message: str, level: str = "INFO"):
    """Log messages with timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] [Pipeline Installer] {message}")

def wait_for_pipelines_service():
    """Wait for the Pipelines service to be ready."""
    log("Waiting for Pipelines service to be ready...")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(f"{PIPELINES_URL}/health", timeout=5)
            if response.status_code == 200:
                log("Pipelines service is ready!")
                return True
        except requests.exceptions.RequestException as e:
            log(f"Attempt {attempt + 1}/{MAX_RETRIES}: Pipelines service not ready yet - {e}")
            time.sleep(RETRY_DELAY)
    
    log("Failed to connect to Pipelines service after maximum retries", "ERROR")
    return False

def check_pipeline_exists():
    """Check if the Enhanced Memory Pipeline already exists."""
    try:
        response = requests.get(f"{PIPELINES_URL}/api/v1/pipelines", timeout=10)
        if response.status_code == 200:
            pipelines = response.json()
            for pipeline in pipelines:
                if pipeline.get("name") == "Enhanced Memory Pipeline":
                    log("Enhanced Memory Pipeline already exists")
                    return True
        return False
    except requests.exceptions.RequestException as e:
        log(f"Error checking existing pipelines: {e}", "ERROR")
        return False

def upload_pipeline():
    """Upload the Enhanced Memory Pipeline to Pipelines service."""
    if not os.path.exists(PIPELINE_FILE):
        log(f"Pipeline file not found: {PIPELINE_FILE}", "ERROR")
        return False
    
    log(f"Reading pipeline file: {PIPELINE_FILE}")
    
    try:
        with open(PIPELINE_FILE, 'r', encoding='utf-8') as f:
            pipeline_content = f.read()
        
        # Prepare the upload payload
        files = {
            'file': ('memory_pipeline.py', pipeline_content, 'text/x-python')
        }
        
        log("Uploading Enhanced Memory Pipeline...")
        response = requests.post(
            f"{PIPELINES_URL}/api/v1/pipelines/upload",
            files=files,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            log("[OK] Enhanced Memory Pipeline uploaded successfully!")
            return True
        else:
            log(f"[FAIL] Failed to upload pipeline: {response.status_code} - {response.text}", "ERROR")
            return False
            
    except Exception as e:
        log(f"[FAIL] Error uploading pipeline: {str(e)}", "ERROR")
        return False

def configure_pipeline():
    """Configure the Enhanced Memory Pipeline with proper settings."""
    try:
        # Get pipeline info
        response = requests.get(f"{PIPELINES_URL}/api/v1/pipelines", timeout=10)
        if response.status_code != 200:
            log("Failed to get pipeline list for configuration", "ERROR")
            return False
        
        pipelines = response.json()
        memory_pipeline = None
        
        for pipeline in pipelines:
            if pipeline.get("name") == "Enhanced Memory Pipeline":
                memory_pipeline = pipeline
                break
        
        if not memory_pipeline:
            log("Enhanced Memory Pipeline not found for configuration", "ERROR")
            return False
        
        pipeline_id = memory_pipeline.get("id")
        
        # Configure valves (pipeline settings)
        valves_config = {
            "backend_url": "http://backend:3000",
            "memory_threshold": 0.05,
            "max_memories": 10,
            "debug": True
        }
        
        log("Configuring pipeline valves...")
        response = requests.post(
            f"{PIPELINES_URL}/api/v1/pipelines/{pipeline_id}/valves",
            json=valves_config,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            log("[OK] Pipeline valves configured successfully!")
            return True
        else:
            log(f"[WARN] Failed to configure pipeline valves: {response.status_code} - {response.text}", "WARN")
            return True  # Pipeline still works, just not optimally configured
            
    except Exception as e:
        log(f"[WARN] Error configuring pipeline: {str(e)}", "WARN")
        return True  # Pipeline still works

def main():
    """Main installation process."""
    log("=== Enhanced Memory Pipeline Auto-Installer ===")
    
    # Step 1: Wait for Pipelines service
    if not wait_for_pipelines_service():
        log("[FAIL] Installation failed: Pipelines service unavailable", "ERROR")
        sys.exit(1)
    
    # Step 2: Check if pipeline already exists
    if check_pipeline_exists():
        log("[OK] Enhanced Memory Pipeline is already installed")
        return
    
    # Step 3: Upload the pipeline
    if not upload_pipeline():
        log("[FAIL] Installation failed: Could not upload pipeline", "ERROR")
        sys.exit(1)
    
    # Step 4: Configure the pipeline
    if configure_pipeline():
        log("[OK] Pipeline configuration completed")
    
    log(" Enhanced Memory Pipeline installation completed successfully!")
    log("")
    log("Next steps:")
    log("1. Go to OpenWebUI Admin Panel > Settings > Connections")
    log("2. Add Pipelines connection: http://localhost:9099 with key: 0p3n-w3bu!")
    log("3. Go to Admin Panel > Settings > Pipelines")
    log("4. Verify 'Enhanced Memory Pipeline' is listed")
    log("5. Use models with the Pipelines icon for memory functionality")

if __name__ == "__main__":
    main()
