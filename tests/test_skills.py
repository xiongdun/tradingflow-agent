# tests/test_skills.py
# 技能注册中心测试 — 注册、查询、过滤

from __future__ import annotations

import pytest


class TestSkillRegistry:
    def test_register_and_get(self):
        from backend.skills.registry import skill, get_skill

        @skill(name="test_skill_1", description="测试技能", category="test")
        def my_skill(symbol: str, market: str) -> dict:
            return {"ok": True}

        meta = get_skill("test_skill_1")
        assert meta is not None
        assert meta.name == "test_skill_1"
        assert meta.description == "测试技能"
        assert "a_share" in meta.markets

    def test_execute(self):
        from backend.skills.registry import skill, get_skill

        @skill(name="test_exec", description="执行测试", category="test")
        def exec_skill(symbol: str, market: str, x: int) -> int:
            return x * 2

        meta = get_skill("test_exec")
        assert meta is not None
        result = meta.execute(symbol="S001", market="a_share", x=5)
        assert result == 10

    def test_execute_missing_params(self):
        """测试 execute 缺少必需参数时抛出 SkillExecutionError"""
        from backend.skills.registry import skill, get_skill
        from backend.core.exceptions import SkillExecutionError

        @skill(name="test_exec_missing", description="参数缺失测试", category="test")
        def miss_skill(symbol: str, market: str) -> dict:
            return {}

        meta = get_skill("test_exec_missing")
        assert meta is not None
        with pytest.raises(SkillExecutionError, match="symbol"):
            meta.execute()
        with pytest.raises(SkillExecutionError, match="market"):
            meta.execute(symbol="S001")

    def test_list_skills(self):
        from backend.skills.registry import skill, list_skills

        @skill(name="test_list_a", description="A", category="cat_a", markets=["a_share"])
        def skill_a():
            pass

        @skill(name="test_list_b", description="B", category="cat_b", markets=["us_stock"])
        def skill_b():
            pass

        all_skills = list_skills()
        names = [s["name"] for s in all_skills]
        assert "test_list_a" in names
        assert "test_list_b" in names

        a_share_skills = list_skills(market="a_share")
        a_names = [s["name"] for s in a_share_skills]
        assert "test_list_a" in a_names

    def test_to_dict(self):
        from backend.skills.registry import skill, get_skill

        @skill(name="test_dict", description="dict test", category="test", markets=["us_stock"])
        def dict_skill():
            pass

        meta = get_skill("test_dict")
        d = meta.to_dict()
        assert d["name"] == "test_dict"
        assert d["markets"] == ["us_stock"]
        assert d["category"] == "test"
