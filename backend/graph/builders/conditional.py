# backend/graph/builders/conditional.py
from __future__ import annotations
from typing import Any
from langgraph.graph import END, START, StateGraph
from backend.agents.base import BaseAgent
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
        def gate_fn(state: dict) -> str:
            if condition == "always":
                return "continue"
            if condition == "check_risk":
                opinions = state.get("opinions", [])
                for op in opinions:
                    if op.get("agent_role") == "risk":
                        stance = op.get("stance", "")
                        if stance in ("bearish", "strong_bearish"):
                            return "skip"
                return "continue"
            return "continue"
        return gate_fn

    for i, stage in enumerate(stages):
        roles = stage["agents"]
        condition = stage.get("condition", "always")

        if i == 0:
            for role in roles:
                builder.add_edge(START, role)
        else:
            gate_fn = make_gate(condition, roles)
            builder.add_conditional_edges(
                stages[i - 1]["agents"][-1],
                gate_fn,
                {role: role for role in roles} | {"skip": "summarizer"},
            )
            for prev_role in stages[i - 1]["agents"][:-1]:
                builder.add_edge(prev_role, roles[0])

    last_roles = stages[-1]["agents"]
    for role in last_roles:
        builder.add_edge(role, "summarizer")
    builder.add_edge("summarizer", END)
    return builder.compile()
