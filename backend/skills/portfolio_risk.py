# backend/skills/portfolio_risk.py
# 投资组合风险评估技能 — 评估波动率、流动性、VaR、最大回撤等风险指标

from __future__ import annotations

import math
from typing import Any

import numpy as np

from backend.data.factory import get_provider
from backend.skills.registry import skill


@skill(
    name="portfolio_risk",
    description="评估股票的风险指标：波动率、流动性、VaR、最大回撤、风险评分",
    markets=["a_share", "h_stock", "us_stock"],
    category="trading",
    label="风险评估",
    params={},
    depends_on=["kline_data"],
)
def evaluate_portfolio_risk(
    symbol: str,
    market: str,
    kline_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """评估投资组合风险指标。

    依赖 kline_data 技能的输出（近 60 日 K 线数据），
    若未传入则自行获取近 120 日 K 线进行计算。

    返回：
    - volatility: 波动率指标（年化、日均）
    - liquidity: 流动性指标（换手率、成交量）
    - var_95: 95% 置信度 VaR（Value at Risk）
    - max_drawdown: 最大回撤
    - risk_score: 综合风险评分（0-100，越高风险越大）
    - risk_level: 风险等级（low/medium/high/extreme）
    """
    provider = get_provider(market)

    # 获取 K 线数据（优先使用上游 kline_data 技能的结果）
    df = _get_kline_df(provider, symbol, kline_data)

    if df is None or len(df) < 20:
        return {
            "error": f"K 线数据不足（需至少 20 个交易日，当前 {len(df) if df is not None else 0} 个）",
            "volatility": {},
            "liquidity": {},
            "var_95": None,
            "max_drawdown": None,
            "risk_score": 50,
            "risk_level": "medium",
        }

    # ── 1. 波动率计算 ──
    volatility = _calc_volatility(df)

    # ── 2. 流动性指标 ──
    liquidity = _calc_liquidity(df)

    # ── 3. VaR (Value at Risk) ──
    var_95 = _calc_var(df, confidence=0.95)

    # ── 4. 最大回撤 ──
    max_drawdown = _calc_max_drawdown(df)

    # ── 5. 综合风险评分 ──
    risk_score = _calc_risk_score(volatility, liquidity, var_95, max_drawdown)
    risk_level = _score_to_level(risk_score)

    # ── 6. 涨跌停风险 ──
    limit_risk = _calc_limit_risk(df)

    return {
        "volatility": volatility,
        "liquidity": liquidity,
        "var_95": var_95,
        "max_drawdown": max_drawdown,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "limit_risk": limit_risk,
    }


def _get_kline_df(provider: Any, symbol: str,
                   kline_data: dict[str, Any] | None) -> Any:
    """获取 K 线 DataFrame — 优先从上游技能结果提取，否则自行请求"""
    # 如果上游 kline_data 已提供数据，尝试从中提取
    if kline_data and "kline" in kline_data:
        raw = kline_data["kline"]
        if isinstance(raw, dict) and "data" in raw:
            import pandas as pd
            records = raw["data"]
            if isinstance(records, list) and len(records) > 0:
                return pd.DataFrame(records)

    # 自行获取近 120 日 K 线
    try:
        from datetime import datetime, timedelta
        start = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        df = provider.get_kline(symbol, period="daily", start_date=start)
        return df
    except Exception:
        return None


def _calc_volatility(df: Any) -> dict[str, Any]:
    """计算波动率指标"""
    try:
        close = df["close"].astype(float).values
        if len(close) < 5:
            return {"daily": 0, "annualized": 0, "level": "medium"}

        # 日收益率
        returns = np.diff(close) / close[:-1]
        daily_vol = float(np.std(returns))
        annualized_vol = daily_vol * math.sqrt(252)

        # 近 5 日 vs 近 20 日波动率对比
        recent_5_vol = float(np.std(returns[-5:])) if len(returns) >= 5 else daily_vol
        recent_20_vol = float(np.std(returns[-20:])) if len(returns) >= 20 else daily_vol
        vol_ratio = recent_5_vol / recent_20_vol if recent_20_vol > 0 else 1.0

        # 波动率等级
        if annualized_vol < 0.20:
            level = "low"
        elif annualized_vol < 0.40:
            level = "medium"
        elif annualized_vol < 0.60:
            level = "high"
        else:
            level = "extreme"

        return {
            "daily": round(daily_vol, 4),
            "annualized": round(annualized_vol, 4),
            "recent_5d": round(recent_5_vol, 4),
            "recent_20d": round(recent_20_vol, 4),
            "vol_ratio": round(vol_ratio, 2),
            "level": level,
        }
    except Exception:
        return {"daily": 0, "annualized": 0, "level": "medium"}


def _calc_liquidity(df: Any) -> dict[str, Any]:
    """计算流动性指标"""
    try:
        # 平均成交量（近 20 日）
        volumes = df["volume"].astype(float).values
        avg_volume_20 = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else float(np.mean(volumes))
        latest_volume = float(volumes[-1]) if len(volumes) > 0 else 0
        volume_ratio = latest_volume / avg_volume_20 if avg_volume_20 > 0 else 1.0

        # 成交额（如果有 turnover 字段）
        turnover_avg = None
        if "turnover" in df.columns:
            turnovers = df["turnover"].astype(float).values
            turnover_avg = float(np.mean(turnovers[-20:])) if len(turnovers) >= 20 else float(np.mean(turnovers))

        # 流动性评分（0-100）
        if avg_volume_20 > 1e7:
            volume_score = 90
        elif avg_volume_20 > 5e6:
            volume_score = 75
        elif avg_volume_20 > 1e6:
            volume_score = 55
        elif avg_volume_20 > 5e5:
            volume_score = 35
        else:
            volume_score = 15

        # 量比修正
        if volume_ratio > 2.0:
            volume_score = min(100, volume_score + 10)
        elif volume_ratio < 0.5:
            volume_score = max(0, volume_score - 20)

        if volume_score >= 75:
            level = "high"
        elif volume_score >= 50:
            level = "medium"
        else:
            level = "low"

        return {
            "avg_volume_20d": round(avg_volume_20, 0),
            "latest_volume": round(latest_volume, 0),
            "volume_ratio": round(volume_ratio, 2),
            "turnover_avg": round(turnover_avg, 2) if turnover_avg else None,
            "score": volume_score,
            "level": level,
        }
    except Exception:
        return {"score": 50, "level": "medium"}


def _calc_var(df: Any, confidence: float = 0.95) -> dict[str, Any]:
    """计算 Value at Risk (参数法)"""
    try:
        close = df["close"].astype(float).values
        if len(close) < 20:
            return {"daily_pct": 0, "level": "medium"}

        returns = np.diff(close) / close[:-1]
        mu = float(np.mean(returns))
        sigma = float(np.std(returns))

        # 参数法 VaR（正态分布假设）
        from scipy import stats
        z = stats.norm.ppf(1 - confidence)
        var_daily = -(mu + z * sigma)
        var_pct = round(var_daily * 100, 2)

        if abs(var_pct) < 2:
            level = "low"
        elif abs(var_pct) < 5:
            level = "medium"
        elif abs(var_pct) < 8:
            level = "high"
        else:
            level = "extreme"

        return {
            "daily_pct": var_pct,
            "confidence": confidence,
            "level": level,
        }
    except ImportError:
        # scipy 不可用时用简单百分位数法
        return _calc_var_percentile(df, confidence)
    except Exception:
        return {"daily_pct": 0, "level": "medium"}


def _calc_var_percentile(df: Any, confidence: float = 0.95) -> dict[str, Any]:
    """VaR 百分位数法（无需 scipy）"""
    try:
        close = df["close"].astype(float).values
        returns = np.diff(close) / close[:-1]
        var_pct = round(float(np.percentile(returns, (1 - confidence) * 100)) * 100, 2)
        return {"daily_pct": var_pct, "confidence": confidence, "level": "medium"}
    except Exception:
        return {"daily_pct": 0, "level": "medium"}


def _calc_max_drawdown(df: Any) -> dict[str, Any]:
    """计算最大回撤"""
    try:
        close = df["close"].astype(float).values
        if len(close) < 2:
            return {"pct": 0, "peak_price": 0, "trough_price": 0, "level": "medium"}

        # 累计最大值
        running_max = np.maximum.accumulate(close)
        drawdowns = (close - running_max) / running_max

        max_dd = float(np.min(drawdowns))
        max_dd_pct = round(max_dd * 100, 2)

        # 找到最大回撤的峰谷位置
        trough_idx = int(np.argmin(drawdowns))
        peak_idx = int(np.argmax(close[:trough_idx + 1])) if trough_idx > 0 else 0

        if abs(max_dd_pct) < 5:
            level = "low"
        elif abs(max_dd_pct) < 15:
            level = "medium"
        elif abs(max_dd_pct) < 30:
            level = "high"
        else:
            level = "extreme"

        return {
            "pct": max_dd_pct,
            "peak_price": round(float(close[peak_idx]), 2),
            "trough_price": round(float(close[trough_idx]), 2),
            "peak_to_trough_days": trough_idx - peak_idx,
            "level": level,
        }
    except Exception:
        return {"pct": 0, "level": "medium"}


def _calc_risk_score(
    volatility: dict, liquidity: dict,
    var_95: dict | None, max_drawdown: dict | None,
) -> int:
    """综合风险评分（0-100，越高风险越大）

    权重分配：
    - 波动率 35%
    - VaR 25%
    - 最大回撤 25%
    - 流动性 15%（流动性越差风险越高）
    """
    scores = {}

    # 波动率评分
    vol_ann = volatility.get("annualized", 0)
    if vol_ann < 0.15:
        scores["volatility"] = 15
    elif vol_ann < 0.25:
        scores["volatility"] = 30
    elif vol_ann < 0.40:
        scores["volatility"] = 50
    elif vol_ann < 0.60:
        scores["volatility"] = 70
    else:
        scores["volatility"] = 90

    # VaR 评分
    var_pct = abs((var_95 or {}).get("daily_pct", 0))
    if var_pct < 2:
        scores["var"] = 15
    elif var_pct < 4:
        scores["var"] = 35
    elif var_pct < 6:
        scores["var"] = 55
    elif var_pct < 8:
        scores["var"] = 75
    else:
        scores["var"] = 90

    # 最大回撤评分
    dd_pct = abs((max_drawdown or {}).get("pct", 0))
    if dd_pct < 5:
        scores["drawdown"] = 10
    elif dd_pct < 15:
        scores["drawdown"] = 35
    elif dd_pct < 25:
        scores["drawdown"] = 55
    elif dd_pct < 40:
        scores["drawdown"] = 75
    else:
        scores["drawdown"] = 95

    # 流动性评分（反向：流动性差 → 风险高）
    liq_score = (liquidity or {}).get("score", 50)
    scores["liquidity"] = 100 - liq_score

    # 加权平均
    weighted = (
        scores["volatility"] * 0.35
        + scores["var"] * 0.25
        + scores["drawdown"] * 0.25
        + scores["liquidity"] * 0.15
    )
    return min(100, max(0, round(weighted)))


def _score_to_level(score: int) -> str:
    """风险评分 → 风险等级"""
    if score < 25:
        return "low"
    elif score < 50:
        return "medium"
    elif score < 75:
        return "high"
    else:
        return "extreme"


def _calc_limit_risk(df: Any) -> dict[str, Any]:
    """涨跌停风险评估"""
    try:
        close = df["close"].astype(float).values
        if len(close) < 5:
            return {"consecutive_limit_count": 0, "level": "low"}

        # 检查近 5 日是否有涨跌停（A 股 ±10%）
        recent = close[-5:]
        changes = np.diff(recent) / recent[:-1]

        limit_count = 0
        for c in changes:
            if abs(c) >= 0.095:
                limit_count += 1

        # 连续涨跌停风险
        consecutive = 0
        for c in reversed(list(changes)):
            if abs(c) >= 0.095:
                consecutive += 1
            else:
                break

        if consecutive >= 3:
            level = "extreme"
        elif consecutive >= 2:
            level = "high"
        elif limit_count >= 2:
            level = "medium"
        else:
            level = "low"

        return {
            "recent_limit_count": limit_count,
            "consecutive_limit_count": consecutive,
            "level": level,
        }
    except Exception:
        return {"recent_limit_count": 0, "level": "low"}
