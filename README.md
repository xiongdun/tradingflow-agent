# 🤖 TradingFlow Agent

AI 多智能体股票分析系统 — 基于 LangGraph 的模块化 Agent 协作平台

---

## 📖 项目概述

TradingFlow Agent 是一个面向股票市场的 AI 多智能体分析系统，采用 **LangGraph** 作为工作流引擎，将不同类型的分析任务分配给专业化的 Analyst Agent，最终由 Summarizer Agent 综合所有观点生成结构化投资报告。

系统支持 **A股、港股、美股** 三大市场，内置 10+ 个专业分析师角色、20+ 个可插拔数据技能，并提供可视化工作流编排、实时 K 线图表、定时任务调度等企业级特性。所有 Agent 均基于大语言模型（LLM）驱动，支持 DeepSeek、OpenAI、Claude、Qwen、Ollama 等多种模型后端。

---

## ✨ 核心特性

### 多智能体协作架构
- **10+ 个专业分析师 Agent**：基本面、技术面、情绪面、新闻、宏观、游资、量化、风控、行业轮动等
- **独立人格与立场**：每个 Agent 拥有专属人设和分析框架，确保观点多样性
- **交叉审阅机制**：多轮迭代模式下，Agent 之间可相互审阅、修正观点

### 可插拔技能系统
- **20+ 个数据 Skill**：财务数据、K线分析、情绪扫描、龙虎榜、资金流向、宏观指标等
- **依赖拓扑执行**：Skill 支持声明依赖关系，系统自动按拓扑序并行调度
- **市场适配**：每个 Skill 可声明支持的市场范围，自动过滤不适用技能

### 灵活的工作流引擎
- **4 种执行模式**：并行、条件分支、多轮迭代、自适应选股
- **JSON 模板定义**：工作流通过 JSON 配置，无需修改代码即可定制分析流程
- **可视化编排**：前端提供 React Flow 拖拽式工作流编辑器

### 多数据源与缓存
- **多源容错**：AKShare、yfinance、efinance、baostock 等多个数据源，支持优先级配置与自动降级
- **磁盘 TTL 缓存**：按数据类型智能设置缓存过期策略，减少重复 API 调用
- **代理自动绕过**：针对国内数据源自动清除系统代理，避免连接问题

### 企业级功能
- **REST API + WebSocket**：完整的 FastAPI 后端，支持实时分析进度推送
- **定时任务调度**：基于 asyncio 的轻量调度器，支持每日/间隔/一次性分析任务
- **分析历史与回测**：SQLite 持久化所有分析记录，支持历史预测准确率统计
- **自选股与关注列表**：管理多组自选股，快速发起批量分析
- **多语言支持**：中英文报告自动切换，前端 i18n 完整覆盖

### 现代化前端
- **React 19 + TypeScript**：函数组件 + Hooks 架构
- **React Flow 工作流编排**：拖拽添加 Agent、连线定义执行顺序
- **Lightweight Charts K线图**：专业级金融图表，支持 Agent 分析标注叠加
- **Zustand 状态管理**：轻量全局状态，支持工作流草稿持久化

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              用户层 (CLI / Web / API)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  CLI 终端    │  │ React 前端   │  │ REST API    │  │ WebSocket 实时  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────────┘ │
└─────────┼────────────────┼────────────────┼─────────────────────────────┘
          │                │                │
          └────────────────┴────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────────────────┐
│                         应用层 (FastAPI + LangGraph)                       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     AnalysisService 统一服务层                       │  │
│  │         (消除 REST/WS/CLI/Scheduler 之间的代码重复)                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                              │                                            │
│  ┌───────────────────────────▼────────────────────────────────────────┐  │
│  │                     Graph Builder 工作流构建器                        │  │
│  │  ┌──────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │  │
│  │  │ parallel │ │ conditional │ │ multi_round │ │    adaptive     │  │  │
│  │  │ 并行模式  │ │  条件分支   │ │  多轮迭代   │ │   自适应选股    │  │  │
│  │  └──────────┘ └─────────────┘ └─────────────┘ └─────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                              │                                            │
│  ┌───────────────────────────▼────────────────────────────────────────┐  │
│  │                      Agent 层 (10+ 分析师)                           │  │
│  │  ┌────────┐ ┌────────┐ ┌──────────┐ ┌─────┐ ┌──────┐ ┌──────────┐ │  │
│  │  │基本面  │ │技术面  │ │ 情绪面   │ │新闻 │ │宏观  │ │  游资    │ │  │
│  │  │fundamental│ technical │ sentiment │ news │ macro │ hot_money │ │  │
│  │  └────────┘ └────────┘ └──────────┘ └─────┘ └──────┘ └──────────┘ │  │
│  │  ┌────────┐ ┌────────┐ ┌──────────┐ ┌────────────────────────────┐ │  │
│  │  │ 量化   │ │ 风控   │ │行业轮动  │ │      总结研判 summarizer    │ │  │
│  │  │ quant  │ │ risk   │ │sector_rot│ │      (投资委员会主席)        │ │  │
│  │  └────────┘ └────────┘ └──────────┘ └────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                              │                                            │
│  ┌───────────────────────────▼────────────────────────────────────────┐  │
│  │                      Skill 层 (20+ 数据技能)                         │  │
│  │  financial_data  kline_analysis  sentiment_scan  news_fetch        │  │
│  │  macro_indicators  dragon_tiger  sector_flow  fund_flow            │  │
│  │  technical_indicators  peer_comparison  shareholder_analysis       │  │
│  │  limit_up_analysis  block_trade  industry_analysis ...             │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────────────────┐
│                         数据层 (多源 + 缓存)                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  AKShare    │  │  yfinance    │  │  efinance   │  │  baostock       │  │
│  │ (A股/港股)  │  │  (美股)      │  │  (A股备用)  │  │  (A股备用)      │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘  │
│                              │                                            │
│  ┌───────────────────────────▼────────────────────────────────────────┐  │
│  │              FallbackProvider → CachedProvider                      │  │
│  │         (多源容错降级 → 磁盘 TTL 缓存 → 线程安全锁)                   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼─────────────────────────────────────────────┐
│                         基础设施层                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   SQLite    │  │   LLM 工厂   │  │  配置中心    │  │   定时调度器     │  │
│  │  (历史记录)  │  │(OpenAI/DS等)│  │  (.env 文件) │  │  (asyncio)      │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
tradingflow-agent/
├── backend/                          # Python 后端 (FastAPI + LangGraph)
│   ├── agents/                       # 分析师 Agent 模块
│   │   ├── base.py                   # BaseAgent 抽象基类 (技能执行 / LLM 推理 / 结构化输出)
│   │   ├── registry.py               # @agent 装饰器 + Agent 注册表 + 运行时技能覆盖
│   │   ├── models.py                 # AgentOpinion Pydantic 模型
│   │   ├── generic.py                # GenericAgent 通用分析师 (自定义角色)
│   │   ├── summarizer.py             # SummarizerAgent 总结研判 + FinalReport 模型
│   │   ├── fundamental.py            # 基本面分析师 (巴菲特价值投资风格)
│   │   ├── technical.py              # 技术面分析师 (纯图表派)
│   │   ├── sentiment.py              # 情绪面分析师 (逆向思维)
│   │   ├── news.py                   # 新闻分析师 (事件驱动)
│   │   ├── macro.py                  # 宏观分析师 (自上而下)
│   │   ├── hot_money.py              # 游资分析师 (短线博弈)
│   │   ├── quant.py                  # 量化分析师 (数据驱动)
│   │   ├── risk.py                   # 风控分析师 (风险识别)
│   │   └── sector_rotation.py        # 行业轮动分析师 (板块切换)
│   ├── skills/                       # 可插拔 Skill 模块
│   │   ├── registry.py               # @skill 装饰器 + SkillMeta 元数据 + 依赖管理
│   │   ├── financial_data.py         # 财务数据获取
│   │   ├── kline_analysis.py         # K线数据分析
│   │   ├── sentiment_scan.py         # 市场情绪扫描
│   │   ├── news_fetch.py             # 新闻事件获取
│   │   ├── macro_indicators.py       # 宏观经济指标
│   │   ├── dragon_tiger.py           # 龙虎榜数据
│   │   ├── sector_flow.py            # 板块资金流向
│   │   ├── fund_flow.py              # 个股资金流向
│   │   ├── technical_indicators.py   # 技术指标计算
│   │   ├── peer_comparison.py        # 同业对比
│   │   ├── shareholder_analysis.py   # 股东结构分析
│   │   ├── limit_up_analysis.py      # 涨停分析
│   │   ├── block_trade.py            # 大宗交易
│   │   ├── industry_analysis.py      # 行业分析
│   │   └── financial_report.py       # 财报解析
│   ├── graph/                        # LangGraph 工作流引擎
│   │   ├── state.py                  # AgentState 共享状态 + merge_opinions 归并器
│   │   ├── builder.py                # 工作流构建器 Facade (模式分发 + JSON 校验)
│   │   ├── builders/                 # 各模式构建策略
│   │   │   ├── common.py             # create_agents / create_summarizer / create_base_graph
│   │   │   ├── parallel.py           # 并行模式：所有 Agent 同时执行
│   │   │   ├── conditional.py        # 条件分支：按阶段 gate 控制执行路径
│   │   │   ├── multi_round.py        # 多轮迭代：交叉审阅 + 观点修正
│   │   │   └── adaptive.py           # 自适应模式：根据股票特征动态选 Agent
│   │   ├── templates/                # 预置工作流模板 (JSON)
│   │   │   ├── quick_scan.json       # 快速扫描 (技术面+情绪面)
│   │   │   ├── deep_analysis.json    # 深度分析 (全 Agent)
│   │   │   ├── debate.json           # 多空辩论
│   │   │   ├── debate_v2.json        # 多空辩论 v2
│   │   │   ├── full_spectrum.json    # 全谱分析
│   │   │   └── risk_first.json       # 风控优先
│   │   └── workflows/                # 编程式工作流示例
│   │       └── debate.py             # 辩论模式代码实现
│   ├── data/                         # 数据层
│   │   ├── provider.py               # DataProvider 抽象基类 + @provider 装饰器
│   │   ├── factory.py                # 数据提供者工厂 (多源容错 + 缓存包装)
│   │   ├── fallback_provider.py      # FallbackProvider 多源降级链
│   │   ├── akshare_provider.py       # AKShare 数据源 (A股/港股)
│   │   ├── yfinance_provider.py      # yfinance 数据源 (美股)
│   │   ├── efinance_provider.py      # efinance 数据源 (备用)
│   │   └── baostock_provider.py      # baostock 数据源 (备用)
│   ├── api/                          # REST API 路由
│   │   └── routes/
│   │       ├── analysis.py           # 分析执行 (REST + WebSocket)
│   │       ├── agents.py             # Agent 管理 (技能增删改查)
│   │       ├── workflows.py          # 工作流模板管理
│   │       ├── market_data.py        # 行情数据接口
│   │       ├── data_sources.py       # 数据源配置
│   │       ├── history.py            # 分析历史记录
│   │       ├── watchlist.py          # 自选股管理
│   │       └── schedules.py          # 定时任务管理
│   ├── core/                         # 核心基础设施
│   │   ├── config.py                 # Settings Pydantic 模型 + .env 加载
│   │   ├── config_writer.py          # 配置写入 .env (持久化)
│   │   ├── llm.py                    # LLM 工厂 (OpenAI/DeepSeek/Claude/Ollama)
│   │   ├── cache.py                  # 磁盘 TTL 缓存 (线程安全)
│   │   ├── database.py               # SQLite 连接管理
│   │   ├── scheduler.py              # 定时任务调度器 (asyncio)
│   │   ├── analysis_service.py       # AnalysisService 统一分析服务
│   │   ├── discovery.py              # 自动发现 (skills/agents/providers)
│   │   ├── locale.py                 # 多语言翻译包 (zh/en)
│   │   ├── parsing.py                # LLM 结构化输出解析
│   │   ├── exceptions.py             # 自定义异常体系
│   │   └── watchlist.py              # 自选股业务逻辑
│   ├── repositories/                 # 数据访问层
│   │   ├── base.py                   # SQLite DB 连接 + 表初始化
│   │   └── history.py                # 分析历史 CRUD + 回测统计
│   ├── output/                       # 报告输出
│   │   └── report.py                 # Markdown / HTML / Text 报告生成器
│   ├── tests/                        # 后端测试
│   ├── cli.py                        # Typer CLI 入口
│   └── main.py                       # FastAPI 应用入口
├── frontend/                         # React 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── WorkflowEditor/       # 工作流编排
│   │   │   │   ├── Sidebar.tsx       # Agent 拖拽侧边栏
│   │   │   │   ├── Canvas.tsx        # React Flow 画布
│   │   │   │   ├── AgentNode.tsx     # Agent 节点组件
│   │   │   │   ├── SummarizerNode.tsx# 总结节点组件
│   │   │   │   ├── NodeConfig.tsx    # 节点配置面板
│   │   │   │   ├── SkillPicker.tsx   # 技能选择器
│   │   │   │   └── AgentDetailModal.tsx # Agent 详情弹窗
│   │   │   ├── TradingView/
│   │   │   │   └── Chart.tsx         # Lightweight Charts K线图
│   │   │   ├── Analysis/
│   │   │   │   └── ReportView.tsx    # 分析报告渲染 (Markdown)
│   │   │   ├── History/
│   │   │   │   └── HistoryPanel.tsx  # 历史记录列表
│   │   │   ├── Watchlist/
│   │   │   │   └── WatchlistPanel.tsx# 自选股面板
│   │   │   ├── Schedule/
│   │   │   │   └── SchedulePanel.tsx # 定时任务面板
│   │   │   └── common/
│   │   │       └── ControlBar.tsx    # 顶部控制栏 (股票输入/市场选择/分析按钮)
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts       # WebSocket 连接管理
│   │   │   └── useTheme.ts           # 主题切换 Hook
│   │   ├── store/
│   │   │   └── workflowStore.ts      # Zustand 工作流状态
│   │   ├── api/
│   │   │   └── client.ts             # Axios API 客户端
│   │   ├── i18n/                     # 国际化
│   │   │   ├── index.ts              # i18n 入口
│   │   │   ├── zh.json               # 中文语言包
│   │   │   └── en.json               # 英文语言包
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript 类型定义
│   │   ├── constants/
│   │   │   └── theme.ts              # 主题常量
│   │   ├── App.tsx                   # 根组件 (标签页路由)
│   │   ├── main.tsx                  # 入口文件
│   │   └── index.css                 # 全局样式
│   ├── package.json                  # 前端依赖
│   └── vite.config.ts                # Vite 配置
├── tests/                            # 集成测试
├── docker-compose.yml                # Docker 一键部署
├── Dockerfile.backend                # 后端镜像
├── Dockerfile.frontend               # 前端镜像
├── nginx.conf                        # Nginx 反向代理配置
├── pyproject.toml                    # Python 项目配置
├── requirements.txt                  # Python 依赖
├── .env.example                      # 环境变量模板
└── README.md                         # 本文件
```

---

## 🚀 快速开始

### 方式一：本地开发

```bash
# 1. 克隆并创建虚拟环境
git clone <repo-url>
cd tradingflow-agent
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -e ".[dev]"

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 LLM API Key

# 4. 启动后端 API 服务
python -m backend.cli serve
# 或: uvicorn backend.main:app --reload

# 5. 启动前端 (新终端)
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

---

## 🖥️ CLI 使用

```bash
# 分析股票 (深度分析)
python -m backend.cli analyze 600519 --market a_share --workflow deep_analysis

# 快速扫描
python -m backend.cli analyze AAPL --market us_stock --workflow quick_scan

# 自定义 Agent 组合
python -m backend.cli analyze 600519 --agents fundamental,technical,quant

# 查看所有技能
python -m backend.cli skills

# 查看所有 Agent
python -m backend.cli agents-list

# 查看配置
python -m backend.cli config --show

# 修改配置
python -m backend.cli config LLM_API_KEY your-key-here

# 启动 API 服务
python -m backend.cli serve --host 0.0.0.0 --port 8000
```

---

## 🧩 Agent 系统详解

### 内置分析师 Agent

| Agent | 角色标识 | 人设风格 | 默认技能 |
|-------|---------|---------|---------|
| 基本面分析师 | `fundamental` | 巴菲特价值投资 | `financial_data`, `stock_info`, `peer_comparison` |
| 技术面分析师 | `technical` | 纯图表派 | `kline_data`, `realtime_quote` |
| 情绪面分析师 | `sentiment` | 逆向思维 | `sentiment_scan`, `realtime_quote` |
| 新闻分析师 | `news` | 事件驱动 | `news_fetch`, `realtime_quote` |
| 宏观分析师 | `macro` | 自上而下 | `macro_indicators`, `stock_info` |
| 游资分析师 | `hot_money` | 短线博弈 | `realtime_quote`, `kline_data`, `sentiment_scan`, `news_fetch`, `dragon_tiger`, `sector_flow` |
| 量化分析师 | `quant` | 数据驱动 | `technical_indicators`, `kline_data` |
| 风控分析师 | `risk` | 风险识别 | `financial_data`, `stock_info` |
| 行业轮动分析师 | `sector_rotation` | 板块切换 | `sector_flow`, `industry_analysis` |
| 总结研判 | `summarizer` | 投资委员会主席 | (无技能，综合所有意见) |

### Agent 基类设计

`BaseAgent` 定义了统一的分析生命周期：

1. **技能执行** (`_execute_skills`)：按依赖拓扑分层并行执行，支持超时保护 (30s)
2. **LLM 推理** (`analyze`)：构建系统提示词 + 数据文本 → 异步调用 LLM (120s 超时)
3. **结构化输出** (`_parse_opinion`)：解析 JSON 输出为 `AgentOpinion` 模型
4. **LangGraph 集成** (`run`)：作为图节点，自动归并到共享状态

### Agent 注册与运行时配置

```python
# 注册新 Agent (使用 @agent 装饰器)
from backend.agents.registry import agent

@agent("我的分析师", "my_analyst", ["financial_data", "kline_data"], "你是...")
class MyAgent(BaseAgent):
    pass

# 运行时动态调整技能
from backend.agents.registry import set_agent_skills, add_agent_skill
set_agent_skills("fundamental", ["financial_data", "peer_comparison"])
add_agent_skill("technical", "fund_flow")
```

---

## 🔧 Skill 插件系统

### 注册新 Skill

```python
# backend/skills/my_skill.py
from backend.skills.registry import skill

@skill(
    name="my_custom_skill",
    description="我的自定义数据技能",
    markets=["a_share", "us_stock"],      # 支持的市场
    category="custom",                     # 分类
    depends_on=["kline_data"],             # 依赖其他技能 (自动注入结果)
)
def my_skill(symbol: str, market: str, kline_data: dict = None) -> dict:
    # kline_data 由系统自动注入
    return {"result": "analysis"}
```

创建文件后无需手动导入，`auto_discover()` 会自动扫描并注册。

### 内置 Skill 列表

| Skill | 描述 | 支持市场 |
|-------|------|---------|
| `financial_data` | 财务数据 (PE/PB/ROE/营收) | 全市场 |
| `kline_analysis` | K线数据分析 | 全市场 |
| `sentiment_scan` | 市场情绪扫描 | 全市场 |
| `news_fetch` | 新闻事件获取 | 全市场 |
| `macro_indicators` | 宏观经济指标 | 全市场 |
| `dragon_tiger` | 龙虎榜数据 | A股 |
| `sector_flow` | 板块资金流向 | A股 |
| `fund_flow` | 个股资金流向 | A股 |
| `technical_indicators` | 技术指标计算 | 全市场 |
| `peer_comparison` | 同业对比 | 全市场 |
| `shareholder_analysis` | 股东结构分析 | A股 |
| `limit_up_analysis` | 涨停分析 | A股 |
| `block_trade` | 大宗交易 | A股 |
| `industry_analysis` | 行业分析 | A股 |
| `financial_report` | 财报解析 | A股 |

---

## 🏗️ 工作流引擎

### 4 种执行模式

#### 1. 并行模式 (parallel)
所有分析师同时执行，最后汇总。适合快速获取多维度观点。

```json
{
  "mode": "parallel",
  "agents": [
    {"role": "fundamental"},
    {"role": "technical"},
    {"role": "sentiment"}
  ]
}
```

#### 2. 条件分支模式 (conditional)
按阶段顺序执行，通过 gate 节点控制是否进入下一阶段。适合风控优先场景。

```json
{
  "mode": "conditional",
  "stages": [
    {"agents": ["risk"], "condition": "always"},
    {"agents": ["fundamental", "technical"], "condition": "check_risk"}
  ]
}
```

#### 3. 多轮迭代模式 (multi_round)
分析师多轮执行，每轮后由交叉审阅员指出逻辑矛盾和遗漏，Agent 修正观点。

```json
{
  "mode": "multi_round",
  "agents": ["fundamental", "technical"],
  "rounds": 3
}
```

#### 4. 自适应模式 (adaptive)
根据股票特征动态选择分析师组合：
- 大市值 (>1000亿) → 基本面 + 宏观 + 量化 + 风控
- 小市值高换手 (<100亿, 换手>5%) → 游资 + 情绪 + 新闻 + 风控
- 科技行业 → 技术面 + 基本面 + 新闻 + 量化
- 其他 → 基本面 + 技术面 + 情绪 + 风控

### 工作流模板

| 模板 | 模式 | 说明 |
|------|------|------|
| `quick_scan` | parallel | 技术面 + 情绪面快速扫描 |
| `deep_analysis` | parallel | 全 Agent 深度分析 |
| `debate` | parallel | 多空辩论模式 |
| `debate_v2` | parallel | 多空辩论 v2 |
| `full_spectrum` | parallel | 全谱分析 |
| `risk_first` | conditional | 风控优先 |

---

## 📡 API 端点

### 分析接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/analyze` | 执行股票分析 |
| WS | `/ws/analyze` | WebSocket 实时分析 |

### Agent 管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/agents` | 列出所有 Agent |
| GET | `/api/agents/{role}/skills` | 获取 Agent 技能 |
| PUT | `/api/agents/{role}/skills` | 批量设置技能 |
| POST | `/api/agents/{role}/skills/add` | 添加技能 |
| POST | `/api/agents/{role}/skills/remove` | 移除技能 |
| POST | `/api/agents/{role}/skills/reset` | 重置为默认 |

### 工作流管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/workflows` | 列出模板 |
| POST | `/api/workflows` | 保存自定义模板 |

### 数据与配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/skills` | 技能列表 |
| GET | `/api/config` | 系统配置 (脱敏) |
| POST | `/api/config` | 更新配置 |
| GET | `/api/locale/{lang}` | 语言包 |
| POST | `/api/market/kline` | K线数据 |
| POST | `/api/market/markers` | 图表标注 |
| GET | `/api/history` | 分析历史 |
| GET | `/api/history/{id}` | 历史详情 |
| GET | `/api/watchlist` | 自选股 |
| GET | `/api/schedules` | 定时任务 |

---

## ⚙️ 配置说明

`.env` 文件支持的所有配置项：

```bash
# LLM 配置
LLM_PROVIDER=deepseek              # openai / deepseek / qwen / claude / ollama
LLM_MODEL=deepseek-chat
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4096

# 分析配置
DEFAULT_MARKET=a_share
ANALYSIS_TIMEOUT=120

# 服务器配置
API_HOST=0.0.0.0
API_PORT=8000

# 数据源优先级 (JSON)
PROVIDER_PRIORITY={"a_share":["akshare","efinance"],"us_stock":["yfinance"]}

# 显示配置
COLOR_SCHEME=cn                    # cn=红涨绿跌, international=绿涨红跌
LANGUAGE=zh                        # zh / en

# 日志配置
LOG_LEVEL=INFO
```

---

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定模块
pytest backend/tests/test_agents.py
pytest backend/tests/test_skills.py
pytest backend/tests/test_scheduler.py
```

---

## 🐳 Docker 部署

```bash
# 构建并启动
docker-compose up --build -d

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 停止
docker-compose down
```

---

## 🔧 项目可优化点

### 前端性能优化

1. **Zustand 选择器粒度** — `workflowStore` 被大量组件全量订阅，任何状态变更都会触发所有订阅组件重渲染。应使用细粒度选择器（如 `useWorkflowStore(s => s.nodes)`）替代全量订阅。

2. **React Flow 边样式计算** — `Canvas.tsx` 中 `styledEdges` 在每次渲染时遍历所有边和节点进行计算，时间复杂度 O(E×N)。应使用 `useMemo` 缓存，或仅在 `edges`/`nodes` 变化时重新计算。

3. **Chart.tsx 图表重建** — 主题或颜色方案变化时，整个图表实例被销毁重建。应改用 `chart.applyOptions()` 动态更新主题颜色，避免重新创建 Series 和 MarkerPlugin。

4. **ReportView SVG 图表** — `AgentRadarChart` 和 `StancePieChart` 在每次 `opinions` 引用变化时重新渲染（即使数据未变）。应使用 `React.memo` + 自定义比较函数，或将计算逻辑抽离到 `useMemo`。

5. **内联样式性能** — 大量组件使用内联 `style` 对象，每次渲染创建新对象引用，导致子组件不必要的重渲染。关键路径组件（如 `AgentNode`、`Sidebar` 列表项）应提取为 CSS 类或使用 `useMemo` 缓存样式对象。

6. **Sidebar 搜索过滤** — 每次输入都会重新遍历所有 agents 和 skills 数组。应使用 `useMemo` 缓存过滤结果，并考虑添加防抖（debounce）。

7. **WebSocket 消息批处理** — `useWebSocket.ts` 中每条消息独立触发 store 更新，高频消息（如 `agent_status`）可能导致密集重渲染。应引入消息队列 + `requestAnimationFrame` 批处理机制。

8. **字体加载阻塞** — `index.css` 通过 `@import` 从 Google Fonts 同步加载 Inter 字体，阻塞首屏渲染。应改为 `<link rel="preload">` 异步加载，或内联关键字体子集。

9. **backdrop-filter 性能** — 大量使用 `backdrop-filter: blur()` 的半透明面板在低端设备上可能导致 GPU 合成层过多。可考虑在移动端或低性能设备上降级为纯色背景。

10. **代码分割与懒加载** — 当前所有组件在 `App.tsx` 中同步导入，首屏加载全部 JS。`ReportView`、`HistoryPanel`、`WatchlistPanel`、`SchedulePanel` 等非首屏组件应使用 `React.lazy` + `Suspense` 懒加载。

### 后端优化

1. **LLM 流式输出** — 当前 LLM 调用使用 `ainvoke` 等待完整响应，分析耗时较长（10+ Agent × 120s 超时）。应支持 SSE 流式输出，让前端实时看到分析内容生成过程。

2. **Skill 结果缓存粒度** — `cache.py` 按方法名+参数整体缓存，但不同 Agent 可能调用相同 Skill 获取相同数据。应在 Skill 层引入跨 Agent 的共享缓存。

3. **数据库连接池** — `repositories/base.py` 每次操作新建 SQLite 连接，高并发时存在性能瓶颈。应使用连接池（如 `aiosqlite` 或 `sqlite3` 的 `check_same_thread=False` + 单连接复用）。

4. **分析结果增量更新** — WebSocket 当前在分析完成后一次性推送所有结果，应支持 Agent 完成一个推送一个，提升前端实时性。

5. **工作流模板编译缓存** — `build_from_json` 每次分析都重新编译 LangGraph，相同模板应缓存编译后的图实例。

### 架构优化

1. **前端状态拆分** — 当前 Zustand store 包含画布状态、分析状态、UI 状态三大类，应拆分为 `useCanvasStore`、`useAnalysisStore`、`useUIStore`，减少无关状态变更的连锁重渲染。

2. **类型安全增强** — 多处使用 `(data as any)` 类型断言，应完善 `NodeProps` 泛型参数和自定义节点数据类型。

3. **错误边界覆盖** — 仅 `App.tsx` 中部分组件包裹了 `ErrorBoundary`，关键组件（如 `Canvas`、`Chart`）应统一添加。

---

## 🎨 前端性能优化详细方案

### 1. Zustand 状态拆分与选择器优化

**当前问题**：`workflowStore` 包含 20+ 个字段，任何字段变更都会触发所有订阅组件重渲染。

**优化方案**：

```typescript
// 拆分为三个独立 store
// store/canvasStore.ts — 仅画布相关
// store/analysisStore.ts — 仅分析相关
// store/uiStore.ts — 仅 UI 相关

// 或使用 Zustand 切片模式
const useCanvasStore = create<CanvasState>(...);
const useAnalysisStore = create<AnalysisState>(...);

// 组件中精确订阅
const nodes = useCanvasStore(s => s.nodes);        // 仅 nodes 变化时重渲染
const isAnalyzing = useAnalysisStore(s => s.isAnalyzing);  // 仅分析状态变化时重渲染
```

**预期收益**：减少 60%+ 的无关联重渲染。

### 2. React Flow 边样式 Memoization

**当前问题**：`styledEdges` 每次渲染都遍历所有边和节点。

**优化方案**：

```typescript
const styledEdges = useMemo(() => {
  return edges.map((e) => {
    const srcNode = nodes.find((n) => n.id === e.source);
    const isSkillEdge = srcNode?.type === 'skill';
    // ...
  });
}, [edges, nodes, selectedEdgeId]);
```

**预期收益**：非画布交互操作（如分析进度更新）不再触发边重计算。

### 3. 图表主题热更新（避免重建）

**当前问题**：`theme` 或 `colorScheme` 变化触发 `createChart` 重新执行。

**优化方案**：

```typescript
// 使用 applyOptions 替代重建
useEffect(() => {
  if (!chartRef.current) return;
  const upColor = colorScheme === 'cn' ? '#ef4444' : '#22c55e';
  chartRef.current.applyOptions({
    layout: { background: { color: bg }, textColor: textColor },
  });
  seriesRef.current?.applyOptions({ upColor, downColor, borderUpColor: upColor, ... });
}, [colorScheme, theme]);
```

**预期收益**：主题切换从 200ms+ 重建降至 16ms 内更新。

### 4. SVG 图表 Memoization

**当前问题**：`AgentRadarChart` 和 `StancePieChart` 在 `opinions` 引用变化时重新渲染。

**优化方案**：

```typescript
const MemoRadarChart = memo(AgentRadarChart, (prev, next) => {
  return JSON.stringify(prev.opinions) === JSON.stringify(next.opinions);
});

// 或使用 useMemo 缓存计算结果
const chartData = useMemo(() => computeChartData(opinions), [opinions]);
```

**预期收益**：分析进度消息更新时，图表不再重新渲染。

### 5. 内联样式提取与缓存

**当前问题**：`AgentNode` 每次渲染创建新的 `style` 对象。

**优化方案**：

```typescript
// 使用 useMemo 缓存样式
const nodeStyle = useMemo(() => ({
  background: 'var(--bg-card)',
  border: `1px solid ${selected ? color : 'var(--border)'}`,
  // ...
}), [selected, color, analyzing]);

// 或提取为 CSS 类 + CSS 变量
// .agent-node { background: var(--bg-card); }
// .agent-node.selected { border-color: var(--agent-color); }
```

**预期收益**：减少子组件的 `style` prop 引用变化导致的重渲染。

### 6. 组件懒加载

**当前问题**：所有标签页组件在 `App.tsx` 中同步导入。

**优化方案**：

```typescript
const ReportView = lazy(() => import('./components/Analysis/ReportView'));
const HistoryPanel = lazy(() => import('./components/History/HistoryPanel'));
const WatchlistPanel = lazy(() => import('./components/Watchlist/WatchlistPanel'));
const SchedulePanel = lazy(() => import('./components/Schedule/SchedulePanel'));

// 使用 Suspense 包裹
<Suspense fallback={<div>Loading...</div>}>
  <ReportView />
</Suspense>
```

**预期收益**：首屏 JS 体积减少 40%+，TTI（可交互时间）显著降低。

### 7. WebSocket 消息批处理

**当前问题**：每条 WebSocket 消息独立触发 store 更新。

**优化方案**：

```typescript
// 引入消息队列
const messageQueue: WSMessage[] = [];
let flushScheduled = false;

function flushMessages() {
  flushScheduled = false;
  const batch = messageQueue.splice(0);
  // 一次性应用所有消息
  useWorkflowStore.setState((state) => {
    // 合并更新...
  });
}

ws.onmessage = (event) => {
  messageQueue.push(JSON.parse(event.data));
  if (!flushScheduled) {
    flushScheduled = true;
    requestAnimationFrame(flushMessages);
  }
};
```

**预期收益**：高频消息场景下重渲染次数减少 80%+。

---

## 📜 免责声明

本系统仅供学习和研究使用，AI 分析结果不构成投资建议。投资有风险，入市需谨慎。

---

## 📄 License

MIT License
