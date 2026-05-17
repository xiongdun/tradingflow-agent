# backend/skills/industry_analysis.py
# 行业分析增强技能 — 综合行业排名、板块资金流向、同行业对比

from __future__ import annotations

from typing import Any

from backend.skills.registry import skill


@skill(
    name="industry_analysis",
    description="综合行业分析：行业排名、板块资金流向、同行业对比、行业趋势",
    markets=["a_share", "h_stock", "us_stock", "bond", "futures", "crypto"],
    category="fundamental",
    label="行业分析",
)
def analyze_industry(symbol: str, market: str) -> dict[str, Any]:
    """获取股票所属行业的综合分析数据"""
    if market == "a_share":
        return _analyze_a_share_industry(symbol)
    return _analyze_yfinance_industry(symbol, market)


def _analyze_a_share_industry(symbol: str) -> dict[str, Any]:
    """A 股行业分析：行业排名 + 板块资金流向 + 同行业个股"""
    import akshare as ak
    result: dict[str, Any] = {"symbol": symbol, "market": "a_share", "industry": "", "sector_data": {}, "peers": []}

    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == symbol]
        if not row.empty:
            r = row.iloc[0]
            industry = str(r.get("所属行业", "")) if "所属行业" in df.columns else ""
            result["industry"] = industry
            result["sector_data"]["pe_ratio"] = str(r.get("市盈率-动态", "N/A"))
            result["sector_data"]["pb_ratio"] = str(r.get("市净率", "N/A"))
            result["sector_data"]["change_pct"] = str(r.get("涨跌幅", "N/A"))
    except Exception:
        pass

    try:
        df_flow = ak.stock_sector_fund_flow_rank(indicator="今日")
        if df_flow is not None and not df_flow.empty:
            top_sectors = []
            for _, row in df_flow.head(5).iterrows():
                top_sectors.append({
                    "name": str(row.get("名称", "")),
                    "change_pct": str(row.get("今日涨跌幅", "")),
                    "main_net_inflow": str(row.get("主力净流入-净额", "")),
                })
            result["sector_data"]["top_sectors"] = top_sectors
    except Exception:
        pass

    try:
        df_rank = ak.stock_board_industry_name_em()
        if df_rank is not None and not df_rank.empty:
            result["sector_data"]["industry_count"] = len(df_rank)
            if result["industry"]:
                match = df_rank[df_rank["板块名称"].str.contains(result["industry"], na=False)]
                if not match.empty:
                    result["sector_data"]["industry_rank"] = int(match.index[0]) + 1
    except Exception:
        pass

    return result


def _analyze_yfinance_industry(symbol: str, market: str) -> dict[str, Any]:
    """港股/美股行业分析"""
    import yfinance as yf
    result: dict[str, Any] = {"symbol": symbol, "market": market, "industry": "", "sector_data": {}, "peers": []}

    try:
        info = yf.Ticker(symbol).info
        result["industry"] = info.get("industry", "")
        result["sector_data"]["sector"] = info.get("sector", "")
        result["sector_data"]["industry"] = info.get("industry", "")
        result["sector_data"]["market_cap"] = info.get("marketCap")
        result["sector_data"]["pe_ratio"] = info.get("trailingPE")
        result["sector_data"]["pb_ratio"] = info.get("priceToBook")
        result["sector_data"]["beta"] = info.get("beta")
        result["sector_data"]["recommendation"] = info.get("recommendationKey", "")
    except Exception:
        pass

    return result
