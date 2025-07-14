#!/bin/bash

# Enhanced API Gateway Deployment Script
# This script helps deploy and test the enhanced API Gateway with best practices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GATEWAY_PORT=8888
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Enhanced API Gateway Deployment Script${NC}"
echo -e "${BLUE}============================================${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if ports are available
    if lsof -Pi :$GATEWAY_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $GATEWAY_PORT is already in use. The gateway might already be running."
    fi
    
    print_status "Prerequisites check completed."
}

# Generate environment configuration
generate_env_config() {
    print_status "Generating environment configuration..."
    
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << EOF
# Enhanced API Gateway Configuration
ENVIRONMENT=development
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8888

# Security Configuration
JWT_SECRET=$(openssl rand -base64 32)
RATE_LIMIT_REQUESTS=100
SSL_ENABLED=false

# Cache Configuration
CACHE_PROVIDER=redis
REDIS_HOST=backend-redis
REDIS_PORT=6379

# Monitoring Configuration
LOG_LEVEL=INFO
TRACING_ENABLED=false
METRICS_ENABLED=true

# CORS Configuration
CORS_ORIGINS=*

# Service Discovery
MEMORY_API_HOST=backend-memory-api
MEMORY_API_PORT=5001
OLLAMA_HOST=backend-ollama
OLLAMA_PORT=11434
OPENWEBUI_HOST=backend-openwebui
OPENWEBUI_PORT=8080
PIPELINES_HOST=backend-pipelines
PIPELINES_PORT=9099
CHROMA_HOST=backend-chroma
CHROMA_PORT=8000
EOF
        print_status "Environment configuration created in $ENV_FILE"
    else
        print_warning "Environment file $ENV_FILE already exists. Skipping generation."
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p storage/gateway
    mkdir -p storage/redis
    mkdir -p storage/chroma
    mkdir -p logs
    mkdir -p config
    
    print_status "Directories created successfully."
}

# Build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Stop any existing services
    docker-compose down 2>/dev/null || true
    
    # Build the enhanced gateway
    print_status "Building enhanced API Gateway image..."
    docker-compose build api-gateway
    
    # Start dependencies first
    print_status "Starting dependency services..."
    docker-compose up -d redis chroma
    
    # Wait for dependencies to be healthy
    print_status "Waiting for dependencies to be ready..."
    sleep 10
    
    # Start core services
    print_status "Starting core services..."
    docker-compose up -d ollama backend memory-api pipelines
    
    # Wait for core services
    print_status "Waiting for core services to be ready..."
    sleep 15
    
    # Start OpenWebUI
    print_status "Starting OpenWebUI..."
    docker-compose up -d openwebui
    
    # Wait for OpenWebUI
    sleep 10
    
    # Finally start the enhanced API Gateway
    print_status "Starting Enhanced API Gateway..."
    docker-compose up -d api-gateway
    
    print_status "All services started successfully."
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$GATEWAY_PORT/gateway/health" > /dev/null 2>&1; then
            print_status "Enhanced API Gateway is ready!"
            break
        fi
        
        echo -ne "\r${YELLOW}[INFO]${NC} Waiting for gateway... (${attempt}/${max_attempts})"
        sleep 2
        ((attempt++))
    done
    
    echo ""
    
    if [ $attempt -gt $max_attempts ]; then
        print_error "Gateway did not start within expected time. Check logs with: docker-compose logs api-gateway"
        exit 1
    fi
}

# Run comprehensive tests
run_tests() {
    print_status "Running comprehensive tests..."
    
    if [ -f "tests/test_enhanced_gateway.py" ]; then
        python tests/test_enhanced_gateway.py
    else
        print_warning "Test file not found. Running basic health checks..."
        
        # Basic health check
        echo "Testing gateway health..."
        curl -s "http://localhost:$GATEWAY_PORT/gateway/health" | jq '.' || echo "Health check failed"
        
        # Test metrics
        echo "Testing gateway metrics..."
        curl -s "http://localhost:$GATEWAY_PORT/gateway/metrics" | jq '.' || echo "Metrics check failed"
        
        # Test configuration
        echo "Testing gateway configuration..."
        curl -s "http://localhost:$GATEWAY_PORT/gateway/config" | jq '.' || echo "Config check failed"
    fi
}

# Display deployment summary
show_summary() {
    print_status "Deployment Summary"
    echo ""
    echo -e "${GREEN}✓ Enhanced API Gateway is running on http://localhost:$GATEWAY_PORT${NC}"
    echo ""
    echo "Key endpoints:"
    echo "  🏥 Health Check:     http://localhost:$GATEWAY_PORT/gateway/health"
    echo "  📊 Metrics:          http://localhost:$GATEWAY_PORT/gateway/metrics"
    echo "  ⚙️  Configuration:    http://localhost:$GATEWAY_PORT/gateway/config"
    echo ""
    echo "Service endpoints (through gateway):"
    echo "  🧠 Memory API:       http://localhost:$GATEWAY_PORT/api/memory/"
    echo "  🤖 Ollama:           http://localhost:$GATEWAY_PORT/api/ollama/"
    echo "  🌐 OpenWebUI:        http://localhost:$GATEWAY_PORT/api/webui/"
    echo "  📊 ChromaDB:         http://localhost:$GATEWAY_PORT/api/vector/"
    echo ""
    echo "Management commands:"
    echo "  📝 View logs:        docker-compose logs api-gateway"
    echo "  🔄 Restart:          docker-compose restart api-gateway"
    echo "  🛑 Stop:             docker-compose down"
    echo "  📊 Monitor:          docker stats"
    echo ""
    echo -e "${GREEN}Deployment completed successfully!${NC}"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    docker-compose down
    print_status "Cleanup completed."
}

# Show help
show_help() {
    echo "Enhanced API Gateway Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy    - Deploy the enhanced API gateway (default)"
    echo "  test      - Run comprehensive tests"
    echo "  status    - Show service status"
    echo "  logs      - Show gateway logs"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart the gateway"
    echo "  cleanup   - Stop and remove all containers"
    echo "  help      - Show this help message"
    echo ""
}

# Show service status
show_status() {
    print_status "Service Status:"
    docker-compose ps
    echo ""
    
    if curl -s -f "http://localhost:$GATEWAY_PORT/gateway/health" > /dev/null 2>&1; then
        print_status "Gateway health check:"
        curl -s "http://localhost:$GATEWAY_PORT/gateway/health" | jq '.'
    else
        print_warning "Gateway is not responding to health checks"
    fi
}

# Show logs
show_logs() {
    print_status "Showing gateway logs (press Ctrl+C to exit):"
    docker-compose logs -f api-gateway
}

# Restart gateway
restart_gateway() {
    print_status "Restarting Enhanced API Gateway..."
    docker-compose restart api-gateway
    wait_for_services
    print_status "Gateway restarted successfully."
}

# Main execution
main() {
    local command=${1:-deploy}
    
    case $command in
        "deploy")
            check_prerequisites
            generate_env_config
            create_directories
            deploy_services
            wait_for_services
            run_tests
            show_summary
            ;;
        "test")
            run_tests
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "stop")
            docker-compose stop
            print_status "Services stopped."
            ;;
        "restart")
            restart_gateway
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"
