# tests/test_agent_models.py
# Agent 数据模型测试 — AgentOpinion Pydantic 验证

from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestAgentOpinion:
    """测试 AgentOpinion Pydantic 模型"""

    def test_valid_opinion(self):
        from backend.agents.models import AgentOpinion
        op = AgentOpinion(
            agent_name="基本面分析师",
            agent_role="fundamental",
            stock="600519",
            market="a_share",
            stance="bullish",
            confidence=0.85,
            key_points=["ROE 高", "现金流好"],
            risk_factors=["政策风险"],
            summary="基本面优秀",
        )
        assert op.agent_name == "基本面分析师"
        assert op.confidence == 0.85
        assert op.data_evidence == {}

    def test_default_data_evidence(self):
        from backend.agents.models import AgentOpinion
        op = AgentOpinion(
            agent_name="test",
            agent_role="test",
            stock="TEST",
            market="a_share",
            stance="neutral",
            confidence=0.5,
            key_points=[],
            risk_factors=[],
            summary="test",
        )
        assert op.data_evidence == {}

    def test_missing_required_field(self):
        from backend.agents.models import AgentOpinion
        with pytest.raises(ValidationError):
            AgentOpinion(
                agent_name="test",
                # missing agent_role
                stock="TEST",
                market="a_share",
                stance="neutral",
                confidence=0.5,
                key_points=[],
                risk_factors=[],
                summary="test",
            )

    def test_confidence_range(self):
        from backend.agents.models import AgentOpinion
        # Pydantic 不会自动限制 float 范围，但模型应接受边界值
        op = AgentOpinion(
            agent_name="test",
            agent_role="test",
            stock="TEST",
            market="a_share",
            stance="neutral",
            confidence=0.0,
            key_points=[],
            risk_factors=[],
            summary="test",
        )
        assert op.confidence == 0.0

        op2 = AgentOpinion(
            agent_name="test",
            agent_role="test",
            stock="TEST",
            market="a_share",
            stance="neutral",
            confidence=1.0,
            key_points=[],
            risk_factors=[],
            summary="test",
        )
        assert op2.confidence == 1.0

    def test_to_dict_conversion(self):
        from backend.agents.models import AgentOpinion
        op = AgentOpinion(
            agent_name="技术面分析师",
            agent_role="technical",
            stock="AAPL",
            market="us_stock",
            stance="bearish",
            confidence=0.7,
            key_points=["跌破均线"],
            risk_factors=["大盘走弱"],
            summary="技术面偏空",
            data_evidence={"ma20": 150.0},
        )
        d = op.model_dump()
        assert d["agent_name"] == "技术面分析师"
        assert d["data_evidence"] == {"ma20": 150.0}
