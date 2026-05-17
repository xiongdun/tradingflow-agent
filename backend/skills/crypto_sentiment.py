# backend/skills/crypto_sentiment.py
# 加密市场情绪技能 — 获取加密货币市场情绪和恐惧贪婪指数

from __future__ import annotations

from typing import Any

from backend.data.factory import get_provider
from backend.skills.registry import skill


@skill(
    name="crypto_sentiment",
    description="加密市场情绪分析 — 恐惧贪婪指数、社交情绪、市场热度",
    markets=["crypto"],
    category="sentiment",
    label="加密市场情绪",
    params={"symbol": "币种代码"},
)
def get_crypto_sentiment(symbol: str, market: str, **kwargs: Any) -> dict[str, Any]:
    provider = get_provider(market)
    try:
        info = provider.get_stock_info(symbol)
        quote = provider.get_realtime_quote(symbol)
        financial = provider.get_financial_data(symbol)
        change_pct = quote.change_pct
        if change_pct > 5:
            sentiment, fear_greed = "极度贪婪", 80
        elif change_pct > 2:
            sentiment, fear_greed = "贪婪", 65
        elif change_pct > -2:
            sentiment, fear_greed = "中性", 50
        elif change_pct > -5:
            sentiment, fear_greed = "恐惧", 35
        else:
            sentiment, fear_greed = "极度恐惧", 20
        ath = financial.get("ath", 0)
        return {
            "symbol": symbol, "name": info.name, "price": quote.price,
            "change_pct": change_pct, "sentiment": sentiment,
            "fear_greed_index": fear_greed, "volume_24h": quote.volume,
            "market_cap": financial.get("market_cap", 0), "ath": ath,
            "distance_from_ath_pct": round((quote.price - ath) / ath * 100, 2) if ath else 0,
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}
