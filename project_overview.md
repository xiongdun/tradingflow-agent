---
name: Project Overview
description: tradingflow-agent architecture, tech stack, and module structure
type: project
originSessionId: 3e937e52-c6af-4c73-92f4-70540a38b442
---
## tradingflow-agent

AI multi-agent stock analysis system powered by LangGraph. Supports A-share, H-stock, and US stock markets.

### Tech Stack
- **Backend**: Python 3.12 + FastAPI + LangGraph + LangChain
- **Frontend**: React 19 + TypeScript + React Flow + Lightweight Charts + shadcn/ui
- **Data**: AKShare (A-share/H-stock) + yfinance (US stocks) + baostock + efinance
- **LLM**: Configurable — DeepSeek, OpenAI, Claude, Qwen, Ollama

### Architecture Layers

1. **Agent System** (`backend/agents/`) — 9 analyst agents + 1 summarizer, registered via `@agent` decorator:
   - `fundamental` — Value investing (Buffett-style), skills: financial_data, stock_info, peer_comparison
   - `technical` — Chart/indicator analysis, skills: kline_data, realtime_quote
   - `sentiment` — Market emotion analysis, skills: sentiment_scan, realtime_quote
   - `news` — Event-driven/news analysis, skills: news_fetch, realtime_quote
   - `macro` — Macroeconomic analysis, skills: macro_indicators, stock_info
   - `quant` — Quantitative analysis, skills: kline_data, technical_indicators, financial_data
   - `risk` — Risk assessment, skills: kline_data, financial_data, realtime_quote, sentiment_scan
   - `hot_money` — Hot money / institutional flow, skills: realtime_quote, kline_data, sentiment_scan, news_fetch, dragon_tiger, sector_flow
   - `sector_rotation` — Sector rotation analysis, skills: sector_flow, realtime_quote, kline_data
   - `summarizer` — Synthesizes all opinions into FinalReport (no skills, uses others' outputs)

2. **Skill Plugin System** (`backend/skills/`) — 18 skills registered via `@skill` decorator:
   - Sentiment: `fund_flow`, `block_trade`, `dragon_tiger`, `limit_up_analysis`, `sentiment_scan`
   - Fundamental: `financial_data` (3 functions: financial_data, realtime_quote, stock_info), `financial_report`, `peer_comparison`, `shareholder_analysis`
   - Technical: `kline_data` (kline_analysis.py), `technical_indicators`
   - Macro: `industry_analysis`, `sector_flow`, `macro_indicators`
   - News: `news_fetch`

3. **Data Providers** (`backend/data/`) — 4 providers + fallback, registered via `@provider` decorator:
   - `akshare` — A-share/H-stock primary (priority 0)
   - `efinance` — A-share/H-stock backup (priority 1)
   - `baostock` — A-share backup (priority 2)
   - `yfinance` — US stocks primary (priority 0)
   - `fallback_provider` — Aggregates multiple providers with retry

4. **Workflow Engine** (`backend/graph/`) — LangGraph StateGraph with 4 build modes + 6 templates:
   - `parallel` — All analysts run concurrently, then summarizer
   - `conditional` — Stage-based with conditional branching
   - `multi_round` — Iterative cross-review (debate mode)
   - `adaptive` — Dynamically selects analysts based on stock characteristics (market cap, turnover, industry)
   - Templates: `quick_scan`, `deep_analysis`, `debate`, `debate_v2`, `full_spectrum`, `risk_first`

5. **API Layer** (`backend/api/routes/`) — 8 route modules:
   - `analysis`, `agents`, `workflows`, `market_data`, `data_sources`, `history`, `watchlist`, `schedules`

6. **Frontend** (`frontend/src/`) — 5 tabs:
   - Workflow editor (drag-and-drop React Flow canvas)
   - Report view (with TradingView K-line chart)
   - History panel
   - Watchlist panel
   - Schedule panel

7. **Core Services** (`backend/core/`):
   - `llm.py` — LLM factory supporting OpenAI-compatible (DeepSeek/Qwen/MiMo), Claude, Ollama
   - `analysis_service.py` — Unified analysis execution (REST/WS/CLI/scheduler share same logic)
   - `scheduler.py` — asyncio-based scheduler for automated periodic analysis (daily/interval/once)
   - `database.py` — SQLite via repositories layer (history, scheduled_tasks tables)
   - `config.py` — Pydantic Settings loaded from `.env`, supports runtime updates
   - `discovery.py` — Auto-imports all skill/agent/provider modules to trigger decorator registration

### Key Design Patterns
- **Decorator-based plugin registration**: `@skill`, `@agent`, `@provider` — all auto-discovered at startup via `auto_discover()`
- **LangGraph StateGraph**: Shared `AgentState` with `merge_opinions` reducer for parallel agent output
- **Strategy pattern**: `builder.py` is a facade that dispatches to concrete builders (`parallel.py`, `conditional.py`, `multi_round.py`, `adaptive.py`)
- **Provider fallback**: `fallback_provider.py` wraps multiple data sources with retry logic

**Why:** This architecture enables pluggable, composable analysis pipelines where new agents, skills, and data sources can be added without modifying core logic.

**How to apply:** When adding new capabilities, follow the decorator registration pattern. New agents go in `backend/agents/`, new skills in `backend/skills/`, new data sources in `backend/data/`.
