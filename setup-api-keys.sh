#!/bin/bash
# OpenWebUI API Key Management Setup Script
# Provides interactive setup and management of OpenWebUI API keys

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emojis
CHECK="✅"
WARNING="⚠️"
ERROR="❌"
INFO="ℹ️"
KEY="🔑"
GEAR="⚙️"
ROCKET="🚀"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/openwebui_api_keys.json"
EXAMPLE_FILE="$SCRIPT_DIR/openwebui_api_keys.example.json"

print_header() {
    echo -e "${BLUE}${KEY} OpenWebUI API Key Management Setup${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_status() {
    local message="$1"
    local type="${2:-info}"
    
    case $type in
        "success") echo -e "   ${CHECK} ${GREEN}$message${NC}" ;;
        "warning") echo -e "   ${WARNING} ${YELLOW}$message${NC}" ;;
        "error") echo -e "   ${ERROR} ${RED}$message${NC}" ;;
        *) echo -e "   ${INFO} $message" ;;
    esac
}

check_dependencies() {
    echo -e "\n${GEAR} Checking dependencies..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_status "Python 3 found: $PYTHON_VERSION" "success"
    else
        print_status "Python 3 not found. Please install Python 3." "error"
        exit 1
    fi
    
    # Check if api_key_manager.py exists
    if [[ -f "$SCRIPT_DIR/api_key_manager.py" ]]; then
        print_status "API Key Manager found" "success"
    else
        print_status "API Key Manager not found. Please ensure api_key_manager.py exists." "error"
        exit 1
    fi
    
    # Check Python dependencies
    python3 -c "import requests, json, pathlib" 2>/dev/null && \
        print_status "Python dependencies available" "success" || \
        print_status "Missing Python dependencies. Install with: pip install requests" "warning"
}

check_config_status() {
    echo -e "\n1. Checking configuration status..."
    
    if [[ -f "$CONFIG_FILE" ]]; then
        print_status "Configuration file exists: $(basename "$CONFIG_FILE")" "success"
        
        # Try to read and parse basic info
        if python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE', 'r') as f:
        data = json.load(f)
    default_key = data.get('default', {}).get('api_key', '')
    users = data.get('users', {})
    envs = data.get('environments', {})
    
    if default_key and default_key != 'YOUR_DEFAULT_API_KEY_HERE':
        print('   ${CHECK} Default key configured: ...${default_key[-8:]}')
    else:
        print('   ${WARNING} No default key configured')
    
    if users:
        user_list = ', '.join(users.keys())
        print(f'   ${CHECK} {len(users)} user(s) configured: {user_list}')
    else:
        print('   ${WARNING} No user keys configured')
        
    if envs:
        env_list = ', '.join(envs.keys())
        print(f'   ${CHECK} {len(envs)} environment(s) configured: {env_list}')
    else:
        print('   ${WARNING} No environment keys configured')
        
except Exception as e:
    print(f'   ${ERROR} Error reading config: {e}')
" 2>/dev/null
    else
        print_status "No configuration file found" "warning"
        if [[ -f "$EXAMPLE_FILE" ]]; then
            print_status "Example file available: $(basename "$EXAMPLE_FILE")" "info"
        fi
    fi
}

check_environment_vars() {
    echo -e "\n2. Checking environment variables..."
    
    if [[ -n "$OPENWEBUI_API_KEY" ]]; then
        local key_preview="${OPENWEBUI_API_KEY: -8}"
        print_status "OPENWEBUI_API_KEY set: ...$key_preview" "success"
        print_status "OPENWEBUI_BASE_URL: ${OPENWEBUI_BASE_URL:-http://localhost:3000}" "success"
    else
        print_status "OPENWEBUI_API_KEY not set" "warning"
    fi
}

check_updated_tools() {
    echo -e "\n3. Checking updated diagnostic tools..."
    
    local tools=(
        "debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py"
        "debug/archived/demo-test/debug-tools/test_memory_cross_chat.py"
    )
    
    for tool in "${tools[@]}"; do
        if [[ -f "$SCRIPT_DIR/$tool" ]]; then
            # Check if tool imports API key manager
            if grep -q "from api_key_manager import" "$SCRIPT_DIR/$tool" 2>/dev/null; then
                print_status "$(basename "$tool") - Updated with API key support" "success"
            else
                print_status "$(basename "$tool") - Found but not updated" "warning"
            fi
        else
            print_status "$(basename "$tool") - Not found" "warning"
        fi
    done
}

show_setup_options() {
    echo -e "\n4. Setup options:"
    echo -e "   ${INFO} Interactive Python setup:"
    echo -e "      ${CYAN}python3 api_key_manager.py${NC}"
    
    echo -e "\n   ${INFO} Environment variables (temporary):"
    echo -e "      ${CYAN}export OPENWEBUI_API_KEY='your-key-here'${NC}"
    echo -e "      ${CYAN}export OPENWEBUI_BASE_URL='http://localhost:3000'${NC}"
    
    echo -e "\n   ${INFO} Create config from example:"
    echo -e "      ${CYAN}cp openwebui_api_keys.example.json openwebui_api_keys.json${NC}"
    echo -e "      ${CYAN}# Then edit openwebui_api_keys.json with your keys${NC}"
}

show_usage_examples() {
    echo -e "\n5. Usage examples:"
    echo -e "   ${INFO} Run diagnostic with auto-detected keys:"
    echo -e "      ${CYAN}python3 debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py${NC}"
    
    echo -e "\n   ${INFO} Run with specific user:"
    echo -e "      ${CYAN}python3 debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py --user=john${NC}"
    
    echo -e "\n   ${INFO} Run with specific environment:"
    echo -e "      ${CYAN}python3 debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py --env=production${NC}"
    
    echo -e "\n   ${INFO} Test memory across chat sessions:"
    echo -e "      ${CYAN}python3 debug/archived/demo-test/debug-tools/test_memory_cross_chat.py${NC}"
}

interactive_setup() {
    echo -e "\n${ROCKET} Starting interactive setup..."
    echo -e "This will run the Python interactive setup tool."
    echo ""
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "\n${INFO} Launching Python setup tool..."
        python3 "$SCRIPT_DIR/api_key_manager.py"
    else
        echo -e "${INFO} Setup cancelled."
    fi
}

quick_env_setup() {
    echo -e "\n${ROCKET} Quick environment variable setup..."
    echo -e "This will help you set temporary environment variables."
    echo ""
    
    read -p "Enter your OpenWebUI API key: " -r api_key
    if [[ -z "$api_key" ]]; then
        print_status "No API key provided. Skipping." "warning"
        return
    fi
    
    read -p "Enter base URL [http://localhost:3000]: " -r base_url
    base_url=${base_url:-http://localhost:3000}
    
    echo -e "\n${INFO} Add these to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo -e "${CYAN}export OPENWEBUI_API_KEY='$api_key'${NC}"
    echo -e "${CYAN}export OPENWEBUI_BASE_URL='$base_url'${NC}"
    
    echo -e "\n${INFO} Or run these commands for this session:"
    export OPENWEBUI_API_KEY="$api_key"
    export OPENWEBUI_BASE_URL="$base_url"
    
    print_status "Environment variables set for this session" "success"
}

test_setup() {
    echo -e "\n${ROCKET} Testing current setup..."
    
    if [[ -f "$SCRIPT_DIR/debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py" ]]; then
        echo -e "${INFO} Running diagnostic tool..."
        python3 "$SCRIPT_DIR/debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py" || \
            print_status "Diagnostic tool failed. Check your API keys and OpenWebUI connection." "error"
    else
        print_status "Diagnostic tool not found." "error"
    fi
}

show_documentation() {
    echo -e "\n${INFO} Documentation available:"
    
    if [[ -f "$SCRIPT_DIR/API_KEY_MANAGEMENT.md" ]]; then
        print_status "Complete documentation: API_KEY_MANAGEMENT.md" "success"
        echo -e "      ${CYAN}cat API_KEY_MANAGEMENT.md${NC}"
    fi
    
    if [[ -f "$SCRIPT_DIR/openwebui_api_keys.example.json" ]]; then
        print_status "Example configuration: openwebui_api_keys.example.json" "success"
        echo -e "      ${CYAN}cat openwebui_api_keys.example.json${NC}"
    fi
}

main_menu() {
    while true; do
        echo -e "\n${GEAR} Setup Menu:"
        echo "1. Run full status check"
        echo "2. Interactive Python setup"
        echo "3. Quick environment variable setup"
        echo "4. Test current setup"
        echo "5. Show documentation"
        echo "6. Exit"
        echo ""
        read -p "Select option (1-6): " choice
        
        case $choice in
            1)
                check_config_status
                check_environment_vars
                check_updated_tools
                show_setup_options
                show_usage_examples
                ;;
            2)
                interactive_setup
                ;;
            3)
                quick_env_setup
                ;;
            4)
                test_setup
                ;;
            5)
                show_documentation
                ;;
            6)
                echo -e "${INFO} Goodbye!"
                exit 0
                ;;
            *)
                print_status "Invalid option. Please select 1-6." "error"
                ;;
        esac
    done
}

# Main execution
main() {
    print_header
    
    # Check if running with specific command line options
    case "${1:-}" in
        "--status"|"-s")
            check_dependencies
            check_config_status
            check_environment_vars
            check_updated_tools
            ;;
        "--setup"|"-i")
            check_dependencies
            interactive_setup
            ;;
        "--env"|"-e")
            quick_env_setup
            ;;
        "--test"|"-t")
            test_setup
            ;;
        "--help"|"-h")
            echo "Usage: $0 [option]"
            echo ""
            echo "Options:"
            echo "  -s, --status    Show configuration status"
            echo "  -i, --setup     Run interactive setup"
            echo "  -e, --env       Quick environment variable setup"
            echo "  -t, --test      Test current setup"
            echo "  -h, --help      Show this help"
            echo ""
            echo "Run without options for interactive menu."
            ;;
        "")
            check_dependencies
            check_config_status
            check_environment_vars
            show_setup_options
            show_usage_examples
            echo ""
            read -p "Would you like to open the interactive menu? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                main_menu
            fi
            ;;
        *)
            print_status "Unknown option: $1" "error"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
