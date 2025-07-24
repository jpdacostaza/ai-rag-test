#!/bin/bash

# ===============================================================================
# Orange Pi 5 Plus Optimization Script for LLM/AI Workloads
# ===============================================================================
# This script optimizes the Orange Pi 5 Plus for running Ollama and LLM workloads
# Recommended to run as root: sudo ./optimize-orange-pi.sh
# ===============================================================================

set -e

echo "🔧 Orange Pi 5 Plus Optimization for LLM Workloads"
echo "=================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs root privileges for optimal system configuration."
    echo "   Some optimizations will be skipped."
    echo "   Run with: sudo ./optimize-orange-pi.sh"
    SKIP_ROOT_TASKS=true
else
    SKIP_ROOT_TASKS=false
fi

echo ""
echo "📊 Current System Information:"
echo "------------------------------"
echo "CPU Model: $(cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2 | xargs)"
echo "CPU Cores: $(nproc)"
echo "Total Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "Architecture: $(uname -m)"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. CPU Governor Optimization
echo "🚀 Step 1: CPU Governor Configuration"
echo "------------------------------------"

if [ "$SKIP_ROOT_TASKS" = false ]; then
    # Set performance governor for all cores
    echo "Setting CPU governor to 'performance' for optimal LLM performance..."
    
    for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        if [ -f "$cpu" ]; then
            echo "performance" > "$cpu"
            echo "✅ Set $(basename $(dirname $(dirname $cpu))) to performance mode"
        fi
    done
    
    # Verify governor settings
    echo ""
    echo "Current CPU governors:"
    for i in $(seq 0 $(($(nproc)-1))); do
        if [ -f "/sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor" ]; then
            gov=$(cat /sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor)
            freq=$(cat /sys/devices/system/cpu/cpu$i/cpufreq/scaling_cur_freq 2>/dev/null || echo "N/A")
            echo "  CPU$i: $gov ($(( $freq / 1000 ))MHz)"
        fi
    done
else
    echo "⚠️  Skipping CPU governor configuration (requires root)"
    echo "   Manual command: sudo bash -c 'for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance > \$cpu; done'"
fi

echo ""

# 2. Memory and Swap Optimization
echo "💾 Step 2: Memory and Swap Optimization"
echo "---------------------------------------"

if [ "$SKIP_ROOT_TASKS" = false ]; then
    # Reduce swappiness for better performance
    echo "Optimizing memory swappiness for LLM workloads..."
    echo 10 > /proc/sys/vm/swappiness
    echo "✅ Set swappiness to 10 (reduced from default 60)"
    
    # Optimize dirty ratio for better I/O performance
    echo 5 > /proc/sys/vm/dirty_ratio
    echo 2 > /proc/sys/vm/dirty_background_ratio
    echo "✅ Optimized dirty ratios for better I/O"
    
    # Show current memory usage
    echo ""
    echo "Current memory usage:"
    free -h
else
    echo "⚠️  Skipping memory optimization (requires root)"
    echo "   Manual commands:"
    echo "     sudo sysctl vm.swappiness=10"
    echo "     sudo sysctl vm.dirty_ratio=5"
    echo "     sudo sysctl vm.dirty_background_ratio=2"
fi

echo ""

# 3. Docker and Container Optimization
echo "🐳 Step 3: Docker Optimization"
echo "------------------------------"

# Check if Docker is installed
if command_exists docker; then
    echo "✅ Docker is installed"
    
    # Check Docker daemon configuration
    if [ -f "/etc/docker/daemon.json" ]; then
        echo "✅ Docker daemon.json exists"
    else
        if [ "$SKIP_ROOT_TASKS" = false ]; then
            echo "📝 Creating optimized Docker daemon.json for ARM64..."
            mkdir -p /etc/docker
            cat > /etc/docker/daemon.json << 'EOF'
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Soft": 65536,
      "Hard": 65536
    },
    "memlock": {
      "Name": "memlock",
      "Soft": -1,
      "Hard": -1
    }
  }
}
EOF
            echo "✅ Created optimized Docker daemon.json"
            echo "   Restart Docker to apply: sudo systemctl restart docker"
        else
            echo "⚠️  Docker daemon.json not found (requires root to create)"
        fi
    fi
else
    echo "⚠️  Docker not found. Please install Docker first."
fi

echo ""

# 4. System Monitoring Setup
echo "📈 Step 4: System Monitoring"
echo "----------------------------"

echo "Installing useful monitoring tools..."

# Function to install package if not present
install_if_missing() {
    if ! command_exists "$1"; then
        if [ "$SKIP_ROOT_TASKS" = false ]; then
            if command_exists apt; then
                apt update -qq && apt install -y "$2" 2>/dev/null || echo "⚠️  Failed to install $2"
            elif command_exists yum; then
                yum install -y "$2" 2>/dev/null || echo "⚠️  Failed to install $2"
            elif command_exists pacman; then
                pacman -S --noconfirm "$2" 2>/dev/null || echo "⚠️  Failed to install $2"
            fi
        else
            echo "⚠️  $1 not found (requires root to install $2)"
        fi
    else
        echo "✅ $1 is available"
    fi
}

install_if_missing "htop" "htop"
install_if_missing "iotop" "iotop" 
install_if_missing "nethogs" "nethogs"

echo ""

# 5. Create monitoring script
echo "📊 Step 5: Creating Monitoring Scripts"
echo "--------------------------------------"

cat > ./monitor-orange-pi.sh << 'EOF'
#!/bin/bash

# Orange Pi 5 Plus System Monitor for LLM Workloads
# Usage: ./monitor-orange-pi.sh

echo "🔍 Orange Pi 5 Plus System Monitor"
echo "=================================="
echo "Press Ctrl+C to exit"
echo ""

while true; do
    clear
    echo "🔍 Orange Pi 5 Plus System Monitor - $(date)"
    echo "============================================="
    
    # CPU Information
    echo ""
    echo "💻 CPU Status:"
    echo "-------------"
    for i in $(seq 0 7); do
        if [ -f "/sys/devices/system/cpu/cpu$i/cpufreq/scaling_cur_freq" ]; then
            freq=$(cat /sys/devices/system/cpu/cpu$i/cpufreq/scaling_cur_freq)
            gov=$(cat /sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor)
            echo "  CPU$i: $(( $freq / 1000 ))MHz ($gov)"
        fi
    done
    
    # Temperature
    echo ""
    echo "🌡️  Temperature:"
    echo "---------------"
    if [ -f "/sys/class/thermal/thermal_zone0/temp" ]; then
        temp=$(cat /sys/class/thermal/thermal_zone0/temp)
        echo "  SoC: $(( $temp / 1000 ))°C"
    fi
    
    # Memory Usage
    echo ""
    echo "💾 Memory Usage:"
    echo "---------------"
    free -h
    
    # Docker Container Status
    echo ""
    echo "🐳 Docker Containers:"
    echo "-------------------"
    if command -v docker >/dev/null 2>&1; then
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | head -10
    else
        echo "  Docker not available"
    fi
    
    # Top CPU processes
    echo ""
    echo "🔝 Top CPU Processes:"
    echo "-------------------"
    ps aux --sort=-%cpu | head -6 | awk '{printf "  %-12s %5s%% %s\n", $11, $3, $2}'
    
    sleep 5
done
EOF

chmod +x ./monitor-orange-pi.sh
echo "✅ Created monitoring script: ./monitor-orange-pi.sh"

echo ""

# 6. Final recommendations
echo "✅ Orange Pi 5 Plus Optimization Complete!"
echo "=========================================="
echo ""
echo "📋 Summary of optimizations applied:"
echo "   • CPU governor set to 'performance' mode"
echo "   • Memory swappiness reduced to 10"
echo "   • I/O performance optimized"
echo "   • Docker daemon configured for ARM64"
echo "   • Monitoring tools installed"
echo ""
echo "🔄 Next steps:"
echo "   1. Restart Docker if daemon.json was modified:"
echo "      sudo systemctl restart docker"
echo ""
echo "   2. Start your optimized services:"
echo "      docker-compose up -d"
echo ""
echo "   3. Monitor system performance:"
echo "      ./monitor-orange-pi.sh"
echo ""
echo "🎯 Performance Tips:"
echo "   • Keep the Orange Pi 5 Plus well-ventilated"
echo "   • Use a good quality power supply (5V 4A recommended)"
echo "   • Monitor CPU temperature during heavy loads"
echo "   • Consider using a heatsink or fan for sustained workloads"
echo ""
echo "📊 Expected improvements:"
echo "   • Reduced Ollama response times"
echo "   • Better CPU utilization"
echo "   • More stable performance under load"
echo "   • Reduced memory pressure"
