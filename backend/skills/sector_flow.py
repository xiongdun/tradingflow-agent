# backend/skills/sector_flow.py
# 板块资金流向技能 — 追踪行业板块资金流入流出情况

from __future__ import annotations

from typing import Any

from backend.skills.registry import skill


@skill(
    name="sector_flow",
    description="获取行业板块资金流向数据，判断资金轮动方向",
    markets=["a_share"],
    category="sentiment",
    label="板块流向",
)
def get_sector_flow(symbol: str, market: str = "a_share") -> dict[str, Any]:
    """获取行业板块资金流向排名，识别当日热门板块"""
    import akshare as ak
    result: dict[str, Any] = {"symbol": symbol, "market": "a_share", "sectors": [], "hot_sectors": []}

    try:
        # 获取今日板块资金流向排名
        df = ak.stock_sector_fund_flow_rank(indicator="今日")
        if df is not None and not df.empty:
            # 取前 10 个板块的流向数据
            for _, row in df.head(10).iterrows():
                sector_info = {
                    "name": str(row.get("名称", "")),
                    "change_pct": str(row.get("今日涨跌幅", "")),
                    "main_net_inflow": str(row.get("主力净流入-净额", "")),
                }
                result["sectors"].append(sector_info)

            # 筛选主力资金净流入为正的热门板块（最多 5 个）
            for _, row in df.iterrows():
                try:
                    inflow = float(row.get("主力净流入-净额", 0))
                    if inflow > 0:
                        result["hot_sectors"].append(str(row.get("名称", "")))
                except (ValueError, TypeError):
                    pass
                if len(result["hot_sectors"]) >= 5:
                    break
    except Exception as e:
        result["error"] = str(e)

    return result
