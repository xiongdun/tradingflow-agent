# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**tradingflow-agent** — An AI multi-agent stock analysis system powered by LangGraph.
Supports A-share, H-stock, and US stock markets with modular, pluggable agent architecture.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + LangGraph
- **Frontend**: React 19 + TypeScript + React Flow + Lightweight Charts + shadcn/ui
- **Data**: AKShare (A-share/H-stock) + yfinance (US stocks)
- **LLM**: Configurable (DeepSeek, OpenAI, Claude, Qwen, Ollama)

## Architecture

### Agent System (backend/agents/)
5 specialized analyst agents, each with independent personas:
- `fundamental.py` — Value investing (Buffett-style)
- `technical.py` — Chart/indicator analysis
- `sentiment.py` — Market emotion analysis
- `news.py` — Event-driven/news analysis
- `macro.py` — Macroeconomic analysis
- `summarizer.py` — Synthesizes all opinions into final report

### Skill Plugin System (backend/skills/)
Skills are registered via `@skill` decorator. Each agent can be assigned different skills.
To add a new skill: create a file in `backend/skills/`, use the `@skill` decorator.

### LangGraph Workflows (backend/graph/)
- `state.py` — Shared state with opinion merging
- `builder.py` — Builds LangGraph StateGraph from JSON definitions
- `templates/` — Pre-built workflow templates (quick_scan, deep_analysis, debate)

### Configuration (backend/core/config.py)
- `.env` file for all settings
- CLI: `python -m backend.cli config KEY VALUE`
- Web UI: `/api/config` endpoint
- All changes persisted to `.env`

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
