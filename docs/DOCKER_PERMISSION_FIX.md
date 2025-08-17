# Docker Permission Fix for api_startup_hook.sh

## Problem
```
Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: exec: "/app/scripts/api_startup_hook.sh": permission denied: unknown
```

## Root Cause
The script `/app/scripts/api_startup_hook.sh` doesn't have execute permissions in the container, despite the Dockerfile having `RUN chmod +x` command.

## Solutions (Choose One)

### Solution 1: Fix File Permissions Before Build (Recommended)

On your Linux host, fix the permissions of the script file:

```bash
cd /opt/backend
chmod +x scripts/api_startup_hook.sh
ls -la scripts/api_startup_hook.sh  # Verify permissions
```

Then rebuild the container:
```bash
docker-compose build backend-api-function-installer
docker-compose up -d backend-api-function-installer
```

### Solution 2: Enhanced Dockerfile Fix

Update `Dockerfile.api-function-installer` to ensure permissions are set correctly:

```dockerfile
# Dockerfile for API-Based Function Auto-Installer with Admin Authentication
FROM python:3.11-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install httpx

# Create app directory structure
RUN mkdir -p /app/scripts

# Copy the API-based installer and hook scripts
COPY scripts/api_function_installer.py /app/scripts/api_function_installer.py
COPY scripts/api_startup_hook.sh /app/scripts/api_startup_hook.sh

# Make scripts executable - force permissions
RUN chmod +x /app/scripts/api_startup_hook.sh && \
    chmod 755 /app/scripts/api_startup_hook.sh && \
    ls -la /app/scripts/api_startup_hook.sh

# Set working directory
WORKDIR /app

# Verify permissions before running
RUN ls -la /app/scripts/api_startup_hook.sh && file /app/scripts/api_startup_hook.sh

# Run the API-based setup
ENTRYPOINT ["/app/scripts/api_startup_hook.sh"]
```

### Solution 3: Use Bash Wrapper (Emergency Fix)

If the above doesn't work, modify the ENTRYPOINT to use bash explicitly:

```dockerfile
# Change the last line from:
ENTRYPOINT ["/app/scripts/api_startup_hook.sh"]

# To:
ENTRYPOINT ["bash", "/app/scripts/api_startup_hook.sh"]
```

### Solution 4: Docker Compose Override

Add this to your `docker-compose.yml` for the `backend-api-function-installer` service:

```yaml
backend-api-function-installer:
  # ... existing configuration ...
  entrypoint: ["bash", "/app/scripts/api_startup_hook.sh"]
  # OR
  command: ["bash", "/app/scripts/api_startup_hook.sh"]
```

## Quick Fix Commands

### Immediate Fix (Run on Linux host):
```bash
# Stop the container
docker stop backend-api-function-installer

# Fix permissions in source
cd /opt/backend
chmod +x scripts/api_startup_hook.sh

# Rebuild and restart
docker-compose build backend-api-function-installer
docker-compose up -d backend-api-function-installer

# Check logs
docker logs backend-api-function-installer
```

### Alternative Quick Fix (Bash wrapper):
```bash
# Stop the container
docker stop backend-api-function-installer

# Run with bash explicitly
docker run -d --name backend-api-function-installer-temp \
  --network backend_default \
  $(docker inspect backend-api-function-installer --format='{{.Config.Image}}') \
  bash /app/scripts/api_startup_hook.sh

# Check if it works
docker logs backend-api-function-installer-temp
```

## Prevention for Future

To prevent this issue in the future:

1. **Use Git attributes** - Add to `.gitattributes`:
   ```
   *.sh text eol=lf
   ```

2. **Pre-commit hook** - Ensure scripts are executable:
   ```bash
   #!/bin/bash
   find . -name "*.sh" -exec chmod +x {} \;
   ```

3. **Docker buildx** - Use buildx for consistent builds:
   ```bash
   docker buildx build --platform linux/amd64 -f Dockerfile.api-function-installer -t backend-api-function-installer .
   ```

## Verification

After applying any fix, verify with:
```bash
# Check container is running
docker ps | grep backend-api-function-installer

# Check logs for success
docker logs backend-api-function-installer

# Verify script permissions inside container
docker exec backend-api-function-installer ls -la /app/scripts/api_startup_hook.sh
```

## Expected Success Output
```
🔧 API-Based Function Auto-Installer with Admin Authentication
============================================================
⏳ Waiting for OpenWebUI API to be ready...
✅ OpenWebUI health endpoint responding
✅ OpenWebUI API ready with admin authentication
🚀 Running API-based function installer with admin auth...
✅ API-based installation completed successfully
🔍 Verifying function installation...
✅ API verification successful - X functions available
🎯 API-based zero-configuration setup complete!
```

Choose **Solution 1** (fix permissions on host) as it's the cleanest approach.
