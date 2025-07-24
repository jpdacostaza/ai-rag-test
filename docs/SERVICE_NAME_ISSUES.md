## Service Name Inconsistencies Analysis

### 🚨 CRITICAL ISSUES FOUND:

1. **Redis Service**: 
   - .env has: `REDIS_URL=redis://backend-redis:6379` 
   - Docker service name: `redis` (not `backend-redis`)
   - Should be: `redis://redis:6379`

2. **Model Names**:
   - .env has: `OLLAMA_MODEL=qwen3:4b` and `DEFAULT_MODEL=qwen3:4b`
   - User is actually using: `qwen2.5:3b`
   - Refresh script now correctly uses: `qwen2.5:3b`

3. **Multiple hardcoded localhost URLs** that won't work inside Docker containers

4. **Container name vs Service name confusion**:
   - Container names: `backend-ollama`, `backend-openwebui`, etc.
   - Service names: `ollama`, `openwebui`, etc.
   - Docker networks use service names, not container names

### 📍 FILES NEEDING FIXES:

1. **.env file** - Redis URL and model names
2. **utilities/force_refresh.py** - hardcoded localhost
3. **Multiple scripts** - localhost URLs for internal service communication
4. **Shell scripts** - container name references in docker exec commands
5. **Configuration files** - mixed service name usage

### 🔧 PRIORITY FIXES NEEDED:

1. Fix Redis URL in .env (HIGH PRIORITY)
2. Update model names to qwen2.5:3b (HIGH PRIORITY)  
3. Fix localhost URLs in Python utilities (MEDIUM)
4. Update shell scripts to use correct container names (LOW)
