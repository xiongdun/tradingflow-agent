# backend/data/fallback_provider.py
# 多数据源容错提供者 — 按优先级依次尝试多个 Provider，第一个成功即返回
# 集成磁盘 TTL 缓存 + tenacity 重试，减少重复 API 调用并提高容错能力

from __future__ import annotations

from typing import Any

from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from backend.core.cache import cached_call
from backend.data.provider import DataProvider, StockInfo, StockQuote

# 数据源可重试异常类型 — 网络/限流/临时性错误
_RETRYABLE_ERRORS = (ConnectionError, TimeoutError, OSError)


def _get_retry_config():
    from backend.core.config import load_settings
    s = load_settings()
    return (
        stop_after_attempt(s.fallback_retry_max),
        wait_exponential(multiplier=1, min=s.fallback_retry_wait_min, max=s.fallback_retry_wait_max),
    )


def _safe_empty_result(method: str) -> Any:
    """所有数据源都失败时，返回安全的空值，避免下游代码崩溃"""
    if method == "search_stock":
        return []
    if method == "get_stock_info":
        return {"error": "数据暂不可用", "market_cap": 0, "turnover_rate": 0, "industry": ""}
    if method == "get_realtime_quote":
        return {"error": "数据暂不可用"}
    if method in ("get_kline", "get_financial_data"):
        return {}
    return {}


class FallbackProvider(DataProvider):
    """容错数据提供者 — 包装多个 DataProvider，按顺序尝试，自动切换"""

    def __init__(self, providers: list[DataProvider]):
        self._providers = providers

    def _try_all(self, method: str, *args, **kwargs) -> Any:
        """按优先级依次调用各 Provider 的指定方法，第一个成功即返回（带缓存+重试）
        
        与普通容错不同：此方法在所有数据源都失败时，返回安全的空结果
        而非抛出异常，确保分析流程不会因数据问题完全中断。
        """
        def _do_try_with_retry(*a: Any, **kw: Any) -> Any:
            last_error = None
            for provider in self._providers:
                def _make_call(_p: DataProvider, _args: tuple, _kw: dict) -> Any:
                    retry_stop, retry_wait = _get_retry_config()
                    @retry(
                        stop=retry_stop,
                        wait=retry_wait,
                        retry=retry_if_exception_type(_RETRYABLE_ERRORS),
                        before_sleep=before_sleep_log(logger, "WARNING"),
                        reraise=True,
                    )
                    def _call() -> Any:
                        return getattr(_p, method)(*_args, **_kw)
                    return _call

                try:
                    result = _make_call(provider, a, kw)()
                    if result is not None:
                        return result
                    logger.debug(f"[fallback] {provider.__class__.__name__}.{method} returned None, trying next")
                    last_error = ValueError(f"{provider.__class__.__name__}.{method} returned None")
                except Exception as e:
                    logger.warning(f"[fallback] {provider.__class__.__name__}.{method} failed after retries: {e}")
                    last_error = e
            # 所有数据源都失败 — 返回安全空值而非抛异常
            logger.error(f"[fallback] All providers failed for {method}: {last_error}")
            return _safe_empty_result(method)

        return cached_call(method, _do_try_with_retry, *args, **kwargs)

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
