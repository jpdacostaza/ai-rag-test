# Memory Configuration Fix for OpenWebUI

## Problem: Memory Not Persisting Across Chat Sessions

### Solution 1: Verify Memory Feature Flag in Chat Payload

**Location**: `Chat.svelte` line ~1670
**Issue**: Memory feature not being passed to backend

```javascript
// In OpenWebUI frontend, ensure memory feature is enabled:
features: {
    memory: $settings?.memory ?? false  // ⚠️ This must be true
}
```

### Solution 2: Backend Memory Handler Debugging

**Location**: `middleware.py` chat_memory_handler()
**Issue**: Memory handler not retrieving context properly

```python
# Add debugging to backend memory handler:
async def chat_memory_handler(request, form_data, extra_params, user):
    print(f"🔍 Memory handler called for user: {user.id}")
    
    try:
        results = await query_memory(
            request,
            QueryMemoryForm(content=get_last_user_message(form_data["messages"]) or "", k=3),
            user,
        )
        print(f"🔍 Memory query results: {results}")
    except Exception as e:
        print(f"❌ Memory query failed: {e}")
        results = None

    user_context = ""
    if results and hasattr(results, "documents"):
        if results.documents and len(results.documents) > 0:
            for doc_idx, doc in enumerate(results.documents[0]):
                user_context += f"{doc_idx + 1}. {doc}\n"
                print(f"📝 Added memory context: {doc[:50]}...")
    
    if user_context:
        print(f"✅ Injecting {len(user_context)} chars of memory context")
        form_data["messages"] = add_or_update_system_message(
            f"User Context:\n{user_context}\n", form_data["messages"], append=True
        )
    else:
        print("⚠️ No memory context found to inject")

    return form_data
```

### Solution 3: Vector Database Collection Issues

**Problem**: ChromaDB collection not properly created/accessible

```bash
# Check ChromaDB collections
curl -X GET "http://localhost:8002/api/v1/collections"

# Expected: Should show collection named "user-memory-{user_id}"
```

### Solution 4: Manual Memory Reset (Last Resort)

```python
# Reset memory system via API
POST /api/v1/memories/reset
Authorization: Bearer {your_token}

# This recreates the vector collection from stored memories
```

## Implementation Steps:

1. **Enable Memory in Settings**:
   - Go to OpenWebUI Settings → Personalization → Memory
   - Toggle Memory ON
   - Add some test memories via "Manage" button

2. **Test Memory Query**:
   ```bash
   curl -X POST "http://localhost:3000/api/v1/memories/query" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"content": "what do you remember about me", "k": 3}'
   ```

3. **Verify Backend Logs**:
   ```bash
   docker logs backend-llm-backend --tail 50 | grep -i memory
   ```

4. **Check Memory Injection in Chat**:
   - Start new chat
   - Ask "What do you remember about me?"
   - Should reference stored memory context

## Common Fixes from GitHub Issues:

1. **Embeddings Model Issue**: Ensure embeddings model is loaded
2. **User ID Mismatch**: Verify user.id consistency across sessions  
3. **Collection Permissions**: ChromaDB access permissions
4. **Feature Flag**: Memory toggle in frontend vs backend mismatch

## Debug Commands:

```bash
# Check if memory collections exist
docker exec backend-chroma-1 ls -la /chroma/

# Verify embeddings model
curl http://localhost:8001/health | jq '.databases.embeddings'

# Test memory directly
python demo-tests/debug-tools/openwebui_memory_diagnostic.py
```
