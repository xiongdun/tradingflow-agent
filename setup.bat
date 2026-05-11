# setup.bat — TradingFlow Agent Windows 一键安装
# 双击即可运行，无需任何命令行知识

@echo off
chcp 65001 >nul
title TradingFlow Agent 安装向导

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║      🤖 TradingFlow Agent — 安装向导              ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ── 检测 Python ──
echo  [1/4] 🐍 检测 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ 未检测到 Python！请先安装 Python 3.10+
    echo  📥 下载地址：https://www.python.org/downloads/
    echo     ⚠️ 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
python --version
echo  ✅ Python 已就绪
echo.

:: ── 创建虚拟环境 ──
echo  [2/4] 📦 创建虚拟环境...
if not exist ".venv" (
    python -m venv .venv
    echo  ✅ 虚拟环境已创建
) else (
    echo  ℹ️  虚拟环境已存在，跳过创建
)
echo.

:: ── 安装依赖 ──
echo  [3/4] 📥 安装项目依赖（需要 1-3 分钟，请耐心等待）...
call .venv\Scripts\activate.bat
pip install -e . >nul 2>&1
if errorlevel 1 (
    echo  ❌ 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)
echo  ✅ 依赖安装完成
echo.

:: ── 检查配置文件 ──
echo  [4/4] ⚙️  检查配置...
if not exist ".env" (
    copy .env.example .env >nul
    echo  ⚠️  已创建默认配置文件 .env
    echo.
    echo  ┌──────────────────────────────────────────────────┐
    echo  │  ⚡ 还需要一步：配置你的 AI 模型密钥                │
    echo  │                                                    │
    echo  │  1️⃣  注册 DeepSeek（推荐，国内可用）                   │
    echo  │      https://platform.deepseek.com                  │
    echo  │  2️⃣  创建 API Key，复制密钥                          │
    echo  │  3️⃣  用记事本打开项目目录下的 .env 文件                  │
    echo  │      把 LLM_API_KEY= 后面改成你的密钥                 │
    echo  │  4️⃣  保存，然后双击 run.bat 启动！                     │
    echo  └──────────────────────────────────────────────────┘
) else (
    echo  ✅ .env 配置文件已存在
)

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║      ✅ 安装完成！                                 ║
echo  ║      下一步：双击 run.bat 启动系统                     ║
echo  ╚══════════════════════════════════════════════════╝
echo.
pause