# backend/skills/block_trade.py
# 大宗交易技能 — 获取个股大宗交易数据

from __future__ import annotations

from typing import Any

from backend.skills.registry import skill


@skill(
    name="block_trade",
    description="获取大宗交易数据（成交价/溢折价率/买卖方向），追踪机构大额交易动向",
    markets=["a_share"],
    category="data",
)
def get_block_trade(symbol: str, market: str = "a_share") -> dict[str, Any]:
    """获取个股近期大宗交易记录"""
    import akshare as ak
    result = {"symbol": symbol, "market": "a_share", "recent_trades": [], "summary": "", "net_direction": "neutral"}

    try:
        df = ak.stock_dzjy_sctj()
        if df is not None and not df.empty:
            stock_data = df[df["证券代码"].astype(str) == symbol]
            if not stock_data.empty:
                for _, row in stock_data.head(10).iterrows():
                    trade = {
                        "date": str(row.get("交易日期", "")),
                        "price": _to_float(row.get("成交价")),
                        "volume": _to_float(row.get("成交量")),
                        "amount": _to_float(row.get("成交额")),
                        "premium_discount": _to_float(row.get("溢折价率")),
                    }
                    result["recent_trades"].append(trade)

                premiums = [t["premium_discount"] for t in result["recent_trades"] if t["premium_discount"] is not None]
                if premiums:
                    avg_premium = sum(premiums) / len(premiums)
                    if avg_premium > 0:
                        result["net_direction"] = "buy"
                    elif avg_premium < 0:
                        result["net_direction"] = "sell"

                result["summary"] = f"近{len(result['recent_trades'])}笔大宗交易"
            else:
                result["summary"] = "近期无大宗交易"
    except Exception as e:
        result["error"] = str(e)
        result["summary"] = "大宗交易数据获取失败"

    return result


def _to_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return round(f, 2) if not (f != f) else None
    except (ValueError, TypeError):
        return None
