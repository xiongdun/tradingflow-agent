# backend/api/routes/trading.py
# 交易管理 API 路由 — 账户、持仓、订单、券商连接

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/trading", tags=["trading"])


# ─── 请求模型 ───

class TradeOrderCreate(BaseModel):
    """手动创建交易订单"""
    symbol: str
    market: str = "a_share"
    side: str  # buy / sell
    price: float = 0  # 0=市价
    quantity: int


class BrokerConnect(BaseModel):
    """连接券商请求"""
    account: str = ""
    password: str = ""
    broker: str = "ths"  # ths / ht


# ─── 交易系统状态 ───

@router.get("/status")
async def get_status() -> dict[str, Any]:
    """获取交易系统状态"""
    from backend.trading.executor import get_executor
    executor = get_executor()
    return executor.get_status()


# ─── 连接券商 ───

@router.post("/connect")
async def connect_broker(req: BrokerConnect) -> dict[str, Any]:
    """连接券商客户端（实盘模式）"""
    from backend.trading.executor import get_executor
    executor = get_executor()
    ok = await executor.connect(req.account, req.password, broker=req.broker)
    if ok:
        return {"status": "ok", "message": f"已连接 {executor.mode} 券商"}
    return {"status": "error", "message": "连接失败，请检查客户端是否启动"}


@router.post("/disconnect")
async def disconnect_broker() -> dict[str, Any]:
    """断开券商连接"""
    from backend.trading.executor import get_executor
    executor = get_executor()
    await executor.disconnect()
    return {"status": "ok", "message": "已断开连接"}


# ─── 账户与持仓 ───

@router.get("/account")
async def get_account() -> dict[str, Any]:
    """获取账户概览"""
    from backend.trading.executor import get_executor
    executor = get_executor()
    acc = await executor.get_account()
    return acc.model_dump()


@router.get("/positions")
async def get_positions() -> list[dict[str, Any]]:
    """获取持仓列表"""
    from backend.trading.executor import get_executor
    executor = get_executor()
    positions = await executor.get_positions()
    return [p.model_dump() for p in positions]


# ─── 订单管理 ───

@router.get("/orders")
async def list_orders(status: str | None = None) -> list[dict[str, Any]]:
    """获取订单列表（可按状态过滤）"""
    from backend.trading.executor import get_executor
    executor = get_executor()
    orders = executor.get_orders(status=status)
    return [o.model_dump() for o in orders]


@router.post("/orders")
async def create_order(req: TradeOrderCreate) -> dict[str, Any]:
    """手动创建交易订单"""
    from backend.trading.executor import get_executor
    executor = get_executor()
    order = await executor.create_order(
        symbol=req.symbol,
        market=req.market,
        side=req.side,
        price=req.price,
        quantity=req.quantity,
    )
    return order.model_dump()


@router.post("/orders/{order_id}/confirm")
async def confirm_order(order_id: str) -> dict[str, Any]:
    """确认订单（用户点击确认按钮后调用）"""
    from backend.trading.executor import get_executor
    executor = get_executor()
    order = await executor.confirm_order(order_id)
    return order.model_dump()


@router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str) -> dict[str, Any]:
    """取消订单"""
    from backend.trading.executor import get_executor
    executor = get_executor()
    order = await executor.cancel_order(order_id)
    return order.model_dump()
