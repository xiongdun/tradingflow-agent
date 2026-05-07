# backend/data/provider.py
# 统一数据提供者 — 跨市场的股票数据抽象接口
# 含 @provider 装饰器注册机制，支持自动发现

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable

from pydantic import BaseModel

# ─── Provider 注册表 ───
_providers_registry: dict[str, type] = {}


def provider(name: str, markets: list[str] | None = None, default_priority: int = 0):
    """装饰器：将 DataProvider 子类注册到全局注册表。

    用法：
        @provider("akshare", ["a_share", "h_stock"], default_priority=0)
        class AKShareProvider(DataProvider):
            ...
    """
    def decorator(cls: type) -> type:
        cls._provider_name = name
        cls._provider_markets = markets or ["a_share", "h_stock", "us_stock"]
        cls._provider_priority = default_priority
        _providers_registry[name] = cls
        return cls
    return decorator


def get_provider_defaults(market: str) -> list[str]:
    """从注册表自动推导指定市场的默认数据源优先级"""
    candidates = [
        (getattr(cls, "_provider_priority", 0), name)
        for name, cls in _providers_registry.items()
        if market in getattr(cls, "_provider_markets", [])
    ]
    return [name for _, name in sorted(candidates)]


def get_provider_class(name: str) -> type | None:
    """根据名称获取已注册的 Provider 类"""
    return _providers_registry.get(name)


def list_providers() -> list[dict[str, Any]]:
    """列出所有已注册的 Provider"""
    return [
        {"name": n, "markets": getattr(c, "_provider_markets", [])}
        for n, c in _providers_registry.items()
    ]


@contextmanager
def bypass_proxy():
    """临时绕过系统代理（用于数据源请求）"""
    keys = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
    old = {k: os.environ.pop(k, None) for k in keys}
    # 同时设置 NO_PROXY 包含目标域名
    old_no_proxy = os.environ.get("NO_PROXY", "")
    os.environ["NO_PROXY"] = old_no_proxy + ",*.eastmoney.com,*.tushare.pro,*.yahoo.com"
    try:
        yield
    finally:
        for k, v in old.items():
            if v is not None:
                os.environ[k] = v
        os.environ["NO_PROXY"] = old_no_proxy


class StockQuote(BaseModel):
    """实时股票行情报价模型"""
    symbol: str            # 股票代码
    name: str              # 股票名称
    market: str            # 所属市场
    price: float           # 最新价
    change: float          # 涨跌额
    change_pct: float      # 涨跌幅（%）
    volume: float          # 成交量
    turnover: float        # 成交额
    high: float            # 最高价
    low: float             # 最低价
    open: float            # 开盘价
    prev_close: float      # 昨收价
    timestamp: datetime    # 行情时间戳


class StockInfo(BaseModel):
    """股票基本信息模型"""
    symbol: str            # 股票代码
    name: str              # 股票名称
    market: str            # 所属市场
    industry: str = ""     # 所属行业
    sector: str = ""       # 所属板块
    market_cap: float = 0.0      # 总市值
    pe_ratio: float = 0.0        # 市盈率（动态）
    pb_ratio: float = 0.0        # 市净率
    dividend_yield: float = 0.0  # 股息率


class DataProvider(ABC):
    """数据提供者抽象基类 — 定义各市场数据源必须实现的标准接口"""

    @abstractmethod
    def get_realtime_quote(self, symbol: str) -> StockQuote:
        """获取实时行情报价"""
        ...

    @abstractmethod
    def get_kline(self, symbol: str, period: str = "daily",
                  start_date: str | None = None, end_date: str | None = None):
        """获取 K 线（OHLCV）历史数据

        Args:
            symbol: 股票代码
            period: 周期类型 — 'daily'(日K)、'weekly'(周K)、'monthly'(月K)
            start_date: 起始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
        """
        ...

    @abstractmethod
    def get_stock_info(self, symbol: str) -> StockInfo:
        """获取股票基本信息（名称/行业/市值等）"""
        ...

    @abstractmethod
    def get_financial_data(self, symbol: str) -> dict[str, Any]:
        """获取财务数据（PE/PB/ROE/营收等）"""
        ...

    @abstractmethod
    def search_stock(self, keyword: str) -> list[dict[str, str]]:
        """按关键词搜索股票"""
        ...
