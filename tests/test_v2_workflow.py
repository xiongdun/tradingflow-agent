# tests/test_v2_workflow.py
# v2 工作流引擎全覆盖测试 — 校验器 / 路由器 / 节点工厂 / 构建器 Facade

from __future__ import annotations

import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

import pytest


# ═══════════════════════════════════════════════════════
#  1. validate_v2_workflow 校验器
# ═══════════════════════════════════════════════════════

class TestValidateV2Workflow:

    def _valid_def(self):
        return {
            "version": 2,
            "nodes": [
                {"id": "s1", "type": "skill", "skill": "kline_data"},
                {"id": "a1", "type": "agent", "role": "technical"},
            ],
            "edges": [
                {"source": "START", "target": "s1"},
                {"source": "s1", "target": "a1"},
                {"source": "a1", "target": "summarizer"},
            ],
        }

    def test_valid_definition(self):
        from backend.plugins.workflow_engine import validate_v2_workflow
        errors = validate_v2_workflow(self._valid_def())
        assert errors == []

    def test_missing_id(self):
        from backend.plugins.workflow_engine import validate_v2_workflow
        d = {"version": 2, "nodes": [{"type": "skill", "skill": "x"}], "edges": []}
        errors = validate_v2_workflow(d)
        assert any("id" in e for e in errors)

    def test_duplicate_ids(self):
        from backend.plugins.workflow_engine import validate_v2_workflow
        d = self._valid_def()
        d["nodes"].append({"id": "s1", "type": "skill", "skill": "x"})
        errors = validate_v2_workflow(d)
        assert any("重复" in e for e in errors)

    def test_invalid_type(self):
        from backend.plugins.workflow_engine import validate_v2_workflow
        d = {"version": 2, "nodes": [{"id": "n1", "type": "bogus"}], "edges": [{"source": "START", "target": "n1"}]}
        errors = validate_v2_workflow(d)
        assert any("类型无效" in e for e in errors)

    def test_skill_missing_skill_field(self):
        from backend.plugins.workflow_engine import validate_v2_workflow
        d = {"version": 2, "nodes": [{"id": "n1", "type": "skill"}], "edges": [{"source": "START", "target": "n1"}]}
        errors = validate_v2_workflow(d)
        assert any("skill" in e and "缺少" in e for e in errors)

    def test_adapter_missing_adapter_field(self):
        from backend.plugins.workflow_engine import validate_v2_workflow
        d = {"version": 2, "nodes": [{"id": "n1", "type": "adapter"}], "edges": [{"source": "START", "target": "n1"}]}
        errors = validate_v2_workflow(d)
        assert any("adapter" in e and "缺少" in e for e in errors)

    def test_agent_missing_role_field(self):
        from backend.plugins.workflow_engine import validate_v2_workflow
        d = {"version": 2, "nodes": [{"id": "n1", "type": "agent"}], "edges": [{"source": "START", "target": "n1"}]}
        errors = validate_v2_workflow(d)
        assert any("role" in e and "缺少" in e for e in errors)

    def test_edge_ref_nonexistent_source(self):
        from backend.plugins.workflow_engine import validate_v2_workflow
        d = {"version": 2, "nodes": [{"id": "n1", "type": "skill", "skill": "x"}],
             "edges": [{"source": "ghost", "target": "n1"}, {"source": "START", "target": "n1"}]}
        errors = validate_v2_workflow(d)
        assert any("不存在的源" in e for e in errors)

    def test_edge_ref_nonexistent_target(self):
        from backend.plugins.workflow_engine import validate_v2_workflow
        d = {"version": 2, "nodes": [{"id": "n1", "type": "skill", "skill": "x"}],
             "edges": [{"source": "START", "target": "n1"}, {"source": "n1", "target": "ghost"}]}
        errors = validate_v2_workflow(d)
        assert any("不存在的目标" in e for e in errors)

    def test_missing_start_edge(self):
        from backend.plugins.workflow_engine import validate_v2_workflow
        d = {"version": 2, "nodes": [{"id": "n1", "type": "skill", "skill": "x"}],
             "edges": [{"source": "n1", "target": "summarizer"}]}
        errors = validate_v2_workflow(d)
        assert any("START" in e for e in errors)

    def test_loop_node_no_end_edge_ok(self):
        """loop 节点隐式路由到 summarizer，不需要显式 end 边"""
        from backend.plugins.workflow_engine import validate_v2_workflow
        d = {
            "version": 2,
            "nodes": [
                {"id": "lp", "type": "loop", "max_iterations": 2},
            ],
            "edges": [
                {"source": "START", "target": "lp"},
                {"source": "lp", "target": "summarizer", "condition": "done"},
            ],
        }
        errors = validate_v2_workflow(d)
        # should NOT have the "没有节点连接到 END" error
        assert not any("END" in e and "summarizer" in e and "没有" in e for e in errors)

    def test_empty_workflow(self):
        from backend.plugins.workflow_engine import validate_v2_workflow
        errors = validate_v2_workflow({"version": 2, "nodes": [], "edges": []})
        assert any("START" in e for e in errors)


# ═══════════════════════════════════════════════════════
#  2. Builder Facade — v2 路由
# ═══════════════════════════════════════════════════════

class TestBuilderFacadeV2:

    def test_build_from_json_v2_routes_to_v2(self):
        from backend.graph.builder import build_from_json
        with patch("backend.graph.builder.validate_workflow_def", return_value=[]), \
             patch("backend.plugins.workflow_engine.build_v2_workflow", return_value="compiled_graph") as mock_v2:
            result = build_from_json({"version": 2, "nodes": [], "edges": []})
            mock_v2.assert_called_once()
            assert result == "compiled_graph"

    def test_build_from_json_v1_routes_to_v1(self):
        from backend.graph.builder import build_from_json
        with patch("backend.graph.builder._build_v1", return_value="v1_graph") as mock_v1, \
             patch("backend.graph.builder.validate_workflow_def", return_value=[]):
            result = build_from_json({"version": 1, "mode": "parallel", "agents": ["technical"]})
            mock_v1.assert_called_once()
            assert result == "v1_graph"

    def test_validate_v2_delegates(self):
        from backend.graph.builder import validate_workflow_def
        with patch("backend.plugins.workflow_engine.validate_v2_workflow", return_value=["err"]) as mock_v:
            result = validate_workflow_def({"version": 2, "nodes": [], "edges": []})
            mock_v.assert_called_once()
            assert result == ["err"]


# ═══════════════════════════════════════════════════════
#  3. Condition Router — 8 种条件标签
# ═══════════════════════════════════════════════════════

class TestConditionRouter:

    def _router(self, route_map):
        from backend.plugins.workflow_engine import _make_condition_router
        return _make_condition_router(route_map)

    def test_has_bearish(self):
        r = self._router({"has_bearish": "bearish_path", "default": "default_path"})
        state = {"opinions": [{"stance": "bearish"}]}
        assert r(state) == "bearish_path"

    def test_has_bearish_strong(self):
        r = self._router({"has_bearish": "bearish_path", "default": "default_path"})
        state = {"opinions": [{"stance": "strong_bearish"}]}
        assert r(state) == "bearish_path"

    def test_has_bullish(self):
        r = self._router({"has_bullish": "bullish_path", "default": "default_path"})
        state = {"opinions": [{"stance": "bullish"}]}
        assert r(state) == "bullish_path"

    def test_has_bullish_strong(self):
        r = self._router({"has_bullish": "bullish_path", "default": "default_path"})
        state = {"opinions": [{"stance": "strong_bullish"}]}
        assert r(state) == "bullish_path"

    def test_high_confidence(self):
        r = self._router({"high_confidence": "hc_path", "default": "default_path"})
        state = {"opinions": [{"confidence": 0.9}]}
        assert r(state) == "hc_path"

    def test_low_confidence(self):
        r = self._router({"low_confidence": "lc_path", "default": "default_path"})
        state = {"opinions": [{"confidence": 0.2}]}
        assert r(state) == "lc_path"

    def test_has_error(self):
        r = self._router({"has_error": "err_path", "default": "default_path"})
        state = {"opinions": [{"error": "timeout"}]}
        assert r(state) == "err_path"

    def test_dynamic_key(self):
        r = self._router({"dynamic:risk_level": "risk_path", "default": "default_path"})
        state = {"dynamic_data": {"risk_level": "high"}}
        assert r(state) == "risk_path"

    def test_always_falls_through(self):
        r = self._router({"always": "always_path"})
        state = {"opinions": []}
        assert r(state) == "always_path"

    def test_default_fallback(self):
        r = self._router({"has_bearish": "bear_path", "default": "fallback"})
        state = {"opinions": []}
        assert r(state) == "fallback"

    def test_no_match_empty_opinions(self):
        r = self._router({"has_bullish": "b_path", "has_bearish": "br_path", "default": "def"})
        state = {"opinions": []}
        assert r(state) == "def"

    def test_neutral_stance_no_match(self):
        r = self._router({"has_bearish": "br_path", "default": "def"})
        state = {"opinions": [{"stance": "neutral"}]}
        assert r(state) == "def"


# ═══════════════════════════════════════════════════════
#  4. Loop Router
# ═══════════════════════════════════════════════════════

class TestLoopRouter:

    def _router(self, max_iter):
        from backend.plugins.workflow_engine import _make_loop_router
        return _make_loop_router(max_iter)

    def test_continue_when_not_reached(self):
        r = self._router(3)
        assert r({"loop_counter": 0}) == "continue"
        assert r({"loop_counter": 1}) == "continue"
        assert r({"loop_counter": 2}) == "continue"

    def test_done_when_reached(self):
        r = self._router(3)
        assert r({"loop_counter": 3}) == "done"
        assert r({"loop_counter": 5}) == "done"

    def test_zero_counter(self):
        r = self._router(1)
        assert r({"loop_counter": 0}) == "continue"
        assert r({"loop_counter": 1}) == "done"

    def test_missing_counter_defaults_zero(self):
        r = self._router(2)
        assert r({}) == "continue"


# ═══════════════════════════════════════════════════════
#  5. Node Factory 函数
# ═══════════════════════════════════════════════════════

class TestNodeFactories:

    def test_condition_node_returns_empty(self):
        from backend.plugins.workflow_engine import _make_condition_node
        node = _make_condition_node()
        result = asyncio.get_event_loop().run_until_complete(node({"opinions": []}))
        assert result == {}

    def test_loop_node_increments_counter(self):
        from backend.plugins.workflow_engine import _make_loop_node
        node = _make_loop_node(3)
        result = asyncio.get_event_loop().run_until_complete(node({"loop_counter": 1}))
        assert result == {"loop_counter": 2}

    def test_loop_node_starting_from_zero(self):
        from backend.plugins.workflow_engine import _make_loop_node
        node = _make_loop_node(3)
        result = asyncio.get_event_loop().run_until_complete(node({}))
        assert result == {"loop_counter": 1}

    def test_skill_node_missing_raises(self):
        from backend.plugins.workflow_engine import _make_skill_node
        from backend.core.exceptions import SkillExecutionError
        node = _make_skill_node("nonexistent_skill", {}, "out")
        with pytest.raises(SkillExecutionError):
            asyncio.get_event_loop().run_until_complete(node({"symbol": "600519", "market": "a_share"}))

    def test_skill_node_executes(self):
        from backend.plugins.workflow_engine import _make_skill_node
        mock_meta = MagicMock()
        mock_meta.execute.return_value = {"klines": [1, 2, 3]}
        with patch("backend.skills.registry.get_skill", return_value=mock_meta):
            node = _make_skill_node("kline_data", {"days": 30}, "kline_out")
            result = asyncio.get_event_loop().run_until_complete(
                node({"symbol": "600519", "market": "a_share", "dynamic_data": {}})
            )
        assert result["dynamic_data"]["kline_out"] == {"klines": [1, 2, 3]}

    def test_skill_node_error_captured(self):
        from backend.plugins.workflow_engine import _make_skill_node
        mock_meta = MagicMock()
        mock_meta.execute.side_effect = RuntimeError("网络超时")
        with patch("backend.skills.registry.get_skill", return_value=mock_meta):
            node = _make_skill_node("kline_data", {}, "out")
            result = asyncio.get_event_loop().run_until_complete(
                node({"symbol": "x", "market": "a_share", "dynamic_data": {}})
            )
        assert "error" in result["dynamic_data"]["out"]

    def test_adapter_node_unknown_type_returns_error(self):
        from backend.plugins.workflow_engine import _make_adapter_node
        node = _make_adapter_node("nonexistent_type", {}, "out")
        result = asyncio.get_event_loop().run_until_complete(
            node({"dynamic_data": {}})
        )
        assert "error" in result["dynamic_data"]["out"]

    def test_adapter_node_config_key(self):
        """adapter 节点支持 adapter_config 作为 config 别名"""
        from backend.plugins.workflow_engine import build_v2_workflow
        # 验证 adapter_config 字段能被正确读取
        d = {
            "version": 2,
            "nodes": [
                {"id": "a1", "type": "adapter", "adapter": "http", "adapter_config": {"url": "https://x.com"}},
            ],
            "edges": [
                {"source": "START", "target": "a1"},
                {"source": "a1", "target": "summarizer"},
            ],
        }
        # 只验证不报错，不真正调用 http
        with patch("backend.plugins.workflow_engine._make_adapter_node") as mock_fn:
            mock_fn.return_value = AsyncMock(return_value={"dynamic_data": {}})
            build_v2_workflow(d)
            mock_fn.assert_called_once_with("http", {"url": "https://x.com"}, "a1")


# ═══════════════════════════════════════════════════════
#  6. build_v2_workflow — 集成测试
# ═══════════════════════════════════════════════════════

class TestBuildV2Workflow:

    def test_simple_linear_builds(self):
        from backend.plugins.workflow_engine import build_v2_workflow
        d = {
            "version": 2,
            "nodes": [
                {"id": "s1", "type": "skill", "skill": "kline_data"},
                {"id": "a1", "type": "agent", "role": "technical"},
            ],
            "edges": [
                {"source": "START", "target": "s1"},
                {"source": "s1", "target": "a1"},
                {"source": "a1", "target": "summarizer"},
            ],
        }
        with patch("backend.plugins.workflow_engine._make_skill_node", return_value=AsyncMock()), \
             patch("backend.plugins.workflow_engine._make_agent_node", return_value=AsyncMock()), \
             patch("backend.plugins.workflow_engine._make_summarizer_node", return_value=AsyncMock()):
            graph = build_v2_workflow(d)
            assert graph is not None

    def test_condition_node_builds(self):
        from backend.plugins.workflow_engine import build_v2_workflow
        d = {
            "version": 2,
            "nodes": [
                {"id": "a1", "type": "agent", "role": "technical"},
                {"id": "gate", "type": "condition"},
            ],
            "edges": [
                {"source": "START", "target": "a1"},
                {"source": "a1", "target": "gate"},
                {"source": "gate", "target": "summarizer", "condition": "always"},
            ],
        }
        with patch("backend.plugins.workflow_engine._make_agent_node", return_value=AsyncMock()), \
             patch("backend.plugins.workflow_engine._make_condition_node", return_value=AsyncMock()), \
             patch("backend.plugins.workflow_engine._make_summarizer_node", return_value=AsyncMock()):
            graph = build_v2_workflow(d)
            assert graph is not None

    def test_loop_node_builds(self):
        from backend.plugins.workflow_engine import build_v2_workflow
        d = {
            "version": 2,
            "nodes": [
                {"id": "lp", "type": "loop", "max_iterations": 2},
            ],
            "edges": [
                {"source": "START", "target": "lp"},
                {"source": "lp", "target": "summarizer", "condition": "done"},
            ],
        }
        with patch("backend.plugins.workflow_engine._make_loop_node", return_value=AsyncMock()), \
             patch("backend.plugins.workflow_engine._make_summarizer_node", return_value=AsyncMock()):
            graph = build_v2_workflow(d)
            assert graph is not None

    def test_end_edge_routes_to_summarizer(self):
        """target == 'END' 的边应路由到 summarizer 节点"""
        from backend.plugins.workflow_engine import build_v2_workflow
        d = {
            "version": 2,
            "nodes": [
                {"id": "s1", "type": "skill", "skill": "kline_data"},
            ],
            "edges": [
                {"source": "START", "target": "s1"},
                {"source": "s1", "target": "END"},
            ],
        }
        with patch("backend.plugins.workflow_engine._make_skill_node", return_value=AsyncMock()), \
             patch("backend.plugins.workflow_engine._make_summarizer_node", return_value=AsyncMock()):
            graph = build_v2_workflow(d)
            assert graph is not None


# ═══════════════════════════════════════════════════════
#  7. v2 模板加载
# ═══════════════════════════════════════════════════════

class TestV2Templates:

    def test_quant_hybrid_validates(self):
        """quant_hybrid.json 是一个合法的 v2 工作流"""
        import json
        from pathlib import Path
        from backend.plugins.workflow_engine import validate_v2_workflow

        tpl_path = Path(__file__).parent.parent / "backend" / "graph" / "templates" / "quant_hybrid.json"
        if tpl_path.exists():
            tpl = json.loads(tpl_path.read_text(encoding="utf-8"))
            assert tpl.get("version") == 2
            errors = validate_v2_workflow(tpl)
            assert errors == [], f"quant_hybrid.json 校验失败: {errors}"
