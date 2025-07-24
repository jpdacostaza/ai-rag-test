#!/bin/bash
# Pipelines Container Startup Script
# Ensures correct dependencies for zero-config system

echo "🚀 [PIPELINES STARTUP] Initializing pipeline dependencies..."

# Install/upgrade to correct versions for zero-config compatibility
echo "📦 [PIPELINES STARTUP] Installing compatible LangChain versions..."
pip install --no-cache-dir --upgrade \
    "pydantic>=2.8.0,<2.12.0" \
    "langchain>=0.1.0,<0.2.0" \
    "langchain-community>=0.0.38,<0.1.0" \
    "langchain-openai>=0.0.8,<0.1.0" \
    "langchain-text-splitters>=0.0.1,<0.1.0"

echo "✅ [PIPELINES STARTUP] Dependencies updated for zero-config compatibility"

# Verify no Pydantic import errors
echo "🔍 [PIPELINES STARTUP] Verifying Pydantic compatibility..."
python3 -c "
try:
    from pydantic._internal._utils import can_be_positional
    print('✅ [PIPELINES STARTUP] Pydantic can_be_positional import: SUCCESS')
except ImportError as e:
    print(f'⚠️  [PIPELINES STARTUP] Pydantic can_be_positional import: {e}')
    print('ℹ️  [PIPELINES STARTUP] This is expected with fixed LangChain version')
"

# Test LangChain imports
echo "🔍 [PIPELINES STARTUP] Verifying LangChain compatibility..."
python3 -c "
try:
    import langchain
    print(f'✅ [PIPELINES STARTUP] LangChain version: {langchain.__version__}')
except ImportError as e:
    print(f'❌ [PIPELINES STARTUP] LangChain import failed: {e}')
"

echo "🎯 [PIPELINES STARTUP] Zero-config dependency verification complete"
echo "🚀 [PIPELINES STARTUP] Starting OpenWebUI Pipelines server..."

# Start the original pipelines server
exec "$@"
