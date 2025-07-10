# Admin Memory Purge Endpoint Guide

## ⚠️ CRITICAL WARNING ⚠️
**THE PURGE ENDPOINT PERMANENTLY DESTROYS ALL USER DATA ACROSS ALL DATABASES**

This endpoint is designed for **administrative, testing, and emergency use only**. Once executed, **ALL user memories, conversations, and data will be irreversibly deleted**.

## Table of Contents
- [Overview](#overview)
- [When to Use](#when-to-use)
- [Safety Mechanisms](#safety-mechanisms)
- [How to Use](#how-to-use)
- [Response Format](#response-format)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

The Admin Purge endpoint (`POST /admin/purge-all`) completely wipes all memory databases:
- **Redis** (short-term memory) - All keys deleted via `FLUSHALL`
- **ChromaDB** (long-term memory) - All collections deleted
- **All user data** across all users permanently destroyed

### Affected Data
- User memories and conversations
- Personal information (names, work, preferences)
- Chat history and context
- Learning interactions
- All metadata and timestamps

## When to Use

### ✅ Appropriate Use Cases:
- **Development/Testing**: Reset system between test runs
- **System Maintenance**: Clean slate before major updates
- **Privacy Compliance**: Complete data wipe when legally required
- **Database Corruption**: Emergency cleanup when databases are corrupted
- **Demo Environments**: Reset demo systems for presentations

### ❌ Inappropriate Use Cases:
- **Individual User Cleanup**: Use `/api/memory/clear` or `/memory/{user_id}` instead
- **Regular Maintenance**: Not needed for normal operation
- **Production Systems**: Extremely dangerous in production environments

## Safety Mechanisms

The endpoint has multiple layers of protection:

### 1. Request Validation
```json
{
  "confirm_purge": true,                           // REQUIRED: Must be true
  "i_understand_this_deletes_everything": true,    // REQUIRED: Must be true
  "admin_key": "your-admin-key"                    // OPTIONAL: If MEMORY_ADMIN_KEY is set
}
```

### 2. Admin Key Protection (Optional)
Set the `MEMORY_ADMIN_KEY` environment variable to require an admin key:
```bash
export MEMORY_ADMIN_KEY="your-secure-admin-key"
```

### 3. Explicit Confirmation Fields
Both confirmation fields must be `true` or the request will be rejected.

## How to Use

### Method 1: Using curl
```bash
curl -X POST http://localhost:8001/admin/purge-all \
  -H "Content-Type: application/json" \
  -d '{
    "confirm_purge": true,
    "i_understand_this_deletes_everything": true,
    "admin_key": "your-admin-key-if-required"
  }'
```

### Method 2: Using PowerShell
```powershell
$body = @{
    confirm_purge = $true
    i_understand_this_deletes_everything = $true
    admin_key = "your-admin-key-if-required"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/admin/purge-all" -Method POST -ContentType "application/json" -Body $body
```

### Method 3: Using Python
```python
import requests

response = requests.post("http://localhost:8001/admin/purge-all", json={
    "confirm_purge": True,
    "i_understand_this_deletes_everything": True,
    "admin_key": "your-admin-key-if-required"  # Optional
})

print(response.json())
```

### Method 4: Testing without Admin Key
If no `MEMORY_ADMIN_KEY` environment variable is set:
```bash
curl -X POST http://localhost:8001/admin/purge-all \
  -H "Content-Type: application/json" \
  -d '{
    "confirm_purge": true,
    "i_understand_this_deletes_everything": true
  }'
```

## Response Format

### Success Response
```json
{
  "status": "success",
  "message": "All memory databases purged",
  "details": {
    "redis_cleared": true,
    "chromadb_cleared": true,
    "errors": []
  },
  "timestamp": "2025-07-10T15:30:45.123456",
  "warning": "ALL USER DATA HAS BEEN PERMANENTLY DELETED"
}
```

### Partial Success Response
```json
{
  "status": "partial_success",
  "message": "Partial purge completed with errors",
  "details": {
    "redis_cleared": true,
    "chromadb_cleared": false,
    "errors": ["ChromaDB clear error: Connection refused"]
  },
  "timestamp": "2025-07-10T15:30:45.123456",
  "warning": "ALL USER DATA HAS BEEN PERMANENTLY DELETED"
}
```

### Error Responses

#### Missing Confirmation
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "confirm_purge"],
      "msg": "confirm_purge must be True to proceed"
    }
  ]
}
```

#### Invalid Admin Key
```json
{
  "detail": "Invalid admin key"
}
```

#### Server Error
```json
{
  "detail": "Memory purge failed: [error details]"
}
```

## Troubleshooting

### Common Issues

#### 1. "Invalid admin key" Error
**Cause**: The `MEMORY_ADMIN_KEY` environment variable is set but wrong key provided.
**Solution**: Check the admin key or remove the environment variable if not needed.

#### 2. "confirm_purge must be True" Error
**Cause**: Request validation failed due to missing or false confirmation fields.
**Solution**: Ensure both `confirm_purge` and `i_understand_this_deletes_everything` are `true`.

#### 3. Partial Success with Database Errors
**Cause**: One database cleared successfully but the other failed.
**Solution**: 
- Check database connections
- Restart failed database services
- Re-run the purge command

#### 4. Connection Refused
**Cause**: Memory API service is not running.
**Solution**: 
```bash
# Check if memory service is running
docker-compose ps memory

# Restart if needed
docker-compose restart memory
```

### Verification Commands

#### Check if purge was successful:
```bash
# Check Redis
curl http://localhost:8001/debug/stats

# Should show:
# "redis": {"total_keys": 0, "users": {}}
# "chromadb": {"total_documents": 0, "users": {}}
```

#### Test memory retrieval (should return empty):
```bash
curl -X POST http://localhost:8001/api/memory/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "query": "anything",
    "limit": 10
  }'

# Should return: {"memories": [], "count": 0}
```

## Best Practices

### 1. Pre-Purge Checklist
- [ ] Confirm this is a test/development environment
- [ ] Backup any important data if needed
- [ ] Notify all users if this affects them
- [ ] Document why the purge is necessary

### 2. Environment Safety
```bash
# Set admin key in production environments
export MEMORY_ADMIN_KEY="complex-secure-key-here"

# Consider IP restrictions in production
# (implement in reverse proxy/firewall)
```

### 3. Post-Purge Verification
```bash
# 1. Check database stats
curl http://localhost:8001/debug/stats

# 2. Test memory system still works
curl -X POST http://localhost:8001/api/memory/save \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "content": "test memory after purge"
  }'

# 3. Verify new memory can be retrieved
curl -X POST http://localhost:8001/api/memory/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "query": "test",
    "limit": 5
  }'
```

### 4. Alternative Individual User Cleanup
If you need to clear data for specific users instead:

```bash
# Clear specific user's memory
curl -X DELETE http://localhost:8001/memory/user123

# Or use the confirmation-based endpoint
curl -X POST http://localhost:8001/api/memory/clear \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "confirm": true
  }'
```

## Security Considerations

### Production Deployment
1. **Always set MEMORY_ADMIN_KEY** in production
2. **Restrict network access** to admin endpoints
3. **Log all purge operations** for audit trails
4. **Implement role-based access** if multiple admins

### Access Control Example
```nginx
# Nginx configuration to restrict admin endpoints
location /admin/ {
    allow 10.0.0.0/8;     # Internal network only
    allow 127.0.0.1;      # Localhost
    deny all;
    proxy_pass http://memory-api:8001;
}
```

## Recovery

### If Purge Was Accidental
**Unfortunately, there is no recovery** - the purge operation is irreversible by design.

### Mitigation Strategies
1. **Regular Backups**: Implement database backups if data recovery is needed
2. **Staging Environment**: Test purge operations in staging first
3. **Confirmation Workflows**: Require multiple approvals for production purges

## Support

For issues with the purge endpoint:
1. Check the memory service logs: `docker-compose logs memory`
2. Verify database connections: `curl http://localhost:8001/health`
3. Test with debug stats: `curl http://localhost:8001/debug/stats`

---

**Remember: The purge endpoint is a powerful administrative tool. Use it responsibly and always double-check your environment before execution.**
