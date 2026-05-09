# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**tradingflow-agent** — An AI multi-agent stock analysis system powered by LangGraph.
Supports A-share, H-stock, and US stock markets with modular, pluggable agent architecture.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + LangGraph + LangChain
- **Frontend**: React 19 + TypeScript + React Flow + Lightweight Charts + Zustand
- **Data**: AKShare (A-share/H-stock) + yfinance (US stocks) + efinance/baostock (fallback)
- **LLM**: Configurable (DeepSeek, OpenAI, Claude, Qwen, Ollama)

## Architecture

### Agent System (backend/agents/)
10+ specialized analyst agents, each with independent personas:
- `fundamental.py` — Value investing (Buffett-style)
- `technical.py` — Chart/indicator analysis
- `sentiment.py` — Market emotion analysis
- `news.py` — Event-driven/news analysis
- `macro.py` — Macroeconomic analysis
- `hot_money.py` — Short-term speculation analysis
- `quant.py` — Quantitative/data-driven analysis
- `risk.py` — Risk assessment
- `sector_rotation.py` — Sector rotation analysis
- `summarizer.py` — Synthesizes all opinions into final report

Base class at `base.py` defines the 4-step lifecycle: skill execution → LLM inference → structured output → LangGraph integration.

### Skill Plugin System (backend/skills/)
Skills are registered via `@skill` decorator. Each agent can be assigned different skills.
To add a new skill: create a file in `backend/skills/`, use the `@skill` decorator.
Supports dependency topology (`depends_on`) for automatic parallel scheduling.

### LangGraph Workflows (backend/graph/)
- `state.py` — Shared state with opinion merging (merge_opinions reducer)
- `builder.py` — Facade that dispatches to strategy builders based on mode
- `builders/` — Strategy pattern implementations:
  - `parallel.py` — All agents execute simultaneously
  - `conditional.py` — Stage-gated conditional execution
  - `multi_round.py` — Multi-round iteration with cross-review
  - `adaptive.py` — Dynamic agent selection based on stock characteristics
- `templates/` — Pre-built workflow templates (quick_scan, deep_analysis, debate, debate_v2, full_spectrum, risk_first)

### Data Layer (backend/data/)
- `provider.py` — Abstract DataProvider base + `@provider` decorator registry
- `factory.py` — Provider factory with multi-source fallback + TTL cache wrapping
- `fallback_provider.py` — Chain-of-responsibility fallback across multiple sources
- `akshare_provider.py`, `yfinance_provider.py`, `efinance_provider.py`, `baostock_provider.py`

### Configuration (backend/core/config.py)
- `.env` file for all settings
- CLI: `python -m backend.cli config KEY VALUE`
- Web UI: `/api/config` endpoint
- All changes persisted to `.env`

### Frontend Architecture (frontend/src/)
- **App.tsx** — Root component with tab navigation (workflow/report/history/watchlist/schedule)
- **WorkflowEditor/** — React Flow canvas with draggable nodes, resizable panels, connection rules
- **TradingView/Chart.tsx** — Lightweight Charts candlestick with agent marker overlays
- **Analysis/ReportView.tsx** — Markdown report + SVG radar/pie charts + export bar
- **store/workflowStore.ts** — Zustand global state (nodes, edges, analysis progress, opinions)
- **hooks/useWebSocket.ts** — WebSocket connection with exponential backoff reconnection
- **hooks/useTheme.ts** — Dark/light theme with localStorage persistence
- **i18n/** — Lightweight i18n system (zh/en) loaded from backend config

## Development

### Quick Start
```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your LLM API key

# CLI
python -m backend.cli analyze 600519 --market a_share --workflow deep_analysis
python -m backend.cli skills
python -m backend.cli agents-list
python -m backend.cli config --show

# API Server
python -m backend.cli serve

# Frontend (new terminal)
cd frontend && npm install && npm run dev
```

### Commands
- `tradingflow analyze <symbol>` — Run stock analysis
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

4. **ReportView SVG charts** — Radar and pie charts are re-rendered on every store update. They should be wrapped in React.memo or extracted to pure components.

5. **Inline styles** — The codebase heavily uses inline `style` props. This is fine for this project's scale but prevents CSS-level optimizations like `content-visibility`.
