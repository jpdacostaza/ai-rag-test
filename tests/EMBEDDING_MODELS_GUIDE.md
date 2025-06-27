# Embedding Models Configuration Guide

## Current Configuration

### Default Embedding Model
**Primary Model:** `nomic-embed-text` (Ollama-based)
- **Location:** `config.py` - `EMBEDDING_MODEL = "nomic-embed-text"`
- **Provider:** Ollama
- **Status:** ✅ Available and working
- **Size:** 274 MB
- **Type:** Text embedding model optimized for semantic search

### Model Availability Check

Current available models in Ollama:
```bash
$ docker exec backend-ollama ollama list
NAME                       ID              SIZE      MODIFIED       
nomic-embed-text:latest    0a109f422b47    274 MB    13 minutes ago
llama3.2:3b                a80c4f17acd5    2.0 GB    46 hours ago
```

## Architecture Overview

### 1. Configuration (config.py)
```python
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")  # Fixed: Use nomic-embed-text for Ollama
```
- Default model can be overridden via environment variable
- Currently optimized for Ollama integration

### 2. Model Loading (database_manager.py)
The system follows this initialization flow:

1. **Check Ollama Availability**: Connects to `OLLAMA_BASE_URL/api/tags`
2. **Model Verification**: Checks if embedding model is available
3. **Auto-Pull Logic**: If `AUTO_PULL_MODELS=true`, automatically pulls missing models
4. **Fallback**: Gracefully degrades if model unavailable

### 3. Embedding Generation (services/llm_service.py)
```python
async def get_embeddings(self, text: str, model: Optional[str] = None) -> Optional[List[float]]:
    """Get embeddings for text using Ollama."""
    model = model or EMBEDDING_MODEL
    # Uses Ollama API: POST /api/embeddings
```

### 4. Usage in Database Operations (database_manager.py)
```python
async def get_embedding(self, text: str) -> Optional[List[float]]:
    """Get embedding for text using Ollama."""
    embedding = await llm_service.get_embeddings(text, self.embedding_model)
    return embedding
```

## Supported Models

### Primary: Ollama Models
- **nomic-embed-text** (Default) ✅
  - Optimized for semantic search
  - Good performance/size ratio
  - Well-integrated with Ollama

### Legacy Support: SentenceTransformers
The codebase maintains backward compatibility for SentenceTransformers:
- **sentence-transformers/all-MiniLM-L6-v2** (Legacy)
  - Only used in `utilities/cpu_enforcer.py` for testing
  - Not actively used for production embeddings
  - Kept for CPU-only verification

## Configuration Options

### Environment Variables
```bash
# Primary embedding model
EMBEDDING_MODEL=nomic-embed-text

# Disable embeddings entirely
DISABLE_EMBEDDINGS=false

# Automatic model pulling
AUTO_PULL_MODELS=true

# Ollama connection
OLLAMA_BASE_URL=http://localhost:11434
```

### Docker Integration
Models are managed through the Ollama container:
```bash
# List available models
docker exec backend-ollama ollama list

# Pull a new embedding model
docker exec backend-ollama ollama pull nomic-embed-text

# Pull alternative models
docker exec backend-ollama ollama pull mxbai-embed-large
```

## Health Monitoring

### Startup Checks
1. **Ollama Connectivity**: Verifies connection to Ollama API
2. **Model Availability**: Confirms embedding model is pulled and ready
3. **Auto-Pull**: Attempts to pull missing models if enabled

### Runtime Health
- Health check endpoint: `/health` includes embedding status
- Watchdog monitoring for embedding availability
- Graceful degradation if embeddings unavailable

## Common Operations

### Adding a New Embedding Model

1. **Pull the model in Ollama:**
   ```bash
   docker exec backend-ollama ollama pull <model-name>
   ```

2. **Update configuration:**
   ```bash
   export EMBEDDING_MODEL=<model-name>
   ```
   Or update in `config.py`

3. **Restart the application:**
   ```bash
   docker-compose restart backend
   ```

### Troubleshooting

#### Model Not Available
```bash
# Check if model exists in Ollama
docker exec backend-ollama ollama list

# Pull missing model
docker exec backend-ollama ollama pull nomic-embed-text

# Verify Ollama is running
docker-compose ps ollama
```

#### Embedding Errors
- Check logs for "embeddings" service status
- Verify `OLLAMA_BASE_URL` is correct
- Ensure Ollama container has sufficient resources

## Performance Considerations

### Model Size vs Performance
- **nomic-embed-text**: 274 MB - Good balance
- **all-MiniLM-L6-v2**: ~80 MB - Smaller but requires different architecture
- **mxbai-embed-large**: ~600 MB - Better quality, larger size

### Resource Requirements
- **Memory**: ~500 MB per embedding model
- **CPU**: Embedding generation is CPU-intensive
- **Storage**: Model files stored in Ollama volume

## Migration Notes

### From SentenceTransformers to Ollama
The system has been migrated from SentenceTransformers to Ollama for:
- Better integration with existing LLM infrastructure
- Consistent API interface
- Improved resource management
- Docker-native deployment

Legacy SentenceTransformers code remains for compatibility but is not actively used in production.

## API Integration

### Direct Usage
```python
from services.llm_service import llm_service

# Get embeddings for text
embeddings = await llm_service.get_embeddings("Sample text", "nomic-embed-text")
```

### Through Database Manager
```python
from database_manager import DatabaseManager

db = DatabaseManager()
await db.initialize()

# Get embeddings (uses configured default model)
embeddings = await db.get_embedding("Sample text")
```

## Status: ✅ WORKING

- **Configuration**: ✅ Properly set to nomic-embed-text
- **Model Availability**: ✅ Model pulled and ready in Ollama
- **Integration**: ✅ LLM service properly integrated
- **Health Checks**: ✅ Monitoring and validation working
- **Auto-Pull**: ✅ Automatic model pulling implemented
- **Fallback**: ✅ Graceful degradation for missing models

The embedding system is fully operational and ready for production use.
