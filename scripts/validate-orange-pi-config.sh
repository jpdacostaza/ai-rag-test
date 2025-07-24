#!/bin/bash

# Orange Pi 5 Plus Configuration Validation Script
# Validates that all ARM64 optimizations are properly configured

echo "🔍 Orange Pi 5 Plus Zero-Config Validation"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if value exists in file
check_config() {
    local file="$1"
    local key="$2"
    local expected="$3"
    local description="$4"
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ $file not found${NC}"
        return 1
    fi
    
    if grep -q "$key.*$expected" "$file"; then
        echo -e "${GREEN}✅ $description${NC}"
        return 0
    else
        echo -e "${RED}❌ $description - Missing or incorrect${NC}"
        return 1
    fi
}

# Function to check environment variable in .env
check_env_var() {
    local key="$1"
    local expected="$2"
    local description="$3"
    
    check_config ".env" "$key" "$expected" "$description"
}

# Function to check docker-compose configuration
check_compose_config() {
    local key="$1"
    local expected="$2"
    local description="$3"
    
    check_config "docker-compose.yml" "$key" "$expected" "$description"
}

echo ""
echo "${BLUE}📋 Checking Configuration Files...${NC}"
echo "-----------------------------------"

# Check if main config files exist
config_files=("docker-compose.yml" ".env" "docs/ORANGE_PI_5_PLUS_OPTIMIZATION.md")
all_files_exist=true

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file exists${NC}"
    else
        echo -e "${RED}❌ $file missing${NC}"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    echo -e "${RED}❌ Missing configuration files. Please check your setup.${NC}"
    exit 1
fi

echo ""
echo "${BLUE}🔧 Validating ARM64 Environment Variables...${NC}"
echo "----------------------------------------------"

# Check ARM64 optimization settings in .env
check_env_var "ARM64_OPTIMIZED" "true" "ARM64 optimization enabled"
check_env_var "OLLAMA_NUM_PARALLEL" "1" "Single parallel request for stability"
check_env_var "OLLAMA_NUM_THREADS" "7" "7 CPU threads configured"
check_env_var "OLLAMA_NUMA" "false" "NUMA disabled for single-socket"
check_env_var "OLLAMA_MAX_VRAM" "6144" "6GB VRAM allocation"
check_env_var "OLLAMA_FLASH_ATTENTION" "false" "Flash attention disabled for stability"
check_env_var "OLLAMA_CONCURRENT_REQUESTS" "1" "Single concurrent request"
check_env_var "OLLAMA_KEEP_ALIVE" "5m" "Short keep-alive configured"
check_env_var "OLLAMA_REQUEST_TIMEOUT" "600" "Extended request timeout"
check_env_var "OLLAMA_LOAD_TIMEOUT" "900" "Extended load timeout"

echo ""
echo "${BLUE}🐳 Validating Docker Compose Configuration...${NC}"
echo "----------------------------------------------"

# Check Docker Compose settings
check_compose_config "cpuset.*1-7" "1-7" "Ollama CPU affinity (cores 1-7)"
check_compose_config "mem_limit.*6g" "6g" "Ollama memory limit (6GB)"
check_compose_config "memswap_limit.*6g" "6g" "Swap disabled (memswap = mem_limit)"
check_compose_config "mem_swappiness.*0" "0" "Memory swappiness disabled"
check_compose_config "mem_reservation.*4g" "4g" "4GB memory reservation"
check_compose_config "cpu_shares.*2048" "2048" "High CPU priority for Ollama"

# Check Redis configuration
check_compose_config "cpuset.*0" "0" "Redis on system core (core 0)"
check_compose_config "mem_limit.*512m" "512m" "Redis memory limit"

echo ""
echo "${BLUE}📊 Configuration Summary...${NC}"
echo "-----------------------------"

# Count configurations
total_checks=0
passed_checks=0

# Re-run checks and count
configs=(
    "ARM64_OPTIMIZED:true:ARM64 optimization"
    "OLLAMA_NUM_THREADS:7:7 CPU threads"
    "OLLAMA_MAX_VRAM:6144:6GB VRAM"
    "cpuset.*1-7:1-7:CPU affinity"
    "mem_limit.*6g:6g:Memory limit"
    "memswap_limit.*6g:6g:Swap disabled"
)

for config in "${configs[@]}"; do
    IFS=':' read -r key expected desc <<< "$config"
    total_checks=$((total_checks + 1))
    
    if [[ "$key" == *"cpuset"* ]] || [[ "$key" == *"mem_limit"* ]] || [[ "$key" == *"memswap"* ]]; then
        if grep -q "$key" "docker-compose.yml" 2>/dev/null; then
            passed_checks=$((passed_checks + 1))
        fi
    else
        if grep -q "$key.*$expected" ".env" 2>/dev/null; then
            passed_checks=$((passed_checks + 1))
        fi
    fi
done

echo ""
echo "${BLUE}📈 Validation Results:${NC}"
echo "Passed: $passed_checks/$total_checks configurations"

if [ $passed_checks -eq $total_checks ]; then
    echo -e "${GREEN}🎉 All ARM64 optimizations are properly configured!${NC}"
    echo -e "${GREEN}✅ Your Orange Pi 5 Plus is ready for optimal LLM performance.${NC}"
    
    echo ""
    echo "${BLUE}🚀 Next Steps:${NC}"
    echo "1. Start services: ${YELLOW}docker-compose up -d${NC}"
    echo "2. Monitor performance: ${YELLOW}./scripts/monitor-orange-pi.sh${NC}"
    echo "3. Apply system optimizations: ${YELLOW}sudo ./scripts/optimize-orange-pi.sh${NC}"
    
    exit 0
else
    echo -e "${YELLOW}⚠️  Some configurations may need attention.${NC}"
    echo -e "${YELLOW}   Check the failing items above and update your configuration.${NC}"
    
    echo ""
    echo "${BLUE}🔧 Quick Fix Commands:${NC}"
    echo "- Re-run setup: ${YELLOW}git pull && docker-compose up -d${NC}"
    echo "- Check config: ${YELLOW}cat .env | grep ARM64${NC}"
    echo "- Validate Docker: ${YELLOW}docker-compose config${NC}"
    
    exit 1
fi
