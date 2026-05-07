# backend/skills/fund_flow.py
# 主力资金流向技能 — 获取个股主力/散户资金净流入数据

from __future__ import annotations

from typing import Any

from backend.skills.registry import skill


@skill(
    name="fund_flow",
    description="获取个股主力资金流向（大单/超大单/中单/小单净流入），判断资金趋势",
    markets=["a_share"],
    category="sentiment",
)
def get_fund_flow(symbol: str, market: str = "a_share") -> dict[str, Any]:
    """获取个股资金流向明细，分析主力和散户资金动向"""
    import akshare as ak
    result = {"symbol": symbol, "market": "a_share", "flow": {}, "trend": "neutral", "days_inflow": 0}

    try:
        df = ak.stock_individual_fund_flow(stock=symbol, market="sh")
        if df is None or df.empty:
            df = ak.stock_individual_fund_flow(stock=symbol, market="sz")
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            result["flow"] = {
                "main_net_inflow": _to_float(latest.get("主力净流入-净额")),
                "super_large_net": _to_float(latest.get("超大单净流入-净额")),
                "large_net": _to_float(latest.get("大单净流入-净额")),
                "medium_net": _to_float(latest.get("中单净流入-净额")),
                "small_net": _to_float(latest.get("小单净流入-净额")),
            }
            main_val = result["flow"].get("main_net_inflow") or 0
            if main_val > 0:
                result["trend"] = "inflow"
            elif main_val < 0:
                result["trend"] = "outflow"

            if "主力净流入-净额" in df.columns:
                consecutive = 0
                for _, row in df.iloc[::-1].iterrows():
                    val = _to_float(row.get("主力净流入-净额"))
                    if val and val > 0:
                        consecutive += 1
                    else:
                        break
                result["days_inflow"] = consecutive
    except Exception as e:
        result["error"] = str(e)

    return result


def _to_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return round(f, 2) if not (f != f) else None
    except (ValueError, TypeError):
        return None
