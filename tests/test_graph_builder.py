# tests/test_graph_builder.py
# 工作流构建器测试 — 校验逻辑、编译缓存、模式分发

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(scope="module", autouse=True)
def _ensure_agents():
    """确保 Agent 注册表已通过 auto_discover 填充"""
    from backend.core.discovery import auto_discover
    auto_discover()


class TestValidateWorkflowDef:
    """测试 validate_workflow_def 校验函数"""

    def test_valid_parallel(self):
        from backend.graph.builder import validate_workflow_def
        errors = validate_workflow_def({
            "mode": "parallel",
            "agents": [{"role": "fundamental"}, {"role": "technical"}]
        })
        assert errors == []

    def test_invalid_mode(self):
        from backend.graph.builder import validate_workflow_def
        errors = validate_workflow_def({
            "mode": "invalid_mode",
            "agents": [{"role": "fundamental"}]
        })
        assert any("invalid_mode" in e for e in errors)

    def test_unknown_agent_role(self):
        from backend.graph.builder import validate_workflow_def
        errors = validate_workflow_def({
            "mode": "parallel",
            "agents": [{"role": "nonexistent_xyz_123"}]
        })
        assert any("nonexistent_xyz_123" in e for e in errors)

    def test_missing_role(self):
        from backend.graph.builder import validate_workflow_def
        errors = validate_workflow_def({
            "mode": "parallel",
            "agents": [{}]
        })
        assert any("role" in e.lower() for e in errors)

    def test_conditional_missing_agents(self):
        from backend.graph.builder import validate_workflow_def
        errors = validate_workflow_def({
            "mode": "conditional",
            "stages": [{"condition": "always"}]
        })
        assert any("agents" in e.lower() for e in errors)

    def test_multi_round_invalid_rounds(self):
        from backend.graph.builder import validate_workflow_def
        errors = validate_workflow_def({
            "mode": "multi_round",
            "agents": ["fundamental"],
            "rounds": 0
        })
        assert any("rounds" in e.lower() for e in errors)

    def test_unsupported_version(self):
        from backend.graph.builder import validate_workflow_def
        errors = validate_workflow_def({
            "version": 999,
            "mode": "parallel",
            "agents": [{"role": "fundamental"}]
        })
        assert any("version" in e.lower() for e in errors)

    def test_unknown_skill(self):
        from backend.graph.builder import validate_workflow_def
        errors = validate_workflow_def({
            "mode": "parallel",
            "agents": [{"role": "fundamental", "skills": ["nonexistent_skill"]}]
        })
        assert any("nonexistent_skill" in e for e in errors)

    def test_custom_agent_allowed(self):
        from backend.graph.builder import validate_workflow_def
        errors = validate_workflow_def({
            "mode": "parallel",
            "agents": [{"role": "custom_analyst"}]
        })
        assert errors == []


class TestBuildFromJson:
    """测试 build_from_json 构建函数"""

    def test_invalid_workflow_raises(self):
        from backend.graph.builder import build_from_json
        from backend.core.exceptions import WorkflowBuildError
        with pytest.raises(WorkflowBuildError):
            build_from_json({"mode": "parallel", "agents": [{"role": "unknown"}]})

    def test_compile_cache(self):
        from backend.graph.builder import build_from_json, _compile_cache
        # 清理缓存
        _compile_cache.clear()
        wf = {"mode": "parallel", "agents": [{"role": "fundamental"}]}
        # 第一次构建
        g1 = build_from_json(wf)
        # 第二次应命中缓存
        g2 = build_from_json(wf)
        assert g1 is g2

    def test_cache_size_limit(self):
        from backend.graph.builder import _compile_cache
        # 验证缓存上限常量存在
        from backend.graph.builder import _COMPILE_CACHE_MAX
        assert _COMPILE_CACHE_MAX == 50
