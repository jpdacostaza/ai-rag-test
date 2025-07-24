#!/bin/bash

# Orange Pi 5 Plus System Information Script
# Gather system information for troubleshooting LLM performance issues

echo "🔍 Orange Pi 5 Plus System Information Report"
echo "============================================="
echo "Generated: $(date)"
echo ""

# Hardware Information
echo "🖥️  Hardware Information:"
echo "------------------------"
echo "Architecture: $(uname -m)"
echo "Kernel: $(uname -r)"
echo "CPU Model: $(cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2 | xargs)"
echo "CPU Cores: $(nproc)"
echo "CPU Thread: $(cat /proc/cpuinfo | grep processor | wc -l)"

# Memory Information
echo ""
echo "💾 Memory Information:"
echo "---------------------"
free -h
echo ""
echo "Swap Information:"
swapon --show 2>/dev/null || echo "No swap configured"

# CPU Status
echo ""
echo "⚡ CPU Status:"
echo "-------------"
for i in $(seq 0 $(($(nproc)-1))); do
    if [ -f "/sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor" ]; then
        gov=$(cat /sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor)
        if [ -f "/sys/devices/system/cpu/cpu$i/cpufreq/scaling_cur_freq" ]; then
            freq=$(cat /sys/devices/system/cpu/cpu$i/cpufreq/scaling_cur_freq)
            echo "CPU$i: $gov governor, $(( $freq / 1000 ))MHz"
        else
            echo "CPU$i: $gov governor, frequency N/A"
        fi
    fi
done

# Temperature
echo ""
echo "🌡️  Temperature Status:"
echo "----------------------"
if [ -d "/sys/class/thermal/" ]; then
    for zone in /sys/class/thermal/thermal_zone*; do
        if [ -f "$zone/temp" ]; then
            temp=$(cat "$zone/temp")
            type=$(cat "$zone/type" 2>/dev/null || echo "unknown")
            echo "$(basename $zone) ($type): $(( $temp / 1000 ))°C"
        fi
    done
else
    echo "Temperature monitoring not available"
fi

# Storage Information
echo ""
echo "💽 Storage Information:"
echo "----------------------"
df -h | grep -E '^/dev|^Filesystem'

# Docker Information
echo ""
echo "🐳 Docker Information:"
echo "---------------------"
if command -v docker >/dev/null 2>&1; then
    echo "Docker Version: $(docker --version)"
    echo "Docker Status: $(systemctl is-active docker 2>/dev/null || echo 'unknown')"
    
    if docker info >/dev/null 2>&1; then
        echo ""
        echo "Running Containers:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}" | head -10
        
        echo ""
        echo "Container Resource Usage:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>/dev/null | head -10
    else
        echo "Docker daemon not accessible"
    fi
else
    echo "Docker not installed"
fi

# Process Information
echo ""
echo "🔝 Top Processes by CPU:"
echo "-----------------------"
ps aux --sort=-%cpu | head -6 | awk '{printf "%-12s %5s%% %5s%% %s\n", $11, $3, $4, $2}'

echo ""
echo "🔝 Top Processes by Memory:"
echo "--------------------------"
ps aux --sort=-%mem | head -6 | awk '{printf "%-12s %5s%% %5s%% %s\n", $11, $4, $3, $2}'

# Network Information
echo ""
echo "🌐 Network Information:"
echo "----------------------"
ip addr show | grep -E "inet |UP|DOWN" | head -10

# System Load
echo ""
echo "📊 System Load:"
echo "--------------"
uptime
echo ""
echo "Load Average Details:"
cat /proc/loadavg

# Memory Details
echo ""
echo "📈 Memory Details:"
echo "-----------------"
echo "MemInfo highlights:"
grep -E "MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal|SwapFree" /proc/meminfo

# Disk I/O
echo ""
echo "💿 Recent Disk I/O:"
echo "------------------"
if command -v iostat >/dev/null 2>&1; then
    iostat -d 1 1 2>/dev/null | tail -10
else
    echo "iostat not available (install sysstat package)"
fi

echo ""
echo "✅ System Information Report Complete"
echo "===================================="
echo ""
echo "📋 Quick Analysis:"
echo "-----------------"

# Quick analysis
total_mem=$(free -m | grep Mem | awk '{print $2}')
free_mem=$(free -m | grep Mem | awk '{print $7}')
cpu_count=$(nproc)

echo "• Total Memory: ${total_mem}MB"
echo "• Available Memory: ${free_mem}MB"
echo "• Memory Usage: $(( (total_mem - free_mem) * 100 / total_mem ))%"
echo "• CPU Cores: $cpu_count"

if [ $free_mem -lt 2048 ]; then
    echo "⚠️  Warning: Low available memory (< 2GB)"
fi

if [ $cpu_count -lt 8 ]; then
    echo "⚠️  Warning: Expected 8 CPU cores for Orange Pi 5 Plus"
fi

temp_file="/sys/class/thermal/thermal_zone0/temp"
if [ -f "$temp_file" ]; then
    temp=$(cat "$temp_file")
    temp_c=$(( temp / 1000 ))
    if [ $temp_c -gt 70 ]; then
        echo "🌡️  Warning: High CPU temperature (${temp_c}°C)"
    else
        echo "🌡️  CPU temperature: ${temp_c}°C (normal)"
    fi
fi

echo ""
echo "💡 Tips for better performance:"
echo "  • Ensure CPU governor is set to 'performance'"
echo "  • Keep system temperature below 70°C"
echo "  • Maintain at least 2GB free memory"
echo "  • Use CPU affinity for Docker containers"
