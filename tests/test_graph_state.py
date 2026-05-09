# tests/test_graph_state.py
# 图状态模块测试 — merge_opinions 归并器、AgentState 结构

from __future__ import annotations

import pytest


class TestMergeOpinions:
    """测试 merge_opinions 归并函数"""

    def test_empty_lists(self):
        from backend.graph.state import merge_opinions
        result = merge_opinions([], [])
        assert result == []

    def test_append_new(self):
        from backend.graph.state import merge_opinions
        existing = [{"agent_role": "fundamental", "stance": "bullish"}]
        new = [{"agent_role": "technical", "stance": "bearish"}]
        result = merge_opinions(existing, new)
        assert len(result) == 2
        assert result[0]["agent_role"] == "fundamental"
        assert result[1]["agent_role"] == "technical"

    def test_deduplicate_by_role(self):
        from backend.graph.state import merge_opinions
        existing = [{"agent_role": "fundamental", "stance": "bullish", "confidence": 0.6}]
        new = [{"agent_role": "fundamental", "stance": "bullish", "confidence": 0.8}]
        result = merge_opinions(existing, new)
        assert len(result) == 1
        # 保留第一个出现的
        assert result[0]["confidence"] == 0.6

    def test_deduplicate_by_role_and_round(self):
        from backend.graph.state import merge_opinions
        existing = [{"agent_role": "fundamental", "round": 1, "stance": "bullish"}]
        new = [{"agent_role": "fundamental", "round": 2, "stance": "bearish"}]
        result = merge_opinions(existing, new)
        assert len(result) == 2
        roles = [(r["agent_role"], r.get("round")) for r in result]
        assert ("fundamental", 1) in roles
        assert ("fundamental", 2) in roles

    def test_fallback_to_agent_name(self):
        from backend.graph.state import merge_opinions
        existing = [{"agent_name": "基本面分析师", "stance": "bullish"}]
        new = [{"agent_name": "技术面分析师", "stance": "bearish"}]
        result = merge_opinions(existing, new)
        assert len(result) == 2

    def test_multiple_new_items(self):
        from backend.graph.state import merge_opinions
        existing = [{"agent_role": "a", "stance": "bullish"}]
        new = [
            {"agent_role": "b", "stance": "bearish"},
            {"agent_role": "c", "stance": "neutral"},
        ]
        result = merge_opinions(existing, new)
        assert len(result) == 3


class TestAgentState:
    """测试 AgentState TypedDict 结构"""

    def test_state_creation(self):
        from backend.graph.state import AgentState
        state: AgentState = {
            "symbol": "600519",
            "market": "a_share",
            "opinions": [],
            "final_report": None,
            "workflow_name": "deep_analysis",
            "status": "running",
            "error": None,
            "round": 0,
            "selected_agents": [],
            "status_callback": None,
        }
        assert state["symbol"] == "600519"
        assert state["status"] == "running"
        assert state["round"] == 0
