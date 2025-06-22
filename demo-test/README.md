# Demo-Test Directory Organization

This directory contains all test files, demo scripts, debug tools, and related utilities organized by category.

## 📁 Directory Structure

### 🧪 `/model-tests/`
Tests specifically for AI models and model management:
- `test_mistral_*.py` - Mistral model testing
- `test_model_*.py` - General model testing 
- `test_ollama_*.py` - Ollama integration testing
- `comprehensive_model_test.py` - Comprehensive model validation

### 💾 `/cache-tests/`
Tests for caching functionality:
- `test_cache_*.py` - Cache hit/miss testing
- `simple_cache_test.py` - Basic cache verification
- `demo_cache_manager.py` - Cache management demos

### 🔗 `/integration-tests/`
Integration and end-to-end tests:
- `test_openwebui_*.py` - OpenWebUI integration testing
- `test_openai_*.py` - OpenAI endpoint testing
- `test_final_*.py` - Final comprehensive tests

### 🔧 `/debug-tools/`
Debugging utilities and tools:
- `debug_*.py` - Various debugging scripts
- `debug-openwebui-models.sh` - Model debugging script

### 🎬 `/demos/`
Demo scripts and examples:
- `demo_*.py` - Feature demonstration scripts
- `demo_adaptive_learning.py` - Adaptive learning demos
- `demo_ai_tools.py` - AI tools showcase

### ⚡ `/performance-tests/`
Performance testing and benchmarking:
- `performance_*.py` - Performance test scripts
- Load testing and optimization tests

### 📊 `/results/`
Test results and reports:
- `*.json` - Test result files
- Test reports and logs
- Performance benchmarks

## 🚀 Quick Start

### Running Model Tests
```bash
cd demo-test/model-tests
python test_mistral_comprehensive.py
```

### Running Cache Tests  
```bash
cd demo-test/cache-tests
python test_cache_comprehensive.py
```

### Running Integration Tests
```bash
cd demo-test/integration-tests
python test_openwebui_validation.py
```

### Running Demos
```bash
cd demo-test/demos
python demo_adaptive_learning.py
```

## 📋 Test Categories

### ✅ Core Functionality Tests
- Model selection and response generation
- Cache hit/miss behavior
- API endpoint validation
- Authentication and authorization

### 🔒 Integration Tests
- OpenWebUI compatibility
- OpenAI API compatibility
- Docker container integration
- Database connectivity

### 📈 Performance Tests
- Response time benchmarks
- Cache performance analysis
- Concurrent request handling
- Memory usage optimization

### 🛠️ Debug and Diagnostic Tools
- Model availability verification
- Cache state inspection
- Error reproduction scripts
- System health checks

## 📝 Naming Conventions

- `test_*.py` - Automated test scripts
- `demo_*.py` - Interactive demonstration scripts  
- `debug_*.py` - Debugging and diagnostic tools
- `comprehensive_*.py` - Full system tests
- `performance_*.py` - Performance benchmarks
- `*_results*.json` - Test result files

## 🔄 Maintenance

All test files have been organized from the root directory into this structured layout for better maintainability and discoverability. 

To add new tests:
1. Place them in the appropriate subdirectory
2. Follow the naming conventions
3. Update this README if adding new categories

---
**Last Updated**: June 22, 2025  
**Organization**: Complete ✅
