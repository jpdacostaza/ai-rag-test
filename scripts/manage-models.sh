#!/bin/bash
# manage-models.sh - Comprehensive model management

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

show_menu() {
    echo -e "${BLUE}🤖 Ollama Model Management${NC}"
    echo "=========================="
    echo "1. List available models"
    echo "2. Add new model"
    echo "3. Remove model"
    echo "4. Set default model"
    echo "5. Test model"
    echo "6. Model information"
    echo "7. Popular models list"
    echo "8. Exit"
    echo ""
}

list_models() {
    echo -e "${BLUE}📋 Currently available models:${NC}"
    docker exec backend-ollama ollama list
}

add_model() {
    echo -e "${YELLOW}📥 Add New Model${NC}"
    echo "Enter model name (e.g., mistral:7b-instruct-v0.3-q4_k_m):"
    read -r model_name
    
    if [[ -n "$model_name" ]]; then
        echo "Downloading $model_name..."
        docker exec backend-ollama ollama pull "$model_name"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Model $model_name downloaded successfully${NC}"
        else
            echo -e "${RED}❌ Failed to download model $model_name${NC}"
        fi
    fi
}

remove_model() {
    echo -e "${YELLOW}🗑️  Remove Model${NC}"
    echo "Available models:"
    docker exec backend-ollama ollama list
    echo ""
    echo "Enter model name to remove:"
    read -r model_name
    
    if [[ -n "$model_name" ]]; then
        echo "Removing $model_name..."
        docker exec backend-ollama ollama rm "$model_name"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Model $model_name removed successfully${NC}"
        else
            echo -e "${RED}❌ Failed to remove model $model_name${NC}"
        fi
    fi
}

set_default_model() {
    echo -e "${YELLOW}⚙️  Set Default Model${NC}"
    echo "Available models:"
    docker exec backend-ollama ollama list
    echo ""
    echo "Enter model name to set as default:"
    read -r model_name
    
    if [[ -n "$model_name" ]]; then
        # Update docker-compose.yml
        if grep -q "DEFAULT_MODEL=" docker-compose.yml; then
            sed -i "s/DEFAULT_MODEL=.*/DEFAULT_MODEL=$model_name/" docker-compose.yml
            echo -e "${GREEN}✅ Updated docker-compose.yml with default model: $model_name${NC}"
            echo -e "${YELLOW}⚠️  Restart the backend container to apply changes:${NC}"
            echo "   docker-compose restart llm_backend"
        else
            echo -e "${RED}❌ Could not find DEFAULT_MODEL in docker-compose.yml${NC}"
        fi
    fi
}

test_model() {
    echo -e "${YELLOW}🧪 Test Model${NC}"
    echo "Available models:"
    docker exec backend-ollama ollama list
    echo ""
    echo "Enter model name to test:"
    read -r model_name
    
    if [[ -n "$model_name" ]]; then
        ./test-model.sh "$model_name"
    fi
}

model_info() {
    echo -e "${YELLOW}ℹ️  Model Information${NC}"
    echo "Available models:"
    docker exec backend-ollama ollama list
    echo ""
    echo "Enter model name for detailed info:"
    read -r model_name
    
    if [[ -n "$model_name" ]]; then
        docker exec backend-ollama ollama show "$model_name"
    fi
}

popular_models() {
    echo -e "${BLUE}🌟 Popular Models${NC}"
    echo "=================="
    echo ""
    echo "🔤 Recommended 4B Models (Optimized for this system):"
    echo "  • llama3.2:4b (recommended) - Fast, efficient, well-balanced"
    echo "  • qwen3:4b - Strong multilingual support and reasoning"
    echo "  • mistral:4b - Excellent instruction following"
    echo "  • phi3:4b - Microsoft's efficient model"
    echo ""
    echo "📊 Other Compatible Models:"
    echo "  • llama3.1:8b - Larger model (may be slower)"
    echo "  • llama3.2:3b - Smaller fallback option"
    echo ""
    echo "💻 Code Generation Models:"
    echo "  • codellama:7b - Code generation and completion"
    echo "  • codellama:13b - Advanced code generation"
    echo "  • deepseek-coder:6.7b - Specialized coding model"
    echo ""
    echo "🏠 Small/Local Models:"
    echo "  • llama3.2:1b - Ultra-lightweight"
    echo "  • phi3:mini - Compact but capable"
    echo "  • gemma2:2b - Google's efficient model"
    echo ""
    echo "🚀 Large/Performance Models:"
    echo "  • llama3.1:70b - Maximum performance (requires significant RAM)"
    echo "  • mixtral:8x7b - Mixture of experts model"
    echo ""
    echo "To add any model: ./add-model.sh <model_name>"
}

# Main menu loop
while true; do
    show_menu
    echo -n "Choose an option (1-8): "
    read -r choice
    
    case $choice in
        1) list_models ;;
        2) add_model ;;
        3) remove_model ;;
        4) set_default_model ;;
        5) test_model ;;
        6) model_info ;;
        7) popular_models ;;
        8) echo "Goodbye!"; exit 0 ;;
        *) echo -e "${RED}❌ Invalid option. Please choose 1-8.${NC}" ;;
    esac
    
    echo ""
    echo "Press Enter to continue..."
    read -r
    clear
done
