# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**tradingflow-agent** — An AI multi-agent stock analysis system powered by LangGraph.
Supports A-share, H-stock, and US stock markets with modular, pluggable agent architecture.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + LangGraph + LangChain
- **Frontend**: React 19 + TypeScript + React Flow + Lightweight Charts + Zustand
- **Data**: AKShare (A-share/H-stock) + yfinance (US stocks) + efinance/baostock (fallback)
- **LLM**: Configurable (DeepSeek, OpenAI, Claude, Qwen, Mimo, Ollama)

## Architecture

### Agent System (backend/agents/) — 11 agents
10+ specialized analyst agents + summarizer, each with independent personas:
- `base.py` — BaseAgent: 4-step lifecycle (skill exec → LLM inference → structured output → LangGraph node)
- `registry.py` — `@agent` decorator + runtime skill override (set_agent_skills/add_agent_skill/remove_agent_skill)
- `models.py` — AgentOpinion Pydantic (stance, confidence, risk_level, target_price, reasoning)
- `fundamental.py` — Value investing (Buffett-style)
- `technical.py` — Chart/indicator analysis
- `sentiment.py` — Market emotion (contrarian thinking)
- `news.py` — Event-driven/news analysis
- `macro.py` — Top-down macroeconomic analysis
- `hot_money.py` — Short-term speculation (dragon_tiger, fund_flow)
- `quant.py` — Quantitative/data-driven analysis
- `risk.py` — Risk assessment (portfolio_risk)
- `sector_rotation.py` — Sector rotation analysis
- `trading.py` — Trading strategy (buy/sell decisions, trade_signal)
- `generic.py` — GenericAgent for custom analyst roles
- `summarizer.py` — Final synthesis committee chair

### Skill Plugin System (backend/skills/) — 19 skills
Skills are registered via `@skill` decorator. Each agent can be assigned different skills.
Supports dependency topology (`depends_on`) for automatic parallel scheduling.
Key skills: `financial_data`, `kline_analysis`, `sentiment_scan`, `news_fetch`,
`macro_indicators`, `dragon_tiger`, `sector_flow`, `fund_flow`, `technical_indicators`,
`peer_comparison`, `shareholder_analysis`, `limit_up_analysis`, `block_trade`,
`industry_analysis`, `financial_report`, `portfolio_risk`, `trade_signal`.

### LangGraph Workflows (backend/graph/)
- `state.py` — Shared AgentState with `merge_opinions` reducer
- `builder.py` — Facade dispatching to strategy builders based on mode + JSON validation (v1/v2)
- `builders/` — Strategy pattern implementations:
  - `parallel.py` — All agents execute simultaneously
  - `conditional.py` — Stage-gated conditional execution with gate conditions
  - `multi_round.py` — Multi-round iteration with cross-review
  - `adaptive.py` — Dynamic agent selection based on stock characteristics (thresholds from config)
- `templates/` — 7 pre-built JSON templates: quick_scan, deep_analysis, debate, debate_v2, full_spectrum, risk_first, quant_hybrid
- `workflows/debate.py` — Programmatic debate workflow example

### V2 Workflow System
Supports condition nodes (gate routing), loop nodes (counter-based iteration),
event triggers (price_alert, indicator_signal, news_event), and adapter nodes
for extensible data processing. All nodes can be composed visually in React Flow.

### Adapter System (backend/adapters/)
Pluggable adapter architecture with `@adapter` decorator registration.
Supports function adapters (sync/async) and MCP (Model Context Protocol) adapters.
Factory creates adapters by name with tool/task mapping.

### Plugin System (backend/plugins/)
Runtime plugin discovery and loading via `PluginRegistry`. Supports hot-reload
and dependency validation through `PluginValidator`.

### Data Layer (backend/data/)
- `provider.py` — Abstract DataProvider base + `@provider` decorator registry
- `factory.py` — Provider factory with multi-source fallback + TTL cache wrapping
- `fallback_provider.py` — Chain-of-responsibility fallback (retries with exponential backoff, configurable via Settings)
- `akshare_provider.py`, `yfinance_provider.py`, `efinance_provider.py`, `baostock_provider.py`

### Configuration (backend/core/)
- `config.py` — Settings Pydantic model with 20+ fields loaded from `.env`
  - LLM config (6 fields): provider, model, api_key, base_url, temperature, max_tokens
  - Analysis config: default_market, analysis_timeout
  - Server config: api_host, api_port
  - Display config: color_scheme (cn/international), language (zh/en)
  - Timeout/Retry config: skill_timeout, llm_timeout, fallback_retry_max/wait_min/wait_max
  - Budget config: max_agents_per_analysis
  - Adaptive thresholds: adaptive_large_cap, adaptive_small_cap, adaptive_high_turnover
- `config_writer.py` — Persists changes to `.env` file
- `llm.py` — LLM factory with `@register_llm` decorator registry (instead of if/elif chain). OpenAI-compatible providers (deepseek/openai/qwen/mimo) share a single builder
- `cache.py` — Thread-safe disk TTL cache with `diskcache`
- `database.py` — SQLite connection pool (queue.Queue) with WAL mode + `check_same_thread=False`
- `scheduler.py` — asyncio-based task scheduler (daily/interval/one-shot)
- `analysis_service.py` — Unified analysis service (eliminates code duplication across REST/WS/CLI/Scheduler)
- `discovery.py` — `auto_discover()` scans and registers all agents/skills/providers
- `skill_manager.py` — Runtime skill management and execution orchestration
- `custom_store.py` — Custom state storage for LangGraph checkpoints
- `locale.py` — Bilingual translation (zh/en) for agent prompts and report headers
- `parsing.py` — Robust JSON extraction from LLM responses (handles markdown fences, trailing commas)
- `exceptions.py` — Custom exception hierarchy

### Repositories (backend/repositories/)
- `base.py` — SQLite connection pool with `get_db()` context manager + auto table init
- `history.py` — Analysis history CRUD + backtest accuracy statistics. All DB access via `get_db()` (proper pool management)

### API Routes (backend/api/routes/) — 12 route modules
`analysis.py`, `agents.py`, `skills.py` (migrated from main.py), `adapters.py`,
`plugins.py`, `workflows.py`, `market_data.py`, `data_sources.py`, `history.py`,
`watchlist.py`, `schedules.py`

### Main Entry (backend/main.py)
- FastAPI app with CORS middleware
- Global `@app.exception_handler(Exception)` — translates technical errors to Chinese-friendly messages with actionable steps
- `atexit` connection pool cleanup
- API key check on startup with friendly guidance

### CLI (backend/cli.py)
7 commands via Typer:
- `demo` — Zero-config demo mode (no API key needed, shows sample report + setup guide)
- `analyze` — Run stock analysis with intelligent error hints (detects API key/network/timeout/quota errors and shows step-by-step solutions in Chinese)
- `search` — Search stock codes by keyword (company name or code fragment) across all 3 markets with fallback common-stock reference
- `config` — View/update configuration with key masking
- `skills` — List skills filtered by market/category
- `agents-list` — List agents in table format
- `serve` — Start FastAPI + Uvicorn

### Frontend Architecture (frontend/src/)

**App.tsx** — Root component with onboarding modal (localStorage-based first-visit detection), tab navigation (workflow/report/history/watchlist/schedule/settings)

**ControlBar.tsx** — Stock symbol input with placeholder "输入股票代码，如 600519", market selector (A股/港股/美股 with emoji flags), quick stock preset buttons (茅台/比亚迪/腾讯/Apple)

**WorkflowEditor/** — V2 node system with 12 node types:
- `Sidebar.tsx` — Draggable agent/skill/template sidebar with search, collapsible sections (Skills default expanded)
- `Canvas.tsx` — React Flow canvas with memoized edge styles
- `AgentNode.tsx`, `SkillNode.tsx`, `TradingNode.tsx`, `SummarizerNode.tsx`
- `ConditionNode.tsx`, `LoopNode.tsx`, `EventTriggerNode.tsx`, `AdapterNode.tsx`
- `ConfigNode.tsx`, `InputNode.tsx`
- `NodeConfig.tsx` — Right-side config panel
- `SkillPicker.tsx`, `AgentDetailModal.tsx`

**Analysis/** — Report rendering:
- `ReportView.tsx` — Markdown report with export bar
- `AgentRadarChart.tsx` — SVG radar chart (React.memo with JSON deep comparison)
- `StancePieChart.tsx` — SVG pie chart (React.memo with JSON deep comparison)

**Settings/** — 5 setting panels:
- `SettingsPanel.tsx`, `GeneralSettings.tsx`, `LLMSettings.tsx`, `AgentSettings.tsx`, `SkillSettings.tsx`

**Other panels**: `History/HistoryPanel.tsx`, `Watchlist/WatchlistPanel.tsx`, `Schedule/SchedulePanel.tsx`

**TradingView/Chart.tsx** — Lightweight Charts candlestick with agent marker overlays

**store/workflowStore.ts** — Zustand global state (nodes, edges, analysis progress, opinions, agents/skills cache)

**hooks/useWebSocket.ts** — WebSocket with exponential backoff reconnection
**hooks/useTheme.ts** — Dark/light theme with localStorage persistence

**i18n/** — Lightweight i18n (zh/en) loaded from backend config

**common/** — Toast notification system with auto-dismiss

## Development

### Quick Start
```bash
# One-click (Windows):
双击 setup.bat  →  run.bat

# One-click (Linux/macOS):
bash setup.sh && bash run.sh

# Manual setup:
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with LLM API key

# Demo (zero config):
python -m backend.cli demo

# CLI:
python -m backend.cli analyze 600519 --market a_share --workflow deep_analysis
python -m backend.cli search 茅台
python -m backend.cli skills
python -m backend.cli agents-list
python -m backend.cli config --show

# API Server:
python -m backend.cli serve

# Frontend (new terminal):
cd frontend && npm install && npm run dev
```

### Commands
- `tradingflow demo` — Zero-config demo report
- `tradingflow analyze <symbol>` — Run stock analysis
- `tradingflow search <keyword>` — Search stock codes
- `tradingflow config [KEY] [VALUE]` — View/update configuration
- `tradingflow skills` — List available skills
- `tradingflow agents-list` — List available agents
- `tradingflow serve` — Start web API server

## Behavioral Guidelines

### Simplicity First
- No speculative features. Minimum code that solves the problem.
- No abstractions for single-use code.
- If 200 lines could be 50, rewrite it.

### Surgical Changes
- Touch only what you must. Match existing style.
- Remove imports/variables YOUR changes made unused.

### Goal-Driven Execution
- State assumptions explicitly. If uncertain, ask.
- For multi-step tasks, state a brief plan with verification steps.

## Frontend Performance Notes

When modifying frontend code, be aware of these performance-sensitive areas:

1. **Zustand selectors** — Always use granular selectors (e.g., `useWorkflowStore(s => s.nodes)`) instead of subscribing to the entire store to prevent unnecessary re-renders.

2. **React Flow canvas** — Large workflows with many nodes can cause jank. The `styledEdges` computation in Canvas.tsx runs on every render; consider memoizing edge styles.

3. **Chart.tsx re-creation** — The chart instance is destroyed and recreated on every `colorScheme` or `theme` change. This is intentional for theme switching but could be optimized to applyOptions instead.

4. **ReportView SVG charts** — AgentRadarChart and StancePieChart are now extracted as independent React.memo components with JSON deep comparison. This resolves the original performance issue of re-rendering on every store update.

5. **Inline styles** — The codebase heavily uses inline `style` props. This is fine for this project's scale but prevents CSS-level optimizations like `content-visibility`.

6. **Onboarding modal** — Uses `position: fixed` overlay with `backdropFilter: blur()`. The modal state checks localStorage synchronously in `useState` initializer — this is intentional to avoid flash-on-load.

## Test Architecture

289 tests across 25+ test files with 89%+ coverage:
- `conftest.py` — Shared fixtures including `patch_db_path` (DB isolation with pool reset)
- Agent tests: lifecycle, opinion parsing, skill execution, timeout handling
- Workflow tests: parallel/conditional/multi_round/adaptive modes, V2 nodes (condition, loop, skill, adapter)
- Data tests: provider fallback chains, retry logic, TTL cache
- Config tests: settings load/update, key masking
- Repository tests: history CRUD, backtest stats, pool management
- Plugin tests: discovery, validation, hot-reload
- Adapter tests: function/sync/async, MCP protocol, factory patterns
- Event/security tests: trigger validation, input sanitization

Run: `pytest tests/ -v`

## Key Patterns

- **Decorator-based registration**: `@agent`, `@skill`, `@provider`, `@register_llm`, `@adapter`
- **Strategy pattern**: Workflow builders (parallel, conditional, multi_round, adaptive)
- **Chain of Responsibility**: FallbackProvider → multiple data sources
- **Facade**: `builder.py` dispatches to strategy-specific builders
- **Factory**: `data/factory.py`, `adapters/factory.py`
- **Singleton via module-level globals**: Agent/Skill registries
- **asyncio.to_thread**: Bridging synchronous DB operations to async context