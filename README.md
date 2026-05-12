# 🤖 TradingFlow Agent

AI 多智能体股票分析系统 — 基于 LangGraph 的模块化 Agent 协作平台

---

## 📖 项目概述

TradingFlow Agent 是一个面向股票市场的 AI 多智能体分析系统，采用 **LangGraph** 作为工作流引擎，将不同类型的分析任务分配给专业化的 Analyst Agent，最终由 Summarizer Agent 综合所有观点生成结构化投资报告。

系统支持 **A股、港股、美股** 三大市场，内置 10+ 个专业分析师角色、20+ 个可插拔数据技能，并提供可视化工作流编排、实时 K 线图表、定时任务调度等企业级特性。所有 Agent 均基于大语言模型（LLM）驱动，支持 DeepSeek、OpenAI、Claude、Qwen、Mimo、Ollama 等多种模型后端。

---

## ✨ 核心特性

### 易用性优先
- **一键安装/启动脚本**：Windows 用户双击 `setup.bat` → `run.bat` 即可完成安装、配置并自动打开浏览器
- **零配置演示模式**：`tradingflow demo` 无需 API Key 即可预览完整分析报告
- **智能错误引导**：分析失败时自动检测原因（API Key 缺失/网络连接/超时等）并提供分步骤的解决方案
- **股票代码搜索**：`tradingflow search 茅台` 快速查询股票代码
- **新手引导弹窗**：前端首次打开自动弹出 3 步上手教程
- **中文友好**：`.env.example` 每条配置均有中文注释，支持中英文报告自动切换

### 多智能体协作架构
- **10+ 个专业分析师 Agent**：基本面、技术面、情绪面、新闻、宏观、游资、量化、风控、行业轮动、交易策略等
- **独立人格与立场**：每个 Agent 拥有专属人设和分析框架，确保观点多样性
- **交叉审阅机制**：多轮迭代模式下，Agent 之间可相互审阅、修正观点

### 可插拔技能系统
- **20+ 个数据 Skill**：财务数据、K线分析、情绪扫描、龙虎榜、资金流向、宏观指标、交易信号、组合风控等
- **依赖拓扑执行**：Skill 支持声明依赖关系，系统自动按拓扑序并行调度
- **市场适配**：每个 Skill 可声明支持的市场范围，自动过滤不适用技能

### 灵活的工作流引擎
- **4 种执行模式**：并行、条件分支、多轮迭代、自适应选股
- **V2 工作流系统**：支持条件节点、循环节点、事件触发器、适配器节点的可视化编排
- **JSON 模板定义**：工作流通过 JSON 配置，无需修改代码即可定制分析流程
- **7 个预置模板**：quick_scan、deep_analysis、debate、debate_v2、full_spectrum、risk_first、quant_hybrid
- **可视化编排**：前端提供 React Flow 拖拽式工作流编辑器

### 多数据源与缓存
- **多源容错**：AKShare、yfinance、efinance、baostock 等多个数据源，支持优先级配置与自动降级
- **磁盘 TTL 缓存**：按数据类型智能设置缓存过期策略，减少重复 API 调用
- **代理自动绕过**：针对国内数据源自动清除系统代理，避免连接问题

### 企业级功能
- **REST API + WebSocket**：完整的 FastAPI 后端，支持实时分析进度推送
- **全局异常处理器**：技术异常自动转为中文友好提示，无需查看 Traceback
- **定时任务调度**：基于 asyncio 的轻量调度器，支持每日/间隔/一次性分析任务
- **分析历史与回测**：SQLite 持久化所有分析记录，支持历史预测准确率统计
- **自选股与关注列表**：管理多组自选股，快速发起批量分析
- **多语言支持**：中英文报告自动切换，前端 i18n 完整覆盖

### 现代化前端
- **React 19 + TypeScript**：函数组件 + Hooks 架构
- **React Flow 工作流编排**：V2 节点系统（分析师、交易、技能、条件、循环、适配器、事件触发）
- **Lightweight Charts K线图**：专业级金融图表，支持 Agent 分析标注叠加
- **Zustand 状态管理**：轻量全局状态，支持工作流草稿持久化
- **独立的图表组件**：AgentRadarChart + StancePieChart 均提取为 React.memo 组件

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
│  │  ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │  │
│  │  │ 量化   │ │ 风控   │ │行业轮动  │ │   交易    │ │   总结研判    │ │  │
│  │  │ quant  │ │ risk   │ │sector_rot│ │  trading  │ │  summarizer  │ │  │
│  │  └────────┘ └────────┘ └──────────┘ └──────────┘ └──────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                              │                                            │
│  ┌───────────────────────────▼────────────────────────────────────────┐  │
│  │                      Skill 层 (20+ 数据技能)                         │  │
│  │  financial_data  kline_analysis  sentiment_scan  news_fetch        │  │
│  │  macro_indicators  dragon_tiger  sector_flow  fund_flow            │  │
│  │  technical_indicators  peer_comparison  shareholder_analysis       │  │
│  │  limit_up_analysis  block_trade  industry_analysis                 │  │
│  │  financial_report  portfolio_risk  trade_signal                    │  │
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
│  │   SQLite    │  │ LLM 注册表   │  │  配置中心    │  │   定时调度器     │  │
│  │  (历史记录)  │  │(@register)  │  │ (.env 文件) │  │  (asyncio)      │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
tradingflow-agent/
├── backend/                          # Python 后端 (FastAPI + LangGraph)
│   ├── agents/                       # 分析师 Agent 模块 (10+ 个)
│   │   ├── base.py                   # BaseAgent 抽象基类
│   │   ├── registry.py               # @agent 装饰器 + 注册表
│   │   ├── models.py                 # AgentOpinion Pydantic 模型
│   │   ├── generic.py                # GenericAgent 通用分析师
│   │   ├── summarizer.py             # SummarizerAgent 总结研判
│   │   ├── fundamental.py            # 基本面 (巴菲特价值投资)
│   │   ├── technical.py              # 技术面 (纯图表派)
│   │   ├── sentiment.py              # 情绪面 (逆向思维)
│   │   ├── news.py                   # 新闻 (事件驱动)
│   │   ├── macro.py                  # 宏观 (自上而下)
│   │   ├── hot_money.py              # 游资 (短线博弈)
│   │   ├── quant.py                  # 量化 (数据驱动)
│   │   ├── risk.py                   # 风控 (风险识别)
│   │   ├── sector_rotation.py        # 行业轮动 (板块切换)
│   │   └── trading.py                # 交易策略 (买卖决策)
│   ├── skills/                       # 可插拔 Skill 模块 (20+ 个)
│   │   ├── registry.py               # @skill 装饰器 + 依赖管理
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
│   │   ├── financial_report.py       # 财报解析
│   │   ├── portfolio_risk.py         # 组合风险评估
│   │   └── trade_signal.py           # 量化交易信号
│   ├── graph/                        # LangGraph 工作流引擎
│   │   ├── state.py                  # AgentState 共享状态
│   │   ├── builder.py                # 工作流构建器 Facade
│   │   ├── builders/                 # 策略模式实现
│   │   │   ├── common.py             # 公共工具函数
│   │   │   ├── parallel.py           # 并行模式
│   │   │   ├── conditional.py        # 条件分支
│   │   │   ├── multi_round.py        # 多轮迭代
│   │   │   └── adaptive.py           # 自适应选股
│   │   ├── templates/                # 预置 JSON 模板
│   │   │   ├── quick_scan.json       # 快速扫描
│   │   │   ├── deep_analysis.json    # 深度分析
│   │   │   ├── debate.json           # 多空辩论
│   │   │   ├── debate_v2.json        # 多空辩论 v2
│   │   │   ├── full_spectrum.json    # 全谱分析
│   │   │   ├── risk_first.json       # 风控优先
│   │   │   └── quant_hybrid.json     # 量化混合
│   │   └── workflows/                # 编程式工作流
│   │       └── debate.py             # 辩论模式实现
│   ├── data/                         # 数据层
│   │   ├── provider.py               # DataProvider 抽象基类
│   │   ├── factory.py                # 数据提供者工厂
│   │   ├── fallback_provider.py      # 多源降级链
│   │   ├── akshare_provider.py       # AKShare (A股/港股)
│   │   ├── yfinance_provider.py      # yfinance (美股)
│   │   ├── efinance_provider.py      # efinance (备用)
│   │   └── baostock_provider.py      # baostock (备用)
│   ├── api/                          # REST API 路由
│   │   └── routes/
│   │       ├── analysis.py           # 分析执行 (REST + WebSocket)
│   │       ├── agents.py             # Agent 管理
│   │       ├── skills.py             # Skills CRUD (独立路由)
│   │       ├── adapters.py           # 适配器管理
│   │       ├── plugins.py            # 插件系统
│   │       ├── workflows.py          # 工作流模板管理
│   │       ├── market_data.py        # 行情数据接口
│   │       ├── data_sources.py       # 数据源配置
│   │       ├── history.py            # 分析历史记录
│   │       ├── watchlist.py          # 自选股管理
│   │       └── schedules.py          # 定时任务管理
│   ├── core/                         # 核心基础设施
│   │   ├── config.py                 # Settings Pydantic (20+ 配置项)
│   │   ├── config_writer.py          # 配置持久化
│   │   ├── llm.py                    # LLM 注册表 (@register_llm)
│   │   ├── cache.py                  # 磁盘 TTL 缓存
│   │   ├── database.py               # SQLite 连接池
│   │   ├── scheduler.py              # 定时任务调度器
│   │   ├── analysis_service.py       # 统一分析服务
│   │   ├── discovery.py              # 自动发现
│   │   ├── skill_manager.py          # 技能管理器
│   │   ├── custom_store.py           # 自定义存储
│   │   ├── locale.py                 # 中英文翻译
│   │   ├── parsing.py                # LLM 输出解析
│   │   └── exceptions.py             # 异常体系
│   ├── repositories/                 # 数据访问层
│   │   ├── base.py                   # 连接池 + WAL 模式
│   │   └── history.py                # 历史 CRUD + 回测
│   ├── output/                       # 报告输出
│   │   └── report.py                 # Markdown 报告生成
│   ├── cli.py                        # CLI 入口 (Typer)
│   └── main.py                       # FastAPI 应用 (含全局异常处理器)
├── frontend/                         # React 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── WorkflowEditor/       # 工作流编排 (V2 节点)
│   │   │   │   ├── Sidebar.tsx       # Agent/Skill 拖拽侧边栏
│   │   │   │   ├── Canvas.tsx        # React Flow 画布
│   │   │   │   ├── AgentNode.tsx     # Agent 节点
│   │   │   │   ├── SkillNode.tsx     # Skill 节点
│   │   │   │   ├── TradingNode.tsx   # 交易节点
│   │   │   │   ├── SummarizerNode.tsx# 总结节点
│   │   │   │   ├── ConditionNode.tsx # 条件分支节点
│   │   │   │   ├── LoopNode.tsx      # 循环节点
│   │   │   │   ├── EventTriggerNode.tsx # 事件触发节点
│   │   │   │   ├── AdapterNode.tsx   # 适配器节点
│   │   │   │   ├── ConfigNode.tsx    # 配置节点
│   │   │   │   ├── InputNode.tsx     # 输入节点
│   │   │   │   ├── NodeConfig.tsx    # 节点配置面板
│   │   │   │   ├── SkillPicker.tsx   # 技能选择器
│   │   │   │   └── AgentDetailModal.tsx # Agent 详情弹窗
│   │   │   ├── TradingView/
│   │   │   │   └── Chart.tsx         # K线图表
│   │   │   ├── Analysis/
│   │   │   │   ├── ReportView.tsx    # 分析报告
│   │   │   │   ├── AgentRadarChart.tsx# 雷达图 (React.memo)
│   │   │   │   └── StancePieChart.tsx# 立场饼图 (React.memo)
│   │   │   ├── Settings/
│   │   │   │   ├── SettingsPanel.tsx  # 设置总面板
│   │   │   │   ├── GeneralSettings.tsx
│   │   │   │   ├── LLMSettings.tsx
│   │   │   │   ├── AgentSettings.tsx
│   │   │   │   └── SkillSettings.tsx
│   │   │   ├── History/HistoryPanel.tsx
│   │   │   ├── Watchlist/WatchlistPanel.tsx
│   │   │   ├── Schedule/SchedulePanel.tsx
│   │   │   └── common/
│   │   │       ├── ControlBar.tsx    # 快捷输入 + 市场选择 + 预设股票
│   │   │       └── Toast.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts       # WebSocket (指数退避重连)
│   │   │   └── useTheme.ts           # 主题切换
│   │   ├── store/workflowStore.ts    # Zustand 全局状态
│   │   ├── api/client.ts             # Axios API 客户端
│   │   ├── i18n/                     # 国际化 (zh/en)
│   │   ├── types/index.ts            # TS 类型定义
│   │   ├── constants/theme.ts        # 主题常量
│   │   ├── App.tsx                   # 根组件 + 新手引导弹窗
│   │   ├── main.tsx                  # 入口文件
│   │   └── index.css                 # 全局样式
│   └── ...
├── tests/                            # 后端测试 (289 个用例)
│   ├── test_agents.py                # Agent 测试
│   ├── test_skills.py                # Skill 测试
│   ├── test_config.py                # 配置测试
│   ├── test_graph_builder.py         # 工作流构建测试
│   ├── test_v2_workflow.py           # V2 工作流测试
│   ├── test_adapters.py              # 适配器测试
│   ├── test_plugin_system.py         # 插件系统测试
│   ├── test_providers.py             # 数据源测试
│   ├── test_repositories.py          # 数据层测试
│   ├── ... (共 25+ 测试文件)
│   └── conftest.py                   # 测试夹具 + DB 隔离
├── setup.bat / run.bat               # Windows 一键安装/启动
├── setup.sh / run.sh                 # Linux/macOS 一键安装/启动
├── docker-compose.yml                # Docker 部署
├── Dockerfile.backend / Dockerfile.frontend
├── pyproject.toml                    # Python 项目配置
├── .env.example                      # 配置模板 (含中文注释)
└── README.md                         # 本文件
```

---

## 🚀 快速开始

### 方式一：Windows 一键启动（推荐）

```bat
双击 setup.bat  →  按提示输入 API Key  →  双击 run.bat
```

### 方式二：Linux/macOS 一键启动

```bash
bash setup.sh   # 安装依赖 + 配置
bash run.sh     # 启动服务 + 打开浏览器
```

### 方式三：本地开发

```bash
# 1. 创建虚拟环境并安装
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env → 修改 LLM_API_KEY=你的密钥

# 3. 演示模式（零配置，立即体验）
python -m backend.cli demo

# 4. 启动服务
python -m backend.cli serve

# 5. 启动前端（新终端）
cd frontend && npm install && npm run dev
# 打开 http://localhost:3000
```

### 方式四：Docker 部署

```bash
cp .env.example .env && docker-compose up --build
# 打开 http://localhost:3000
```

---

## 🖥️ CLI 使用

```bash
# 🎓 零配置演示 — 无需 API Key，立即查看报告效果
python -m backend.cli demo

# 🔍 搜索股票代码
python -m backend.cli search 茅台
python -m backend.cli search 比亚迪
python -m backend.cli search AAPL

# 📊 分析股票（深度分析）
python -m backend.cli analyze 600519 --market a_share --workflow deep_analysis

# ⚡ 快速扫描
python -m backend.cli analyze AAPL --market us_stock --workflow quick_scan

# 🛠️ 自定义 Agent 组合
python -m backend.cli analyze 600519 --agents fundamental,technical,quant

# 🔧 查看/修改配置
python -m backend.cli config --show
python -m backend.cli config LLM_API_KEY your-key-here

# 🧩 列出所有技能/Agent
python -m backend.cli skills
python -m backend.cli agents-list

# 🌐 启动 API 服务
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
| 风控分析师 | `risk` | 风险识别 | `financial_data`, `stock_info`, `portfolio_risk` |
| 行业轮动分析师 | `sector_rotation` | 板块切换 | `sector_flow`, `industry_analysis` |
| 交易策略分析师 | `trading` | 买卖决策 | `trade_signal`, `kline_data`, `realtime_quote` |
| 总结研判 | `summarizer` | 投资委员会主席 | (综合所有 Agent 意见) |

### Agent 生命周期

`BaseAgent` 定义了统一的分析生命周期：

1. **技能执行** — 按依赖拓扑分层并行执行，支持可配置超时 (默认 30s)
2. **LLM 推理** — 构建系统提示词 + 数据文本 → 异步调用 LLM (默认 120s 超时)
3. **结构化输出** — 解析 JSON 为 `AgentOpinion` 模型（含 stance、confidence、risk_level 等）
4. **LangGraph 集成** — 作为图节点归并到共享状态 `AgentState`

### Agent 注册与运行时配置

```python
# 注册新 Agent
from backend.agents.registry import agent

@agent("我的分析师", "my_analyst", ["financial_data", "kline_data"], "你是...")
class MyAgent(BaseAgent):
    pass

# 运行时动态调整技能
from backend.agents.registry import set_agent_skill, add_agent_skill
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
    markets=["a_share", "us_stock"],
    category="custom",
    depends_on=["kline_data"],  # 自动注入依赖结果
)
def my_skill(symbol: str, market: str, kline_data: dict = None) -> dict:
    return {"result": "analysis"}
```

创建文件后无需手动导入，`auto_discover()` 自动扫描注册。

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
| `portfolio_risk` | 组合风险评估 | 全市场 |
| `trade_signal` | 量化交易信号 | 全市场 |

---

## 🏗️ 工作流引擎

### 4 种执行模式

#### 1. 并行模式 (parallel)
所有分析师同时执行，最后汇总。适合快速获取多维度观点。

```json
{"mode": "parallel", "agents": [{"role": "fundamental"}, {"role": "technical"}, {"role": "sentiment"}]}
```

#### 2. 条件分支模式 (conditional)
按阶段顺序执行，通过 gate 节点控制执行路径。适合风控优先场景。

```json
{"mode": "conditional", "stages": [
  {"agents": ["risk"], "condition": "always"},
  {"agents": ["fundamental", "technical"], "condition": "check_risk"}
]}
```

#### 3. 多轮迭代模式 (multi_round)
多轮执行 + 交叉审阅 + 观点修正。

```json
{"mode": "multi_round", "agents": ["fundamental", "technical"], "rounds": 3}
```

#### 4. 自适应模式 (adaptive)
根据股票特征动态选择 Agent 组合（阈值通过 `.env` 可配）：
- 大市值 (>1000亿) → 基本面 + 宏观 + 量化 + 风控
- 小市值高换手 (<100亿) → 游资 + 情绪 + 新闻 + 风控
- 科技行业 → 技术面 + 基本面 + 新闻 + 量化
- 其他 → 基本面 + 技术面 + 情绪 + 风控

### 预置模板

| 模板 | 模式 | 说明 |
|------|------|------|
| `quick_scan` | parallel | 技术面 + 情绪面快速扫描 |
| `deep_analysis` | parallel | 全 Agent 深度分析 |
| `debate` | parallel | 多空辩论模式 |
| `debate_v2` | parallel | 多空辩论 v2 (更全面) |
| `full_spectrum` | parallel | 全谱分析 |
| `risk_first` | conditional | 风控优先 (风控通过后才继续) |
| `quant_hybrid` | V2 workflow | 量化混合策略 (条件+循环节点) |

### V2 工作流系统

支持条件节点、循环节点、事件触发器、适配器，可在前端 React Flow 画布上可视化编排。

---

## 📡 API 端点

### 分析

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/analyze` | 执行股票分析 |
| WS | `/ws/analyze` | WebSocket 实时推送进度 |

### Agent 管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/agents` | 列出所有 Agent |
| GET | `/api/agents/{role}/skills` | 获取 Agent 技能 |
| PUT | `/api/agents/{role}/skills` | 批量设置技能 |
| POST | `/api/agents/{role}/skills/add` | 添加技能 |
| POST | `/api/agents/{role}/skills/remove` | 移除技能 |
| POST | `/api/agents/{role}/skills/reset` | 重置为默认 |

### 技能管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/skills` | 列出所有 Skill |
| GET | `/api/skills/{name}` | Skill 详情 |
| POST | `/api/skills` | 创建 Skill |
| PUT | `/api/skills/{name}` | 更新 Skill |
| DELETE | `/api/skills/{name}` | 删除 Skill |

### 工作流与模板

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/workflows` | 列出模板 |
| POST | `/api/workflows` | 保存自定义模板 |

### 数据与配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/config` | 系统配置 (脱敏) |
| POST | `/api/config` | 更新配置 |
| GET | `/api/locale/{lang}` | 语言包 |
| POST | `/api/market/kline` | K线数据 |
| POST | `/api/market/markers` | 图表标注 |
| GET | `/api/history` | 分析历史 |
| GET | `/api/history/{id}` | 历史详情 |
| GET | `/api/data_sources` | 数据源状态 |
| GET | `/api/watchlist` | 自选股 |
| GET | `/api/schedules` | 定时任务 |
| GET | `/api/adapters` | 适配器列表 |
| GET | `/api/plugins` | 插件列表 |

---

## ⚙️ 配置说明

完整的 `.env` 配置项（`.env.example` 包含详细中文注释）：

```bash
# 🔑 LLM 大模型配置
LLM_PROVIDER=deepseek              # deepseek / openai / qwen / mimo / claude / ollama
LLM_MODEL=deepseek-chat            # 模型名称
LLM_API_KEY=your-api-key           # API 密钥（必填）
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4096

# ⚙️ 分析配置
DEFAULT_MARKET=a_share
ANALYSIS_TIMEOUT=120

# 🌐 服务器配置
API_HOST=0.0.0.0
API_PORT=8000

# 📝 日志配置
LOG_LEVEL=INFO

# 🎨 显示配置
COLOR_SCHEME=cn                    # cn=红涨绿跌 / international=绿涨红跌
LANGUAGE=zh                        # zh / en

# ⏱️ 超时与重试
SKILL_TIMEOUT=30                   # 单个技能执行超时（秒）
FALLBACK_RETRY_MAX=3               # 数据源最大重试次数
FALLBACK_RETRY_WAIT_MIN=1.0        # 重试最小等待（秒）
FALLBACK_RETRY_WAIT_MAX=8.0        # 重试最大等待（秒）

# 📊 分析预算
MAX_AGENTS_PER_ANALYSIS=10         # 单次分析最大 Agent 数

# 🎯 自适应选股阈值
ADAPTIVE_LARGE_CAP=100000000000    # 大市值阈值（1000亿）
ADAPTIVE_SMALL_CAP=10000000000     # 小市值阈值（100亿）
ADAPTIVE_HIGH_TURNOVER=5.0         # 高换手率阈值（%）
```

---

## 🧪 测试

```bash
# 运行所有 289 个测试 (89%+ 覆盖率)
pytest tests/ -v

# 运行特定模块
pytest tests/test_agents.py
pytest tests/test_v2_workflow.py
pytest tests/test_skills.py
pytest tests/test_adapters.py
```

---

## 🐳 Docker 部署

```bash
cp .env.example .env
# 编辑 .env 填写 API Key
docker-compose up --build -d
# 打开 http://localhost:3000
```

---

## 🛡️ 稳定性保障

### 异常处理体系

| 层级 | 策略 | 说明 |
|------|------|------|
| **数据层** | 安全降级 | FallbackProvider 在所有数据源失败时返回空值而非崩溃，确保分析流程不中断 |
| **Agent 层** | 双层超时 | 技能执行 (30s) + LLM 推理 (120s) 分别配置独立超时，超时后生成占位意见 |
| **工作流层** | 硬上限兜底 | multi_round 循环上限 min(rounds, 10)，防止配置错误导致无限循环 |
| **存储层** | 连接回滚 | `get_db()` 异常时自动 `rollback()`，防止脏连接污染连接池 |
| **API 层** | 正确状态码 | 分析失败返回 HTTP 500 + 日志记录，模板不存在返回 HTTP 404 |
| **前端** | Null Safety | workflowStore 所有节点 data 访问加 `|| {}` 防护，skillName/role 空值默认 '' |
| **全局** | 中文异常翻译 | `main.py` 全局异常处理器将技术异常转为中文引导，无需查看 Traceback |

### 关键防护节点

```
请求入口
  ├─ API 404/500 正确状态码 + 日志
  ├─ WebSocket 异常完整捕获 + 独立 per-connection 并发控制
  ↓
数据获取
  ├─ FallbackProvider → 安全空值降级 (永不抛异常)
  ├─ TTL 缓存损坏检测 → 自动清除 + 提示重试
  ↓
Agent 执行
  ├─ 技能 None → {} 转换，避免下游格式化崩溃
  ├─ LLM 超时 → 生成 {stance: neutral, confidence: 0} 占位意见
  ├─ JSON 解析 → confidence float() 失败兜底 0.5
  ↓
工作流编排
  ├─ conditional gate → isinstance(op, dict) 类型守卫
  ├─ multi_round → max(round, 1) + min(rounds, 10) 双重防护
  ├─ adaptive → 异常静默回退默认 Agent 组 + logger.warning
  ↓
数据持久化
  └─ SQLite 异常 → rollback + 归还连接池 (finally 保证)
```

---

## 📜 免责声明

本系统仅供学习和研究使用，AI 分析结果不构成投资建议。投资有风险，入市需谨慎。

---

## 📄 License

MIT License