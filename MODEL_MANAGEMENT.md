# 🤖 Model Management Guide

## Adding the Mistral Model: `mistral:7b-instruct-v0.3-q4_k_m`

### 🚀 Quick Start (Recommended)

```bash
# Add the Mistral model
./add-model.sh mistral:7b-instruct-v0.3-q4_k_m

# Test the model
./test-model.sh mistral:7b-instruct-v0.3-q4_k_m
```

### 📋 Manual Method

#### 1. Add the Model via Script
```bash
chmod +x add-model.sh test-model.sh manage-models.sh
./add-model.sh mistral:7b-instruct-v0.3-q4_k_m
```

#### 2. Add the Model Manually
```bash
# Ensure Ollama container is running
docker-compose up -d ollama

# Download the model
docker exec backend-ollama ollama pull mistral:7b-instruct-v0.3-q4_k_m

# Verify download
docker exec backend-ollama ollama list
```

#### 3. Set as Default Model (Optional)
```bash
# Edit docker-compose.yml to change the default model
# Change this line:
DEFAULT_MODEL=llama3.2:3b

# To this:
DEFAULT_MODEL=mistral:7b-instruct-v0.3-q4_k_m

# Restart the backend
docker-compose restart llm_backend
```

### 🧪 Testing the Model

#### Via API Test Script
```bash
./test-model.sh mistral:7b-instruct-v0.3-q4_k_m
```

#### Via Direct API Call
```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer f2b985dd-219f-45b1-a90e-170962cc7082" \
  -d '{
    "model": "mistral:7b-instruct-v0.3-q4_k_m",
    "messages": [
      {
        "role": "user",
        "content": "Hello! What can you help me with?"
      }
    ],
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

#### Via Backend API Verification
```bash
# Verify model is available
curl http://localhost:8001/v1/models/verify/mistral:7b-instruct-v0.3-q4_k_m
```

### 🎛️ Interactive Model Management

```bash
# Launch interactive model manager
./manage-models.sh
```

This provides a menu-driven interface to:
- List available models
- Add new models
- Remove models
- Set default model
- Test models
- View model information
- Browse popular models

### 📊 Model Comparison

| Model | Size | Strengths | Use Case |
|-------|------|-----------|----------|
| `llama3.2:3b` (current) | ~2GB | Fast, efficient | General chat, quick responses |
| `mistral:7b-instruct-v0.3-q4_k_m` | ~4GB | Instruction following | Complex tasks, detailed answers |
| `llama3.1:8b` | ~5GB | Balanced performance | Versatile applications |
| `codellama:7b` | ~4GB | Code generation | Programming assistance |

### 🔧 Configuration Options

#### Using Multiple Models Simultaneously

The system supports switching between models per request:

```python
# In your API calls, specify the model
{
  "model": "mistral:7b-instruct-v0.3-q4_k_m",  # Use Mistral
  "messages": [...]
}

# Or use the default
{
  "model": "llama3.2:3b",  # Use Llama (current default)
  "messages": [...]
}
```

#### Model-Specific Optimizations

Each model may perform better with different parameters:

```bash
# Mistral: Good with higher temperature for creativity
{
  "model": "mistral:7b-instruct-v0.3-q4_k_m",
  "temperature": 0.8,
  "max_tokens": 500
}

# Llama3.2: Good with lower temperature for precision
{
  "model": "llama3.2:3b", 
  "temperature": 0.3,
  "max_tokens": 300
}
```

### 🚨 Troubleshooting

#### Model Download Issues
```bash
# Check Ollama container logs
docker logs backend-ollama

# Restart Ollama if needed
docker-compose restart ollama

# Retry download
docker exec backend-ollama ollama pull mistral:7b-instruct-v0.3-q4_k_m
```

#### Model Not Available in API
```bash
# Verify model exists
docker exec backend-ollama ollama list

# Check backend logs
docker logs backend-llm-backend

# Restart backend to refresh model list
docker-compose restart llm_backend
```

#### Memory Issues
```bash
# Check available space
df -h

# Remove unused models
docker exec backend-ollama ollama rm <model_name>

# Clean up Docker
docker system prune -f
```

### 📈 Performance Monitoring

#### Check Model Performance
```bash
# Monitor resource usage
docker stats

# Check model response times
curl -w "Response time: %{time_total}s\n" \
  -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:7b-instruct-v0.3-q4_k_m", "messages": [{"role": "user", "content": "Test"}]}'
```

#### Model Information
```bash
# Get detailed model info
docker exec backend-ollama ollama show mistral:7b-instruct-v0.3-q4_k_m

# List all models with sizes
docker exec backend-ollama ollama list
```

### 🎯 Best Practices

1. **Model Selection**
   - Use `llama3.2:3b` for fast, lightweight tasks
   - Use `mistral:7b-instruct-v0.3-q4_k_m` for complex instructions
   - Consider system resources when choosing models

2. **Storage Management**
   - Regularly clean up unused models
   - Monitor disk space in `./storage/ollama/`
   - Use quantized models (q4_k_m) for better efficiency

3. **Performance Optimization**
   - Keep frequently used models downloaded
   - Use appropriate temperature settings per model
   - Monitor response times and adjust as needed

4. **Development Workflow**
   - Test new models before setting as default
   - Use model-specific prompting strategies
   - Keep backup of working configurations

### 🔄 Switching Between Models

#### Temporary Switch (Single Request)
```bash
# Use Mistral for one request
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:7b-instruct-v0.3-q4_k_m", ...}'
```

#### Permanent Switch (Change Default)
```bash
# Update docker-compose.yml
sed -i 's/DEFAULT_MODEL=.*/DEFAULT_MODEL=mistral:7b-instruct-v0.3-q4_k_m/' docker-compose.yml

# Restart backend
docker-compose restart llm_backend
```

---

## 🎉 Ready to Use!

Your Mistral model is now available alongside the existing Llama model. You can:

✅ **Use via API** with the `model` parameter  
✅ **Set as default** in docker-compose.yml  
✅ **Test and compare** performance  
✅ **Manage multiple models** easily  

The system will automatically download and use the model as needed! 🚀
