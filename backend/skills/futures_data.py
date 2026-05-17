# backend/skills/futures_data.py
# 期货数据技能 — 获取期货合约基本面数据

from __future__ import annotations

from typing import Any

from backend.data.factory import get_provider
from backend.skills.registry import skill


@skill(
    name="futures_data",
    description="获取期货合约数据（价格、持仓量、保证金、交割月等）",
    markets=["futures"],
    category="fundamental",
    label="期货数据",
    params={"symbol": "合约代码（如 IF2506）"},
)
def get_futures_data(symbol: str, market: str, **kwargs: Any) -> dict[str, Any]:
    """获取期货合约基本数据"""
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
            "open": quote.open,
            "high": quote.high,
            "low": quote.low,
            "prev_close": quote.prev_close,
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}
