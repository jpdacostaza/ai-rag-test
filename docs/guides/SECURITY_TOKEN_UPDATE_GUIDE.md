# Security Token Update Guide for Linux Deployment

## 🔐 **YES - You SHOULD Change JWT Token & API Keys on New Host**

### ⚠️ **Security Risk Analysis**

Your current configuration has **hardcoded tokens** that should be changed for production:

```yaml
# Current docker-compose.yml (INSECURE for production)
- JWT_SECRET=change_this_in_production     # ❌ Default value
- API_KEY=f2b985dd-219f-45b1-a90e-170962cc7082  # ❌ Exposed in code
- PIPELINES_API_KEY=0p3n-w3bu!            # ❌ Default value
- FUNCTIONS_API_KEY=0p3n-w3bu!             # ❌ Same as pipelines
```

### 🔑 **What Needs to Be Changed**

#### **1. JWT Secret (Critical)**
- **Current**: `JWT_SECRET=change_this_in_production`
- **Risk**: Authentication bypass
- **Action**: Generate new secure JWT secret

#### **2. API Keys (Important)**
- **Backend API**: `API_KEY=f2b985dd-219f-45b1-a90e-170962cc7082`
- **Pipelines**: `PIPELINES_API_KEY=0p3n-w3bu!`
- **Functions**: `FUNCTIONS_API_KEY=0p3n-w3bu!`
- **Risk**: Unauthorized API access
- **Action**: Generate new unique API keys

#### **3. External API Keys (Required)**
- **OpenAI**: `OPENAI_API_KEY` (your actual key)
- **Weather**: `WEATHERAPI_KEY` (if used)
- **Action**: Use your actual API keys

## 🛠️ **Linux Deployment Security Setup**

### **Step 1: Generate Secure Tokens**

```bash
# Generate JWT Secret (256-bit)
JWT_SECRET=$(openssl rand -hex 32)
echo "JWT_SECRET=$JWT_SECRET"

# Generate API Keys (UUID format)
BACKEND_API_KEY=$(uuidgen)
PIPELINES_API_KEY=$(uuidgen)
FUNCTIONS_API_KEY=$(uuidgen)

echo "BACKEND_API_KEY=$BACKEND_API_KEY"
echo "PIPELINES_API_KEY=$PIPELINES_API_KEY"
echo "FUNCTIONS_API_KEY=$FUNCTIONS_API_KEY"
```

### **Step 2: Create Secure .env File**

```bash
# On Linux host, create /opt/backend/.env
cd /opt/backend

cat > .env << EOF
# Security Tokens (Generated for this deployment)
JWT_SECRET=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256

# API Keys (Unique for this instance)
API_KEY=$(uuidgen)
PIPELINES_API_KEY=$(uuidgen)
FUNCTIONS_API_KEY=$(uuidgen)

# External API Keys (Your actual keys)
OPENAI_API_KEY=your_actual_openai_key_here
WEATHERAPI_KEY=your_actual_weather_key_here

# Database Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# ChromaDB Configuration
CHROMA_HOST=chroma
CHROMA_PORT=8000

# Service Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=9099
MEMORY_API_PORT=8000

# Security Settings
MAX_REQUESTS_PER_MINUTE=60
ENABLE_RATE_LIMITING=true

# Logging
LOG_LEVEL=INFO
ENABLE_DEBUG=false
EOF

# Secure the .env file
chmod 600 .env
chown $USER:$USER .env
```

### **Step 3: Update docker-compose.yml for Security**

Instead of hardcoding tokens, use environment variables:

```yaml
# Replace hardcoded values with environment variables
services:
  llm_backend:
    environment:
      - JWT_SECRET=${JWT_SECRET}
      - JWT_ALGORITHM=${JWT_ALGORITHM:-HS256}
      - API_KEY=${API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      # ...other variables...

  pipelines:
    environment:
      - PIPELINES_API_KEY=${PIPELINES_API_KEY}

  api_bridge:
    environment:
      - FUNCTIONS_API_KEY=${FUNCTIONS_API_KEY}

  openwebui:
    environment:
      - PIPELINES_API_KEY=${PIPELINES_API_KEY}
      - FUNCTIONS_API_KEY=${FUNCTIONS_API_KEY}
```

## 🔧 **Automated Security Setup Script**

Let me create a script that does this automatically:

```bash
#!/bin/bash
# secure_deployment.sh - Generate secure tokens for Linux deployment

echo "🔐 Generating secure tokens for Linux deployment..."

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists. Creating backup..."
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
fi

# Generate secure tokens
JWT_SECRET=$(openssl rand -hex 32)
BACKEND_API_KEY=$(uuidgen)
PIPELINES_API_KEY=$(uuidgen)  
FUNCTIONS_API_KEY=$(uuidgen)

# Create secure .env file
cat > .env << EOF
# Security Configuration - Generated $(date)
JWT_SECRET=$JWT_SECRET
JWT_ALGORITHM=HS256

# API Keys - Unique for this deployment
API_KEY=$BACKEND_API_KEY
PIPELINES_API_KEY=$PIPELINES_API_KEY
FUNCTIONS_API_KEY=$FUNCTIONS_API_KEY

# External API Keys (REPLACE WITH YOUR ACTUAL KEYS)
OPENAI_API_KEY=your_openai_key_here
WEATHERAPI_KEY=your_weather_key_here

# Service Configuration
REDIS_HOST=redis
REDIS_PORT=6379
CHROMA_HOST=chroma
CHROMA_PORT=8000

# Performance Settings
MAX_REQUESTS_PER_MINUTE=60
LOG_LEVEL=INFO
EOF

# Secure the file
chmod 600 .env
chown $USER:$USER .env

echo "✅ Secure .env file created!"
echo ""
echo "🔑 Generated tokens:"
echo "   JWT_SECRET: ${JWT_SECRET:0:16}..."
echo "   API_KEY: $BACKEND_API_KEY"
echo "   PIPELINES_KEY: $PIPELINES_API_KEY"
echo "   FUNCTIONS_KEY: $FUNCTIONS_API_KEY"
echo ""
echo "⚠️  IMPORTANT: Edit .env and add your actual OPENAI_API_KEY!"
echo "   nano .env"
echo ""
echo "🚀 Start services with: docker-compose up -d"
```

## 📊 **Security Comparison**

| Token | Current (Insecure) | New (Secure) | Risk Level |
|-------|-------------------|--------------|------------|
| JWT_SECRET | `change_this_in_production` | 64-char random hex | 🔴 Critical |
| API_KEY | Exposed in repo | UUID generated | 🟡 High |
| PIPELINES_KEY | `0p3n-w3bu!` | UUID generated | 🟡 High |
| FUNCTIONS_KEY | `0p3n-w3bu!` | UUID generated | 🟡 High |

## 🚀 **Quick Linux Deployment with Security**

```bash
# 1. Copy project to Linux
scp -r backend/ user@linux-host:/opt/backend/

# 2. Generate secure tokens
cd /opt/backend
chmod +x secure_deployment.sh
./secure_deployment.sh

# 3. Edit .env with your actual API keys
nano .env

# 4. Start services
docker-compose up -d
```

## ⚡ **Automatic Security Update Script**

Let me create this for you:
