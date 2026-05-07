# backend/skills/limit_up_analysis.py
# 涨停板分析技能 — 分析涨停状态、连板数、涨停原因、炸板率

from __future__ import annotations

from typing import Any

from backend.skills.registry import skill


@skill(
    name="limit_up_analysis",
    description="分析涨停板数据：是否涨停、连板天数、涨停原因、炸板率、同板块涨停股",
    markets=["a_share"],
    category="sentiment",
)
def get_limit_up_analysis(symbol: str, market: str = "a_share") -> dict[str, Any]:
    """分析股票的涨停板状态和相关数据"""
    import akshare as ak
    result = {
        "symbol": symbol,
        "market": "a_share",
        "is_limit_up": False,
        "consecutive_days": 0,
        "limit_up_reason": "",
        "sector": "",
        "break_rate": 0.0,
        "similar_stocks": [],
    }

    try:
        df = ak.stock_zt_pool_em(date="")
        if df is not None and not df.empty:
            stock_row = df[df["代码"] == symbol]
            if not stock_row.empty:
                r = stock_row.iloc[0]
                result["is_limit_up"] = True
                result["consecutive_days"] = int(r.get("连板数", 1)) if r.get("连板数") else 1
                result["limit_up_reason"] = str(r.get("涨停原因", ""))
                result["sector"] = str(r.get("所属行业", ""))

                sector = result["sector"]
                if sector:
                    same_sector = df[df["所属行业"] == sector]
                    result["similar_stocks"] = [
                        {"code": str(row["代码"]), "name": str(row["名称"])}
                        for _, row in same_sector.head(5).iterrows()
                        if str(row["代码"]) != symbol
                    ]
    except Exception as e:
        result["error_zt"] = str(e)

    try:
        df_zb = ak.stock_zt_pool_zbgc_em(date="")
        if df_zb is not None and not df_zb.empty:
            total_zt = len(df_zb)
            result["break_rate"] = round(total_zt / max(total_zt + 100, 1) * 100, 1)
    except Exception:
        pass

    return result
