# OpenWebUI API Key Management System

This system provides secure storage and automated retrieval of OpenWebUI API keys for project automation and user lookup.

## Quick Start

### 1. Setup API Keys

Run the interactive setup:
```bash
python api_key_manager.py
```

Or set environment variables:
```bash
export OPENWEBUI_API_KEY="your-api-key-here"
export OPENWEBUI_BASE_URL="http://localhost:3000"
```

### 2. Use Updated Tools

The diagnostic and test tools now automatically use stored API keys:

```bash
# Use default key
python debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py

# Use specific user's key
python debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py --user=john

# Use environment-specific key
python debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py --env=production
```

## API Key Storage Options

### 1. Configuration File (Recommended)

The system uses `openwebui_api_keys.json` for secure key storage:

```json
{
  "default": {
    "api_key": "sk-your-default-key-here",
    "base_url": "http://localhost:3000",
    "description": "Default OpenWebUI instance"
  },
  "users": {
    "john": {
      "api_key": "sk-john-key-here",
      "base_url": "http://localhost:3000",
      "email": "john@example.com",
      "description": "John's personal key"
    }
  },
  "environments": {
    "development": {
      "api_key": "sk-dev-key-here",
      "base_url": "http://localhost:3000"
    },
    "production": {
      "api_key": "sk-prod-key-here",
      "base_url": "https://your-openwebui-domain.com"
    }
  }
}
```

### 2. Environment Variables

Set these for temporary or CI/CD usage:
```bash
OPENWEBUI_API_KEY="your-api-key-here"
OPENWEBUI_BASE_URL="http://localhost:3000"
```

## Key Retrieval Priority

The system uses this fallback order:

1. **Environment Variables** (`OPENWEBUI_API_KEY`, `OPENWEBUI_BASE_URL`)
2. **User-specific key** (if `--user=username` specified)
3. **Environment-specific key** (if `--env=environment` specified)
4. **Default key** from config file
5. **Manual input** (prompts user if no keys found)

## Security Features

### File Protection
- Config file is automatically set to read-only for owner (Unix systems)
- `.gitignore` rules prevent accidental commits
- Example file provided for reference

### Secure Storage
- Keys stored locally only
- No cloud synchronization
- Clear separation of users and environments

## Using the API Key Manager

### Programmatic Usage

```python
from api_key_manager import APIKeyManager

# Initialize manager
manager = APIKeyManager()

# Get key with fallback logic
credentials = manager.get_key(user="john", environment="production")
if credentials:
    api_key = credentials["api_key"]
    base_url = credentials["base_url"]
    print(f"Using key from: {credentials['source']}")

# Add a new user
manager.add_user_key(
    username="alice",
    api_key="sk-alice-key-here",
    base_url="http://localhost:3000",
    email="alice@example.com"
)

# Validate a key
is_valid = manager.validate_key(api_key, base_url)
```

### Interactive Setup

```bash
python api_key_manager.py
```

Menu options:
1. Set default API key
2. Add user-specific API key
3. Add environment-specific API key
4. List configured keys
5. Test a key
6. Exit

### Command Line Tools

Both diagnostic tools support automatic key lookup:

```bash
# Memory diagnostic
python debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py [--user=username] [--env=environment]

# Cross-chat memory test
python debug/archived/demo-test/debug-tools/test_memory_cross_chat.py [--user=username] [--env=environment]
```

## File Structure

```
backend/
├── api_key_manager.py              # Key management utility
├── openwebui_api_keys.json         # Your keys (ignored by git)
├── openwebui_api_keys.example.json # Example configuration
├── .gitignore                      # Updated with key protection
└── debug/archived/demo-test/debug-tools/
    ├── openwebui_memory_diagnostic.py  # Updated diagnostic tool
    └── test_memory_cross_chat.py        # Updated test tool
```

## Getting Your API Key

1. Open OpenWebUI in your browser
2. Go to **Settings** → **Account** → **API Keys**
3. Click **Create new secret key**
4. Copy the generated key (starts with `sk-`)
5. Store it using the key manager or environment variables

## Best Practices

### Development
- Use the `development` environment for local testing
- Store your personal key under your username
- Keep the default key for shared/automated scripts

### Production
- Use environment-specific keys for different deployments
- Validate keys before deployment
- Monitor key usage and rotate regularly

### Security
- Never commit `openwebui_api_keys.json` to version control
- Use environment variables in CI/CD pipelines
- Regularly audit and rotate API keys
- Set appropriate file permissions

## Troubleshooting

### "No API keys found"
1. Run `python api_key_manager.py` to set up keys
2. Or set environment variables: `OPENWEBUI_API_KEY` and `OPENWEBUI_BASE_URL`
3. Check that `openwebui_api_keys.json` exists and is readable

### "Key validation failed"
1. Verify OpenWebUI is running and accessible
2. Check the base URL is correct
3. Ensure the API key is valid (not expired/revoked)
4. Test manual API calls: `curl -H "Authorization: Bearer your-key" http://localhost:3000/api/v1/users/user`

### "Permission denied"
1. Check file permissions on `openwebui_api_keys.json`
2. Ensure the directory is writable
3. On Windows, check file is not read-only

## Migration from Manual Keys

If you were previously entering keys manually:

1. Run the interactive setup: `python api_key_manager.py`
2. Add your existing keys using option 1 (default) or 2 (user-specific)
3. Test with: `python debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py`
4. The tools will now use stored keys automatically

## API Reference

### APIKeyManager Class

#### Methods

- `get_key(user=None, environment=None)` - Get key with fallback logic
- `add_user_key(username, api_key, base_url, email="", description="")` - Add user key
- `add_environment_key(env_name, api_key, base_url)` - Add environment key
- `set_default_key(api_key, base_url, description="")` - Set default key
- `validate_key(api_key, base_url)` - Test key validity
- `list_users()` - List all configured users
- `list_environments()` - List all configured environments

#### Configuration Structure

```json
{
  "default": {
    "api_key": "string",
    "base_url": "string", 
    "description": "string"
  },
  "users": {
    "username": {
      "api_key": "string",
      "base_url": "string",
      "email": "string",
      "description": "string"
    }
  },
  "environments": {
    "env_name": {
      "api_key": "string",
      "base_url": "string"
    }
  }
}
```
