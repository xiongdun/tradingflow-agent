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

# 重试策略：最多 3 次，指数退避 1~8 秒
_RETRY_STOP = stop_after_attempt(3)
_RETRY_WAIT = wait_exponential(multiplier=1, min=1, max=8)


class FallbackProvider(DataProvider):
    """容错数据提供者 — 包装多个 DataProvider，按顺序尝试，自动切换"""

    def __init__(self, providers: list[DataProvider]):
        self._providers = providers

    def _try_all(self, method: str, *args, **kwargs) -> Any:
        """按优先级依次调用各 Provider 的指定方法，第一个成功即返回（带缓存+重试）"""
        def _do_try_with_retry(*a: Any, **kw: Any) -> Any:
            """对每个 provider 做重试，失败后 fallback 到下一个"""
            last_error = None
            for provider in self._providers:
                # 通过闭包捕获 provider 和参数，避免默认参数语法限制
                def _make_call(_p: DataProvider, _args: tuple, _kw: dict) -> Any:
                    @retry(
                        stop=_RETRY_STOP,
                        wait=_RETRY_WAIT,
                        retry=retry_if_exception_type(_RETRYABLE_ERRORS),
                        before_sleep=before_sleep_log(logger, "WARNING"),
                        reraise=True,
                    )
                    def _call() -> Any:
                        return getattr(_p, method)(*_args, **_kw)
                    return _call

                try:
                    return _make_call(provider, a, kw)()
                except Exception as e:
                    logger.warning(f"[fallback] {provider.__class__.__name__}.{method} failed after retries: {e}")
                    last_error = e
            if last_error is None:
                raise ValueError(f"No providers available for {method}")
            raise last_error

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
