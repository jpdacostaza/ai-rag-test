#!/bin/bash

# Enhanced Memory System Setup Script for OpenWebUI  
# Bash version for Linux/macOS

echo "🚀 Setting up Enhanced Memory System for OpenWebUI..."
echo "============================================================"

# Check if Docker is running
if ! docker version &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! docker-compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Build and start the complete system with automatic installer
echo "🔧 Starting Enhanced Memory System (includes automatic installer)..."
echo "   • Building containers..."
echo "   • Starting services..."
echo "   • Running automatic memory installer..."

docker-compose up --build -d

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Enhanced Memory System setup completed!"
    echo ""
    echo "📋 Installation Summary:"
    echo "   • Memory installer: ✅ Ran automatically on startup"
    echo "   • Enhanced Memory Pipeline: ✅ Installed automatically"
    echo "   • Enhanced Memory Function: 📋 Manual setup required"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Access OpenWebUI at: http://localhost:8080"
    echo "   2. Complete manual Function installation:"
    echo "      • Go to Admin Panel → Workspace → Functions"
    echo "      • Check installer logs for function code:"
    echo "        docker logs backend-memory-installer"
    echo ""
    echo "🔗 Access Points:"
    echo "   • OpenWebUI: http://localhost:8080"
    echo "   • Backend API: http://localhost:3000"
    echo "   • Memory API: http://localhost:8001"
    echo "   • Pipelines: http://localhost:9099"
    echo ""
    echo "📖 Memory System Features:"
    echo "   • ✅ Automatic conversation memory"
    echo "   • ✅ Semantic memory search"
    echo "   • ✅ User-specific memory isolation"
    echo "   • ✅ Adaptive learning system"
else
    echo ""
    echo "❌ Setup failed. Check the logs:"
    echo "   docker-compose logs"
    exit 1
fi

echo ""
echo "🏁 Setup completed! Enjoy your enhanced OpenWebUI experience!"
