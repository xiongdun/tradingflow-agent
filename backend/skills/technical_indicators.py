# backend/skills/technical_indicators.py
# 技术指标计算技能 — 基于 K 线数据本地计算 MA/MACD/RSI/BOLL/KDJ

from __future__ import annotations

from typing import Any

from backend.data.factory import get_provider
from backend.skills.registry import skill


@skill(
    name="technical_indicators",
    description="计算技术指标（MA/MACD/RSI/BOLL/KDJ），返回当前信号和综合判断",
    markets=["a_share", "h_stock", "us_stock"],
    category="technical",
    label="技术指标",
)
def get_technical_indicators(symbol: str, market: str) -> dict[str, Any]:
    """获取 K 线数据并计算全部技术指标，返回信号判断"""
    import pandas as pd
    provider = get_provider(market)
    from datetime import datetime, timedelta
    start = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    df = provider.get_kline(symbol, period="daily", start_date=start)

    if df.empty:
        return {"error": "No data found"}

    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)

    # ── MA 均线 ──
    ma5 = close.rolling(5).mean()
    ma10 = close.rolling(10).mean()
    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()
    latest_close = close.iloc[-1]
    ma_signal = "bullish" if ma5.iloc[-1] > ma20.iloc[-1] else "bearish"

    # ── MACD ──
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9).mean()
    histogram = dif - dea
    if dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2]:
        macd_signal = "golden_cross"
    elif dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2]:
        macd_signal = "dead_cross"
    else:
        macd_signal = "neutral"

    # ── RSI ──
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, 1e-10)
    rsi14 = 100 - (100 / (1 + rs))
    rsi6_gain = delta.where(delta > 0, 0).rolling(6).mean()
    rsi6_loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
    rsi6 = 100 - (100 / (1 + rsi6_gain / rsi6_loss.replace(0, 1e-10)))
    rsi_val = rsi14.iloc[-1]
    if rsi_val > 70:
        rsi_signal = "overbought"
    elif rsi_val < 30:
        rsi_signal = "oversold"
    else:
        rsi_signal = "neutral"

    # ── BOLL 布林带 ──
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    if latest_close > bb_upper.iloc[-1]:
        boll_position = "above"
    elif latest_close < bb_lower.iloc[-1]:
        boll_position = "below"
    else:
        boll_position = "within"

    # ── KDJ ──
    low_min = low.rolling(9).min()
    high_max = high.rolling(9).max()
    rsv = (close - low_min) / (high_max - low_min).replace(0, 1e-10) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    j = 3 * k - 2 * d
    if k.iloc[-1] > d.iloc[-1] and k.iloc[-2] <= d.iloc[-2]:
        kdj_signal = "golden_cross"
    elif k.iloc[-1] < d.iloc[-1] and k.iloc[-2] >= d.iloc[-2]:
        kdj_signal = "dead_cross"
    else:
        kdj_signal = "neutral"

    # ── OBV 能量潮 ──
    vol = df["volume"].astype(float)
    obv = (close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0)) * vol).cumsum()
    obv_ma = obv.rolling(20).mean()
    obv_signal = "bullish" if obv.iloc[-1] > obv_ma.iloc[-1] else "bearish"

    # ── WR 威廉指标 ──
    wr_period = 14
    wr_high = high.rolling(wr_period).max()
    wr_low = low.rolling(wr_period).min()
    wr = -100 * (wr_high - close) / (wr_high - wr_low).replace(0, 1e-10)
    wr_val = wr.iloc[-1]
    wr_signal = "overbought" if wr_val > -20 else ("oversold" if wr_val < -80 else "neutral")

    # ── CCI 顺势指标 ──
    tp = (high + low + close) / 3
    cci_sma = tp.rolling(20).mean()
    cci_mad = tp.rolling(20).apply(lambda x: abs(x - x.mean()).mean(), raw=True)
    cci = (tp - cci_sma) / (0.015 * cci_mad).replace(0, 1e-10)
    cci_val = cci.iloc[-1]
    cci_signal = "overbought" if cci_val > 100 else ("oversold" if cci_val < -100 else "neutral")

    # ── DMI/ADX 趋向指标 ──
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr14 = tr.rolling(14).sum()
    plus_di = 100 * plus_dm.rolling(14).sum() / atr14.replace(0, 1e-10)
    minus_di = 100 * minus_dm.rolling(14).sum() / atr14.replace(0, 1e-10)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1e-10)
    adx = dx.rolling(14).mean()
    adx_val = adx.iloc[-1]
    dmi_signal = "bullish" if plus_di.iloc[-1] > minus_di.iloc[-1] else "bearish"

    # ── 综合信号统计 ──
    signals = {
        "ma": ma_signal,
        "macd": macd_signal,
        "rsi": rsi_signal,
        "boll": "bearish" if boll_position == "above" else ("bullish" if boll_position == "below" else "neutral"),
        "kdj": kdj_signal,
        "obv": obv_signal,
        "wr": wr_signal,
        "cci": cci_signal,
        "dmi": dmi_signal,
    }
    bullish_count = sum(1 for v in signals.values() if v in ("bullish", "golden_cross", "oversold"))
    bearish_count = sum(1 for v in signals.values() if v in ("bearish", "dead_cross", "overbought"))
    total_signals = len(signals)
    if bullish_count > bearish_count:
        overall = "bullish"
    elif bearish_count > bullish_count:
        overall = "bearish"
    else:
        overall = "neutral"

    return {
        "symbol": symbol,
        "latest_price": round(float(latest_close), 2),
        "ma": {
            "ma5": _round(ma5.iloc[-1]),
            "ma10": _round(ma10.iloc[-1]),
            "ma20": _round(ma20.iloc[-1]),
            "ma60": _round(ma60.iloc[-1]),
            "signal": ma_signal,
        },
        "macd": {
            "dif": _round(dif.iloc[-1], 4),
            "dea": _round(dea.iloc[-1], 4),
            "histogram": _round(histogram.iloc[-1], 4),
            "signal": macd_signal,
        },
        "rsi": {
            "rsi6": _round(rsi6.iloc[-1]),
            "rsi14": _round(rsi14.iloc[-1]),
            "signal": rsi_signal,
        },
        "boll": {
            "upper": _round(bb_upper.iloc[-1]),
            "middle": _round(bb_mid.iloc[-1]),
            "lower": _round(bb_lower.iloc[-1]),
            "position": boll_position,
        },
        "kdj": {
            "k": _round(k.iloc[-1]),
            "d": _round(d.iloc[-1]),
            "j": _round(j.iloc[-1]),
            "signal": kdj_signal,
        },
        "obv": {
            "value": _round(obv.iloc[-1]),
            "ma20": _round(obv_ma.iloc[-1]),
            "signal": obv_signal,
        },
        "wr": {
            "value": _round(wr_val),
            "signal": wr_signal,
        },
        "cci": {
            "value": _round(cci_val),
            "signal": cci_signal,
        },
        "dmi": {
            "plus_di": _round(plus_di.iloc[-1]),
            "minus_di": _round(minus_di.iloc[-1]),
            "adx": _round(adx_val),
            "signal": dmi_signal,
        },
        "overall_signal": overall,
        "signal_count": {
            "bullish": bullish_count,
            "bearish": bearish_count,
            "neutral": total_signals - bullish_count - bearish_count,
        },
    }


def _round(val: Any, digits: int = 2) -> float | None:
    import pandas as pd
    if pd.isna(val):
        return None
    return round(float(val), digits)
