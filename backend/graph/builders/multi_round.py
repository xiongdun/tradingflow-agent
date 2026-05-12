# backend/graph/builders/multi_round.py
from __future__ import annotations
from typing import Any
from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage
from backend.graph.builders.common import create_agents, create_summarizer
from backend.graph.state import AgentState


def build_multi_round_workflow(
    agent_roles: list[str],
    rounds: int = 2,
    summarizer_prompt: str = "",
) -> Any:
    """构建多轮迭代工作流：分析师多轮执行，每轮后交叉审阅修正意见。

    START → fan_out → [分析师们并行] → cross_review → (loop or summarizer) → END
    """
    llm, agents = create_agents(agent_roles)
    summarizer = create_summarizer(llm, summarizer_prompt)

    cross_review_prompt = """你是交叉审阅员。以下是各分析师上一轮的意见：
{opinions_text}

请指出各分析师意见中的：
1. 逻辑矛盾或不一致之处
2. 被忽视的重要信息
3. 需要修正或补充的论点

输出简洁的审阅意见，供分析师下一轮参考。"""

    async def cross_review_node(state: dict) -> dict:
        opinions = state.get("opinions", [])
        latest_round = max((op.get("round", 0) for op in opinions), default=0)
        opinions = [op for op in opinions if op.get("round", 0) == latest_round]
        opinions_text = "\n".join(
            f"- {op.get('agent_name', '')} ({op.get('stance', '')}): {op.get('summary', '')[:200]}"
            for op in opinions
        )
        response = await llm.ainvoke([
            SystemMessage(content=cross_review_prompt.format(opinions_text=opinions_text)),
            HumanMessage(content="请给出交叉审阅意见。"),
        ])
        current_round = state.get("round", 0)
        return {"cross_review": response.content, "round": current_round + 1}

    async def fan_out_node(state: dict) -> dict:
        return {}

    class MultiRoundState(AgentState):
        cross_review: str

    builder = StateGraph(MultiRoundState)
    builder.add_node("fan_out", fan_out_node)
    for role, agent in agents.items():
        builder.add_node(role, agent.run)
    builder.add_node("cross_review", cross_review_node)
    builder.add_node("summarizer", summarizer.run)

    builder.add_edge(START, "fan_out")
    for role in agents:
        builder.add_edge("fan_out", role)
    for role in agents:
        builder.add_edge(role, "cross_review")

    def round_router(state: dict) -> str:
        current = max(state.get("round", 1), 1)
        max_rounds = min(rounds, 10)
        if current < max_rounds:
            return "fan_out"
        return "summarizer"

    builder.add_conditional_edges(
        "cross_review",
        round_router,
        {"fan_out": "fan_out", "summarizer": "summarizer"},
    )
    builder.add_edge("summarizer", END)
    return builder.compile()
