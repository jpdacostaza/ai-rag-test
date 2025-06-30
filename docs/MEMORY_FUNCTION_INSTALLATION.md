# Memory Function Installation Guide

This guide explains how to install the Enhanced Memory Function into your OpenWebUI instance.

## 📋 Prerequisites

1. **OpenWebUI running** - Your OpenWebUI should be accessible (default: http://localhost:3000)
2. **Admin access** - You need administrator privileges in OpenWebUI
3. **Memory API running** - The memory API should be running on http://localhost:8001

## 🚀 Installation Methods

### Method 1: Automatic Installation (Recommended)

The system includes automatic installation that runs when you start the backend:

```powershell
# Complete startup with automatic function installation
.\scripts\start_backend_complete.ps1

# Or start services individually (auto-installer runs automatically)
docker-compose up -d
```

The auto-installer will:
- ✅ Wait for OpenWebUI to be ready
- ✅ Prepare installation files
- ✅ Provide step-by-step instructions
- ✅ Save function code for easy copy-paste

### Method 2: Manual Installation Scripts

#### PowerShell Script (Windows)

```powershell
# Navigate to the backend directory
cd e:\Projects\opt\backend

# Run the installation script
.\scripts\install_memory_function.ps1

# With custom URL
.\scripts\install_memory_function.ps1 -OpenWebUIUrl "http://localhost:3000"

# With API key (if required)
.\scripts\install_memory_function.ps1 -ApiKey "your-api-key"
```

#### Python Script (Cross-platform)

```bash
# Navigate to the backend directory
cd /path/to/backend

# Install dependencies
pip install httpx

# Run the installation script
python scripts/install_memory_function.py

# With custom URL
python scripts/install_memory_function.py --url "http://localhost:3000"

# With API key (if required)
python scripts/install_memory_function.py --api-key "your-api-key"
```

### Method 3: Manual Installation via OpenWebUI

1. **Access OpenWebUI Admin**
   - Go to http://localhost:3000
   - Login as admin
   - Navigate to **Admin → Functions**

2. **Create New Function**
   - Click "Add Function" or "+"
   - Copy the entire contents of `memory_function.py`
   - Paste into the function editor

3. **Configure Function**
   - Set **Function ID**: `memory_function`
   - Set **Function Name**: `Enhanced Memory Function`
   - Enable **"Active"** checkbox
   - Enable **"Global"** checkbox (optional)
   - Save the function

## 🤖 Automatic Installation Details

The backend includes a **function_installer** service that automatically runs when you start the system:

```yaml
# In docker-compose.yml
function_installer:
  image: python:3.11-slim
  container_name: backend-function-installer
  restart: "no"  # Run once and exit
  depends_on:
    openwebui:
      condition: service_started
  command: # Automatically installs the function
```

**What it does:**
- ✅ Waits for OpenWebUI to be ready
- ✅ Reads the memory function code
- ✅ Prepares installation files
- ✅ Provides detailed instructions
- ✅ Saves function code to `/tmp/memory_function_code.py`

**To disable automatic installation:**
```bash
export SKIP_FUNCTION_INSTALL=true
docker-compose up -d
```

## ⚙️ Configuration

After installation, you can configure the function:

1. Go to **Admin → Functions → Enhanced Memory Function**
2. Click **"Configure"** or **"Settings"**
3. Adjust the following valves:

```python
# Backend integration
memory_api_url: "http://memory_api:8000"  # Your memory API URL

# Memory settings  
enable_memory: true          # Enable memory functionality
max_memories: 3             # Maximum memories to retrieve
memory_threshold: 0.7       # Similarity threshold for retrieval

# Debug
debug: true                 # Enable debug logging
```

## 🔧 Verification

To verify the installation worked:

1. **Check Function List**
   ```powershell
   # PowerShell
   .\scripts\test\test_memory_function_import.ps1
   ```

2. **Test in Chat**
   - Start a new conversation in OpenWebUI
   - Type a message
   - Check if the memory function appears in the function list
   - Look for memory-related responses

3. **Check Memory API**
   ```powershell
   # Test memory API directly
   Invoke-RestMethod -Uri "http://localhost:8001/" -Method GET
   ```

## 🐛 Troubleshooting

### Common Issues

1. **"Cannot connect to OpenWebUI"**
   - Ensure OpenWebUI is running on the specified port
   - Check if port 3000 is accessible
   - Try: `curl http://localhost:3000`

2. **"Function not found after installation"**
   - Refresh the OpenWebUI page
   - Check Admin → Functions list
   - Verify the function is marked as "Active"

3. **"Memory API not accessible"**
   - Ensure memory API is running: `docker ps`
   - Check logs: `docker logs backend-memory-api`
   - Test API: `curl http://localhost:8001/`

4. **"401/403 Authorization Error"**
   - Ensure you're logged in as admin
   - Try providing an API key
   - Check OpenWebUI authentication settings

### Debug Steps

1. **Check Container Status**
   ```bash
   docker ps
   docker logs backend-openwebui
   docker logs backend-memory-api
   ```

2. **Test API Endpoints**
   ```bash
   # Test OpenWebUI
   curl http://localhost:3000/api/v1/functions/

   # Test Memory API  
   curl http://localhost:8001/api/memory/retrieve
   ```

3. **Function Logs**
   - Enable debug mode in function settings
   - Check OpenWebUI logs for function execution
   - Look for memory-related error messages

## 📚 Usage

Once installed, the memory function will:

1. **Automatically store** conversations in memory
2. **Retrieve relevant** past conversations
3. **Enhance responses** with contextual memory
4. **Learn from** user interactions

The function works transparently - no special commands needed!

## 🔄 Updates

To update the memory function:

1. **Re-run installation script** - it will update the existing function
2. **Manual update** - copy new code to the function editor
3. **Restart OpenWebUI** if needed

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs for error messages
3. Ensure all services are running properly
4. Test the memory API directly

The memory function integrates seamlessly with your existing OpenWebUI setup and enhances conversations with persistent memory capabilities.
