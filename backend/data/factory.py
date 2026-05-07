# backend/data/factory.py
# 数据提供者工厂 — 根据市场类型返回对应的数据源实例，支持多源容错

from __future__ import annotations

from typing import Any

from loguru import logger

from backend.core.cache import cached_call
from backend.data.provider import DataProvider, StockInfo, StockQuote, get_provider_class
from backend.data.fallback_provider import FallbackProvider


class CachedProvider(DataProvider):
    """缓存包装器 — 为单个 DataProvider 添加磁盘 TTL 缓存"""

    def __init__(self, provider: DataProvider):
        self._provider = provider

    def get_realtime_quote(self, symbol: str) -> StockQuote:
        return cached_call("get_realtime_quote", self._provider.get_realtime_quote, symbol)

    def get_kline(self, symbol: str, period: str = "daily",
                  start_date: str | None = None, end_date: str | None = None):
        return cached_call("get_kline", self._provider.get_kline, symbol,
                           period=period, start_date=start_date, end_date=end_date)

    def get_stock_info(self, symbol: str) -> StockInfo:
        return cached_call("get_stock_info", self._provider.get_stock_info, symbol)

    def get_financial_data(self, symbol: str) -> dict[str, Any]:
        return cached_call("get_financial_data", self._provider.get_financial_data, symbol)

    def search_stock(self, keyword: str) -> list[dict[str, str]]:
        return cached_call("search_stock", self._provider.search_stock, keyword)

# 已缓存的数据提供者实例（惰性初始化，避免重复创建）
_providers: dict[str, DataProvider] = {}


def _load_provider_config() -> dict[str, list[str]]:
    """从 .env 加载数据源优先级配置，未配置则从注册表自动推导"""
    try:
        from backend.core.config import load_settings
        settings = load_settings()
        raw = getattr(settings, "provider_priority", "")
        if raw:
            import json
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return {k: v for k, v in parsed.items() if isinstance(v, list)}
    except Exception:
        pass
    # 从注册表自动推导默认优先级
    from backend.data.provider import get_provider_defaults
    return {m: get_provider_defaults(m) for m in ("a_share", "h_stock", "us_stock")}


# 数据源优先级配置（启动时从 .env 加载，可通过 API 动态修改）
_provider_config: dict[str, list[str]] = _load_provider_config()


def _build_provider(market: str) -> DataProvider:
    """根据配置构建数据提供者（单个或容错链）"""
    chain = _provider_config.get(market, [])
    if not chain:
        raise ValueError(f"No provider configured for market: {market}")

    providers = []
    for name in chain:
        cls = get_provider_class(name)
        if cls:
            providers.append(cls())
        else:
            logger.warning(f"Unknown provider: {name}")

    if not providers:
        raise ValueError(f"No valid providers for market: {market}")
    if len(providers) == 1:
        return CachedProvider(providers[0])
    return FallbackProvider(providers)


def get_provider(market: str) -> DataProvider:
    """获取指定市场的数据提供者（单例缓存，支持多源容错）"""
    if market not in _providers:
        _providers[market] = _build_provider(market)
    return _providers[market]


def get_provider_info() -> dict[str, list[str]]:
    """获取当前各市场的数据源优先级配置"""
    return dict(_provider_config)


def set_provider_priority(market: str, providers: list[str]) -> bool:
    """设置指定市场的数据源优先级（自动清除缓存 + 持久化到 .env）"""
    if market not in _provider_config:
        return False
    _provider_config[market] = providers
    _providers.pop(market, None)  # 清除缓存，下次 get_provider 时重建
    # 持久化到 .env
    try:
        import json
        from backend.core.config_writer import update_setting
        update_setting("provider_priority", json.dumps(_provider_config, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"Failed to persist provider config: {e}")
    return True


def reset_provider(market: str | None = None):
    """重置数据提供者缓存（清除后下次调用时重新创建）"""
    if market:
        _providers.pop(market, None)
    else:
        _providers.clear()
