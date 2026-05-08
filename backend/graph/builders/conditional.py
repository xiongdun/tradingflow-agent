# backend/graph/builders/conditional.py
from __future__ import annotations
from typing import Any
from langgraph.graph import END, START, StateGraph
from backend.graph.builders.common import create_agents, create_summarizer
from backend.graph.state import AgentState


def build_conditional_workflow(
    stages: list[dict[str, Any]],
    summarizer_prompt: str = "",
) -> Any:
    """构建条件分支工作流：按阶段顺序执行，每个阶段通过 gate 节点控制。

    执行流程：START → stage0_agents → gate1 → stage1_agents → summarizer → END

    stages 格式：
    [
        {"agents": ["risk"], "condition": "always"},
        {"agents": ["fundamental", "technical", "quant"], "condition": "check_risk"},
    ]
    """
    if not stages:
        raise ValueError("conditional workflow requires at least one stage")

    all_roles: list[str] = []
    for stage in stages:
        for role in stage["agents"]:
            if role not in all_roles:
                all_roles.append(role)
    llm, all_agents = create_agents(all_roles)
    summarizer = create_summarizer(llm, summarizer_prompt)

    builder = StateGraph(AgentState)
    for role, agent in all_agents.items():
        builder.add_node(role, agent.run)
    builder.add_node("summarizer", summarizer.run)

    def make_gate(condition: str, next_roles: list[str]):
        def gate_fn(state: dict) -> str | list[str]:
            if condition == "always":
                return next_roles
            if condition == "check_risk":
                opinions = state.get("opinions", [])
                for op in opinions:
                    if op.get("agent_role") == "risk":
                        stance = op.get("stance", "")
                        if stance in ("bearish", "strong_bearish"):
                            return "skip"
                return next_roles
            return next_roles
        return gate_fn

    async def gate_node(state: dict) -> dict:
        return {}

    for i in range(len(stages) - 1):
        builder.add_node(f"gate_{i}", gate_node)

    for i, stage in enumerate(stages):
        roles = stage["agents"]

        if i == 0:
            for role in roles:
                builder.add_edge(START, role)
        if i < len(stages) - 1:
            gate_name = f"gate_{i}"
            next_stage = stages[i + 1]
            next_roles = next_stage["agents"]
            condition = next_stage.get("condition", "always")
            for role in roles:
                builder.add_edge(role, gate_name)
            builder.add_conditional_edges(
                gate_name,
                make_gate(condition, next_roles),
                {role: role for role in next_roles} | {"skip": "summarizer"},
            )

    last_roles = stages[-1]["agents"]
    for role in last_roles:
        builder.add_edge(role, "summarizer")
    builder.add_edge("summarizer", END)
    return builder.compile()
