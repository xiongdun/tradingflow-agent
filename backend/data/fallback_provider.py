# backend/data/fallback_provider.py
# 多数据源容错提供者 — 按优先级依次尝试多个 Provider，第一个成功即返回
# 集成磁盘 TTL 缓存，减少重复 API 调用

from __future__ import annotations

from typing import Any

from loguru import logger

from backend.core.cache import cached_call
from backend.data.provider import DataProvider, StockInfo, StockQuote


class FallbackProvider(DataProvider):
    """容错数据提供者 — 包装多个 DataProvider，按顺序尝试，自动切换"""

    def __init__(self, providers: list[DataProvider]):
        self._providers = providers

    def _try_all(self, method: str, *args, **kwargs) -> Any:
        """按优先级依次调用各 Provider 的指定方法，第一个成功即返回（带缓存）"""
        def _do_try(*a: Any, **kw: Any) -> Any:
            last_error = None
            for provider in self._providers:
                try:
                    return getattr(provider, method)(*a, **kw)
                except Exception as e:
                    logger.warning(f"[fallback] {provider.__class__.__name__}.{method} failed: {e}")
                    last_error = e
            if last_error is None:
                raise ValueError(f"No providers available for {method}")
            raise last_error

        return cached_call(method, _do_try, *args, **kwargs)

    def get_realtime_quote(self, symbol: str) -> StockQuote:
        return self._try_all("get_realtime_quote", symbol)

    def get_kline(self, symbol: str, period: str = "daily",
                  start_date: str | None = None, end_date: str | None = None):
        return self._try_all("get_kline", symbol, period=period, start_date=start_date, end_date=end_date)

    def get_stock_info(self, symbol: str) -> StockInfo:
        return self._try_all("get_stock_info", symbol)

    def get_financial_data(self, symbol: str) -> dict[str, Any]:
        return self._try_all("get_financial_data", symbol)

    def search_stock(self, keyword: str) -> list[dict[str, str]]:
        return self._try_all("search_stock", keyword)
