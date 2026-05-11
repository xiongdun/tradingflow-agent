@echo off
chcp 65001 >nul
title TradingFlow Agent

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║      🚀 TradingFlow Agent 启动中...                 ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ── 检测 .env 配置 ──
if not exist ".env" (
    echo  ❌ 未找到 .env 配置文件
    echo  👉 请先运行 setup.bat 完成安装
    pause
    exit /b 1
)

:: ── 检查 API Key 是否已配置 ──
findstr /c:"LLM_API_KEY=your-api-key" .env >nul 2>&1
if not errorlevel 1 (
    findstr /c:"LLM_API_KEY=请填入你的密钥" .env >nul 2>&1
    if not errorlevel 1 (
        echo  ⚠️  检测到 API 密钥尚未配置！
        echo.
        echo  ┌─────────────────────────────────────────┐
        echo  │  快速配置指南                              │
        echo  │                                          │
        echo  │  1. 注册 https://platform.deepseek.com   │
        echo  │  2. 创建 API Key，复制                    │
        echo  │  3. 右键 .env → 用记事本打开              │
        echo  │  4. 把 LLM_API_KEY= 后面改成你的 Key       │
        echo  │  5. 保存后重新双击 run.bat                │
        echo  └─────────────────────────────────────────┘
        echo.
        start https://platform.deepseek.com
        pause
        exit /b 1
    )
)

echo  🐍 启动后端服务...
call .venv\Scripts\activate.bat
start "TradingFlow Backend" cmd /c "title TradingFlow 后端 && python -m backend.cli serve"

echo  🌐 启动前端界面...
start "TradingFlow Frontend" cmd /c "title TradingFlow 前端 && cd frontend && npm run dev"

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  ✅ 服务已启动！                                    ║
echo  ║  📍 浏览器打开: http://localhost:3000              ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  💡 第一次使用？输入股票代码（如 600519）即可开始分析
echo  💡 关闭此窗口不会停止服务，关闭两个命令行窗口即可
echo  💡 按 Ctrl+C 停止

timeout /t 5
start http://localhost:3000