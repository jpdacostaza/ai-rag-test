# Quick Pipeline Installation & Testing Guide

## 🚀 **IMMEDIATE NEXT STEPS**

### **Step 1: Install the Pipeline in OpenWebUI**

1. **Copy the Pipeline Code**:
   - Select ALL the code from `openwebui_memory_pipeline.py` (Ctrl+A, Ctrl+C)

2. **Access OpenWebUI Pipeline Settings**:
   - Go to: `http://localhost:3000`
   - Click your **profile/avatar** (top right)
   - Select **Settings** → **Functions** → **Pipelines**

3. **Add the Pipeline**:
   - Click **"+"** or **"Add Pipeline"**
   - Select **"Add from Code"** or **"Import Pipeline"**
   - Paste the entire pipeline code
   - Click **"Save"** or **"Install"**

### **Step 2: Configure Pipeline Settings**

After installation, configure these **Valves** (settings):
```json
{
  "backend_url": "http://host.docker.internal:8001",
  "api_key": "f2b985dd-219f-45b1-a90e-170962cc7082",
  "memory_limit": 3,
  "enable_learning": true,
  "enable_memory_injection": true,
  "max_memory_length": 500,
  "debug_mode": true
}
```

**Important**: Set `debug_mode: true` initially for testing!

### **Step 3: Enable the Pipeline**
- Toggle the pipeline to **"Enabled"** state
- Select which models should use this pipeline
- Save the configuration

## 🧪 **Test the Memory Functionality**

### **Test 1: Basic Memory Storage**
1. Start a new conversation in OpenWebUI
2. Say: "My name is John and I love pizza"
3. Wait for response
4. Start a **new chat/conversation**
5. Ask: "What's my name and what food do I like?"
6. The AI should remember from the previous conversation

### **Test 2: Debug Output Check**
With `debug_mode: true`, open browser console (F12) and look for:
- `[Memory Pipeline] Processing message for user...`
- `[Memory Pipeline] Injected memory context...`
- `[Memory Pipeline] Stored interaction for learning`

## 🔍 **Verification Checklist**

- [ ] Pipeline shows as "Memory Pipeline" (not "Pipelines Not Detected")
- [ ] Pipeline status is "Enabled" or "Active"
- [ ] Debug messages appear in browser console
- [ ] Memory works across different conversations
- [ ] Backend receives memory API calls

## 🚨 **If Issues Occur**

### **Pipeline Not Installing**
- Check for Python syntax errors in the code
- Ensure all code is copied (including the docstring at top)
- Try refreshing OpenWebUI and trying again

### **Memory Not Working**
- Check `backend_url` is correct: `http://host.docker.internal:8001`
- Verify API key matches: `f2b985dd-219f-45b1-a90e-170962cc7082`
- Enable `debug_mode: true` and check console for errors
- Check backend logs: `docker logs backend-llm-backend --tail 20`

### **Connection Errors**
- Verify backend is running: `curl http://localhost:8001/health`
- Test memory endpoint: `curl http://localhost:8001/api/memory/retrieve`

---
**Ready to Install**: Copy the pipeline code and follow the steps above!
