#!/bin/bash
# setup.sh — TradingFlow Agent Linux/macOS 一键安装
# 使用方式: chmod +x setup.sh && ./setup.sh

set -e

echo ""
echo " ╔══════════════════════════════════════════════════╗"
echo " ║      🤖 TradingFlow Agent — 安装向导              ║"
echo " ╚══════════════════════════════════════════════════╝"
echo ""

# ── 检测 Python ──
echo " [1/4] 🐍 检测 Python..."
if ! command -v python3 &> /dev/null; then
    echo " ❌ 未检测到 Python 3！请先安装 Python 3.10+"
    echo " 📥 Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo " 📥 macOS: brew install python3"
    exit 1
fi
python3 --version
echo " ✅ Python 已就绪"
echo ""

# ── 创建虚拟环境 ──
echo " [2/4] 📦 创建虚拟环境..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo " ✅ 虚拟环境已创建"
else
    echo " ℹ️  虚拟环境已存在，跳过创建"
fi
echo ""

# ── 安装依赖 ──
echo " [3/4] 📥 安装项目依赖..."
source .venv/bin/activate
pip install -e . -q
echo " ✅ 依赖安装完成"
echo ""

# ── 检查配置文件 ──
echo " [4/4] ⚙️  检查配置..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo " ⚠️  已创建默认配置文件 .env"
    echo ""
    echo " ┌──────────────────────────────────────────────────┐"
    echo " │  ⚡ 还需要一步：配置你的 AI 模型密钥                │"
    echo " │                                                    │"
    echo " │  1️⃣  注册 DeepSeek（推荐，国内可用）                   │"
    echo " │      https://platform.deepseek.com                  │"
    echo " │  2️⃣  创建 API Key，复制密钥                          │"
    echo " │  3️⃣  编辑项目目录下的 .env 文件                        │"
    echo " │      把 LLM_API_KEY= 后面改成你的密钥                 │"
    echo " │  4️⃣  保存，然后运行 ./run.sh 启动！                   │"
    echo " └──────────────────────────────────────────────────┘"
else
    echo " ✅ .env 配置文件已存在"
fi

echo ""
echo " ╔══════════════════════════════════════════════════╗"
echo " ║      ✅ 安装完成！                                 ║"
echo " ║      下一步：./run.sh 启动系统                         ║"
echo " ╚══════════════════════════════════════════════════╝"
echo ""