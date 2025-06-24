# Advanced Memory Pipeline Setup Guide

## Overview

The Advanced Memory Pipeline integrates OpenWebUI with your backend's adaptive learning and ChromaDB memory systems. It provides:

- **Contextual Memory Injection**: Retrieves relevant memories and injects them into user prompts
- **Adaptive Learning**: Stores user/assistant interactions for continuous improvement
- **Async Communication**: High-performance HTTP communication with the backend
- **Flexible Configuration**: Configurable via OpenWebUI admin panel

## Installation Steps

### 1. Backend Setup

First, ensure your backend is running with the new pipeline endpoints:

```bash
# Start your backend (make sure it's running on the configured port)
cd /path/to/your/backend
python main.py
```

The backend should now have these new endpoints:
- `POST /api/memory/retrieve` - Retrieve user memories
- `POST /api/learning/process_interaction` - Store learning interactions
- `GET /api/pipeline/status` - Get backend status

### 2. Test Backend Endpoints

Run the test script to verify the backend is working:

```bash
cd setup
python debug/setup/test_pipeline.py
```

This will test all the pipeline endpoints and confirm they're working correctly.

### 3. Install Pipeline in OpenWebUI

1. **Copy the Pipeline File**:
   ```bash
   cp setup/advanced_memory_pipeline.py /path/to/openwebui/pipelines/
   ```

2. **Restart OpenWebUI**:
   ```bash
   # If using Docker
   docker restart openwebui
   
   # If running directly
   # Restart your OpenWebUI service
   ```

3. **Configure in Admin Panel**:
   - Go to OpenWebUI Admin Panel
   - Navigate to Pipelines section
   - Find "Advanced Memory Pipeline"
   - Configure the settings:
     - `backend_url`: Your backend URL (e.g., `http://localhost:8080`)
     - `api_key`: Your API key for authentication
     - `memory_limit`: Number of memories to retrieve (default: 3)
     - `memory_threshold`: Relevance threshold for memories (default: 0.7)
     - `enable_learning`: Enable adaptive learning storage (default: true)
     - `enable_memory_injection`: Enable memory context injection (default: true)

## Configuration Options

### Backend Settings
- **`backend_url`**: URL of your backend service
- **`api_key`**: API key for authentication (optional for development)

### Memory Settings
- **`memory_limit`**: Maximum number of memories to retrieve per query
- **`memory_threshold`**: Minimum relevance score for memory inclusion
- **`enable_memory_injection`**: Enable/disable memory context injection
- **`max_memory_length`**: Maximum length of individual memory content

### Learning Settings
- **`enable_learning`**: Enable/disable adaptive learning storage
- All user/assistant interactions are stored for learning when enabled

## How It Works

### Memory Injection (Filter Mode)
1. User sends a message to OpenWebUI
2. Pipeline intercepts the message (inlet function)
3. Retrieves relevant memories from backend using semantic search
4. Injects memory context into the user's message
5. Enhanced message goes to the LLM
6. LLM responds with additional context

### Learning Storage (Outlet Mode)
1. After LLM generates a response
2. Pipeline captures the user/assistant interaction (outlet function)
3. Stores the interaction in the backend for adaptive learning
4. Backend processes the interaction to improve future responses

## Example Usage

Once installed and configured, the pipeline works automatically:

```
User: "How do I configure Redis?"

Pipeline retrieves memories:
- Previous Redis configuration discussions
- Related database setup conversations
- Troubleshooting experiences

Enhanced prompt sent to LLM:
[RELEVANT CONTEXT FROM PREVIOUS CONVERSATIONS]
1. You previously configured Redis for caching...
2. Last week you had issues with Redis connection...
[END CONTEXT]

How do I configure Redis?
```

## Troubleshooting

### Common Issues

1. **Backend Connection Failed**
   - Check `backend_url` in pipeline configuration
   - Ensure backend is running and accessible
   - Verify network connectivity

2. **API Authentication Failed**
   - Check `api_key` configuration
   - Ensure backend accepts the provided key
   - For development, you can use "development" as the key

3. **No Memories Retrieved**
   - Check if ChromaDB is running and has data
   - Verify embedding model is working
   - Lower the `memory_threshold` value

4. **Learning Not Working**
   - Ensure `enable_learning` is true
   - Check backend logs for learning endpoint errors
   - Verify adaptive learning system is initialized

### Debug Mode

Enable debug logging in the pipeline configuration:
- Check OpenWebUI logs for pipeline messages
- Look for emoji-prefixed log messages from the pipeline
- Backend logs will show API endpoint calls

### Test Commands

```bash
# Test backend endpoints
python setup/test_pipeline.py

# Check pipeline status in OpenWebUI
# Go to Admin Panel > Pipelines > Advanced Memory Pipeline > Status

# Check backend health
curl http://localhost:8080/api/pipeline/status
```

## Advanced Configuration

### Custom Memory Formatting

You can modify the `_format_memory_context` method to change how memories are presented to the LLM:

```python
def _format_memory_context(self, memories: List[dict]) -> str:
    # Custom formatting logic here
    pass
```

### Multiple Backend Support

To support multiple backends, modify the `_call_backend` method to route to different endpoints based on request type.

### Performance Tuning

- Adjust `memory_limit` based on your LLM's context window
- Tune `memory_threshold` for relevance vs. quantity
- Monitor response times and adjust timeout values

## Security Considerations

1. **API Key Security**: Use proper API keys in production
2. **Data Privacy**: Ensure sensitive conversations are handled appropriately
3. **Network Security**: Use HTTPS in production environments
4. **Access Control**: Implement proper user authentication and authorization

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run the test script to identify specific problems
3. Review backend and OpenWebUI logs
4. Ensure all dependencies are installed correctly

The pipeline is designed to fail gracefully - if the backend is unavailable, conversations will continue normally without memory enhancement.
