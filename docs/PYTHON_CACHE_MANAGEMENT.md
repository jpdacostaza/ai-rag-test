# Python Cache Management Guide

## What are `__pycache__` folders?

`__pycache__` directories contain compiled Python bytecode files (`.pyc`) that Python creates automatically to speed up module loading. When you import a Python module, Python compiles it to bytecode and caches it for faster subsequent imports.

## Why do they appear?

- **Automatic Creation**: Created whenever Python imports a module for the first time
- **Performance**: Significantly speeds up module loading on subsequent runs
- **Per-Version**: Different Python versions create separate cache files

## How to Handle Them

### 1. 🧹 Clean Existing Cache

#### Option A: Manual PowerShell Command
```powershell
Get-ChildItem -Recurse -Directory -Name "__pycache__" | ForEach-Object { Remove-Item $_ -Recurse -Force }
```

#### Option B: Use Cleanup Scripts
```bash
# Python script
python scripts/cleanup_pycache.py

# PowerShell script  
.\scripts\cleanup_pycache.ps1
```

### 2. 🚫 Prevent Creation (Development)

#### Environment Variable Method:
```bash
# In your terminal/shell
export PYTHONDONTWRITEBYTECODE=1

# In PowerShell
$env:PYTHONDONTWRITEBYTECODE = "1"

# In Docker container
ENV PYTHONDONTWRITEBYTECODE=1
```

#### Command Line Method:
```bash
python -B your_script.py  # -B flag disables .pyc creation
```

### 3. ✅ Ensure Git Ignores Them

The `.gitignore` already contains:
```gitignore
__pycache__/
*.py[cod]
```

### 4. 🐳 Docker Best Practices

In your Dockerfile:
```dockerfile
# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1
```

## Should You Disable Cache?

### ✅ **Disable** for:
- Development environments
- Docker containers (already compiled during build)
- CI/CD pipelines
- Version control cleanliness

### ❌ **Keep** for:
- Production environments (performance benefit)
- Long-running applications
- Frequently imported modules

## Quick Commands

```bash
# Remove all cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# PowerShell equivalent
Get-ChildItem -Recurse -Directory "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -File "*.pyc" | Remove-Item -Force

# Run Python without creating cache
python -B script.py

# Set environment variable permanently (Linux/Mac)
echo 'export PYTHONDONTWRITEBYTECODE=1' >> ~/.bashrc
```

## Current Project Status

✅ **Already Configured:**
- `.gitignore` properly ignores `__pycache__/` and `*.pyc`
- Cleanup scripts created in `scripts/` directory
- Docker containers should use `PYTHONDONTWRITEBYTECODE=1`

**Recommendation**: For this project, keep cache disabled in development and Docker environments for cleaner file system management.
