# 🔑 Super Simple API Key Setup

## The Easiest Way: Just Edit a JSON File

### Step 1: Copy the Example
```bash
copy openwebui_api_keys.example.json openwebui_api_keys.json
```

### Step 2: Edit Your API Keys
Open `openwebui_api_keys.json` and replace the placeholder values:

```json
{
  "default": {
    "api_key": "sk-your-actual-api-key-here",
    "base_url": "http://localhost:3000",
    "description": "Default OpenWebUI instance"
  },
  "users": {
    "john": {
      "api_key": "sk-john-actual-key-here", 
      "base_url": "http://localhost:3000",
      "email": "john@example.com",
      "description": "John's API key"
    }
  },
  "environments": {
    "development": {
      "api_key": "sk-dev-actual-key-here",
      "base_url": "http://localhost:3000"
    },
    "production": {
      "api_key": "sk-prod-actual-key-here", 
      "base_url": "https://your-openwebui-domain.com"
    }
  }
}
```

### Step 3: Test It
```bash
python demo-tests/debug-tools/openwebui_memory_diagnostic.py
```

That's it! Your tools will automatically find and use the keys.

## What You Need to Change

1. **Replace `"YOUR_DEFAULT_API_KEY_HERE"`** with your actual OpenWebUI API key
2. **Replace `"sk-example-user-key-here"`** with real API keys
3. **Update URLs** if you're not using localhost:3000
4. **Add/remove users** as needed

## Get Your API Key

1. Open OpenWebUI in browser
2. Go to **Settings** → **Account** → **API Keys** 
3. Click **Create new secret key**
4. Copy the key (starts with `sk-`)

## File Security

✅ **Safe**: The file is already in `.gitignore` - won't be committed to git
✅ **Local**: Keys stay on your machine only
✅ **Simple**: Just a JSON file you can edit with any text editor

## Usage Examples

```bash
# Use default key
python demo-tests/debug-tools/openwebui_memory_diagnostic.py

# Use john's key  
python demo-tests/debug-tools/openwebui_memory_diagnostic.py --user=john

# Use production environment key
python demo-tests/debug-tools/openwebui_memory_diagnostic.py --env=production
```

No complex setup needed - just edit the JSON file and you're done! 🎉
