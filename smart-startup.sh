#!/bin/bash
# smart-startup.sh - Intelligent startup script with automatic permission fixing and health checks
# Combines startup.sh and fix-permissions.sh with enhanced logic for Linux deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Check if running in Docker container
is_docker() {
    [ -f /.dockerenv ] || grep -q 'docker\|lxc' /proc/1/cgroup 2>/dev/null
}

# Check if running as root
is_root() {
    [ "$EUID" -eq 0 ]
}

# Check if llama user exists
user_exists() {
    id "llama" &>/dev/null
}

# Check if directory exists and has correct permissions
check_directory_permissions() {
    local dir="$1"
    local expected_owner="$2"
    local expected_perms="$3"
    
    if [ ! -d "$dir" ]; then
        return 1  # Directory doesn't exist
    fi
    
    local actual_owner=$(stat -c "%U:%G" "$dir" 2>/dev/null || echo "unknown")
    local actual_perms=$(stat -c "%a" "$dir" 2>/dev/null || echo "000")
    
    if [[ "$actual_owner" == "$expected_owner" && "$actual_perms" == "$expected_perms" ]]; then
        return 0  # Permissions are correct
    else
        return 1  # Permissions need fixing
    fi
}

# Create llama user if needed
ensure_llama_user() {
    log_step "Checking llama user"
    
    if user_exists; then
        log_success "User 'llama' already exists"
        # Verify UID is 1000
        local current_uid=$(id -u llama)
        if [ "$current_uid" != "1000" ]; then
            log_warning "User 'llama' exists but UID is $current_uid, expected 1000"
        else
            log_success "User 'llama' has correct UID: 1000"
        fi
    else
        if is_root; then
            log_info "Creating llama user (UID 1000) with home directory..."
            # Create llama group if it doesn't exist
            if ! getent group llama >/dev/null 2>&1; then
                groupadd -g 1000 llama
                log_info "Created llama group (GID 1000)"
            fi
            # Create llama user with home directory (fixes ChromaDB permission issue)
            useradd -r -u 1000 -g llama -m -d /home/llama -s /bin/bash llama
            log_success "Created llama user with home directory /home/llama"
        else
            log_error "User 'llama' does not exist and script is not running as root"
            log_error "Please run with sudo or create the user manually"
            exit 1
        fi
    fi
}

# Create storage directory structure
create_storage_structure() {
    log_step "Creating storage directory structure"
    
    local directories=(
        "./storage"
        "./storage/redis"
        "./storage/chroma"
        "./storage/chroma/onnx_cache"
        "./storage/ollama"
        "./storage/backend"
        "./storage/models"
        "./storage/openwebui"
        "./storage/openwebui/cache"
        "./storage/openwebui/cache/audio"
        "./storage/openwebui/cache/embedding"
        "./storage/openwebui/cache/image"
        "./storage/openwebui/uploads"
        "./storage/openwebui/vector_db"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        else
            log_info "Directory exists: $dir"
        fi
    done
    
    log_success "Storage directory structure created"
}

# Fix permissions for all storage directories
fix_permissions() {
    log_step "Checking and fixing permissions"
    
    local needs_fixing=false
    
    # Check if we need to fix permissions
    local storage_dirs=(
        "./storage/redis:llama:llama:777"
        "./storage/chroma:llama:llama:777"
        "./storage/ollama:llama:llama:777"
        "./storage/backend:llama:llama:777"
        "./storage/models:llama:llama:777"
        "./storage/openwebui:llama:llama:777"
    )
    
    for entry in "${storage_dirs[@]}"; do
        IFS=':' read -r dir owner group perms <<< "$entry"
        if ! check_directory_permissions "$dir" "$owner:$group" "$perms"; then
            needs_fixing=true
            break
        fi
    done
    
    if [ "$needs_fixing" = true ]; then
        log_warning "Permissions need fixing"
        
        if is_root; then
            log_info "Fixing ownership and permissions..."
            
            # Set ownership to llama user
            if user_exists; then
                chown -R llama:llama ./storage
                log_info "Set ownership to llama:llama"
            else
                log_error "Cannot set ownership: llama user does not exist"
                exit 1
            fi
            
            # Set directory permissions
            chmod -R 755 ./storage
            chmod -R 777 ./storage/redis      # Redis needs write access
            chmod -R 777 ./storage/chroma     # ChromaDB needs write access  
            chmod -R 777 ./storage/ollama     # Ollama needs write access
            chmod -R 777 ./storage/backend    # Backend data needs write access
            chmod -R 777 ./storage/models     # Model cache needs write access
            chmod -R 777 ./storage/openwebui  # OpenWebUI data needs write access
            
            log_success "Permissions fixed successfully"
        else
            log_error "Permissions need fixing but script is not running as root"
            log_error "Please run with sudo to fix permissions"
            exit 1
        fi
    else
        log_success "All permissions are correct"
    fi
}

# Verify Python dependencies
check_python_dependencies() {
    log_step "Checking Python dependencies"
    
    if [ -f "requirements.txt" ]; then
        log_info "Installing/verifying Python dependencies..."
        if is_docker; then
            # In Docker, use pip directly
            pip install -r requirements.txt --no-cache-dir --quiet
        else
            # On host system, be more careful
            pip install -r requirements.txt --user --quiet
        fi
        log_success "Python dependencies verified"
    else
        log_warning "requirements.txt not found, skipping Python dependency check"
    fi
}

# Check if required services are available
check_service_dependencies() {
    log_step "Checking service dependencies"
    
    local services_ok=true
    
    # Check if Redis is accessible
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli ping >/dev/null 2>&1; then
            log_success "Redis is accessible"
        else
            log_warning "Redis command available but service not responding"
        fi
    else
        log_info "Redis CLI not available (expected in containerized environment)"
    fi
    
    # Check if Docker is available (for non-container runs)
    if ! is_docker; then
        if command -v docker >/dev/null 2>&1; then
            log_success "Docker is available"
        else
            log_warning "Docker not found - may need to install Docker"
            services_ok=false
        fi
        
        if command -v docker-compose >/dev/null 2>&1; then
            log_success "Docker Compose is available"
        else
            log_warning "Docker Compose not found - may need to install docker-compose"
            services_ok=false
        fi
    fi
    
    if [ "$services_ok" = true ]; then
        log_success "Service dependencies check passed"
    else
        log_warning "Some service dependencies may be missing"
    fi
}

# Verify internal cache directories
check_internal_cache() {
    log_step "Checking internal cache directories"
    
    local cache_dirs=(
        "/opt/internal_cache"
        "/opt/internal_cache/sentence_transformers"
        "/home/llama/.cache"
    )
    
    for dir in "${cache_dirs[@]}"; do
        if [ -d "$dir" ]; then
            log_success "Internal cache directory exists: $dir"
        else
            log_info "Internal cache directory will be created on demand: $dir"
        fi
    done
}

# Health check for storage and permissions
health_check() {
    log_step "Performing health check"
    
    local health_ok=true
    
    # Check storage structure
    local required_dirs=(
        "./storage/redis"
        "./storage/chroma"
        "./storage/ollama"
        "./storage/backend"
        "./storage/models"
        "./storage/openwebui"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            log_success "✓ Directory exists: $dir"
        else
            log_error "✗ Missing directory: $dir"
            health_ok=false
        fi
    done
    
    # Check permissions if running as root or llama user
    if is_root || [ "$(whoami)" = "llama" ]; then
        for dir in "${required_dirs[@]}"; do
            if [ -w "$dir" ]; then
                log_success "✓ Write access: $dir"
            else
                log_error "✗ No write access: $dir"
                health_ok=false
            fi
        done
    else
        log_info "Permission check skipped (not running as root or llama user)"
    fi
    
    if [ "$health_ok" = true ]; then
        log_success "Health check passed - system ready for startup"
        return 0
    else
        log_error "Health check failed - please review errors above"
        return 1
    fi
}

# Main startup logic
main() {
    log_step "LLM Backend Smart Startup Script"
    log_info "Running on: $(uname -s) $(uname -m)"
    log_info "User: $(whoami) (UID: $(id -u))"
    log_info "Docker container: $(if is_docker; then echo "Yes"; else echo "No"; fi)"
    log_info "Root privileges: $(if is_root; then echo "Yes"; else echo "No"; fi)"
    
    # Step 1: Ensure llama user exists (if we have permission)
    if is_root; then
        ensure_llama_user
    else
        log_info "Skipping user creation (not running as root)"
    fi
    
    # Step 2: Create storage structure
    create_storage_structure
    
    # Step 3: Fix permissions if needed and possible
    if is_root; then
        fix_permissions
    else
        log_warning "Skipping permission fixes (not running as root)"
        log_info "If you encounter permission issues, run: sudo $0"
    fi
    
    # Step 4: Check dependencies
    check_service_dependencies
    check_internal_cache
    
    # Step 5: Python dependencies (only in Docker or if explicitly requested)
    if is_docker || [ "$1" = "--install-deps" ]; then
        check_python_dependencies
    else
        log_info "Skipping Python dependency installation (use --install-deps to force)"
    fi
    
    # Step 6: Health check
    if ! health_check; then
        log_error "Startup health check failed"
        exit 1
    fi
    
    # Step 7: Start application (only if running in Docker)
    if is_docker; then
        log_step "Starting FastAPI backend"
        log_info "Backend will start on http://0.0.0.0:8001"
        exec uvicorn app:app --host 0.0.0.0 --port 8001 --log-level debug --reload
    else
        log_success "Setup complete! Ready to run: docker-compose up -d"
        log_info "To start the application manually: uvicorn app:app --host 0.0.0.0 --port 8001"
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "LLM Backend Smart Startup Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h         Show this help message"
        echo "  --install-deps     Force Python dependency installation"
        echo "  --check-only       Only perform checks, don't start services"
        echo ""
        echo "This script automatically:"
        echo "  • Creates llama user if needed (requires root)"
        echo "  • Creates storage directory structure"
        echo "  • Fixes permissions automatically (requires root)"
        echo "  • Verifies dependencies and health"
        echo "  • Starts the application (in Docker only)"
        echo ""
        echo "Run with sudo for full permission management:"
        echo "  sudo $0"
        exit 0
        ;;
    --check-only)
        log_step "Check-only mode"
        ensure_llama_user
        create_storage_structure
        check_service_dependencies
        check_internal_cache
        health_check
        log_success "Check-only mode complete"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
