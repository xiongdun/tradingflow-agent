# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

**tradingflow-agent** — An AI multi-agent stock analysis system powered by LangGraph.
Supports A-share, H-stock, and US stock markets with modular, pluggable agent architecture.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + LangGraph
- **Frontend**: React 19 + TypeScript + React Flow + Lightweight Charts + shadcn/ui
- **Data**: AKShare (A-share/H-stock) + yfinance (US stocks)
- **LLM**: Configurable (DeepSeek, OpenAI, Codex, Qwen, Mimo, Ollama)

## Architecture

### Agent System (backend/agents/) — 11 agents
10+ specialized analyst agents, each with independent personas:
- `base.py` — BaseAgent: 4-step lifecycle (skill exec → LLM inference → structured output → LangGraph node)
- `registry.py` — `@agent` decorator registration + runtime skill management
- `fundamental.py` — Value investing (Buffett-style)
- `technical.py` — Chart/indicator analysis
- `sentiment.py` — Market emotion analysis
- `news.py` — Event-driven/news analysis
- `macro.py` — Macroeconomic analysis
- `hot_money.py` — Short-term speculation analysis
- `quant.py` — Quantitative/data-driven analysis
- `risk.py` — Risk assessment
- `sector_rotation.py` — Sector rotation analysis
- `trading.py` — Trading strategy (buy/sell decisions)
- `generic.py` — GenericAgent for custom analyst roles
- `summarizer.py` — Synthesizes all opinions into final report

### Skill Plugin System (backend/skills/) — 19 skills
Skills are registered via `@skill` decorator. Each agent can be assigned different skills.
Supports dependency topology (`depends_on`) for automatic parallel scheduling.
To add a new skill: create a file in `backend/skills/`, use the `@skill` decorator.

### V2 Workflow System (backend/graph/)
- `state.py` — Shared state with opinion merging
- `builder.py` — Facade dispatching to strategy builders (v1/v2 validation)
- `builders/` — Strategy pattern: parallel, conditional, multi_round, adaptive
- `templates/` — 7 pre-built templates (quick_scan, deep_analysis, debate, debate_v2, full_spectrum, risk_first, quant_hybrid)
- V2 nodes: condition (gate routing), loop (counter iteration), event triggers, adapters

### Adapter & Plugin Systems
- `backend/adapters/` — Pluggable adapters with `@adapter` decorator (function async/sync, MCP protocol)
- `backend/plugins/` — Runtime plugin discovery, hot-reload, dependency validation

### Data Layer (backend/data/)
- `provider.py` — Abstract DataProvider base + `@provider` decorator registry
- `factory.py` — Provider factory with multi-source fallback + TTL cache wrapping
- `fallback_provider.py` — Chain-of-responsibility fallback across multiple sources (configurable retry)

### Configuration (backend/core/)
- `config.py` — 20+ config fields in Pydantic Settings (.env loaded)
  - LLM: provider, model, api_key, base_url, temperature, max_tokens
  - Timeouts: skill_timeout, llm_timeout, analysis_timeout
  - Retry: fallback_retry_max/wait_min/wait_max
  - Budget: max_agents_per_analysis
  - Adaptive thresholds: adaptive_large_cap, adaptive_small_cap, adaptive_high_turnover
- `config_writer.py` — Persists changes to `.env`
- `llm.py` — LLM factory with `@register_llm` decorator registry
- `cache.py` — Thread-safe disk TTL cache
- `database.py` — SQLite connection pool with WAL mode
- `analysis_service.py` — Unified analysis service
- `discovery.py` — `auto_discover()` scans and registers all modules
- `skill_manager.py` — Runtime skill orchestration
- `.env.example` — Annotated with Chinese comments explaining each field

### Frontend (frontend/src/)
- **App.tsx** — Root with onboarding modal (first-visit detection via localStorage), 6-tab navigation
- **ControlBar.tsx** — Stock input with placeholder, market selector (emoji flags), quick stock buttons (茅台/比亚迪/腾讯/Apple)
- **WorkflowEditor/** — React Flow canvas with 12 node types (Agent, Skill, Trading, Summarizer, Condition, Loop, EventTrigger, Adapter, Config, Input) + Sidebar (Skills default expanded)
- **Analysis/** — ReportView + AgentRadarChart (React.memo) + StancePieChart (React.memo)
- **Settings/** — 5 panels: General, LLM, Agent, Skill, Settings
- **History/**, **Watchlist/**, **Schedule/** panels
- **TradingView/Chart.tsx** — Lightweight Charts candlestick with agent markers
- **store/workflowStore.ts** — Zustand global state
- **hooks/useWebSocket.ts** — WebSocket with exponential backoff reconnection
- **i18n/** — Chinese/English language support
- **common/Toast.tsx** — Toast notification system

## Development

### Quick Start
```bash
# One-click (Windows):
双击 setup.bat  →  按提示配置  →  双击 run.bat

# One-click (Linux/macOS):
bash setup.sh && bash run.sh

# Manual:
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your LLM API key

# Demo (zero config, no API key needed):
python -m backend.cli demo

# Analyze:
python -m backend.cli analyze 600519 --market a_share --workflow deep_analysis

# Search stock codes:
python -m backend.cli search 茅台

# List skills/agents:
python -m backend.cli skills
python -m backend.cli agents-list

# API Server:
python -m backend.cli serve

# Frontend (new terminal):
cd frontend && npm install && npm run dev
```

### Commands
- `tradingflow demo` — Zero-config demo report
- `tradingflow analyze <symbol>` — Run stock analysis (with Chinese error guidance)
- `tradingflow search <keyword>` — Search stock codes
- `tradingflow config [KEY] [VALUE]` — View/update configuration
- `tradingflow skills` — List available skills
- `tradingflow agents-list` — List available agents
- `tradingflow serve` — Start web API server

### Testing
289 tests across 25+ files: `pytest tests/ -v`

### Error Handling & Stability
- Data layer: FallbackProvider safe empty value fallback on all-provider failure
- Agent layer: Dual timeout + None→{} conversion + confidence parse safety
- Graph layer: multi_round max round cap + conditional gate type guards
- Storage: auto-rollback on exception with connection pool return
- API: correct HTTP status codes (404/500) + WebSocket error logging
- Frontend: null safety guards on all node data accesses

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