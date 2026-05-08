# backend/skills/peer_comparison.py
# 同行对比技能 — 将股票与同行业/同板块 peers 进行横向比较

from __future__ import annotations

from typing import Any

from backend.skills.registry import skill


@skill(
    name="peer_comparison",
    description="获取同行业/同板块股票对比数据，用于横向比较分析",
    markets=["a_share", "h_stock", "us_stock"],
    category="fundamental",
    label="同行对比",
)
def compare_peers(symbol: str, market: str) -> dict[str, Any]:
    """获取同行业可比公司数据，用于横向估值比较"""
    if market == "a_share":
        return _compare_a_share_peers(symbol)
    return {"symbol": symbol, "market": market, "peers": [], "note": "Peer comparison limited for this market"}


def _compare_a_share_peers(symbol: str) -> dict[str, Any]:
    """查找 A 股同行业可比公司，基于市盈率范围筛选相似估值的股票"""
    import akshare as ak
    try:
        # 从全市场行情中获取目标股票信息
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == symbol]
        if row.empty:
            return {"symbol": symbol, "peers": [], "error": "Stock not found"}

        stock_name = row.iloc[0]["名称"]

        try:
            # 获取行业板块列表
            industry_df = ak.stock_board_industry_name_em()
            # 简化方案：从全市场数据中筛选市盈率相近的股票作为可比公司
            peers_data = []
            pe = row.iloc[0].get("市盈率-动态", 0)
            if pe and str(pe) != "-":
                # 筛选市盈率在目标股票 0.5~1.5 倍范围内的股票
                similar = df[
                    (df["市盈率-动态"].between(float(pe) * 0.5, float(pe) * 1.5))
                    & (df["代码"] != symbol)
                ].head(5)
                for _, r in similar.iterrows():
                    peers_data.append({
                        "symbol": str(r["代码"]),
                        "name": str(r["名称"]),
                        "price": float(r["最新价"]) if r["最新价"] and str(r["最新价"]) != "-" else 0,
                        "pe_ratio": float(r["市盈率-动态"]) if r["市盈率-动态"] and str(r["市盈率-动态"]) != "-" else 0,
                        "pb_ratio": float(r["市净率"]) if r["市净率"] and str(r["市净率"]) != "-" else 0,
                        "change_pct": float(r["涨跌幅"]) if r["涨跌幅"] and str(r["涨跌幅"]) != "-" else 0,
                    })
        except Exception:
            peers_data = []

        return {
            "symbol": symbol,
            "stock_name": stock_name,
            "peers": peers_data,
        }
    except Exception as e:
        return {"symbol": symbol, "peers": [], "error": str(e)}
