# backend/graph/builders/parallel.py
from __future__ import annotations
from typing import Any
from langgraph.graph import END, START
from backend.graph.builders.common import create_base_graph


def build_parallel_workflow(
    agent_roles: list[str],
    extra_prompts: dict[str, str] | None = None,
    summarizer_prompt: str = "",
    agent_skills: dict[str, list[str]] | None = None,
    agent_names: dict[str, str] | None = None,
    system_prompts: dict[str, str] | None = None,
) -> Any:
    """构建并行分析工作流：所有分析师并行执行，汇总到总结分析师。

    执行流程：START → [分析师1, 分析师2, ...]（并行） → summarizer → END
    """
    _, agents, _, builder = create_base_graph(
        agent_roles, summarizer_prompt,
        extra_prompts=extra_prompts or {},
        agent_skills=agent_skills,
        agent_names=agent_names or {},
        system_prompts=system_prompts or {},
    )
    for role in agents:
        builder.add_edge(START, role)
    for role in agents:
        builder.add_edge(role, "summarizer")
    builder.add_edge("summarizer", END)
    return builder.compile()
