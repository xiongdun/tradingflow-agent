# backend/graph/builders/common.py
from __future__ import annotations
from typing import Any
from langgraph.graph import StateGraph
from backend.agents.base import BaseAgent
from backend.agents.summarizer import SummarizerAgent
from backend.core.config import load_settings
from backend.core.llm import create_llm
from backend.agents.registry import get_agent_class, get_agent_skills
from backend.graph.state import AgentState


def create_agents(
    agent_roles: list[str],
    extra_prompts: dict[str, str] | None = None,
    agent_skills: dict[str, list[str]] | None = None,
    agent_names: dict[str, str] | None = None,
    system_prompts: dict[str, str] | None = None,
) -> tuple[Any, dict[str, BaseAgent]]:
    """创建 LLM 实例和所有分析师 Agent，返回 (llm, agents_dict)"""
    settings = load_settings()
    llm = create_llm(settings)
    extra_prompts = extra_prompts or {}
    agent_names = agent_names or {}
    system_prompts = system_prompts or {}

    agents: dict[str, BaseAgent] = {}
    for role in agent_roles:
        cls = get_agent_class(role)
        from backend.agents.generic import GenericAgent
        if cls is None and role.startswith("custom_"):
            cls = GenericAgent
        if cls is None:
            raise ValueError(f"Unknown agent role: {role}")
        skills = (
            agent_skills.get(role)
            if agent_skills and role in agent_skills
            else get_agent_skills(role)
        )
        if cls is GenericAgent:
            agents[role] = cls(llm=llm, skills=skills, extra_prompt=extra_prompts.get(role, ""), role=role, name=agent_names.get(role, ""))
        else:
            agents[role] = cls(llm=llm, skills=skills, extra_prompt=extra_prompts.get(role, ""))
        if role in system_prompts:
            agents[role].system_prompt = system_prompts[role]
    return llm, agents


def create_summarizer(llm: Any, summarizer_prompt: str = "") -> SummarizerAgent:
    return SummarizerAgent(llm=llm, extra_prompt=summarizer_prompt)


def create_base_workflow(
    agent_roles: list[str],
    summarizer_prompt: str = "",
    **kwargs: Any,
) -> tuple[Any, dict[str, BaseAgent], SummarizerAgent]:
    """创建 LLM、分析师 Agents 和 Summarizer，返回 (llm, agents, summarizer)"""
    llm, agents = create_agents(agent_roles, **kwargs)
    summarizer = create_summarizer(llm, summarizer_prompt)
    return llm, agents, summarizer


def create_base_graph(
    agent_roles: list[str],
    summarizer_prompt: str = "",
    state_class: type = AgentState,
    **agent_kwargs: Any,
) -> tuple[Any, dict[str, BaseAgent], SummarizerAgent, StateGraph]:
    """创建完整的 StateGraph 基础结构：LLM + Agents + Summarizer + StateGraph。

    各 builder 只需在此基础上添加自己的拓扑逻辑（边、条件分支等）。
    返回 (llm, agents, summarizer, builder)
    """
    llm, agents = create_agents(agent_roles, **agent_kwargs)
    summarizer = create_summarizer(llm, summarizer_prompt)

    from langgraph.graph import StateGraph

    builder: StateGraph = StateGraph(state_class)
    for role, agent in agents.items():
        builder.add_node(role, agent.run)
    builder.add_node("summarizer", summarizer.run)

    return llm, agents, summarizer, builder
