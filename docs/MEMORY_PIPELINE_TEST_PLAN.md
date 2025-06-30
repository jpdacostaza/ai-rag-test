# OpenWebUI Memory Pipeline - Complete End-to-End Test
**Date: June 29, 2025**
**Status: READY FOR TESTING**

## 🎯 Test Plan: Memory Pipeline Complete Functionality

### Prerequisites ✅
- All Docker services running and healthy
- OpenWebUI accessible at http://localhost:3000
- Functions discoverable via API bridge
- Memory pipeline loaded and functional

### Test Steps

#### 1. Access OpenWebUI Functions 🔧
1. **Go to**: http://localhost:3000
2. **Login/Register** as admin user
3. **Navigate to**: Admin → Functions
4. **Expected**: Should see 2 memory functions:
   - `openwebui_memory_pipeline_v2`
   - `simple_working_pipeline`

#### 2. Enable Memory Function 🧠
1. **Select**: `simple_working_pipeline` function
2. **Click**: Enable/Activate the function
3. **Configure**: Set any valve parameters if needed
4. **Expected**: Function shows as active/enabled

#### 3. Configure Model with Memory Filter 🤖
1. **Navigate to**: Admin → Models → llama3.2:3b
2. **Go to**: Filters/Functions section
3. **Select**: `simple_working_pipeline` as a filter
4. **Save**: Apply the configuration
5. **Expected**: Model now has memory filter enabled

#### 4. Test Memory Storage (First Conversation) 💾
1. **Start new chat** with llama3.2:3b model
2. **Send message**: "Hello, my name is John and I work at Acme Corp. I'm a software engineer."
3. **Expected**: 
   - AI responds normally
   - Memory pipeline processes the interaction (check logs)
   - Interaction stored in Redis/ChromaDB

#### 5. Test Memory Retrieval (Second Conversation) 🔍
1. **Start a NEW chat** (different conversation)
2. **Send message**: "What do you remember about me?"
3. **Expected**:
   - AI retrieves and mentions previous context
   - Should remember name "John" and company "Acme Corp"
   - Should know user is a software engineer

#### 6. Verify Memory Persistence 🔄
1. **Test with different user** (if available)
2. **Send message**: "What do you know about John?"
3. **Expected**:
   - Different user should NOT see John's personal info
   - Memory should be user-isolated

#### 7. Check Memory Logs 📋
1. **Pipeline Logs**: `docker-compose logs pipelines --tail=20`
2. **Memory API Logs**: `docker-compose logs memory_api --tail=20`
3. **Expected**:
   - Memory retrieval and storage events logged
   - No errors in memory processing

### Success Criteria ✅

- [ ] Functions visible in OpenWebUI Admin
- [ ] Memory filter can be enabled on models
- [ ] First conversation stores information correctly
- [ ] Second conversation retrieves previous context
- [ ] Memory is user-isolated
- [ ] No errors in system logs

### If Test Passes 🎉
**The OpenWebUI Memory Pipeline project is 100% COMPLETE!**

### If Test Fails ❌
Check:
1. API bridge logs for function discovery issues
2. Pipeline logs for memory processing errors
3. Memory API logs for storage/retrieval issues
4. OpenWebUI logs for configuration problems

---

## Quick Debug Commands

```bash
# Check all services
docker-compose ps

# Test functions endpoint
curl -H "Authorization: Bearer test" http://localhost:8003/api/v1/functions

# Test memory pipeline directly
curl -X POST "http://localhost:9098/v1/simple_working_pipeline/filter/inlet" \
  -H "Authorization: Bearer 0p3n-w3bu!" \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "messages": [{"role": "user", "content": "Test message"}]
    },
    "user": {"id": "test_user", "name": "Test User"}
  }'

# Check memory storage
curl http://localhost:8000/api/memory/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "query": "test",
    "limit": 5
  }'
```

---

**Ready to test the complete memory pipeline! 🚀**
