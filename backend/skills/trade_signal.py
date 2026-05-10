# backend/skills/trade_signal.py
# 交易信号技能 — 获取实时行情和交易数据，为交易员 Agent 提供决策依据

from __future__ import annotations

from typing import Any

from backend.data.factory import get_provider
from backend.skills.registry import skill


@skill(
    name="trade_signal",
    description="获取股票实时行情、涨跌停信息、成交量异动，用于生成交易信号",
    markets=["a_share", "h_stock", "us_stock"],
    category="trading",
    label="交易信号",
    params={},
)
def get_trade_signal(symbol: str, market: str) -> dict[str, Any]:
    """获取交易信号相关数据：实时报价 + 当日涨跌 + 成交量 + 交易指标"""
    provider = get_provider(market)

    result: dict[str, Any] = {}

    # 实时报价
    try:
        quote = provider.get_realtime_quote(symbol)
        result["quote"] = {
            "symbol": symbol,
            "name": getattr(quote, "name", symbol),
            "price": getattr(quote, "price", 0),
            "change_pct": getattr(quote, "change_pct", 0),
            "volume": getattr(quote, "volume", 0),
            "turnover": getattr(quote, "turnover", 0),
            "high": getattr(quote, "high", 0),
            "low": getattr(quote, "low", 0),
            "open": getattr(quote, "open", 0),
            "prev_close": getattr(quote, "prev_close", 0),
        }
    except Exception as e:
        result["quote"] = {"error": str(e)}

    # 近 5 日 K 线（用于判断趋势）+ 交易指标
    try:
        from datetime import datetime, timedelta
        start = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        df = provider.get_kline(symbol, period="daily", start_date=start)
        if df is not None and not df.empty:
            recent = df.tail(5)
            result["recent_trend"] = {
                "days": len(recent),
                "close_prices": recent["close"].tolist(),
                "volumes": recent["volume"].tolist() if "volume" in recent.columns else [],
                "trend": "up" if recent["close"].iloc[-1] > recent["close"].iloc[0] else "down",
            }

            # 近 5 日振幅（用于判断市场活跃度）
            if "high" in recent.columns and "low" in recent.columns:
                highs = recent["high"].astype(float)
                lows = recent["low"].astype(float)
                closes = recent["close"].astype(float)
                daily_ranges = ((highs - lows) / closes * 100).tolist()
                result["volatility_hint"] = {
                    "daily_ranges_pct": [round(r, 2) for r in daily_ranges],
                    "avg_range_pct": round(sum(daily_ranges) / len(daily_ranges), 2),
                    "max_range_pct": round(max(daily_ranges), 2),
                }

            # 量价关系（近 5 日）
            if "volume" in recent.columns:
                vols = recent["volume"].astype(float).tolist()
                result["volume_price"] = {
                    "recent_5d_volumes": [round(v) for v in vols],
                    "avg_5d_volume": round(sum(vols) / len(vols)) if vols else 0,
                    "volume_trend": "increasing" if len(vols) >= 2 and vols[-1] > vols[0] else "decreasing",
                }

    except Exception as e:
        result["recent_trend"] = {"error": str(e)}

    return result
