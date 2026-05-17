# backend/skills/bond_data.py
# 债券数据技能 — 获取债券基本面和行情数据

from __future__ import annotations

from typing import Any

from backend.data.factory import get_provider
from backend.skills.registry import skill


@skill(
    name="bond_data",
    description="获取债券基本面数据（价格、涨跌、票面利率、到期日等）",
    markets=["bond"],
    category="fundamental",
    label="债券数据",
    params={"symbol": "债券代码"},
)
def get_bond_data(symbol: str, market: str, **kwargs: Any) -> dict[str, Any]:
    """获取债券基本数据"""
    provider = get_provider(market)
    try:
        info = provider.get_stock_info(symbol)
        quote = provider.get_realtime_quote(symbol)
        return {
            "name": info.name,
            "symbol": info.symbol,
            "price": quote.price,
            "change": quote.change,
            "change_pct": quote.change_pct,
            "volume": quote.volume,
            "turnover": quote.turnover,
            "industry": info.industry,
            "sector": info.sector,
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}
