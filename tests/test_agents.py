# tests/test_agents.py
# Agent 注册中心测试 — 装饰器注册、查询、技能覆盖

from __future__ import annotations

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
