# OpenWebUI Memory Pipeline Setup Guide

## Current Status: WORKING! 🎉

The memory pipeline system is now properly configured and working. Here's how to use it:

## Available Components

### Base Models (from Ollama)
- **llama3.2:3b** - Main language model (recommended)

### Memory Pipelines (Filters)
- **simple_working_pipeline** - Main memory filter with Redis + ChromaDB
- **memory_pipeline** - Advanced memory pipeline
- **openwebui_memory_pipeline_v2** - Alternative memory implementation

## How to Use in OpenWebUI

### Step 1: Select Base Model
1. Go to OpenWebUI (http://localhost:3000)
2. In the model selector, choose **llama3.2:3b** as your base model
3. DO NOT select "test" or any pipeline name as a model

### Step 2: Enable Memory Filter
1. After selecting llama3.2:3b, look for **Functions** or **Filters** options
2. Enable the **simple_working_pipeline** filter
3. This will add memory capabilities to your base model

### Step 3: Configure Pipeline (Optional)
1. Go to Admin panel → Pipelines
2. Find **simple_working_pipeline**
3. Configure settings like:
   - `enable_memory`: true (default)
   - `max_memories`: 3 (default)
   - `memory_threshold`: 0.7 (default)
   - `debug`: true (to see logs)

### Step 4: Start Chatting!
1. Your conversations will now be remembered across sessions
2. The AI will have context from previous conversations
3. Memory is isolated per user
4. You can see memory activity in the logs

## Memory Features

### What Gets Remembered
- Previous conversations and responses
- User preferences and context
- Important facts mentioned in chats
- Response patterns and user feedback

### Memory Storage
- **Short-term**: Redis (fast access, recent conversations)
- **Long-term**: ChromaDB (persistent, searchable memories)
- **User Isolation**: Each user has their own memory space

### Debug Information
- Enable debug mode in pipeline settings to see:
  - Memory retrieval logs
  - Context injection details
  - Storage confirmation messages

## Troubleshooting

### "500 no filters in model" Error
This happens when you select a pipeline name as a model instead of using it as a filter:
- ❌ Wrong: Select "simple_working_pipeline" as model
- ✅ Correct: Select "llama3.2:3b" as model, then enable "simple_working_pipeline" as filter

### No Memory Context
- Check that the pipeline is enabled in Functions/Filters
- Verify debug logs show memory retrieval
- Ensure you're chatting with the same user account

### Pipeline Not Visible
- Restart OpenWebUI: `docker-compose restart openwebui`
- Check pipelines are loaded: `docker-compose logs pipelines`
- Verify pipeline server is accessible

## Testing the Memory

Try this conversation flow:
1. "Hello, my name is John and I work at Acme Corp"
2. (In a new chat) "What do you remember about me?"
3. The AI should recall your name and workplace

## Technical Details

### Architecture
```
User → OpenWebUI → [Memory Filter] → llama3.2:3b → Response
                        ↓
                   Memory API (Redis + ChromaDB)
```

### API Endpoints
- Memory API: http://localhost:8000
- Pipelines: http://localhost:9098
- OpenWebUI: http://localhost:3000
- Ollama: http://localhost:11434

### Services Status
All services should be running and healthy:
- ✅ Redis (memory cache)
- ✅ ChromaDB (long-term storage)  
- ✅ Memory API (learning & retrieval)
- ✅ Pipelines (filters)
- ✅ OpenWebUI (interface)
- ✅ Ollama (base models)

## Success Indicators

When working correctly, you should see:
1. Pipeline filters available in OpenWebUI
2. Base model (llama3.2:3b) selectable
3. Memory context in system messages
4. Logs showing memory retrieval and storage
5. Persistent memory across chat sessions

The system is ready for use! 🚀
