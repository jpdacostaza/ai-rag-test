#!/bin/bash
# Enhanced Memory System - Simplified Deployment Script

set -e

echo "🚀 Enhanced Memory System - Simplified Deployment"
echo "=================================================="

# Configuration
COMPOSE_FILE="docker-compose.simplified.yml"
PROJECT_NAME="enhanced-memory"

# Functions
log_info() {
    echo "ℹ️  $1"
}

log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1"
}

log_warning() {
    echo "⚠️  $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Stop and clean up existing deployment
cleanup_existing() {
    log_info "Cleaning up existing deployment..."
    
    # Stop services
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down --remove-orphans 2>/dev/null || true
    
    # Remove old containers
    docker container prune -f 2>/dev/null || true
    
    # Remove unused images (optional)
    if [[ "$1" == "--clean" ]]; then
        log_warning "Removing unused Docker images..."
        docker image prune -f 2>/dev/null || true
    fi
    
    log_success "Cleanup completed"
}

# Build and start services
start_services() {
    log_info "Building and starting services..."
    
    # Build images
    log_info "Building application images..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME build --no-cache
    
    # Start core services first
    log_info "Starting core data services..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d redis chroma ollama
    
    # Wait for core services to be healthy
    log_info "Waiting for core services to be ready..."
    sleep 30
    
    # Start application services
    log_info "Starting application services..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d backend memory-api
    
    # Wait for application services
    log_info "Waiting for application services to be ready..."
    sleep 20
    
    # Start OpenWebUI services
    log_info "Starting OpenWebUI services..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d open-webui pipelines
    
    # Wait for OpenWebUI to be ready
    log_info "Waiting for OpenWebUI to be ready..."
    sleep 15
    
    # Run installer
    log_info "Running automatic configuration..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up installer
    
    log_success "All services started successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check service status
    log_info "Checking service status..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps
    
    # Health checks
    log_info "Performing health checks..."
    
    # Backend API
    if curl -f -s http://localhost:3000/api/health > /dev/null; then
        log_success "Backend API is healthy"
    else
        log_error "Backend API health check failed"
    fi
    
    # Memory API
    if curl -f -s http://localhost:5001/health > /dev/null; then
        log_success "Memory API is healthy"
    else
        log_error "Memory API health check failed"
    fi
    
    # Ollama
    if curl -f -s http://localhost:11434/api/tags > /dev/null; then
        log_success "Ollama service is healthy"
    else
        log_warning "Ollama service may still be starting up"
    fi
    
    # OpenWebUI
    if curl -f -s http://localhost:8080 > /dev/null; then
        log_success "OpenWebUI is accessible"
    else
        log_error "OpenWebUI is not accessible"
    fi
    
    log_success "Deployment verification completed"
}

# Download default model
download_model() {
    log_info "Downloading default model (llama3.2:3b)..."
    docker exec enhanced-ollama ollama pull llama3.2:3b || {
        log_warning "Model download failed. You can download it later from OpenWebUI."
    }
    log_success "Model download completed"
}

# Display access information
show_access_info() {
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo "===================================="
    echo ""
    echo "🌐 Access URLs:"
    echo "   OpenWebUI:    http://localhost:8080"
    echo "   Backend API:  http://localhost:3000"
    echo "   Memory API:   http://localhost:5001"
    echo "   Ollama:       http://localhost:11434"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Open http://localhost:8080 in your browser"
    echo "   2. Create your first user account"
    echo "   3. The Enhanced Memory System is automatically configured"
    echo "   4. Start chatting - your conversations will be remembered!"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs:    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f"
    echo "   Stop system:  docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down"
    echo "   Restart:      docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME restart"
    echo ""
}

# Main deployment flow
main() {
    case "$1" in
        --clean)
            check_prerequisites
            cleanup_existing --clean
            start_services
            verify_deployment
            download_model
            show_access_info
            ;;
        --verify)
            verify_deployment
            ;;
        --stop)
            log_info "Stopping Enhanced Memory System..."
            docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down
            log_success "System stopped"
            ;;
        --restart)
            log_info "Restarting Enhanced Memory System..."
            docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME restart
            verify_deployment
            log_success "System restarted"
            ;;
        --logs)
            docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f
            ;;
        *)
            check_prerequisites
            cleanup_existing
            start_services
            verify_deployment
            download_model
            show_access_info
            ;;
    esac
}

# Run main function with all arguments
main "$@"
