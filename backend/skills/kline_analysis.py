# backend/skills/kline_analysis.py
# K线分析技能 — 获取 OHLCV 数据并计算技术指标

from __future__ import annotations

from typing import Any

from backend.data.factory import get_provider
from backend.skills.registry import skill


@skill(
    name="kline_data",
    description="获取股票K线历史数据（OHLCV），支持日K/周K/月K",
    markets=["a_share", "h_stock", "us_stock", "bond", "futures", "crypto"],
    category="technical",
    label="K线数据",
    params={"period": "daily|weekly|monthly", "days": "number of days"},
)
def get_kline_data(symbol: str, market: str, period: str = "daily", days: int = 120) -> dict[str, Any]:
    """获取K线数据并计算技术指标（MA/RSI/MACD/布林带）"""
    import pandas as pd
    provider = get_provider(market)
    from datetime import datetime, timedelta
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    df = provider.get_kline(symbol, period=period, start_date=start)

    if df.empty:
        return {"error": "No data found", "bars": []}

    # ── 计算均线指标 ──
    df["ma5"] = df["close"].rolling(5).mean()     # 5日均线
    df["ma10"] = df["close"].rolling(10).mean()   # 10日均线
    df["ma20"] = df["close"].rolling(20).mean()   # 20日均线
    df["ma60"] = df["close"].rolling(60).mean()   # 60日均线

    # ── RSI 相对强弱指标（14周期）──
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, 1e-10)  # 避免除零
    df["rsi14"] = 100 - (100 / (1 + rs))

    # ── MACD 指标 ──
    ema12 = df["close"].ewm(span=12).mean()       # 12日EMA
    ema26 = df["close"].ewm(span=26).mean()       # 26日EMA
    df["macd"] = ema12 - ema26                     # DIF 线
    df["macd_signal"] = df["macd"].ewm(span=9).mean()  # DEA 信号线
    df["macd_hist"] = df["macd"] - df["macd_signal"]    # MACD 柱状图

    # ── 布林带（20周期，2倍标准差）──
    df["bb_mid"] = df["close"].rolling(20).mean()
    bb_std = df["close"].rolling(20).std()
    df["bb_upper"] = df["bb_mid"] + 2 * bb_std    # 上轨
    df["bb_lower"] = df["bb_mid"] - 2 * bb_std    # 下轨

    # 取最新一根K线的指标值
    latest = df.iloc[-1]
    return {
        "symbol": symbol,
        "latest_price": float(latest["close"]),
        "ma5": round(float(latest.get("ma5", 0)), 2) if pd.notna(latest.get("ma5")) else None,
        "ma10": round(float(latest.get("ma10", 0)), 2) if pd.notna(latest.get("ma10")) else None,
        "ma20": round(float(latest.get("ma20", 0)), 2) if pd.notna(latest.get("ma20")) else None,
        "ma60": round(float(latest.get("ma60", 0)), 2) if pd.notna(latest.get("ma60")) else None,
        "rsi14": round(float(latest.get("rsi14", 50)), 2) if pd.notna(latest.get("rsi14")) else None,
        "macd": round(float(latest.get("macd", 0)), 4) if pd.notna(latest.get("macd")) else None,
        "macd_signal": round(float(latest.get("macd_signal", 0)), 4) if pd.notna(latest.get("macd_signal")) else None,
        "macd_hist": round(float(latest.get("macd_hist", 0)), 4) if pd.notna(latest.get("macd_hist")) else None,
        "bb_upper": round(float(latest.get("bb_upper", 0)), 2) if pd.notna(latest.get("bb_upper")) else None,
        "bb_lower": round(float(latest.get("bb_lower", 0)), 2) if pd.notna(latest.get("bb_lower")) else None,
        "volume": float(latest.get("volume", 0)),
        "recent_trend": _describe_trend(df),
    }


def _describe_trend(df) -> str:
    """根据最近5根K线生成简短的趋势描述"""
    if len(df) < 5:
        return "数据不足"
    recent = df.tail(5)
    pct = (recent["close"].iloc[-1] - recent["close"].iloc[0]) / recent["close"].iloc[0] * 100
    if pct > 3:
        return f"近5日强势上涨 {pct:.1f}%"
    elif pct > 0:
        return f"近5日小幅上涨 {pct:.1f}%"
    elif pct > -3:
        return f"近5日小幅下跌 {pct:.1f}%"
    else:
        return f"近5日明显下跌 {pct:.1f}%"
