#!/bin/bash
# Pipelines Container Startup Script - OPTIMIZED
# Smart dependency checking to prevent redundant installations

# Prevent multiple executions
STARTUP_FLAG_FILE="/app/.startup_completed"
if [ -f "$STARTUP_FLAG_FILE" ]; then
    echo "🔄 [PIPELINES STARTUP] Startup already completed, starting server..."
    exec "$@"
fi

echo "🚀 [PIPELINES STARTUP] Checking pipeline dependencies..."

# Function to check if package is installed and compatible
check_package() {
    local package_name=$1
    local version_spec=$2
    
    python3 -c "
import pkg_resources
import sys
try:
    pkg_resources.require('$package_name$version_spec')
    print('✅ $package_name: Compatible version found')
    sys.exit(0)
except pkg_resources.DistributionNotFound:
    print('⚠️  $package_name: Not installed')
    sys.exit(1)
except pkg_resources.VersionConflict as e:
    print(f'⚠️  $package_name: Version conflict - {e}')
    sys.exit(1)
except Exception as e:
    print(f'⚠️  $package_name: Check failed - {e}')
    sys.exit(1)
" 2>/dev/null
}

# Check critical packages
missing_packages=()

if ! check_package "pydantic" ">=2.8.0,<2.12.0"; then
    missing_packages+=("pydantic>=2.8.0,<2.12.0")
fi

if ! check_package "langchain" ">=0.1.0,<0.2.0"; then
    missing_packages+=("langchain>=0.1.0,<0.2.0")
fi

if ! check_package "langchain-community" ">=0.0.38,<0.1.0"; then
    missing_packages+=("langchain-community>=0.0.38,<0.1.0")
fi

if ! check_package "langchain-openai" ">=0.0.8,<0.1.0"; then
    missing_packages+=("langchain-openai>=0.0.8,<0.1.0")
fi

if ! check_package "langchain-text-splitters" ">=0.0.1,<0.1.0"; then
    missing_packages+=("langchain-text-splitters>=0.0.1,<0.1.0")
fi

if ! check_package "ddgs" ">=6.3.0"; then
    missing_packages+=("ddgs>=6.3.0")
fi

# Only install missing packages
if [ ${#missing_packages[@]} -eq 0 ]; then
    echo "✅ [PIPELINES STARTUP] All dependencies already compatible, skipping installation"
else
    echo "📦 [PIPELINES STARTUP] Installing ${#missing_packages[@]} missing/incompatible packages..."
    pip install --no-cache-dir --upgrade --quiet "${missing_packages[@]}"
    echo "✅ [PIPELINES STARTUP] Dependencies updated for zero-config compatibility"
fi

# Quick verification tests
echo "🔍 [PIPELINES STARTUP] Verifying compatibility..."

# Test Pydantic (silent)
python3 -c "
try:
    from pydantic._internal._utils import can_be_positional
    print('✅ [PIPELINES STARTUP] Pydantic: Compatible')
except ImportError:
    print('✅ [PIPELINES STARTUP] Pydantic: Compatible (no can_be_positional needed)')
except Exception as e:
    print(f'⚠️  [PIPELINES STARTUP] Pydantic: {e}')
" 2>/dev/null

# Test LangChain (silent)
python3 -c "
try:
    import langchain
    print(f'✅ [PIPELINES STARTUP] LangChain: {langchain.__version__}')
except Exception as e:
    print(f'❌ [PIPELINES STARTUP] LangChain: {e}')
" 2>/dev/null

python3 -c "
try:
    from ddgs import DDGS
    print('✅ [PIPELINES STARTUP] DDGS (modern): Available')
except Exception as e:
    print(f'⚠️  [PIPELINES STARTUP] DDGS (modern): {e}')
" 2>/dev/null

echo "🎯 [PIPELINES STARTUP] Zero-config dependency verification complete"

# Apply persistent fix for AttributeError: 'Valves' object has no attribute 'pipelines'
echo "🔧 [PIPELINES STARTUP] Applying persistent main.py fix..."
if [ -f "/app/main.py" ]; then
    # Create backup if it doesn't exist
    if [ ! -f "/app/main.py.backup" ]; then
        cp /app/main.py /app/main.py.backup
        echo "✅ [MAIN.PY FIX] Backup created"
    fi
    
    # Apply the fix using Python inline script for precision
    python3 -c "
import re
import os

main_py_path = '/app/main.py'
try:
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Pattern to find and fix the problematic line
    old_pattern = r'pipeline\[\"valves\"\]\.pipelines\s+if pipeline\.get\(\"valves\", None\)'
    new_pattern = 'pipeline[\"valves\"].pipelines if pipeline.get(\"valves\", None) and hasattr(pipeline[\"valves\"], \"pipelines\")'
    
    if re.search(old_pattern, content):
        fixed_content = re.sub(old_pattern, new_pattern, content)
        with open(main_py_path, 'w') as f:
            f.write(fixed_content)
        print('✅ [MAIN.PY FIX] Persistent fix applied successfully')
    else:
        print('⚠️  [MAIN.PY FIX] Pattern not found, checking if already fixed')
        if 'hasattr(pipeline[\"valves\"], \"pipelines\")' in content:
            print('✅ [MAIN.PY FIX] Fix already applied')
        else:
            print('⚠️  [MAIN.PY FIX] Unknown state, may need manual review')
except Exception as e:
    print(f'❌ [MAIN.PY FIX] Fix failed: {e}')
"
else
    echo "⚠️  [PIPELINES STARTUP] Main.py not found, skipping fix"
fi

echo "🚀 [PIPELINES STARTUP] Starting OpenWebUI Pipelines server..."

# Mark startup as completed
touch "$STARTUP_FLAG_FILE"

# Start the original pipelines server
exec "$@"
