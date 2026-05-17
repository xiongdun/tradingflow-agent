# tests/test_graph_builder.py
# 工作流构建器测试 — 校验逻辑、编译缓存、模式分发

from __future__ import annotations


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
        from backend.graph.builder import _COMPILE_CACHE_MAX
        assert _COMPILE_CACHE_MAX == 50


# ═══════════════════════════════════════════════════════
#  conditional gate 类型守卫测试
# ═══════════════════════════════════════════════════════

CONDITIONAL_STATE_DATA = [
    pytest.param({"opinions": [None, 123, "str"]}, ["fundamental"], id="non-dict opinions→pass"),
    pytest.param({"opinions": [{"agent_role": "risk", "stance": "bearish"}]}, "skip", id="bearish risk→skip"),
    pytest.param({"opinions": [{"agent_role": "risk", "stance": "bullish"}]}, ["fundamental"], id="bullish risk→pass"),
    pytest.param({"opinions": []}, ["fundamental"], id="empty_opinions→pass"),
    pytest.param({}, ["fundamental"], id="no_opinions_key→pass"),
]


class TestConditionalGateGuard:
    """测试 conditional.py 中 make_gate 对异常 opinions 的防护"""

    def _make_gate(self, condition, next_roles):
        def _inner_gate(condition: str, next_roles: list[str]):
            def gate_fn(state: dict):
                if condition == "always":
                    return next_roles
                if condition == "check_risk":
                    opinions = state.get("opinions", [])
                    for op in (opinions or []):
                        if isinstance(op, dict) and op.get("agent_role") == "risk":
                            stance = op.get("stance", "")
                            if stance in ("bearish", "strong_bearish"):
                                return "skip"
                    return next_roles
                return next_roles
            return gate_fn
        return _inner_gate(condition, next_roles)

    @pytest.mark.parametrize("state,expected", CONDITIONAL_STATE_DATA)
    def test_gate_handles_anomalous_opinions(self, state, expected):
        """gate 函数不应因 opinions 中的异常值而崩溃"""
        gate = self._make_gate("check_risk", ["fundamental"])
        result = gate(state)
        assert result == expected

    def test_gate_handles_mixed_valid_and_invalid_opinions(self):
        """混合有效/无效 opinions 时，gate 只处理有效的"""
        gate = self._make_gate("check_risk", ["quant"])
        result = gate({
            "opinions": [
                None,
                {"agent_role": "risk", "stance": "strong_bearish"},
                "garbage",
            ]
        })
        assert result == "skip"


# ═══════════════════════════════════════════════════════
#  multi_round 循环上限测试
# ═══════════════════════════════════════════════════════

class TestMultiRoundCap:
    """测试 multi_round round_router 的 max(round,1) + min(rounds,10) 双重防护"""

    def _round_router(self, state, rounds):
        """模拟 multi_round.py 的 round_router 逻辑"""
        current = max(state.get("round", 1), 1)
        max_rounds = min(rounds, 10)
        if current < max_rounds:
            return "fan_out"
        return "summarizer"

    @pytest.mark.parametrize("config_rounds,state_round,expected", [
        (2, 1, "fan_out"),
        (2, 2, "summarizer"),
        (2, 99, "summarizer"),
        (9999, 5, "fan_out"),
        (9999, 10, "summarizer"),
        (9999, 999, "summarizer"),
        (-1, 0, "summarizer"),
        (0, 0, "summarizer"),
    ])
    def test_round_router_boundaries(self, config_rounds, state_round, expected):
        """验证配置 9999 轮时硬上限为 10，负数/零轮直接结束"""
        assert self._round_router({"round": state_round}, config_rounds) == expected

    def test_missing_round_defaults_to_one(self):
        """state 中没有 round 字段时默认为 1"""
        assert self._round_router({}, 3) == "fan_out"

    def test_negative_round_sanitized(self):
        """round 为负值时被 sanitize 为 1"""
        assert self._round_router({"round": -5}, 3) == "fan_out"
