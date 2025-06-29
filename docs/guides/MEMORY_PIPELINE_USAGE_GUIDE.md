# Memory Pipeline Configuration Guide
## How to Use the Memory System in OpenWebUI

⚠️ **IMPORTANT**: The memory pipeline is a **FILTER**, not a standalone model. It must be applied to an existing base model like `llama3.2:3b`.

## ❌ WRONG Way (Causes 500 Error):
- Selecting "memory_pipeline" as the model in chat
- This tries to use the memory pipeline as a standalone model, which causes a 500 Internal Server Error

## ✅ CORRECT Way:

### Step 1: Access OpenWebUI Admin
1. Open OpenWebUI: http://localhost:3000
2. Log in with admin credentials
3. Go to **Admin Panel** → **Settings** → **Pipelines**

### Step 2: Configure Memory Pipeline
1. You should see "Simple Memory Pipeline" listed
2. Click on the pipeline to configure it
3. Set it to apply to the base model (`llama3.2:3b`)

### Step 3: Use the System
1. In the chat interface, select **`llama3.2:3b`** as your model (NOT memory_pipeline)
2. Ensure the memory pipeline filter is applied to this model
3. Start chatting - the memory pipeline will:
   - **Inlet**: Add memory context before messages go to llama3.2:3b
   - **Outlet**: Store conversation for future memory after llama3.2:3b responds

## How It Works:

```
User Message → Memory Pipeline (inlet) → llama3.2:3b → Memory Pipeline (outlet) → Response
                ↓                                           ↓
        Adds memory context                           Stores for future memory
```

## Features:
- ✅ **User Isolation**: Each user has separate memory
- ✅ **Persistent Memory**: Stored in Redis (short-term) and ChromaDB (long-term)
- ✅ **Context Injection**: Relevant past conversations automatically added
- ✅ **Adaptive Learning**: Stores interactions for future retrieval

## Troubleshooting:

### If you get a 500 Internal Server Error:
- Check if you're selecting "memory_pipeline" as the model (this is wrong)
- Instead, select "llama3.2:3b" and apply memory as a filter

### If memory doesn't seem to work:
- Check that the memory pipeline is configured as a filter
- Verify that Redis and ChromaDB services are running
- Check pipeline logs: `docker-compose logs pipelines`

### If pipeline doesn't appear in admin:
- Check that the pipeline file is mounted correctly
- Restart pipelines service: `docker-compose restart pipelines`

## Validation:
Run the test script to verify the memory pipeline works:
```bash
cd e:\Projects\opt\backend
python test_memory_pipeline_filter.py
```

## Current Status:
✅ Memory API working (Redis + ChromaDB)
✅ Memory pipeline code working as filter  
✅ All services healthy and running
⚠️ **Action Required**: Configure pipeline as filter in OpenWebUI admin, don't use as standalone model

The 500 error was caused by trying to use the memory pipeline as a standalone model instead of as a filter applied to llama3.2:3b.
