# 🤖 TradingFlow Agent

AI 多智能体股票分析系统 — 基于 LangGraph 的模块化 Agent 协作平台

## ✨ 核心特性

- **6 个专业分析师 Agent**：基本面、技术面、情绪面、新闻、宏观经济、游资
- **10 个可插拔 Skill**：每个 Agent 可动态增删技能
- **拖拽式工作流编排**：React Flow 可视化编排 Agent 执行流程
- **TradingView K线图**：Lightweight Charts 集成，Agent 分析标注叠加
- **实时 WebSocket**：分析进度实时推送
- **多市场支持**：A股、H股、美股
- **可配置 LLM**：支持 DeepSeek、OpenAI、Claude、Qwen、Ollama

## 📁 项目结构

```
tradingflow-agent/
├── backend/                     Python 后端 (FastAPI + LangGraph)
│   ├── agents/                  6 个分析师 Agent
│   ├── skills/                  10 个可插拔 Skill
│   ├── graph/                   LangGraph 工作流引擎
│   │   └── templates/           预置工作流模板
│   ├── data/                    数据层 (AKShare + yfinance)
│   ├── api/routes/              API 路由
│   ├── cli.py                   CLI 入口
│   └── main.py                  FastAPI 入口
├── frontend/                    React 前端 (React Flow + Lightweight Charts)
│   └── src/
│       ├── components/
│       │   ├── WorkflowEditor/  拖拽式工作流编排
│       │   ├── TradingView/     K线图表 + Agent 标注
│       │   └── Analysis/        分析报告展示
│       ├── hooks/               WebSocket + 自定义 hooks
│       └── store/               Zustand 状态管理
├── docker-compose.yml           Docker 一键部署
└── .env.example                 配置模板
```

## 🚀 快速开始

### 方式一：本地开发

```bash
# 1. 克隆并安装
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. 配置
cp .env.example .env
# 编辑 .env 填入你的 LLM API Key

# 3. 启动后端
python -m backend.cli serve

# 4. 启动前端（另一个终端）
cd frontend
npm install
npm run dev
# 打开 http://localhost:3000
```

### 方式二：Docker 一键部署

```bash
cp .env.example .env
# 编辑 .env 填入 API Key
docker-compose up --build
# 打开 http://localhost:3000
```

### CLI 使用

```bash
# 分析股票
python -m backend.cli analyze 600519 --market a_share --workflow deep_analysis

# 快速扫描
python -m backend.cli analyze AAPL --market us_stock --workflow quick_scan

# 查看技能
python -m backend.cli skills

# 查看 Agent
python -m backend.cli agents-list

# 查看/修改配置
python -m backend.cli config --show
python -m backend.cli config LLM_API_KEY your-key-here
```

## 🧩 Agent 系统

| Agent | 角色 | 人设 | 默认技能 |
|-------|------|------|----------|
| 基本面分析师 | fundamental | 巴菲特价值投资 | financial_data, stock_info, peer_comparison |
| 技术面分析师 | technical | 纯图表派 | kline_data, realtime_quote |
| 情绪面分析师 | sentiment | 逆向思维 | sentiment_scan, realtime_quote |
| 新闻分析师 | news | 事件驱动 | news_fetch, realtime_quote |
| 宏观分析师 | macro | 自上而下 | macro_indicators, stock_info |
| 游资分析师 | hot_money | 短线博弈 | realtime_quote, kline_data, sentiment_scan, news_fetch, dragon_tiger, sector_flow |

## 🔧 Skill 插件系统

新增 Skill 只需创建文件并用 `@skill` 装饰器注册：

```python
# backend/skills/my_skill.py
from backend.skills.registry import skill

@skill(
    name="my_custom_skill",
    description="我的自定义技能",
    markets=["a_share", "us_stock"],
    category="custom",
)
def my_skill(symbol: str, market: str) -> dict:
    return {"result": "data"}
```

然后在 `backend/main.py` 中 import 即可自动注册。

## 📡 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| POST | /api/analyze | 执行分析 |
| GET | /api/agents | Agent 列表 |
| GET | /api/skills | 技能列表 |
| GET | /api/workflows | 工作流模板 |
| POST | /api/market/kline | K线数据 |
| POST | /api/market/markers | 图表标注 |
| PUT | /api/agents/{role}/skills | 更新 Agent 技能 |
| POST | /api/agents/{role}/skills/add | 添加技能 |
| POST | /api/agents/{role}/skills/remove | 移除技能 |
| WS | /ws/analyze | WebSocket 实时分析 |

## 🏗️ 工作流模板

- **quick_scan**：技术面 + 情绪面快速扫描
- **deep_analysis**：全 6 个 Agent 深度分析
- **debate**：多空辩论模式（多头律师 vs 空头律师）

## 📜 免责声明

本系统仅供学习和研究使用，AI 分析结果不构成投资建议。投资有风险，入市需谨慎。
