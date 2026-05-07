#!/bin/bash
set -e
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT=8000
FRONTEND_PORT=3000

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

kill_port() {
    local port=$1 name=$2
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}⚠  端口 $port ($name) 被占用，正在关闭...${NC}"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}   ✓ 已关闭${NC}"
    fi
}

echo -e "${CYAN}╔══════════════════════════════════════════════╗"
echo    "║      🤖 TradingFlow Agent — 启动中...       ║"
echo    "╚══════════════════════════════════════════════╝${NC}"

kill_port $BACKEND_PORT "Backend"
kill_port $FRONTEND_PORT "Frontend"

echo -e "${CYAN}▶ 启动后端 (port $BACKEND_PORT)...${NC}"
cd "$PROJECT_DIR" && source .venv/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port $BACKEND_PORT > /tmp/tradingflow_backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}   ✓ Backend PID: $BACKEND_PID${NC}"

echo -ne "   等待后端就绪"
for i in $(seq 1 20); do
    curl -s http://127.0.0.1:$BACKEND_PORT/api/health > /dev/null 2>&1 && echo -e " ${GREEN}✓${NC}" && break
    echo -n "."; sleep 1
done

echo -e "${CYAN}▶ 启动前端 (port $FRONTEND_PORT)...${NC}"
cd "$PROJECT_DIR/frontend"
npm run dev > /tmp/tradingflow_frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}   ✓ Frontend PID: $FRONTEND_PID${NC}"
sleep 3

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗"
echo    "║           ✅ 启动成功！                       ║"
echo    "╠══════════════════════════════════════════════╣"
echo    "║  后端 API:   http://localhost:$BACKEND_PORT       ║"
echo    "║  API 文档:   http://localhost:$BACKEND_PORT/docs  ║"
echo    "║  前端 UI:    http://localhost:$FRONTEND_PORT       ║"
echo    "║  日志:       /tmp/tradingflow_backend|frontend.log  ║"
echo    "║  停止:       ./stop.sh                        ║"
echo    "╚══════════════════════════════════════════════╝${NC}"
