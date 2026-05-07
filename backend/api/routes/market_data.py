# backend/api/routes/market_data.py
# 行情数据 API 路由 — 为前端提供 K 线数据和图表标注

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.data.factory import get_provider

router = APIRouter(prefix="/api/market", tags=["market"])


class KlineRequest(BaseModel):
    """K 线数据请求模型"""
    symbol: str              # 股票代码
    market: str = "a_share"  # 市场类型
    period: str = "daily"    # K 线周期：daily/weekly/monthly
    days: int = 120          # 获取天数


class MarkerRequest(BaseModel):
    """图表标注请求模型 — 将分析师意见转换为买卖信号标记"""
    symbol: str
    market: str
    opinions: list[dict[str, Any]]  # 分析师意见列表


@router.post("/kline")
async def get_kline(req: KlineRequest):
    """获取 K 线数据，格式化为 TradingView Lightweight Charts 可用格式"""
    provider = get_provider(req.market)
    start = (datetime.now() - timedelta(days=req.days)).strftime("%Y-%m-%d")
    df = provider.get_kline(req.symbol, period=req.period, start_date=start)

    if df.empty:
        return {"symbol": req.symbol, "bars": [], "error": "No data"}

    # 转换为 Lightweight Charts 所需的 {time, open, high, low, close, volume} 格式
    bars = []
    for _, row in df.iterrows():
        bar = {
            "time": str(row.get("date", ""))[:10],
            "open": float(row.get("open", 0)),
            "high": float(row.get("high", 0)),
            "low": float(row.get("low", 0)),
            "close": float(row.get("close", 0)),
        }
        if "volume" in row:
            bar["volume"] = float(row.get("volume", 0))
        bars.append(bar)

    return {"symbol": req.symbol, "market": req.market, "bars": bars}


@router.post("/markers")
async def get_markers(req: MarkerRequest):
    """将分析师意见转换为图表买卖信号标记（箭头 + 悬浮提示）"""
    markers = []
    for op in req.opinions:
        stance = op.get("stance", "neutral")
        agent_name = op.get("agent_name", "")
        agent_role = op.get("agent_role", "")
        confidence = op.get("confidence", 0.5)
        summary = op.get("summary", "")

        # 跳过中性观点，只标记看多/看空
        if stance == "neutral":
            continue

        # 看多用绿色上箭头（K 线下方），看空用红色下箭头（K 线上方）
        is_buy = stance == "bullish"
        marker = {
            "position": "belowBar" if is_buy else "aboveBar",
            "color": "#22c55e" if is_buy else "#ef4444",
            "shape": "arrowUp" if is_buy else "arrowDown",
            "text": f"{agent_name[:4]}",
            "tooltip": f"{agent_name}: {summary[:100]}",
            "agent_role": agent_role,
            "confidence": confidence,
            "stance": stance,
        }
        markers.append(marker)

    # 同时生成分析师意见摘要列表，供前端面板展示
    lines = []
    for op in req.opinions:
        stance = op.get("stance", "neutral")
        if stance == "neutral":
            continue
        lines.append({
            "agent_name": op.get("agent_name", ""),
            "stance": stance,
            "confidence": op.get("confidence", 0.5),
            "key_points": op.get("key_points", []),
            "summary": op.get("summary", ""),
        })

    return {"markers": markers, "opinion_lines": lines}
