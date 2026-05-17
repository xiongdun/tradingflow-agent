# backend/graph/builders/adaptive.py
from __future__ import annotations
from typing import Any
from langgraph.graph import END, START, StateGraph
from backend.agents.base import BaseAgent
from backend.graph.builders.common import create_agents, create_summarizer
from backend.graph.state import AgentState


def build_adaptive_workflow(
    summarizer_prompt: str = "",
) -> Any:
    """构建自适应工作流：根据股票特征动态选择分析师组合。

    执行流程：START → selector → [所有分析师(带过滤)] → summarizer → END
    """
    all_roles = [
        "fundamental", "technical", "sentiment", "news",
        "macro", "hot_money", "sector_rotation", "quant", "risk",
    ]
    llm, agents = create_agents(all_roles)
    summarizer = create_summarizer(llm, summarizer_prompt)

    filtered_agents: dict[str, Any] = {}
    for role, agent in agents.items():
        def make_filtered_node(r: str, a: BaseAgent):
            async def filtered_node(state: dict) -> dict:
                selected = state.get("selected_agents", [])
                if r not in selected:
                    return {}
                return await a.run(state)
            return filtered_node

        filtered_agents[role] = make_filtered_node(role, agent)

    async def selector_node(state: dict) -> dict:
        symbol = state.get("symbol", "")
        market = state.get("market", "a_share")
        selected = ["fundamental", "technical", "sentiment"]

        if market == "a_share":
            try:
                from backend.data.factory import get_provider
                from backend.core.config import load_settings
                cfg = load_settings()
                provider = get_provider(market)
                info = provider.get_stock_info(symbol)
                if info:
                    info_dict: dict[str, Any] = info.model_dump() if hasattr(info, "model_dump") else dict(info)
                    market_cap = info_dict.get("market_cap", 0) or 0
                    turnover = info_dict.get("turnover_rate", 0) or 0
                    industry = info_dict.get("industry", "") or ""

                    if market_cap > cfg.adaptive_large_cap:
                        selected = ["fundamental", "macro", "quant", "risk"]
                    elif market_cap < cfg.adaptive_small_cap and turnover > cfg.adaptive_high_turnover:
                        selected = ["hot_money", "sentiment", "news", "risk"]
                    elif any(kw in industry for kw in ["科技", "电子", "计算机", "半导体", "软件"]):
                        selected = ["technical", "fundamental", "news", "quant"]
                    else:
                        selected = ["fundamental", "technical", "sentiment", "risk"]
            except Exception:
                from loguru import logger
                logger.warning(f"[adaptive] Failed to get stock info for {symbol}, using default agent set")
                selected = ["fundamental", "technical", "sentiment", "risk"]

        return {"selected_agents": selected}

    builder = StateGraph(AgentState)
    builder.add_node("selector", selector_node)  # type: ignore[type-var]
    for role, node_fn in filtered_agents.items():
        builder.add_node(role, node_fn)  # type: ignore[type-var]
    builder.add_node("summarizer", summarizer.run)  # type: ignore[type-var]

    builder.add_edge(START, "selector")
    for role in filtered_agents:
        builder.add_edge("selector", role)
    for role in filtered_agents:
        builder.add_edge(role, "summarizer")
    builder.add_edge("summarizer", END)
    return builder.compile()
