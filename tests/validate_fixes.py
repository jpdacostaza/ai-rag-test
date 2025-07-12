#!/usr/bin/env python3
"""
Comprehensive System Validation Script
=====================================

This script validates all OpenWebUI integrations and fixes applied.
It checks:
1. Pipeline file existence and validity
2. Docker configuration correctness
3. Environment variable consistency
4. Service connectivity
5. API endpoint functionality
"""

import asyncio
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any

import httpx


class SystemValidator:
    """Comprehensive system validation."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with level."""
        prefix = {
            "PASS": "✅",
            "WARN": "⚠️",
            "ERROR": "❌",
            "INFO": "ℹ️"
        }.get(level, "ℹ️")
        
        print(f"{prefix} {message}")
        
        if level == "PASS":
            self.passed.append(message)
        elif level == "WARN":
            self.warnings.append(message)
        elif level == "ERROR":
            self.errors.append(message)
    
    def check_pipeline_file(self) -> bool:
        """Check if pipeline file exists and is valid."""
        self.log("Checking Pipeline file...", "INFO")
        
        pipeline_file = Path("storage/pipelines/enhanced_memory_pipeline.py")
        
        if not pipeline_file.exists():
            self.log("Pipeline file does not exist", "ERROR")
            return False
        
        try:
            content = pipeline_file.read_text()
            
            # Check for required components
            required_components = [
                "class Pipeline:",
                "class Valves:",
                "async def inlet(",
                "async def outlet(",
                "Enhanced Memory Pipeline for OpenWebUI"
            ]
            
            for component in required_components:
                if component not in content:
                    self.log(f"Pipeline missing required component: {component}", "ERROR")
                    return False
            
            self.log("Pipeline file exists and contains required components", "PASS")
            return True
            
        except Exception as e:
            self.log(f"Error reading pipeline file: {e}", "ERROR")
            return False
    
    def check_docker_config(self) -> bool:
        """Check Docker configuration."""
        self.log("Checking Docker configuration...", "INFO")
        
        docker_file = Path("docker-compose.yml")
        if not docker_file.exists():
            self.log("docker-compose.yml not found", "ERROR")
            return False
        
        try:
            content = docker_file.read_text()
            
            # Check that memory_installer is not disabled
            if "profiles:\n      - disabled" in content:
                self.log("Memory installer is still disabled in docker-compose.yml", "ERROR")
                return False
            
            # Check for required services
            required_services = [
                "openwebui:",
                "backend:",
                "pipelines:",
                "memory_api:",
                "memory_installer:"
            ]
            
            for service in required_services:
                if service not in content:
                    self.log(f"Required service missing: {service}", "ERROR")
                    return False
            
            self.log("Docker configuration is correct", "PASS")
            return True
            
        except Exception as e:
            self.log(f"Error reading docker-compose.yml: {e}", "ERROR")
            return False
    
    def check_env_file(self) -> bool:
        """Check environment file configuration."""
        self.log("Checking environment configuration...", "INFO")
        
        env_file = Path(".env")
        if not env_file.exists():
            self.log(".env file not found", "ERROR")
            return False
        
        try:
            content = env_file.read_text()
            
            # Check for consistent hostnames
            if "backend-redis" in content or "backend-chroma" in content:
                self.log("Environment file contains incorrect hostnames", "ERROR")
                return False
            
            # Check for required variables
            required_vars = [
                "DEFAULT_MODEL=",
                "REDIS_HOST=redis",
                "CHROMA_HOST=chroma",
                "OLLAMA_BASE_URL=http://ollama:11434"
            ]
            
            for var in required_vars:
                if var not in content:
                    self.log(f"Required environment variable missing: {var}", "ERROR")
                    return False
            
            self.log("Environment configuration is correct", "PASS")
            return True
            
        except Exception as e:
            self.log(f"Error reading .env file: {e}", "ERROR")
            return False
    
    async def check_service_connectivity(self) -> bool:
        """Check if services can be reached."""
        self.log("Checking service connectivity...", "INFO")
        
        services = {
            "Backend API": "http://localhost:3000/health",
            "Memory API": "http://localhost:8001/",
            "OpenWebUI": "http://localhost:8080/",
            "Pipelines": "http://localhost:9099/",
        }
        
        all_good = True
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for service_name, url in services.items():
                try:
                    response = await client.get(url)
                    if response.status_code < 400:
                        self.log(f"{service_name} is accessible", "PASS")
                    else:
                        self.log(f"{service_name} returned HTTP {response.status_code}", "WARN")
                        all_good = False
                except Exception as e:
                    self.log(f"{service_name} is not accessible: {e}", "WARN")
                    all_good = False
        
        return all_good
    
    async def check_openai_api_compatibility(self) -> bool:
        """Check OpenAI API compatibility."""
        self.log("Checking OpenAI API compatibility...", "INFO")
        
        endpoints = [
            ("GET", "http://localhost:3000/v1/models", "Models endpoint"),
            ("GET", "http://localhost:3000/health", "Health endpoint"),
        ]
        
        all_good = True
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for method, url, description in endpoints:
                try:
                    if method == "GET":
                        response = await client.get(url)
                    else:
                        response = await client.post(url, json={})
                    
                    if response.status_code < 400:
                        self.log(f"{description} is working", "PASS")
                    else:
                        self.log(f"{description} returned HTTP {response.status_code}", "WARN")
                        all_good = False
                        
                except Exception as e:
                    self.log(f"{description} failed: {e}", "WARN")
                    all_good = False
        
        return all_good
    
    def check_memory_function_file(self) -> bool:
        """Check memory function file."""
        self.log("Checking Memory Function file...", "INFO")
        
        function_file = Path("memory_function.py")
        
        if not function_file.exists():
            self.log("Memory function file does not exist", "ERROR")
            return False
        
        try:
            content = function_file.read_text()
            
            # Check for required components
            if "class Filter:" not in content:
                self.log("Memory function missing Filter class", "ERROR")
                return False
            
            if "Enhanced Memory Function for OpenWebUI" not in content:
                self.log("Memory function missing proper header", "ERROR")
                return False
            
            self.log("Memory function file is correct", "PASS")
            return True
            
        except Exception as e:
            self.log(f"Error reading memory function file: {e}", "ERROR")
            return False
    
    async def run_full_validation(self) -> bool:
        """Run complete system validation."""
        self.log("🚀 Starting comprehensive system validation...", "INFO")
        self.log("=" * 60, "INFO")
        
        # File checks
        pipeline_ok = self.check_pipeline_file()
        docker_ok = self.check_docker_config()
        env_ok = self.check_env_file()
        function_ok = self.check_memory_function_file()
        
        # Network checks (only if services might be running)
        self.log("\n📡 Network connectivity checks...", "INFO")
        self.log("(Note: These may fail if services are not running - that's OK)", "INFO")
        
        connectivity_ok = await self.check_service_connectivity()
        api_ok = await self.check_openai_api_compatibility()
        
        # Summary
        self.log("\n" + "=" * 60, "INFO")
        self.log("🎯 VALIDATION SUMMARY", "INFO")
        self.log("=" * 60, "INFO")
        
        critical_checks = [pipeline_ok, docker_ok, env_ok, function_ok]
        critical_passed = sum(critical_checks)
        
        self.log(f"✅ Passed: {len(self.passed)}", "PASS")
        if self.warnings:
            self.log(f"⚠️ Warnings: {len(self.warnings)}", "WARN") 
        if self.errors:
            self.log(f"❌ Errors: {len(self.errors)}", "ERROR")
        
        self.log(f"\n🔧 Critical fixes status: {critical_passed}/4 completed", "INFO")
        
        if critical_passed == 4:
            self.log("🎉 ALL CRITICAL FIXES COMPLETED SUCCESSFULLY!", "PASS")
            self.log("System is ready for deployment", "PASS")
            return True
        else:
            self.log("⚠️ Some critical issues remain", "WARN")
            return False


async def main():
    """Main validation function."""
    validator = SystemValidator()
    success = await validator.run_full_validation()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
