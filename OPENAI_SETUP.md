# OpenAI API Setup Guide

## Quick Setup for gpt-4o-mini Testing

### Step 1: Get OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with "sk-...")

### Step 2: Configure the Environment
Edit the `.env` file in the backend directory and replace:
```
OPENAI_API_KEY=your_openai_api_key_here
```
with:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 3: Restart Containers
Run in PowerShell from the backend directory:
```powershell
docker-compose down
docker-compose up -d
```

### Step 4: Test the Setup
1. Open OpenWebUI at http://localhost:8080
2. Go to Settings > Models
3. You should see "gpt-4o-mini" available
4. Set it as default if not already
5. Test with: "Hello my name is J.P. I work at Swift, can you remember that?"

## What We've Configured

Based on community research, we've optimized:

- **Model**: gpt-4o-mini (better context handling than local models)
- **Context Length**: 16384 tokens for memory operations
- **RAG Settings**: Top K=10, lower threshold=0.03 for more memory retrieval
- **Embedding**: nomic-embed-text (already pulled to Ollama)
- **Chunk Size**: 2000 tokens with 200 overlap

These settings should resolve the memory context injection issues you were experiencing.
