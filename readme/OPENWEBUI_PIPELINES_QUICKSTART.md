# OpenWebUI Pipelines - Quick Start Implementation Guide

## 🚀 Getting Started with OpenWebUI Pipelines

This guide provides step-by-step instructions for implementing OpenWebUI Pipelines with your existing backend system.

---

## 📋 Prerequisites

### System Requirements
- **Docker** (recommended) or **Python 3.11+**
- **OpenWebUI** instance running
- **Your existing backend** (the current project) running
- **Network connectivity** between all services

### Current Backend Services
Ensure these are running:
- ✅ **Redis** (port 6379) - for caching
- ✅ **ChromaDB** (port 8002) - for vector storage
- ✅ **Your FastAPI Backend** (port 8001) - main service
- ✅ **Ollama** (port 11434) - LLM service

---

## 🔧 Step 1: Set Up Pipeline Server

### Option A: Docker Setup (Recommended)
```bash
# Create pipeline directory
mkdir -p ~/openwebui-pipelines

# Run Pipeline server
docker run -d \
  --name openwebui-pipelines \
  -p 9099:9099 \
  --add-host=host.docker.internal:host-gateway \
  -v ~/openwebui-pipelines:/app/pipelines \
  --restart always \
  ghcr.io/open-webui/pipelines:main

# Verify it's running
curl http://localhost:9099/health
```

### Option B: Python Development Setup
```bash
# Clone the repository
git clone https://github.com/open-webui/pipelines.git
cd pipelines

# Install dependencies
pip install -r requirements.txt

# Start the server
./start.sh

# Server will be available at http://localhost:9099
```

---

## 🔌 Step 2: Connect to OpenWebUI

### Configure Pipeline Connection
1. **Open OpenWebUI** in your browser
2. **Navigate to**: Admin Panel → Settings → Connections
3. **Click**: `+` button to add new connection
4. **Configure**:
   - **API URL**: `http://localhost:9099`
   - **API Key**: `0p3n-w3bu!`
   - **Name**: `Custom Pipelines`
5. **Test Connection** and verify it shows ✅
6. **Save** the configuration

### Verify Integration
- Go to **Chat interface**
- Check **Model dropdown** - you should see Pipeline models available
- Test with a simple message to ensure connectivity

---

## 🧠 Step 3: Create Your First Pipeline

### Memory Enhancement Filter
Create a pipeline that integrates your adaptive learning system:

```bash
# Create pipeline file
mkdir -p ~/openwebui-pipelines
cat > ~/openwebui-pipelines/memory_enhancement_filter.py << 'EOF'
"""
title: Memory Enhancement Filter
author: Your Project
date: 2025-01-27
version: 1.0
license: MIT
description: Integrates adaptive learning and memory retrieval from your backend
requirements: requests, httpx
"""

import requests
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from schemas import OpenAIChatMessage

class Pipeline:
    class Valves(BaseModel):
        # Configuration for your backend
        backend_url: str = "http://host.docker.internal:8001"
        api_key: str = "your_api_key_here"
        enable_memory_retrieval: bool = True
        enable_learning: bool = True
        max_memory_results: int = 3
        
    def __init__(self):
        self.type = "filter"
        self.name = "Memory Enhancement Filter"
        self.valves = self.Valves()
        
    async def on_startup(self):
        print(f"🧠 Memory Enhancement Filter started")
        
    async def on_shutdown(self):
        print(f"🧠 Memory Enhancement Filter stopped")
        
    def get_user_memory(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Retrieve user memory from your backend's ChromaDB"""
        try:
            response = requests.post(
                f"{self.valves.backend_url}/api/memory/retrieve",
                headers={"Authorization": f"Bearer {self.valves.api_key}"},
                json={
                    "user_id": user_id,
                    "query": query,
                    "limit": self.valves.max_memory_results
                },
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json().get("memories", [])
            else:
                print(f"❌ Memory retrieval failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Memory retrieval error: {e}")
            return []
    
    def store_interaction(self, user_id: str, user_message: str, assistant_response: str):
        """Store interaction for learning (call your adaptive learning system)"""
        try:
            requests.post(
                f"{self.valves.backend_url}/api/learning/process_interaction",
                headers={"Authorization": f"Bearer {self.valves.api_key}"},
                json={
                    "user_id": user_id,
                    "conversation_id": f"pipeline_{user_id}",
                    "user_message": user_message,
                    "assistant_response": assistant_response,
                    "response_time": 1.0,
                    "tools_used": ["memory_enhancement"]
                },
                timeout=5
            )
        except Exception as e:
            print(f"⚠️ Learning storage error: {e}")
    
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Pre-process user input - inject memory context"""
        if not self.valves.enable_memory_retrieval or not user:
            return body
            
        user_id = user.get("id", "default_user")
        user_message = body["messages"][-1]["content"]
        
        print(f"🔍 Retrieving memory for user: {user_id}")
        
        # Get relevant memory from your system
        memories = self.get_user_memory(user_id, user_message)
        
        if memories:
            # Inject memory context into the conversation
            memory_context = "\\n".join([f"- {mem.get('text', mem)}" for mem in memories[:2]])
            enhanced_message = f"Context from your previous conversations:\\n{memory_context}\\n\\nCurrent question: {user_message}"
            
            body["messages"][-1]["content"] = enhanced_message
            print(f"✅ Injected {len(memories)} memory items")
        else:
            print(f"ℹ️ No relevant memories found")
        
        return body
    
    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Post-process assistant response - store for learning"""
        if not self.valves.enable_learning or not user:
            return body
            
        try:
            user_id = user.get("id", "default_user")
            messages = body.get("messages", [])
            
            # Find the last user message and assistant response
            user_message = ""
            assistant_response = ""
            
            for i, msg in enumerate(reversed(messages)):
                if msg["role"] == "assistant" and not assistant_response:
                    assistant_response = msg["content"]
                elif msg["role"] == "user" and not user_message:
                    user_message = msg["content"]
                    
                if user_message and assistant_response:
                    break
            
            if user_message and assistant_response:
                print(f"💾 Storing interaction for learning: {user_id}")
                self.store_interaction(user_id, user_message, assistant_response)
            
        except Exception as e:
            print(f"⚠️ Learning processing error: {e}")
        
        return body
EOF

# Restart pipeline server to load the new pipeline
docker restart openwebui-pipelines
```

---

## 🔗 Step 4: Backend API Integration

### Add Pipeline Support Endpoints
Add these endpoints to your `main.py` to support Pipeline calls:

```python
# Add to your main.py file

@app.post("/api/memory/retrieve")
async def retrieve_memory_for_pipeline(
    request: dict = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """Retrieve user memory for Pipeline integration"""
    try:
        user_id = request.get("user_id", "default")
        query = request.get("query", "")
        limit = request.get("limit", 3)
        
        # Use your existing memory retrieval
        query_embedding = get_embedding(db_manager, query)
        if query_embedding is not None:
            memories = retrieve_user_memory(db_manager, user_id, query_embedding, limit)
            return {"memories": memories, "count": len(memories)}
        else:
            return {"memories": [], "count": 0}
            
    except Exception as e:
        log_error(e, "pipeline_memory_retrieval")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/learning/process_interaction")
async def process_interaction_for_pipeline(
    request: dict = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """Process interaction for adaptive learning from Pipeline"""
    try:
        # Use your existing adaptive learning system
        result = await adaptive_learning_system.process_interaction(
            user_id=request.get("user_id"),
            conversation_id=request.get("conversation_id"),
            user_message=request.get("user_message"),
            assistant_response=request.get("assistant_response"),
            response_time=request.get("response_time", 1.0),
            tools_used=request.get("tools_used")
        )
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        log_error(e, "pipeline_learning")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🧪 Step 5: Testing Your Pipeline

### Test Memory Enhancement
1. **Chat with OpenWebUI** using the Pipeline model
2. **Ask a question** and provide some information
3. **Ask a follow-up question** that should use the memory
4. **Verify** that context from previous conversation is included

### Example Test Conversation
```
You: "My name is Alex and I work as a data scientist"
AI: [Response acknowledging the information]

You: "What career advice do you have for me?"
AI: [Should reference that you're Alex, a data scientist, based on memory]
```

### Debug Pipeline
```bash
# Check pipeline logs
docker logs openwebui-pipelines

# Check if pipeline is loaded
curl http://localhost:9099/v1/models

# Test pipeline health
curl http://localhost:9099/health
```

---

## 🔄 Step 6: Advanced Pipeline Examples

### Tool Integration Pipeline
Create a pipeline that uses your AI tools:

```python
# tools_integration_filter.py
class ToolIntegrationPipeline:
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        user_message = body["messages"][-1]["content"]
        
        # Detect if tools are needed
        if any(keyword in user_message.lower() for keyword in ["weather", "time", "calculate", "python"]):
            # Call your backend's tool system
            tool_response = requests.post(
                f"{self.valves.backend_url}/chat",
                headers={"Authorization": f"Bearer {self.valves.api_key}"},
                json={
                    "message": user_message,
                    "user_id": user.get("id", "default"),
                    "use_tools": True
                }
            )
            
            if tool_response.status_code == 200:
                result = tool_response.json()
                enhanced_message = f"{user_message}\\n\\nTool Results: {result.get('response', '')}"
                body["messages"][-1]["content"] = enhanced_message
        
        return body
```

### RAG Enhancement Pipeline
```python
# rag_enhancement_pipeline.py
class RAGEnhancementPipeline:
    def pipe(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> str:
        user_id = body.get("user", {}).get("id", "default")
        
        # Use your RAG system
        rag_response = requests.post(
            f"{self.valves.backend_url}/search",
            headers={"Authorization": f"Bearer {self.valves.api_key}"},
            json={
                "query": user_message,
                "user_id": user_id,
                "limit": 5
            }
        )
        
        if rag_response.status_code == 200:
            documents = rag_response.json().get("documents", [])
            if documents:
                context = "\\n".join([doc.get("content", "") for doc in documents])
                enhanced_prompt = f"Context: {context}\\n\\nQuestion: {user_message}"
                
                # Forward to your LLM backend
                llm_response = requests.post(
                    f"{self.valves.backend_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.valves.api_key}"},
                    json={
                        "model": model_id,
                        "messages": [{"role": "user", "content": enhanced_prompt}],
                        "max_tokens": body.get("max_tokens", 500)
                    }
                )
                
                if llm_response.status_code == 200:
                    return llm_response.json()["choices"][0]["message"]["content"]
        
        return "I couldn't process your request with RAG enhancement."
```

---

## 📊 Step 7: Monitoring & Management

### Pipeline Management UI
1. **OpenWebUI Admin Panel** → **Pipelines**
2. **View active pipelines** and their configurations
3. **Modify valve values** (configuration parameters)
4. **Enable/disable** specific pipelines

### Health Monitoring
```bash
# Check pipeline server health
curl http://localhost:9099/health

# List available pipelines
curl http://localhost:9099/v1/models

# Monitor logs
docker logs -f openwebui-pipelines
```

### Performance Monitoring
Add logging to your pipelines:
```python
import time

async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
    start_time = time.time()
    
    # Your pipeline logic here
    
    processing_time = time.time() - start_time
    print(f"⏱️ Pipeline processing time: {processing_time:.3f}s")
    return body
```

---

## 🚀 Next Steps

### Phase 1 Completion Checklist
- [ ] Pipeline server running and accessible
- [ ] OpenWebUI connected to Pipeline server
- [ ] Memory enhancement pipeline created and tested
- [ ] Backend API endpoints for Pipeline integration added
- [ ] Basic functionality verified through testing

### Phase 2: Advanced Features
- [ ] Tool integration pipeline
- [ ] RAG enhancement pipeline
- [ ] Security and rate limiting filters
- [ ] Advanced monitoring and analytics

### Phase 3: Production Deployment
- [ ] Production-ready Pipeline server setup
- [ ] Load balancing and high availability
- [ ] Security hardening and authentication
- [ ] Comprehensive monitoring and alerting

---

## 🛠️ Troubleshooting

### Common Issues

#### Pipeline Not Loading
```bash
# Check pipeline syntax
python -m py_compile ~/openwebui-pipelines/memory_enhancement_filter.py

# Check logs for errors
docker logs openwebui-pipelines
```

#### Connection Issues
```bash
# Verify network connectivity
curl http://localhost:9099/health

# Check Docker networking
docker network ls
docker inspect openwebui-pipelines
```

#### API Integration Issues
```bash
# Test backend endpoints directly
curl -X POST http://localhost:8001/api/memory/retrieve \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "query": "hello", "limit": 3}'
```

### Getting Help
- **OpenWebUI Documentation**: https://docs.openwebui.com/pipelines/
- **GitHub Repository**: https://github.com/open-webui/pipelines
- **Discord Community**: OpenWebUI Discord server
- **Your Project Documentation**: `/readme/` folder

---

**Generated by**: OpenWebUI Pipelines Quick Start Guide  
**Status**: Ready for Implementation  
**Next Steps**: Begin with Step 1 - Pipeline Server Setup
