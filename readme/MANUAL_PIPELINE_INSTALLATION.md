# Manual Pipeline Installation Guide for OpenWebUI

## 🔧 **Pipeline Installation Issue Resolution**

**Issue**: OpenWebUI is not automatically detecting pipelines via `PIPELINES_URLS`  
**Solution**: Manual pipeline installation using OpenWebUI's interface  

## 📋 **Step-by-Step Installation**

### **Step 1: Access OpenWebUI Pipeline Settings**
1. Go to OpenWebUI: `http://localhost:3000`
2. Click on your **profile/avatar** (top right)
3. Select **Settings**
4. Navigate to **Functions** → **Pipelines**

### **Step 2: Add Pipeline from Code**
1. In the Pipelines section, click **"+"** or **"Add Pipeline"**
2. Select **"Add from Code"** or **"Import Pipeline"**
3. Copy the entire content from `openwebui_memory_pipeline.py`
4. Paste it into the code editor
5. Click **"Save"** or **"Install"**

### **Step 3: Configure Pipeline**
1. Once installed, you should see **"Memory Pipeline"** in the list
2. Click on the pipeline to configure it
3. Adjust the **Valves** (configuration settings):
   - `backend_url`: Should be `http://host.docker.internal:8001`
   - `api_key`: `f2b985dd-219f-45b1-a90e-170962cc7082`
   - `memory_limit`: `3` (number of memories to inject)
   - `enable_learning`: `true`
   - `enable_memory_injection`: `true`
   - `debug_mode`: `false` (set to `true` for troubleshooting)

### **Step 4: Enable Pipeline**
1. Toggle the pipeline to **"Enabled"** state
2. Select which models should use this pipeline
3. Save the configuration

## 🎯 **Pipeline Features**

### **Memory Injection**
- Automatically injects relevant context from previous conversations
- Configurable memory limit (default: 3 memories)
- Smart context formatting for LLM understanding

### **Learning System**
- Stores interactions for future context retrieval
- Learns from conversation patterns
- Configurable learning toggle

### **Configuration Options (Valves)**
```json
{
  "backend_url": "http://host.docker.internal:8001",
  "api_key": "f2b985dd-219f-45b1-a90e-170962cc7082", 
  "memory_limit": 3,
  "enable_learning": true,
  "enable_memory_injection": true,
  "max_memory_length": 500,
  "debug_mode": false
}
```

## 🔍 **Verification Steps**

### **Check Pipeline Status**
1. In OpenWebUI Settings → Functions → Pipelines
2. Verify "Memory Pipeline" shows as **"Active"** or **"Enabled"**
3. Check that it's assigned to your preferred models

### **Test Memory Functionality**
1. Start a conversation in OpenWebUI
2. Ask about something specific (e.g., "My favorite color is blue")
3. Start a new chat
4. Ask "What's my favorite color?" 
5. The AI should remember from the previous conversation

### **Debug Mode Testing**
1. Enable `debug_mode: true` in pipeline settings
2. Check browser console (F12) for pipeline debug messages
3. Look for messages like:
   - `[Memory Pipeline] Processing message for user...`
   - `[Memory Pipeline] Injected memory context...`
   - `[Memory Pipeline] Stored interaction for learning`

## 🚨 **Troubleshooting**

### **Pipeline Not Installing**
- Ensure the Python code is valid (no syntax errors)
- Check that all required imports are available
- Verify OpenWebUI has necessary permissions

### **Memory Not Working**
- Check `backend_url` points to correct backend
- Verify `api_key` matches backend configuration
- Enable `debug_mode` to see error messages
- Check backend logs: `docker logs backend-llm-backend`

### **Connection Issues**
- Verify backend is running: `curl http://localhost:8001/health`
- Check network connectivity: `docker exec backend-openwebui curl http://llm_backend:8001/health`
- Ensure firewall/ports are open

## 📝 **Pipeline Code Location**

The complete pipeline code is available in:
- **File**: `openwebui_memory_pipeline.py`
- **Purpose**: Standalone OpenWebUI pipeline for memory functionality
- **Integration**: Copy-paste into OpenWebUI interface

## 🎉 **Expected Results**

Once properly installed and configured:
- ✅ Pipeline appears in OpenWebUI Settings → Functions → Pipelines
- ✅ Shows as "Active" or "Enabled" 
- ✅ Memory injection works across conversations
- ✅ Learning system stores interaction data
- ✅ Debug messages appear in console (if enabled)

## 📈 **Alternative: Direct Installation Method**

If the manual method doesn't work, try:

1. **File Upload Method** (if supported):
   - Save `openwebui_memory_pipeline.py` locally
   - Use OpenWebUI's file upload for pipelines

2. **URL Installation** (if supported):
   - Host the pipeline file on a web server
   - Use OpenWebUI's "Install from URL" feature

3. **Admin Installation** (if admin access):
   - Copy pipeline file to OpenWebUI's pipeline directory
   - Restart OpenWebUI container

---
**Status**: Manual installation required due to automatic discovery limitations  
**Next Action**: Follow Step-by-Step Installation guide above  
**Expected Outcome**: Memory Pipeline visible and functional in OpenWebUI
