# backend/skills/financial_data.py
# 财务数据技能 — 获取股票基本面财务指标

from __future__ import annotations

from typing import Any

from backend.data.factory import get_provider
from backend.skills.registry import skill


@skill(
    name="financial_data",
    description="获取股票基本面财务数据（PE/PB/ROE/市值/营收等），用于基本面分析",
    markets=["a_share", "h_stock", "us_stock", "bond", "futures", "crypto"],
    category="fundamental",
    label="财务数据",
)
def get_financial_data(symbol: str, market: str) -> dict[str, Any]:
    """获取股票的财务基本面数据，并附加基本信息"""
    provider = get_provider(market)
    raw = provider.get_financial_data(symbol)

    # 补充股票名称、行业、板块信息
    info = provider.get_stock_info(symbol)
    raw["stock_name"] = info.name
    raw["industry"] = info.industry
    raw["sector"] = info.sector

    return raw


@skill(
    name="stock_info",
    description="获取股票基本信息（名称/行业/市值等）",
    markets=["a_share", "h_stock", "us_stock", "bond", "futures", "crypto"],
    category="fundamental",
    label="股票信息",
)
def get_stock_info(symbol: str, market: str) -> dict[str, Any]:
    """获取股票基本资料"""
    provider = get_provider(market)
    info = provider.get_stock_info(symbol)
    return info.model_dump()


@skill(
    name="realtime_quote",
    description="获取股票实时行情报价（最新价/涨跌幅/成交量等）",
    markets=["a_share", "h_stock", "us_stock", "bond", "futures", "crypto"],
    category="data",
    label="实时行情",
)
def get_realtime_quote(symbol: str, market: str) -> dict[str, Any]:
    """获取股票实时行情"""
    provider = get_provider(market)
    quote = provider.get_realtime_quote(symbol)
    return quote.model_dump()
