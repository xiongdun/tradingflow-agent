# tests/test_events_security.py
# 事件总线 + 安全治理全覆盖测试

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock



# ═══════════════════════════════════════════════════════
#  1. Event 对象
# ═══════════════════════════════════════════════════════

class TestEvent:

    def test_creation(self):
        from backend.plugins.events import Event
        e = Event("price_alert", {"symbol": "600519", "price": 1800}, source="test")
        assert e.type == "price_alert"
        assert e.data["symbol"] == "600519"
        assert e.source == "test"
        assert isinstance(e.timestamp, str)

    def test_to_dict(self):
        from backend.plugins.events import Event
        e = Event("custom", {"key": "val"})
        d = e.to_dict()
        assert d["type"] == "custom"
        assert d["data"]["key"] == "val"
        assert "timestamp" in d


# ═══════════════════════════════════════════════════════
#  2. EventBus 核心
# ═══════════════════════════════════════════════════════

class TestEventBus:

    def test_subscribe_and_emit(self):
        from backend.plugins.events import EventBus, Event
        bus = EventBus()
        received = []
        async def handler(data):
            received.append(data)
        bus.on("test_event", handler)
        asyncio.get_event_loop().run_until_complete(
            bus.emit(Event("test_event", {"v": 1}))
        )
        assert len(received) == 1
        assert received[0]["v"] == 1

    def test_wildcard_handler(self):
        from backend.plugins.events import EventBus, Event
        bus = EventBus()
        received = []
        async def handler(data):
            received.append(data)
        bus.on("*", handler)
        asyncio.get_event_loop().run_until_complete(
            bus.emit(Event("any_type", {"x": 1}))
        )
        assert len(received) == 1

    def test_off_unsubscribe(self):
        from backend.plugins.events import EventBus, Event
        bus = EventBus()
        received = []
        async def handler(data):
            received.append(data)
        bus.on("evt", handler)
        bus.off("evt", handler)
        asyncio.get_event_loop().run_until_complete(
            bus.emit(Event("evt", {}))
        )
        assert len(received) == 0

    def test_emit_history(self):
        from backend.plugins.events import EventBus, Event
        bus = EventBus()
        asyncio.get_event_loop().run_until_complete(
            bus.emit(Event("e1", {"a": 1}))
        )
        asyncio.get_event_loop().run_until_complete(
            bus.emit(Event("e2", {"b": 2}))
        )
        history = bus.get_history()
        assert len(history) == 2
        assert history[0]["type"] == "e1"
        assert history[1]["type"] == "e2"

    def test_history_filter_by_type(self):
        from backend.plugins.events import EventBus, Event
        bus = EventBus()
        asyncio.get_event_loop().run_until_complete(
            bus.emit(Event("a", {"x": 1}))
        )
        asyncio.get_event_loop().run_until_complete(
            bus.emit(Event("b", {"y": 2}))
        )
        assert len(bus.get_history(event_type="a")) == 1
        assert bus.get_history(event_type="a")[0]["type"] == "a"

    def test_history_limit(self):
        from backend.plugins.events import EventBus, Event
        bus = EventBus()
        for i in range(10):
            asyncio.get_event_loop().run_until_complete(
                bus.emit(Event("e", {"i": i}))
            )
        assert len(bus.get_history(limit=3)) == 3

    def test_history_max_rollover(self):
        from backend.plugins.events import EventBus, Event
        bus = EventBus()
        bus._max_history = 5
        for i in range(8):
            asyncio.get_event_loop().run_until_complete(
                bus.emit(Event("e", {"i": i}))
            )
        assert len(bus.get_history(limit=100)) == 5

    def test_handler_exception_does_not_break_emit(self):
        from backend.plugins.events import EventBus, Event
        bus = EventBus()
        async def bad_handler(data):
            raise RuntimeError("boom")
        async def good_handler(data):
            pass
        bus.on("e", bad_handler)
        bus.on("e", good_handler)
        # should not raise
        asyncio.get_event_loop().run_until_complete(
            bus.emit(Event("e", {}))
        )

    def test_different_type_not_triggered(self):
        from backend.plugins.events import EventBus, Event
        bus = EventBus()
        received = []
        async def handler(data):
            received.append(data)
        bus.on("type_a", handler)
        asyncio.get_event_loop().run_until_complete(
            bus.emit(Event("type_b", {}))
        )
        assert len(received) == 0


# ═══════════════════════════════════════════════════════
#  3. EventTrigger
# ═══════════════════════════════════════════════════════

class TestEventTrigger:

    def test_matches_exact(self):
        from backend.plugins.events import EventTrigger, Event
        t = EventTrigger("t1", "price_alert", {"symbol": "600519"}, "deep_analysis")
        e = Event("price_alert", {"symbol": "600519"})
        assert t.matches(e) is True

    def test_matches_wrong_type(self):
        from backend.plugins.events import EventTrigger, Event
        t = EventTrigger("t1", "price_alert", {}, "wf")
        e = Event("news_event", {})
        assert t.matches(e) is False

    def test_matches_disabled(self):
        from backend.plugins.events import EventTrigger, Event
        t = EventTrigger("t1", "price_alert", {}, "wf")
        t.enabled = False
        e = Event("price_alert", {})
        assert t.matches(e) is False

    def test_matches_condition_gt(self):
        from backend.plugins.events import EventTrigger, Event
        t = EventTrigger("t1", "price_alert", {"price": {"op": "gt", "value": 100}}, "wf")
        assert t.matches(Event("price_alert", {"price": 150})) is True
        assert t.matches(Event("price_alert", {"price": 50})) is False

    def test_matches_condition_lt(self):
        from backend.plugins.events import EventTrigger, Event
        t = EventTrigger("t1", "price_alert", {"price": {"op": "lt", "value": 100}}, "wf")
        assert t.matches(Event("price_alert", {"price": 50})) is True
        assert t.matches(Event("price_alert", {"price": 150})) is False

    def test_matches_condition_eq(self):
        from backend.plugins.events import EventTrigger, Event
        t = EventTrigger("t1", "price_alert", {"price": {"op": "eq", "value": 100}}, "wf")
        assert t.matches(Event("price_alert", {"price": 100})) is True
        assert t.matches(Event("price_alert", {"price": 200})) is False

    def test_matches_condition_contains(self):
        from backend.plugins.events import EventTrigger, Event
        t = EventTrigger("t1", "news_event", {"headline": {"op": "contains", "value": "涨"}}, "wf")
        assert t.matches(Event("news_event", {"headline": "股票大涨"})) is True
        assert t.matches(Event("news_event", {"headline": "股票大跌"})) is False

    def test_matches_multiple_conditions(self):
        from backend.plugins.events import EventTrigger, Event
        t = EventTrigger("t1", "price_alert", {"symbol": "600519", "price": {"op": "gt", "value": 100}}, "wf")
        assert t.matches(Event("price_alert", {"symbol": "600519", "price": 200})) is True
        assert t.matches(Event("price_alert", {"symbol": "000001", "price": 200})) is False

    def test_to_dict(self):
        from backend.plugins.events import EventTrigger
        t = EventTrigger("t1", "price_alert", {"symbol": "600519"}, "wf", params={"market": "a_share"})
        d = t.to_dict()
        assert d["id"] == "t1"
        assert d["enabled"] is True
        assert d["trigger_count"] == 0
        assert d["last_triggered"] is None

    def test_bus_add_remove_trigger(self):
        from backend.plugins.events import EventBus, EventTrigger
        bus = EventBus()
        t = EventTrigger("t1", "price_alert", {}, "wf")
        bus.add_trigger(t)
        assert len(bus.list_triggers()) == 1
        assert bus.remove_trigger("t1") is True
        assert len(bus.list_triggers()) == 0
        assert bus.remove_trigger("nonexistent") is False


# ═══════════════════════════════════════════════════════
#  4. 工厂函数
# ═══════════════════════════════════════════════════════

class TestEventFactoryFunctions:

    def test_create_price_alert(self):
        from backend.plugins.events import create_price_alert
        t = create_price_alert("pa1", "600519", "gt:1800", "deep_analysis")
        assert t.event_type == "price_alert"
        assert t.condition["symbol"] == "600519"
        assert t.condition["price"]["op"] == "gt"
        assert t.condition["price"]["value"] == 1800.0
        assert t.params["symbol"] == "600519"

    def test_create_price_alert_lt(self):
        from backend.plugins.events import create_price_alert
        t = create_price_alert("pa2", "000001", "lt:10", "quick_scan")
        assert t.condition["price"]["op"] == "lt"
        assert t.condition["price"]["value"] == 10.0

    def test_create_indicator_signal(self):
        from backend.plugins.events import create_indicator_signal
        t = create_indicator_signal("is1", "600519", "rsi", "oversold", "deep_analysis")
        assert t.event_type == "indicator_signal"
        assert t.condition["indicator"] == "rsi"
        assert t.condition["signal"] == "oversold"

    def test_create_news_trigger(self):
        from backend.plugins.events import create_news_trigger
        t = create_news_trigger("nt1", ["降息", "加息"], "macro_analysis")
        assert t.event_type == "news_event"
        assert t.condition["keywords"] == ["降息", "加息"]


# ═══════════════════════════════════════════════════════
#  5. EventBus + Trigger 集成
# ═══════════════════════════════════════════════════════

class TestEventBusTriggerIntegration:

    def test_trigger_matches_and_records(self):
        from backend.plugins.events import EventBus, Event, EventTrigger
        bus = EventBus()
        t = EventTrigger("t1", "price_alert", {"symbol": "600519"}, "wf")
        bus.add_trigger(t)
        # execute 会尝试调用 AnalysisService，用 mock 绕过
        with patch.object(t, "execute", new_callable=AsyncMock):
            asyncio.get_event_loop().run_until_complete(
                bus.emit(Event("price_alert", {"symbol": "600519", "price": 1800}))
            )
            t.execute.assert_called_once()


# ═══════════════════════════════════════════════════════
#  6. PermissionChecker
# ═══════════════════════════════════════════════════════

class TestPermissionChecker:

    def _manifest(self, source="local", perms=None):
        from backend.plugins.manifest import PluginManifest, PluginType, Permission
        return PluginManifest(
            name="test", version="1.0.0", type=PluginType.SKILL, description="t",
            permissions=perms or [Permission.NETWORK],
            source=source,
        )

    def test_local_plugin_no_warnings(self):
        from backend.plugins.security import PermissionChecker
        pc = PermissionChecker()
        m = self._manifest(source="local", perms=[])
        assert pc.check(m) == []

    def test_remote_full_access_warning(self):
        from backend.plugins.security import PermissionChecker
        from backend.plugins.manifest import Permission
        pc = PermissionChecker()
        m = self._manifest(source="remote", perms=[Permission.FULL_ACCESS])
        warnings = pc.check(m)
        assert any("FULL_ACCESS" in w for w in warnings)

    def test_remote_execute_warning(self):
        from backend.plugins.security import PermissionChecker
        from backend.plugins.manifest import Permission
        pc = PermissionChecker()
        m = self._manifest(source="remote", perms=[Permission.EXECUTE])
        warnings = pc.check(m)
        assert any("EXECUTE" in w for w in warnings)

    def test_validate_for_execution_local_always_ok(self):
        from backend.plugins.security import PermissionChecker
        from backend.plugins.manifest import Permission
        pc = PermissionChecker()
        m = self._manifest(source="local", perms=[Permission.FULL_ACCESS])
        assert pc.validate_for_execution(m) is True

    def test_validate_for_execution_remote_full_access_rejected(self):
        from backend.plugins.security import PermissionChecker
        from backend.plugins.manifest import Permission
        pc = PermissionChecker()
        m = self._manifest(source="remote", perms=[Permission.FULL_ACCESS])
        assert pc.validate_for_execution(m) is False

    def test_validate_for_execution_remote_network_ok(self):
        from backend.plugins.security import PermissionChecker
        from backend.plugins.manifest import Permission
        pc = PermissionChecker()
        m = self._manifest(source="remote", perms=[Permission.NETWORK])
        assert pc.validate_for_execution(m) is True


# ═══════════════════════════════════════════════════════
#  7. AuditLog
# ═══════════════════════════════════════════════════════

class TestAuditLog:

    def test_log_execution(self, tmp_path):
        from backend.plugins.security import AuditLog
        import backend.plugins.security as sec_mod
        with patch.object(sec_mod, "_AUDIT_DIR", tmp_path):
            al = AuditLog()
            al.log_execution("my_plugin", "run", "success", {"duration": 1.2})
            entries = al.get_audit_trail()
            assert len(entries) == 1
            assert entries[0]["plugin"] == "my_plugin"
            assert entries[0]["action"] == "run"

    def test_log_permission_request(self, tmp_path):
        from backend.plugins.security import AuditLog
        import backend.plugins.security as sec_mod
        with patch.object(sec_mod, "_AUDIT_DIR", tmp_path):
            al = AuditLog()
            al.log_permission_request("plugin_a", "network", granted=True)
            entries = al.get_audit_trail()
            assert entries[0]["permission"] == "network"
            assert entries[0]["granted"] is True

    def test_log_install_and_uninstall(self, tmp_path):
        from backend.plugins.security import AuditLog
        import backend.plugins.security as sec_mod
        with patch.object(sec_mod, "_AUDIT_DIR", tmp_path):
            al = AuditLog()
            al.log_install("plugin_b", "2.0.0", "git")
            al.log_uninstall("plugin_b")
            entries = al.get_audit_trail(plugin="plugin_b")
            assert len(entries) == 2
            actions = [e["action"] for e in entries]
            assert "install" in actions
            assert "uninstall" in actions

    def test_get_audit_trail_filter(self, tmp_path):
        from backend.plugins.security import AuditLog
        import backend.plugins.security as sec_mod
        with patch.object(sec_mod, "_AUDIT_DIR", tmp_path):
            al = AuditLog()
            al.log_execution("p1", "run", "ok")
            al.log_execution("p2", "run", "ok")
            assert len(al.get_audit_trail(plugin="p1")) == 1
            assert len(al.get_audit_trail(plugin="p2")) == 1

    def test_get_audit_trail_limit(self, tmp_path):
        from backend.plugins.security import AuditLog
        import backend.plugins.security as sec_mod
        with patch.object(sec_mod, "_AUDIT_DIR", tmp_path):
            al = AuditLog()
            for i in range(10):
                al.log_execution("p", "act", f"r{i}")
            assert len(al.get_audit_trail(limit=5)) == 5

    def test_cleanup_old_files(self, tmp_path):
        from backend.plugins.security import AuditLog
        import backend.plugins.security as sec_mod
        with patch.object(sec_mod, "_AUDIT_DIR", tmp_path):
            al = AuditLog()
            # 创建一个 60 天前的日志文件
            old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
            old_file = tmp_path / f"audit_{old_date}.jsonl"
            old_file.write_text('{"old": true}\n', encoding="utf-8")
            # 创建一个今天的文件
            al.log_execution("p", "run", "ok")
            removed = al.cleanup(keep_days=30)
            assert removed == 1
            remaining = list(tmp_path.glob("audit_*.jsonl"))
            assert len(remaining) == 1  # only today's file remains


# ═══════════════════════════════════════════════════════
#  8. LLMBudgetGuard
# ═══════════════════════════════════════════════════════

class TestLLMBudgetGuard:

    def test_rate_limit_within_bounds(self):
        from backend.plugins.security import LLMBudgetGuard
        bg = LLMBudgetGuard(max_calls_per_minute=5)
        for _ in range(4):
            assert bg.check_rate_limit() is True
        assert bg.check_rate_limit() is True  # 5th call still ok

    def test_rate_limit_exceeded(self):
        from backend.plugins.security import LLMBudgetGuard
        bg = LLMBudgetGuard(max_calls_per_minute=3)
        bg.check_rate_limit()
        bg.check_rate_limit()
        bg.check_rate_limit()
        assert bg.check_rate_limit() is False  # 4th call exceeds

    def test_budget_within_bounds(self):
        from backend.plugins.security import LLMBudgetGuard
        bg = LLMBudgetGuard(max_cost_per_day=10.0)
        bg.record_usage(1000, cost=1.0)
        assert bg.check_budget() is True

    def test_budget_exceeded(self):
        from backend.plugins.security import LLMBudgetGuard
        bg = LLMBudgetGuard(max_cost_per_day=5.0)
        bg.record_usage(10000, cost=5.0)
        assert bg.check_budget() is False

    def test_record_usage(self):
        from backend.plugins.security import LLMBudgetGuard
        bg = LLMBudgetGuard()
        bg.record_usage(1000, cost=0.5)
        bg.record_usage(2000, cost=1.0)
        usage = bg.get_usage()
        assert usage["daily_tokens"] == 3000
        assert usage["daily_cost"] == 1.5

    def test_reset_daily(self):
        from backend.plugins.security import LLMBudgetGuard
        bg = LLMBudgetGuard()
        bg.record_usage(5000, cost=3.0)
        bg.reset_daily()
        usage = bg.get_usage()
        assert usage["daily_tokens"] == 0
        assert usage["daily_cost"] == 0.0

    def test_get_usage_fields(self):
        from backend.plugins.security import LLMBudgetGuard
        bg = LLMBudgetGuard(max_calls_per_minute=60, max_cost_per_day=10.0)
        usage = bg.get_usage()
        assert "calls_this_minute" in usage
        assert "max_calls_per_minute" in usage
        assert "daily_tokens" in usage
        assert "daily_cost" in usage
        assert "max_cost_per_day" in usage

    def test_custom_limits(self):
        from backend.plugins.security import LLMBudgetGuard
        bg = LLMBudgetGuard(max_tokens_per_call=2048, max_calls_per_minute=10, max_cost_per_day=50.0)
        assert bg.max_tokens_per_call == 2048
        assert bg.max_calls_per_minute == 10
        assert bg.max_cost_per_day == 50.0


# ═══════════════════════════════════════════════════════
#  9. 全局实例
# ═══════════════════════════════════════════════════════

class TestGlobalInstances:

    def test_global_event_bus(self):
        from backend.plugins.events import event_bus
        assert event_bus is not None
        assert hasattr(event_bus, "emit")

    def test_global_permission_checker(self):
        from backend.plugins.security import permission_checker
        assert permission_checker is not None
        assert hasattr(permission_checker, "check")

    def test_global_audit_log(self):
        from backend.plugins.security import audit_log
        assert audit_log is not None
        assert hasattr(audit_log, "log_execution")

    def test_global_llm_budget_guard(self):
        from backend.plugins.security import llm_budget_guard
        assert llm_budget_guard is not None
        assert hasattr(llm_budget_guard, "check_rate_limit")
