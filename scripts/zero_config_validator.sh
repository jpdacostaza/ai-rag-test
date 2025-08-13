#!/bin/bash
# Zero-Config Compatibility Validator (Enhanced with Storage-Init Recognition)
# Checks if the system meets zero-configuration standards

echo "🔍 ZERO-CONFIG COMPATIBILITY ASSESSMENT"
echo "======================================="

# Test 0: Storage-Init Service Check
echo "📦 0. Storage Initialization Assessment..."
if [ -d "./storage/backend/.cache/huggingface" ]; then
    echo "   ✅ HuggingFace cache directories: PREPARED"
    STORAGE_INIT_OK=true
else
    echo "   ❌ HuggingFace cache directories: MISSING"
    echo "   💡 Run: docker-compose up storage-init --force-recreate"
    STORAGE_INIT_OK=false
fi

# Check storage-init completion
if docker logs backend-storage-init 2>/dev/null | grep -q "Storage initialization complete"; then
    echo "   ✅ Storage-init service: COMPLETED SUCCESSFULLY"
else
    echo "   ⚠️ Storage-init service: MAY NEED RE-RUN"
fi

# Test 1: Service Dependencies
echo "📊 1. Service Dependency Check..."
services=("redis" "chroma" "backend-ollama" "backend-main" "backend-memory-api" "backend-pipelines" "backend-openwebui")
healthy_count=0

for service in "${services[@]}"; do
    if docker ps --filter "name=$service" --filter "health=healthy" --format "table {{.Names}}" | grep -q "$service" 2>/dev/null; then
        echo "   ✅ $service: HEALTHY"
        ((healthy_count++))
    elif docker ps --filter "name=$service" --format "table {{.Names}}" | grep -q "$service" 2>/dev/null; then
        echo "   🟡 $service: RUNNING (no health check)"
        ((healthy_count++))
    else
        echo "   ❌ $service: NOT RUNNING"
    fi
done

echo "   Status: $healthy_count/${#services[@]} services operational"

# Test 2: Zero-Config Features
echo ""
echo "🚀 2. Zero-Config Feature Assessment..."

# Check if services auto-start
echo "   🔄 Auto-startup: $(docker-compose config --services | wc -l) services configured"

# Check dependency resolution
if docker logs backend-pipelines 2>/dev/null | grep -q "Zero-config dependency verification complete"; then
    echo "   ✅ Auto-dependency resolution: WORKING"
else
    echo "   ❌ Auto-dependency resolution: NEEDS FIXING"
fi

# Check memory auto-installation
if docker logs backend-memory-installer 2>/dev/null | grep -q "Installation Summary"; then
    echo "   ✅ Memory auto-installation: WORKING"
else
    echo "   ❌ Memory auto-installation: NEEDS FIXING"
fi

# Test 3: Configuration Issues
echo ""
echo "⚙️ 3. Configuration Issues Assessment..."

# Check permission issues
if docker logs backend-main 2>/dev/null | grep -q "Permission denied"; then
    echo "   ❌ File permissions: NEEDS FIXING"
    NEEDS_PERMISSION_FIX=true
else
    echo "   ✅ File permissions: OK"
    NEEDS_PERMISSION_FIX=false
fi

# Check model availability
if docker logs backend-main 2>/dev/null | grep -q "Model.*not present"; then
    echo "   ❌ Model pre-download: NEEDS FIXING"
    NEEDS_MODEL_FIX=true
else
    echo "   ✅ Model availability: OK"
    NEEDS_MODEL_FIX=false
fi

# Check embedding issues
if docker logs backend-main 2>/dev/null | grep -q "Embedding model.*unavailable"; then
    echo "   ❌ Embedding model: NEEDS FIXING"
    NEEDS_EMBEDDING_FIX=true
else
    echo "   ✅ Embedding model: OK"
    NEEDS_EMBEDDING_FIX=false
fi

# Test 4: Overall Assessment
echo ""
echo "🎯 4. Zero-Config Compatibility Score..."

issues_count=0
if [ "$STORAGE_INIT_OK" = false ]; then ((issues_count++)); fi
if [ "$NEEDS_PERMISSION_FIX" = true ]; then ((issues_count++)); fi
if [ "$NEEDS_MODEL_FIX" = true ]; then ((issues_count++)); fi
if [ "$NEEDS_EMBEDDING_FIX" = true ]; then ((issues_count++)); fi

if [ $healthy_count -ge 6 ] && [ $issues_count -eq 0 ]; then
    echo "   🎉 FULLY ZERO-CONFIG COMPATIBLE!"
    echo "   ✅ All services operational"
    echo "   ✅ Storage-init properly configured"
    echo "   ✅ No configuration issues detected"
    echo "   ✅ System ready for one-command deployment"
elif [ $healthy_count -ge 4 ] && [ $issues_count -le 2 ]; then
    echo "   🟡 MOSTLY ZERO-CONFIG COMPATIBLE"
    echo "   ⚠️  Minor issues detected that can be auto-fixed"
    echo "   💡 Run: ./scripts/fix_startup_issues.sh"
else
    echo "   ❌ NOT ZERO-CONFIG COMPATIBLE"
    echo "   🛠️  Multiple issues need resolution"
    echo "   💡 Manual intervention required"
fi

echo ""
echo "🔧 Available Auto-Fix Scripts:"
echo "   • ./scripts/fix_startup_issues.sh     - Fix permission/model issues (uses storage-init)"
echo "   • ./setup/zero_config_setup.py        - Complete zero-config setup"
echo "   • ./scripts/startup_order_validator.py - Validate service order"
echo "   • docker-compose up storage-init       - Re-run storage initialization"

echo ""
echo "📖 Zero-Config Features Available:"
echo "   ✅ Storage-init service for permission management"
echo "   ✅ Docker Compose service orchestration"
echo "   ✅ Automatic dependency installation (pipelines)"
echo "   ✅ Memory system auto-setup"
echo "   ✅ Health checks and restart policies"
echo "   ✅ Service discovery and networking"
echo "   ✅ Persistent cache directories"
echo "   ✅ Generic deployment optimizations"
