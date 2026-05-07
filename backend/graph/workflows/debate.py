# backend/graph/workflows/debate.py
# 辩论模式工作流 — 多头 vs 空头结构化对抗辩论

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from backend.agents.base import BaseAgent
from backend.agents.summarizer import SummarizerAgent
from backend.core.config import load_settings
from backend.core.llm import create_llm
from backend.agents.registry import get_agent_class, get_agent_skills
from backend.graph.state import AgentState


def build_debate_workflow(
    agent_roles: list[str] | None = None,
) -> Any:
    """构建辩论工作流：多头律师与空头律师轮流交锋，最终由总结分析师裁决。

    执行流程：
    START → [分析师们并行] → 多头论据 → 空头反驳 → 多头回应 → 总结研判 → END
    """
    if agent_roles is None:
        agent_roles = ["fundamental", "technical", "sentiment", "hot_money"]

    settings = load_settings()
    llm = create_llm(settings)

    # 创建各领域分析师
    analysts: dict[str, BaseAgent] = {}
    for role in agent_roles:
        cls = get_agent_class(role)
        if cls:
            analysts[role] = cls(llm=llm, skills=get_agent_skills(role))

    # 多头律师提示词：提取看多论据，反驳空头质疑
    bull_prompt = """你是一个坚定的多头辩护律师。你的任务是：
1. 从所有分析师的意见中，提取支持看多的论据
2. 用最强有力的逻辑组织这些论据
3. 针对空头的质疑进行有力反驳
你要有激情、有逻辑、有数据支撑。但也要诚实——如果确实有重大风险，要承认。"""

    # 空头律师提示词：提取看空论据，逐条反驳多头
    bear_prompt = """你是一个坚定的空头辩护律师。你的任务是：
1. 从所有分析师的意见中，提取支持看空的论据
2. 对多头的论据进行逐条质疑和反驳
3. 指出被忽视的风险和隐患
你要犀利、要专业、要一针见血。你的目标是帮助投资者看清风险。"""

    summarizer = SummarizerAgent(llm=llm)

    async def bull_node(state: dict) -> dict:
        """多头律师节点：汇总分析师意见，生成看多论据"""
        opinions = state.get("opinions", [])
        opinions_text = "\n".join(
            f"- {op.get('agent_name', '')}: {op.get('stance', '')} - {op.get('summary', '')}"
            for op in opinions
        )
        response = await llm.ainvoke([
            SystemMessage(content=bull_prompt),
            HumanMessage(content=f"以下是各分析师的意见：\n{opinions_text}\n\n请给出你的多头论据。"),
        ])
        return {"bull_argument": response.content}

    async def bear_node(state: dict) -> dict:
        """空头律师节点：针对多头论据和分析师意见，生成空头反驳"""
        opinions = state.get("opinions", [])
        opinions_text = "\n".join(
            f"- {op.get('agent_name', '')}: {op.get('stance', '')} - {op.get('summary', '')}"
            for op in opinions
        )
        bull_arg = state.get("bull_argument", "")
        response = await llm.ainvoke([
            SystemMessage(content=bear_prompt),
            HumanMessage(content=f"以下是各分析师的意见：\n{opinions_text}\n\n多头论据：\n{bull_arg}\n\n请给出你的空头反驳。"),
        ])
        return {"bear_argument": response.content}

    async def bull_rebuttal_node(state: dict) -> dict:
        """多头回应节点：针对空头反驳进行最终辩护"""
        bear_arg = state.get("bear_argument", "")
        response = await llm.ainvoke([
            SystemMessage(content=bull_prompt),
            HumanMessage(content=f"空头的反驳：\n{bear_arg}\n\n请回应这些质疑，维护你的多头观点。"),
        ])
        return {"bull_rebuttal": response.content}

    async def summarizer_node(state: dict) -> dict:
        """总结研判节点：综合分析师意见和辩论结果，生成最终报告"""
        # 将辩论双方观点封装为 AgentOpinion 格式
        debate_context = {
            "agent_name": "多头律师",
            "agent_role": "bull",
            "stock": state["symbol"],
            "market": state["market"],
            "stance": "bullish",
            "confidence": 0.7,
            "key_points": [state.get("bull_argument", "")[:300]],
            "risk_factors": [],
            "summary": state.get("bull_rebuttal", "")[:500],
            "data_evidence": {},
        }
        bear_opinion = {
            "agent_name": "空头律师",
            "agent_role": "bear",
            "stock": state["symbol"],
            "market": state["market"],
            "stance": "bearish",
            "confidence": 0.7,
            "key_points": [state.get("bear_argument", "")[:300]],
            "risk_factors": [],
            "summary": state.get("bear_argument", "")[:500],
            "data_evidence": {},
        }
        # 合并分析师原始意见和辩论观点
        all_opinions = state.get("opinions", []) + [debate_context, bear_opinion]
        report = await summarizer.summarize(state["symbol"], state["market"], all_opinions)
        return {"final_report": report.model_dump()}

    # 构建辩论状态图（扩展 AgentState，增加辩论字段）
    class DebateState(AgentState):
        bull_argument: str      # 多头论据
        bear_argument: str      # 空头反驳
        bull_rebuttal: str      # 多头回应

    builder = StateGraph(DebateState)

    # 添加分析师节点（并行执行）
    for role, agent in analysts.items():
        builder.add_node(role, agent.run)
        builder.add_edge(START, role)

    # 添加辩论节点
    builder.add_node("bull", bull_node)
    builder.add_node("bear", bear_node)
    builder.add_node("bull_rebuttal", bull_rebuttal_node)
    builder.add_node("summarizer", summarizer_node)

    # 分析师 → 多头论据 → 空头反驳 → 多头回应 → 总结
    for role in analysts:
        builder.add_edge(role, "bull")

    builder.add_edge("bull", "bear")
    builder.add_edge("bear", "bull_rebuttal")
    builder.add_edge("bull_rebuttal", "summarizer")
    builder.add_edge("summarizer", END)

    return builder.compile()
