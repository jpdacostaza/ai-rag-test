#!/bin/bash
# Orange Pi 5 Plus Performance Monitor
# Monitor system resources and Ollama performance

echo "🍊 Orange Pi 5 Plus Performance Monitor"
echo "========================================"

# System Information
echo "📊 System Resources:"
echo "CPU: $(nproc) cores ($(cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2))"
echo "Memory: $(free -h | grep '^Mem:' | awk '{print $2}') total, $(free -h | grep '^Mem:' | awk '{print $3}') used"
echo "Load: $(uptime | awk '{print $10, $11, $12}')"

echo ""
echo "🐋 Docker Container Status:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo ""
echo "🤖 Ollama Performance:"
echo "Models loaded:"
docker exec backend-ollama ollama list 2>/dev/null || echo "Ollama not responding"

echo ""
echo "🔥 CPU Temperature (if available):"
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    temp=$(cat /sys/class/thermal/thermal_zone0/temp)
    echo "CPU: $((temp/1000))°C"
else
    echo "Temperature monitoring not available"
fi

echo ""
echo "💾 Memory Breakdown:"
echo "Available: $(free -h | grep '^Mem:' | awk '{print $7}')"
echo "Cache: $(free -h | grep '^Mem:' | awk '{print $6}')"

echo ""
echo "⚡ Performance Tips:"
echo "1. Keep CPU temp under 85°C for sustained performance"
echo "2. Monitor memory usage - should stay under 28GB"
echo "3. Use 'docker logs backend-ollama -f' to monitor AI inference"
echo "4. Check network with 'docker exec backend-ollama curl -s http://localhost:11434/api/tags'"
