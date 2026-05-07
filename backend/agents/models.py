# backend/agents/models.py
# Agent 数据模型 — AgentOpinion 结构化输出

from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class AgentOpinion(BaseModel):
    """分析师 Agent 的结构化输出"""
    agent_name: str
    agent_role: str
    stock: str
    market: str
    stance: str               # bullish/bearish/neutral
    confidence: float         # 0.0 ~ 1.0
    key_points: list[str]
    risk_factors: list[str]
    summary: str
    data_evidence: dict[str, Any] = {}
