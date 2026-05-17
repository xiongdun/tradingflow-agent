# backend/skills/crypto_data.py
# 加密货币数据技能 — 获取加密货币基本面数据

from __future__ import annotations

from typing import Any

from backend.data.factory import get_provider
from backend.skills.registry import skill


@skill(
    name="crypto_data",
    description="获取加密货币数据（价格、市值、流通量、24h交易量等）",
    markets=["crypto"],
    category="fundamental",
    label="加密货币数据",
    params={"symbol": "币种代码（如 BTC, ETH）"},
)
def get_crypto_data(symbol: str, market: str, **kwargs: Any) -> dict[str, Any]:
    provider = get_provider(market)
    try:
        info = provider.get_stock_info(symbol)
        quote = provider.get_realtime_quote(symbol)
        financial = provider.get_financial_data(symbol)
        return {
            "name": info.name, "symbol": info.symbol,
            "price": quote.price, "change": quote.change,
            "change_pct": quote.change_pct, "volume": quote.volume,
            "market_cap": financial.get("market_cap", 0),
            "circulating_supply": financial.get("circulating_supply", 0),
            "max_supply": financial.get("max_supply", 0),
            "ath": financial.get("ath", 0), "atl": financial.get("atl", 0),
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}
