# Shell Script Quick Reference

## PowerShell (Windows) - `setup-api-keys.ps1`

### Basic Usage
```powershell
# Show help
.\setup-api-keys.ps1 -Help

# Check configuration status
.\setup-api-keys.ps1 -Status

# Run interactive setup
.\setup-api-keys.ps1 -Setup

# Quick environment variable setup
.\setup-api-keys.ps1 -Env

# Test current configuration
.\setup-api-keys.ps1 -Test

# Interactive menu (default)
.\setup-api-keys.ps1
```

### Features
- ✅ Colorized output with emojis
- ✅ Dependency checking (Python, packages)
- ✅ Configuration file status
- ✅ Environment variable detection
- ✅ Tool integration verification
- ✅ Interactive menus
- ✅ Quick environment setup

## Bash (Linux/macOS) - `setup-api-keys.sh`

### Basic Usage
```bash
# Make executable first
chmod +x setup-api-keys.sh

# Show help
./setup-api-keys.sh --help

# Check configuration status
./setup-api-keys.sh --status

# Run interactive setup
./setup-api-keys.sh --setup

# Quick environment variable setup
./setup-api-keys.sh --env

# Test current configuration
./setup-api-keys.sh --test

# Interactive menu (default)
./setup-api-keys.sh
```

### Features
- ✅ Cross-platform bash compatibility
- ✅ Colorized output with emojis
- ✅ Error handling with `set -e`
- ✅ Dependency validation
- ✅ Configuration analysis
- ✅ Interactive workflows

## Quick Setup Workflows

### Option 1: Environment Variables (Temporary)
```powershell
# PowerShell
.\setup-api-keys.ps1 -Env
```
```bash
# Bash
./setup-api-keys.sh --env
```

### Option 2: Configuration File (Persistent)
```powershell
# PowerShell
.\setup-api-keys.ps1 -Setup
```
```bash
# Bash
./setup-api-keys.sh --setup
```

### Option 3: Manual Configuration
```bash
# Copy example file
cp openwebui_api_keys.example.json openwebui_api_keys.json
# Edit with your keys
nano openwebui_api_keys.json
```

## Testing Your Setup

After configuration, test with:
```powershell
# PowerShell
.\setup-api-keys.ps1 -Test
```
```bash
# Bash
./setup-api-keys.sh --test
```

Or run the diagnostic tools directly:
```bash
python debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py
python debug/archived/demo-test/debug-tools/test_memory_cross_chat.py
```

## Advanced Usage

### User-Specific Keys
```bash
python debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py --user=john
```

### Environment-Specific Keys
```bash
python debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py --env=production
```

### Programmatic Access
```python
from api_key_manager import APIKeyManager
manager = APIKeyManager()
credentials = manager.get_key(user="john", environment="production")
```
