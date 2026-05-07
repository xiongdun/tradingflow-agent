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
