#!/bin/bash
GREEN='\033[0;32m'; NC='\033[0m'

stop_port() {
    local port=$1 name=$2
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -9 2>/dev/null || true
        echo -e "${GREEN}✓ $name (port $port) 已停止${NC}"
    else
        echo "  $name (port $port) 未运行"
    fi
}

echo "Stopping TradingFlow Agent..."
stop_port 8000 "Backend"
stop_port 3000 "Frontend"
echo -e "${GREEN}Done.${NC}"
