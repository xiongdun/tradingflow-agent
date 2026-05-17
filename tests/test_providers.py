# tests/test_providers.py
# Provider 注册中心测试 — 装饰器注册、工厂查询、优先级配置

from __future__ import annotations

import pytest


class TestProviderDecorator:
    """测试 @provider 装饰器注册机制"""

    @pytest.fixture(autouse=True)
    def _ensure_providers_loaded(self):
        """确保 provider 模块已导入（测试环境不走 main.py 自动发现）"""
        from backend.core.discovery import auto_discover
        auto_discover()

    def test_register_provider(self):
        from backend.data.provider import provider, _providers_registry

        @provider("test_prov", ["test_market"])
        class TestProvider:
            pass

        assert "test_prov" in _providers_registry
        assert _providers_registry["test_prov"] is TestProvider
        assert TestProvider._provider_name == "test_prov"
        assert TestProvider._provider_markets == ["test_market"]

    def test_get_provider_class(self):
        from backend.data.provider import get_provider_class
        cls = get_provider_class("akshare")
        assert cls is not None
        assert get_provider_class("nonexistent_xyz") is None

    def test_list_providers(self):
        from backend.data.provider import list_providers
        result = list_providers()
        assert isinstance(result, list)
        names = [p["name"] for p in result]
        assert "akshare" in names or len(result) > 0


class TestProviderFactory:
    """测试 factory.py 中的优先级配置"""

    def test_get_provider_info(self):
        from backend.data.factory import get_provider_info
        info = get_provider_info()
        assert "a_share" in info
        assert "us_stock" in info
        assert isinstance(info["a_share"], list)

    def test_set_provider_priority(self):
        from backend.data.factory import set_provider_priority, get_provider_info, reset_provider
        original = get_provider_info()["a_share"]
        ok = set_provider_priority("a_share", ["akshare"])
        assert ok is True
        info = get_provider_info()
        assert info["a_share"] == ["akshare"]
        set_provider_priority("a_share", original)
        reset_provider()

    def test_invalid_market(self):
        from backend.data.factory import set_provider_priority
        ok = set_provider_priority("invalid_market", ["akshare"])
        assert ok is False


# ═══════════════════════════════════════════════════════
#  FallbackProvider 安全空值 + None 处理测试
# ═══════════════════════════════════════════════════════

class TestFallbackSafety:
    """测试 FallbackProvider _safe_empty_result 和安全降级逻辑"""

    def test_safe_empty_result_all_methods(self):
        """验证 _safe_empty_result 为每个 data 方法返回正确类型的空值"""
        from backend.data.fallback_provider import _safe_empty_result

        test_cases = [
            ("search_stock", list, []),
            ("get_stock_info", dict, {"error": "数据暂不可用"}),
            ("get_realtime_quote", dict, {"error": "数据暂不可用"}),
            ("get_kline", dict, {}),
            ("get_financial_data", dict, {}),
            ("unknown_method", dict, {}),
        ]

        for method, expected_type, expected_min in test_cases:
            result = _safe_empty_result(method)
            assert isinstance(result, expected_type), f"{method}: expected {expected_type}, got {type(result)}"
            if isinstance(expected_min, dict):
                for k, v in expected_min.items():
                    assert k in result, f"{method}: missing key {k}"
                    assert result[k] == v, f"{method}: {k}={result[k]} != {v}"

    def test_all_providers_fail_returns_safe_empty(self):
        """所有数据源都失败时，FallbackProvider 应返回安全空值而非抛异常"""
        from unittest.mock import MagicMock, patch
        from backend.data.fallback_provider import FallbackProvider

        bad_provider = MagicMock()
        bad_provider.__class__.__name__ = "BadProvider"
        bad_provider.get_kline.side_effect = ConnectionError("网络不可达")

        with patch("backend.data.fallback_provider._get_retry_config", return_value=(None, None)):
            fb = FallbackProvider([bad_provider])
            result = fb.get_kline("600519")
            assert isinstance(result, dict)
            assert result == {}

    def test_provider_returns_none_falls_through(self):
        """Provider 返回 None 时应尝试下一个，而非直接返回 None"""
        from unittest.mock import MagicMock, patch
        from backend.data.fallback_provider import FallbackProvider

        none_provider = MagicMock()
        none_provider.__class__.__name__ = "NoneProvider"
        none_provider.search_stock.return_value = None

        good_provider = MagicMock()
        good_provider.__class__.__name__ = "GoodProvider"
        good_provider.search_stock.return_value = [{"code": "600519", "name": "茅台"}]

        with patch("backend.data.fallback_provider._get_retry_config", return_value=(None, None)):
            fb = FallbackProvider([none_provider, good_provider])
            result = fb.search_stock("茅台")
            assert result == [{"code": "600519", "name": "茅台"}]
