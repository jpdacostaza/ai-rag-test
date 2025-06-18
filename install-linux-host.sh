#!/bin/bash
# install-linux-host.sh - Prepare Linux host for LLM Backend deployment
# Run this script on the Linux host before deploying with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root or with sudo"
    echo "Usage: sudo $0"
    exit 1
fi

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    else
        echo "unknown"
    fi
}

# Install Docker based on distribution
install_docker() {
    local distro=$(detect_distro)
    log_info "Detected distribution: $distro"
    
    case "$distro" in
        ubuntu|debian)
            log_info "Installing Docker for Ubuntu/Debian..."
            apt-get update
            apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            
            # Add Docker's official GPG key
            curl -fsSL https://download.docker.com/linux/$distro/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            
            # Add Docker repository
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$distro $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        centos|rhel|fedora)
            log_info "Installing Docker for CentOS/RHEL/Fedora..."
            yum install -y yum-utils
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        *)
            log_warning "Unknown distribution. Please install Docker manually."
            log_info "Visit: https://docs.docker.com/engine/install/"
            return 1
            ;;
    esac
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    log_success "Docker installed and started"
}

# Install Docker Compose (standalone version for older systems)
install_docker_compose() {
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_info "Installing Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        log_success "Docker Compose installed"
    else
        log_success "Docker Compose already installed"
    fi
}

# Main installation process
main() {
    log_step "Linux Host Preparation for LLM Backend"
    
    # Check if Docker is already installed
    if command -v docker >/dev/null 2>&1; then
        log_success "Docker is already installed"
        docker --version
    else
        log_warning "Docker not found, installing..."
        install_docker
    fi
    
    # Check Docker Compose
    if command -v docker-compose >/dev/null 2>&1; then
        log_success "Docker Compose is already installed"
        docker-compose --version
    else
        log_warning "Docker Compose not found, installing..."
        install_docker_compose
    fi
    
    # Create deployment directory
    log_step "Setting up deployment directory"
    local deploy_dir="/opt/backend"
    
    if [ ! -d "$deploy_dir" ]; then
        mkdir -p "$deploy_dir"
        log_info "Created deployment directory: $deploy_dir"
    else
        log_info "Deployment directory exists: $deploy_dir"
    fi
    
    # Run the smart startup script for initial setup
    if [ -f "./smart-startup.sh" ]; then
        log_step "Running initial setup"
        chmod +x ./smart-startup.sh
        ./smart-startup.sh --check-only
    else
        log_warning "smart-startup.sh not found in current directory"
        log_info "Make sure to copy all files to $deploy_dir before deployment"
    fi
    
    log_step "Installation Complete"
    log_success "Linux host is now ready for LLM Backend deployment!"
    echo ""
    log_info "Next steps:"
    echo "  1. Copy all backend files to $deploy_dir"
    echo "  2. cd $deploy_dir"
    echo "  3. Run: sudo ./smart-startup.sh"
    echo "  4. Run: docker-compose up --build -d"
    echo ""
    log_info "The smart-startup.sh script will automatically:"
    echo "  • Create the llama user with proper home directory"
    echo "  • Set up storage directories with correct permissions"
    echo "  • Verify all dependencies and configurations"
    echo "  • Provide health checks and diagnostics"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Linux Host Preparation Script for LLM Backend"
        echo ""
        echo "This script prepares a Linux host for LLM Backend deployment by:"
        echo "  • Installing Docker and Docker Compose"
        echo "  • Setting up deployment directories"
        echo "  • Running initial system checks"
        echo ""
        echo "Usage: sudo $0"
        echo ""
        echo "After running this script, deploy with:"
        echo "  sudo ./smart-startup.sh"
        echo "  docker-compose up --build -d"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
