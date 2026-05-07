# backend/skills/shareholder_analysis.py
# 股东分析技能 — 获取前十大流通股东和机构持仓变动

from __future__ import annotations

from typing import Any

from backend.skills.registry import skill


@skill(
    name="shareholder_analysis",
    description="获取股东变动数据（前十大流通股东/机构持仓比例/变动趋势）",
    markets=["a_share"],
    category="fundamental",
)
def get_shareholder_analysis(symbol: str, market: str = "a_share") -> dict[str, Any]:
    """获取股票的股东结构和变动数据"""
    import akshare as ak
    result = {
        "symbol": symbol,
        "market": "a_share",
        "top10_holders": [],
        "institution_count": 0,
        "institution_holding_pct": 0.0,
        "change_trend": "stable",
    }

    try:
        df = ak.stock_gdfx_free_holding_analyse_em(symbol=symbol)
        if df is not None and not df.empty:
            for _, row in df.head(10).iterrows():
                holder = {
                    "name": str(row.get("股东名称", "")),
                    "holding_pct": _to_float(row.get("占流通股比例")),
                    "change": str(row.get("变动", "")),
                    "holding_type": str(row.get("股东性质", "")),
                }
                result["top10_holders"].append(holder)

            institutions = [h for h in result["top10_holders"] if "机构" in h.get("holding_type", "") or "基金" in h.get("name", "")]
            result["institution_count"] = len(institutions)
            result["institution_holding_pct"] = round(sum(h["holding_pct"] or 0 for h in institutions), 2)

            changes = [h["change"] for h in result["top10_holders"] if h["change"]]
            increases = sum(1 for c in changes if "增" in c)
            decreases = sum(1 for c in changes if "减" in c)
            if increases > decreases:
                result["change_trend"] = "increasing"
            elif decreases > increases:
                result["change_trend"] = "decreasing"
    except Exception as e:
        result["error"] = str(e)

    return result


def _to_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return round(float(val), 2)
    except (ValueError, TypeError):
        return None
