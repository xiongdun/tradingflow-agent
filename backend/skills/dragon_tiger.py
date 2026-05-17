# backend/skills/dragon_tiger.py
# 龙虎榜技能 — 获取龙虎榜数据，追踪机构和游资买卖动向

from __future__ import annotations

from typing import Any

from backend.skills.registry import skill


@skill(
    name="dragon_tiger",
    description="获取龙虎榜数据（机构/游资买卖明细），追踪主力资金动向",
    markets=["a_share"],
    category="sentiment",
    label="龙虎榜",
)
def get_dragon_tiger(symbol: str, market: str = "a_share") -> dict[str, Any]:
    """获取 A 股龙虎榜数据，包含上榜日期、原因、买卖金额等"""
    import akshare as ak
    result: dict[str, Any] = {"symbol": symbol, "market": "a_share", "listings": [], "summary": ""}

    try:
        # 获取近 30 天龙虎榜明细数据
        df = ak.stock_lhb_detail_em(
            start_date=(__import__("datetime").datetime.now() - __import__("datetime").timedelta(days=30)).strftime("%Y%m%d"),
            end_date=__import__("datetime").datetime.now().strftime("%Y%m%d"),
        )
        if df is not None and not df.empty:
            # 筛选目标股票的上榜记录
            stock_data = df[df["代码"].astype(str) == symbol]
            if not stock_data.empty:
                for _, row in stock_data.head(5).iterrows():
                    result["listings"].append({
                        "date": str(row.get("上榜日期", "")),
                        "reason": str(row.get("上榜原因", "")),
                        "close": str(row.get("收盘价", "")),
                        "change_pct": str(row.get("涨跌幅", "")),
                        "buy_total": str(row.get("龙虎榜买入额", "")),
                        "sell_total": str(row.get("龙虎榜卖出额", "")),
                        "net_buy": str(row.get("龙虎榜净买额", "")),
                    })
                result["summary"] = f"近30天上榜 {len(stock_data)} 次"
            else:
                result["summary"] = "近30天未上龙虎榜"
    except Exception as e:
        result["error"] = str(e)
        result["summary"] = "龙虎榜数据获取失败"

    return result
