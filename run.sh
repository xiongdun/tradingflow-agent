#!/bin/bash
# run.sh — TradingFlow Agent Linux/macOS 启动脚本
# 使用方式: chmod +x run.sh && ./run.sh

set -e

echo ""
echo " ╔══════════════════════════════════════════════════╗"
echo " ║      🚀 TradingFlow Agent 启动中...                 ║"
echo " ╚══════════════════════════════════════════════════╝"
echo ""

# ── 检测 .env 配置 ──
if [ ! -f ".env" ]; then
    echo " ❌ 未找到 .env 配置文件"
    echo " 👉 请先运行 ./setup.sh 完成安装"
    exit 1
fi

# ── 检查 API Key ──
if grep -q "LLM_API_KEY=your-api-key\|LLM_API_KEY=请填入你的密钥\|LLM_API_KEY=$" .env; then
    echo " ⚠️  检测到 API 密钥尚未配置！"
    echo ""
    echo " ┌─────────────────────────────────────────┐"
    echo " │  快速配置指南                              │"
    echo " │                                          │"
    echo " │  1. 注册 https://platform.deepseek.com   │"
    echo " │  2. 创建 API Key，复制                    │"
    echo " │  3. 编辑 .env 文件                        │"
    echo " │  4. 修改 LLM_API_KEY= 后面为你的 Key       │"
    echo " │  5. 保存后重新 ./run.sh                   │"
    echo " └─────────────────────────────────────────┘"
    echo ""
    exit 1
fi

echo " 🐍 启动后端服务（新终端窗口）..."
source .venv/bin/activate
python -m backend.cli serve &
BACKEND_PID=$!

echo " 🌐 启动前端界面（新终端窗口）..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo " ╔══════════════════════════════════════════════════╗"
echo " ║  ✅ 服务已启动！                                    ║"
echo " ║  📍 浏览器打开: http://localhost:3000              ║"
echo " ╚══════════════════════════════════════════════════╝"
echo ""
echo " 💡 第一次使用？输入股票代码（如 600519）即可开始分析"
echo " 💡 按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait