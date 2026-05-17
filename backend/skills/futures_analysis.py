# backend/skills/futures_analysis.py
# 期货技术分析技能 — 获取期货 K 线并计算技术指标

from __future__ import annotations

from typing import Any

from backend.data.factory import get_provider
from backend.skills.registry import skill


@skill(
    name="futures_analysis",
    description="期货技术分析 — K线数据、均线、RSI、MACD等指标",
    markets=["futures"],
    category="technical",
    label="期货技术分析",
    params={"symbol": "合约代码", "days": "分析天数"},
)
def get_futures_analysis(symbol: str, market: str, days: int = 120, **kwargs: Any) -> dict[str, Any]:
    import pandas as pd
    provider = get_provider(market)
    try:
        from datetime import datetime, timedelta
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        df = provider.get_kline(symbol, period="daily", start_date=start)
        if df.empty:
            return {"error": "No data found", "symbol": symbol}
        result: dict[str, Any] = {"symbol": symbol, "bars": []}
        if "close" in df.columns:
            for n in [5, 10, 20, 60]:
                df[f"ma{n}"] = df["close"].rolling(n).mean()
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            df["rsi"] = 100 - (100 / (1 + gain / loss))
            ema12 = df["close"].ewm(span=12).mean()
            ema26 = df["close"].ewm(span=26).mean()
            df["macd"] = ema12 - ema26
            df["signal"] = df["macd"].ewm(span=9).mean()
            df["bb_mid"] = df["close"].rolling(20).mean()
            df["bb_std"] = df["close"].rolling(20).std()
            latest = df.iloc[-1]
            result["indicators"] = {
                "ma5": round(float(latest.get("ma5", 0)), 2) if pd.notna(latest.get("ma5")) else None,
                "ma20": round(float(latest.get("ma20", 0)), 2) if pd.notna(latest.get("ma20")) else None,
                "rsi": round(float(latest.get("rsi", 50)), 2) if pd.notna(latest.get("rsi")) else None,
                "macd": round(float(latest.get("macd", 0)), 4) if pd.notna(latest.get("macd")) else None,
            }
        for _, row in df.iterrows():
            bar: dict[str, Any] = {}
            for col in df.columns:
                val = row[col]
                if pd.notna(val):
                    bar[col] = float(val) if isinstance(val, (int, float)) else str(val)
            if "date" in bar:
                bar["date"] = str(bar["date"])[:10]
            result["bars"].append(bar)
        return result
    except Exception as e:
        return {"error": str(e), "symbol": symbol}
