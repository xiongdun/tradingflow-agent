# backend/skills/macro_indicators.py
# 宏观指标技能 — 获取宏观经济数据（CPI/PMI/利率等）

from __future__ import annotations

from typing import Any

from backend.skills.registry import skill


@skill(
    name="macro_indicators",
    description="获取宏观经济指标（GDP/CPI/PMI/利率/汇率等），用于宏观分析背景",
    markets=["a_share", "h_stock", "us_stock"],
    category="macro",
    label="宏观指标",
)
def get_macro_indicators(symbol: str, market: str) -> dict[str, Any]:
    """获取与当前市场相关的宏观经济指标"""
    if market in ("a_share", "h_stock"):
        return _get_china_macro()
    elif market == "us_stock":
        return _get_us_macro()
    return {"market": market, "indicators": {}}


def _get_china_macro() -> dict[str, Any]:
    """通过 AKShare 获取中国宏观经济指标（CPI、PMI、Shibor）"""
    import akshare as ak
    indicators = {}
    try:
        # 获取月度 CPI 数据
        df = ak.macro_china_cpi_monthly()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            indicators["cpi"] = str(latest.to_dict())
    except Exception:
        pass

    try:
        # 获取 PMI 采购经理指数
        df = ak.macro_china_pmi()
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            indicators["pmi"] = str(latest.to_dict())
    except Exception:
        pass

    try:
        # 获取 Shibor 上海银行间同业拆放利率（1月期）
        df = ak.rate_interbank(market="上海银行间同业拆放利率(Shibor)", symbol="Shibor人民币", indicator="1月")
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            indicators["shibor_1m"] = str(latest.to_dict())
    except Exception:
        pass

    return {"market": "china", "indicators": indicators}


def _get_us_macro() -> dict[str, Any]:
    """美国宏观指标占位符（需接入 FRED API）"""
    return {
        "market": "us",
        "indicators": {},
        "note": "US macro data requires FRED API integration",
    }
