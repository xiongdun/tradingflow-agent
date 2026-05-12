# tests/test_agents.py
# Agent 注册中心测试 — 装饰器注册、查询、技能覆盖

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAgentDecorator:
    """测试 @agent 装饰器注册机制"""

    def test_register_agent(self):
        from backend.agents.base import BaseAgent, agent, _agents_registry

        @agent("测试分析师", "test_role", ["skill_a"], "测试 prompt")
        class TestAgent(BaseAgent):
            pass

        assert "test_role" in _agents_registry
        assert _agents_registry["test_role"] is TestAgent
        assert TestAgent.name == "测试分析师"
        assert TestAgent.role == "test_role"
        assert TestAgent.default_skills == ["skill_a"]
        assert TestAgent.system_prompt == "测试 prompt"

    def test_get_agent_class(self):
        from backend.agents.base import get_agent_class, agent, BaseAgent

        @agent("查询测试", "query_test")
        class QueryTestAgent(BaseAgent):
            pass

        cls = get_agent_class("query_test")
        assert cls is QueryTestAgent
        # 未知角色返回 None
        assert get_agent_class("nonexistent_role_xyz") is None

    def test_list_all_agents(self):
        from backend.agents.base import list_all_agents
        result = list_all_agents()
        assert isinstance(result, list)
        roles = [a["role"] for a in result]
        assert "fundamental" in roles or len(result) > 0


class TestAgentRegistry:
    """测试 registry.py 中的技能覆盖机制"""

    @pytest.fixture(autouse=True)
    def _ensure_agents_loaded(self):
        """确保 agent 模块已导入（测试环境不走 main.py 自动发现）"""
        from backend.core.discovery import auto_discover
        auto_discover()

    def test_get_agent_skills(self):
        from backend.agents.registry import get_agent_skills
        skills = get_agent_skills("fundamental")
        assert isinstance(skills, list)

    def test_set_agent_skills(self):
        from backend.agents.registry import set_agent_skills, get_agent_skills, reset_agent_skills
        ok = set_agent_skills("fundamental", ["custom_skill_1"])
        assert ok is True
        skills = get_agent_skills("fundamental")
        assert skills == ["custom_skill_1"]
        reset_agent_skills("fundamental")

    def test_add_remove_skill(self):
        from backend.agents.registry import add_agent_skill, remove_agent_skill, get_agent_skills, reset_agent_skills
        reset_agent_skills("technical")
        add_agent_skill("technical", "new_skill")
        skills = get_agent_skills("technical")
        assert "new_skill" in skills
        remove_agent_skill("technical", "new_skill")
        skills = get_agent_skills("technical")
        assert "new_skill" not in skills
        reset_agent_skills("technical")

    def test_unknown_role(self):
        from backend.agents.registry import set_agent_skills, get_agent_skills
        ok = set_agent_skills("nonexistent_xyz", ["skill"])
        assert ok is False
        skills = get_agent_skills("nonexistent_xyz")
        assert skills == []


# ═══════════════════════════════════════════════════════
#  安全/稳定性测试 — Skill None → {}, confidence 容错
# ═══════════════════════════════════════════════════════

class TestAgentSkillSafety:
    """测试 Agent 技能执行时的安全防护"""

    @pytest.fixture(autouse=True)
    def _ensure_agents_loaded(self):
        from backend.core.discovery import auto_discover
        auto_discover()

    @pytest.mark.asyncio
    async def test_skill_none_result_converted_to_empty_dict(self):
        """技能返回 None 时应被安全转换为 {}，避免下游格式化崩溃"""
        from backend.agents.base import BaseAgent

        agent = BaseAgent.__new__(BaseAgent)
        agent.name = "TestAgent"
        agent.role = "test_role"
        agent.llm = AsyncMock()
        agent.prompt_template = ""
        agent.extra_prompt = ""

        mock_skill = MagicMock()
        mock_skill.name = "test_skill"
        mock_skill.depends_on = []
        mock_skill.execute.return_value = None
        agent._skill_metas = [mock_skill]

        results = await agent._execute_skills("600519", "a_share")
        assert results == {"test_skill": {}}

    @pytest.mark.asyncio
    async def test_skill_result_is_none_after_error(self):
        """技能执行异常时应返回 {"error": "..."}而非 None"""
        from backend.agents.base import BaseAgent

        agent = BaseAgent.__new__(BaseAgent)
        agent.name = "TestAgent"
        agent.role = "test_role"
        agent.llm = AsyncMock()
        agent.prompt_template = ""
        agent.extra_prompt = ""

        mock_skill = MagicMock()
        mock_skill.name = "failing_skill"
        mock_skill.depends_on = []
        mock_skill.execute.side_effect = ConnectionError("网络不可达")
        agent._skill_metas = [mock_skill]

        results = await agent._execute_skills("600519", "a_share")
        assert "failing_skill" in results
        assert isinstance(results["failing_skill"], dict)
        assert "error" in results["failing_skill"]

    @pytest.mark.asyncio
    async def test_skill_mixed_none_and_valid_results(self):
        """混合场景：一个技能返回 None，另一个返回有效数据"""
        from backend.agents.base import BaseAgent

        agent = BaseAgent.__new__(BaseAgent)
        agent.name = "TestAgent"
        agent.role = "test_role"
        agent.llm = AsyncMock()
        agent.prompt_template = ""
        agent.extra_prompt = ""

        valid_skill = MagicMock()
        valid_skill.name = "valid_skill"
        valid_skill.depends_on = []
        valid_skill.execute.return_value = {"data": [1, 2, 3]}

        none_skill = MagicMock()
        none_skill.name = "none_skill"
        none_skill.depends_on = []
        none_skill.execute.return_value = None

        agent._skill_metas = [valid_skill, none_skill]

        results = await agent._execute_skills("600519", "a_share")
        assert results["valid_skill"] == {"data": [1, 2, 3]}
        assert results["none_skill"] == {}


# ═══════════════════════════════════════════════════════
#  confidence 解析容错测试
# ═══════════════════════════════════════════════════════

CONFIDENCE_TEST_DATA = [
    pytest.param('{"stance": "bullish", "confidence": "", "key_points": ["a"], "risk_factors": ["b"], "summary": "ok"}', 0.5, id="empty_string→0.5"),
    pytest.param('{"stance": "bullish", "confidence": "invalid", "key_points": ["a"], "risk_factors": ["b"], "summary": "ok"}', 0.5, id="non_numeric→0.5"),
    pytest.param('{"stance": "bullish", "confidence": 0.95, "key_points": ["a"], "risk_factors": ["b"], "summary": "ok"}', 0.95, id="numeric_float→0.95"),
    pytest.param('{"stance": "bullish", "confidence": 0, "key_points": ["a"], "risk_factors": ["b"], "summary": "ok"}', 0.0, id="zero→0.0"),
    pytest.param('{"stance": "bullish", "confidence": 1.0, "key_points": ["a"], "risk_factors": ["b"], "summary": "ok"}', 1.0, id="one→1.0"),
    pytest.param('{"stance": "bullish", "key_points": ["a"], "risk_factors": ["b"], "summary": "ok"}', 0.5, id="missing_field→0.5"),
]


class TestConfidenceParsing:
    """测试 _parse_opinion 中 confidence 字段的安全解析"""

    @pytest.mark.parametrize("content,expected", CONFIDENCE_TEST_DATA)
    def test_confidence_float_parsing(self, content, expected):
        """各种异常 confidence 值不应导致 float() 崩溃"""
        from backend.agents.base import _parse_opinion, AgentOpinion

        opinion = _parse_opinion(content, "Test", "test_role", "600519", "a_share", {})
        assert isinstance(opinion, AgentOpinion)
        assert opinion.confidence == expected

    def test_confidence_boolean_true_crashes_safe(self):
        """confidence 意外为 JSON 布尔 true 时 float() 返回 1.0，不崩溃"""
        from backend.agents.base import _parse_opinion, AgentOpinion

        opinion = _parse_opinion(
            '{"stance": "bullish", "confidence": true, "key_points": ["a"], "risk_factors": ["b"], "summary": "ok"}',
            "Test", "test_role", "600519", "a_share", {},
        )
        assert isinstance(opinion, AgentOpinion)
        assert opinion.confidence == 1.0


# ═══════════════════════════════════════════════════════
#  Summarizer None opinions 安全测试
# ═══════════════════════════════════════════════════════

class TestSummarizerSafety:
    """测试 Summarizer 对 None opinions 的防护"""

    def test_summarize_none_opinions_no_crash(self):
        """传入 None 不应崩溃，应返回空字符串或占位报告"""
        from backend.agents.summarizer import SummarizerAgent

        s = SummarizerAgent.__new__(SummarizerAgent)
        s.name = "Test"
        s.role = "summarizer"
        s.extra_prompt = ""
        s.llm = MagicMock()
        s.llm.ainvoke = AsyncMock()
        s.llm.ainvoke.return_value = MagicMock()
        s.llm.ainvoke.return_value.content = '{"overall_stance":"neutral","overall_confidence":0.5,"consensus_points":[],"disagreement_points":[],"key_risks":[],"opportunities":[],"action_suggestion":"hold","summary":"ok"}'

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            s.summarize("600519", "a_share", None)
        )
        assert result is not None

    def test_summarize_empty_opinions_no_crash(self):
        """传入空列表不应崩溃"""
        from backend.agents.summarizer import SummarizerAgent

        s = SummarizerAgent.__new__(SummarizerAgent)
        s.name = "Test"
        s.role = "summarizer"
        s.extra_prompt = ""
        s.llm = MagicMock()
        s.llm.ainvoke = AsyncMock()
        s.llm.ainvoke.return_value = MagicMock()
        s.llm.ainvoke.return_value.content = '{"overall_stance":"neutral","overall_confidence":0.5,"consensus_points":[],"disagreement_points":[],"key_risks":[],"opportunities":[],"action_suggestion":"hold","summary":"ok"}'

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            s.summarize("600519", "a_share", [])
        )
        assert result is not None
