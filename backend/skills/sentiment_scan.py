# backend/skills/sentiment_scan.py
# 情绪扫描技能 — 分析市场情绪指标（量比/换手率/资金流向等）

from __future__ import annotations

from typing import Any

from backend.skills.registry import skill


@skill(
    name="sentiment_scan",
    description="扫描股票市场情绪指标（量比/换手率/涨跌停/资金流向等），用于情绪面分析",
    markets=["a_share", "h_stock", "us_stock"],
    category="sentiment",
)
def scan_sentiment(symbol: str, market: str) -> dict[str, Any]:
    """扫描股票市场情绪指标，返回情绪面分析数据"""
    if market == "a_share":
        return _scan_a_share_sentiment(symbol)
    return _scan_yfinance_sentiment(symbol, market)


def _scan_a_share_sentiment(symbol: str) -> dict[str, Any]:
    """扫描 A 股市场情绪指标，包括资金流向、量比、换手率、振幅等"""
    import akshare as ak
    result = {"symbol": symbol, "market": "a_share", "indicators": {}}

    # 根据股票代码判断交易所：6开头=上海，0/3开头=深圳
    exchange = "sh" if symbol.startswith("6") else "sz"

    try:
        # 获取个股资金流向数据（主力/散户净流入）
        df = ak.stock_individual_fund_flow(stock=symbol, market=exchange)
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            result["indicators"]["fund_flow"] = {
                "main_net_inflow": str(latest.get("主力净流入-净额", "N/A")),
                "retail_net_inflow": str(latest.get("小单净流入-净额", "N/A")),
            }
    except Exception:
        pass

    try:
        # 从全市场行情数据中提取量比、换手率、振幅
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == symbol]
        if not row.empty:
            r = row.iloc[0]
            result["indicators"]["volume_ratio"] = (
                float(r["量比"]) if r.get("量比") is not None and str(r["量比"]) != "-" else None
            )
            result["indicators"]["turnover_rate"] = (
                float(r["换手率"]) if r.get("换手率") is not None and str(r["换手率"]) != "-" else None
            )
            result["indicators"]["amplitude"] = (
                float(r["振幅"]) if r.get("振幅") is not None and str(r["振幅"]) != "-" else None
            )
    except Exception:
        pass

    # 根据量比推导情绪标签：量比>2为高活跃，<0.5为低迷
    vol_ratio = result["indicators"].get("volume_ratio")
    if vol_ratio and vol_ratio > 2:
        result["sentiment_label"] = "high_activity"
        result["sentiment_desc"] = f"量比 {vol_ratio}，市场交投活跃"
    elif vol_ratio and vol_ratio < 0.5:
        result["sentiment_label"] = "low_activity"
        result["sentiment_desc"] = f"量比 {vol_ratio}，市场交投低迷"
    else:
        result["sentiment_label"] = "normal"
        result["sentiment_desc"] = "市场交投正常"

    return result


def _scan_yfinance_sentiment(symbol: str, market: str) -> dict[str, Any]:
    """通过 yfinance 扫描港股/美股情绪指标（量比、涨跌趋势、Beta、波动率）"""
    import yfinance as yf
    import pandas as pd
    result = {"symbol": symbol, "market": market, "indicators": {}}

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")

        if hist is not None and not hist.empty and len(hist) >= 5:
            # 近 5 日成交量 vs 近 20 日均量 → 量比
            vol_5 = hist["Volume"].tail(5).mean()
            vol_20 = hist["Volume"].tail(20).mean()
            if vol_20 > 0:
                result["indicators"]["volume_ratio"] = round(vol_5 / vol_20, 2)

            # 近 5 日涨跌幅
            close_5 = hist["Close"].iloc[-5:]
            pct_change_5d = (close_5.iloc[-1] - close_5.iloc[0]) / close_5.iloc[0] * 100
            result["indicators"]["change_5d_pct"] = round(float(pct_change_5d), 2)

            # 近 5 日涨跌方向统计
            daily_returns = close_5.pct_change().dropna()
            up_days = int((daily_returns > 0).sum())
            result["indicators"]["up_days_5"] = up_days
            result["indicators"]["down_days_5"] = len(daily_returns) - up_days

            # 波动率（近 20 日年化）
            returns_20 = hist["Close"].tail(20).pct_change().dropna()
            if len(returns_20) > 1:
                vol_annual = float(returns_20.std() * (252 ** 0.5) * 100)
                result["indicators"]["volatility_annual_pct"] = round(vol_annual, 2)

    except Exception:
        pass

    # 从 yfinance info 获取 Beta
    try:
        info = ticker.info
        beta = info.get("beta")
        if beta is not None:
            result["indicators"]["beta"] = round(float(beta), 2)
    except Exception:
        pass

    # 综合情绪判定
    vol_ratio = result["indicators"].get("volume_ratio")
    change_5d = result["indicators"].get("change_5d_pct", 0)
    up_days = result["indicators"].get("up_days_5", 0)
    beta = result["indicators"].get("beta")

    score = 0  # -3 极度看空，+3 极度看多
    if vol_ratio:
        if vol_ratio > 1.5:
            score += 1  # 放量
        elif vol_ratio < 0.5:
            score -= 1  # 缩量
    if change_5d > 3:
        score += 1
    elif change_5d < -3:
        score -= 1
    if up_days >= 4:
        score += 1
    elif up_days <= 1:
        score -= 1
    if beta and beta > 1.5:
        # 高 Beta 股在放量时情绪更极端
        if vol_ratio and vol_ratio > 1.5:
            score += 1 if change_5d > 0 else -1

    if score >= 2:
        result["sentiment_label"] = "bullish"
        result["sentiment_desc"] = f"近5日涨{change_5d:.1f}%，量比{vol_ratio}，市场情绪偏多"
    elif score <= -2:
        result["sentiment_label"] = "bearish"
        result["sentiment_desc"] = f"近5日跌{change_5d:.1f}%，量比{vol_ratio}，市场情绪偏空"
    elif vol_ratio and vol_ratio > 2:
        result["sentiment_label"] = "high_activity"
        result["sentiment_desc"] = f"量比{vol_ratio}，交投活跃但方向不明"
    elif vol_ratio and vol_ratio < 0.5:
        result["sentiment_label"] = "low_activity"
        result["sentiment_desc"] = f"量比{vol_ratio}，交投低迷"
    else:
        result["sentiment_label"] = "neutral"
        result["sentiment_desc"] = "市场情绪中性"

    return result
