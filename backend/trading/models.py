# backend/trading/models.py
# 交易数据模型 — 订单、账户、持仓

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OrderSide(str, Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """订单状态流转：pending → confirmed → submitted → filled / rejected / cancelled"""
    PENDING = "pending"          # 待确认（Agent 生成，等待用户确认）
    CONFIRMED = "confirmed"      # 已确认（用户点击确认）
    SUBMITTED = "submitted"      # 已提交（发送到券商）
    FILLED = "filled"            # 已成交
    REJECTED = "rejected"        # 被拒绝
    CANCELLED = "cancelled"      # 已取消


class TradeOrder(BaseModel):
    """交易订单"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    symbol: str                     # 股票代码
    market: str                     # 市场类型
    side: OrderSide                 # 买/卖
    price: float                    # 委托价格（0=市价）
    quantity: int                   # 委托数量（股）
    status: OrderStatus = OrderStatus.PENDING
    broker_order_id: str | None = None  # 券商返回的订单号
    agent_opinion: dict[str, Any] | None = None  # 触发此订单的 Agent 意见
    confirmed_by_user: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    note: str = ""                  # 备注（错误信息等）

    @property
    def total_amount(self) -> float:
        return self.price * self.quantity


class AccountInfo(BaseModel):
    """账户概览"""
    total_assets: float = 0.0       # 总资产
    available_cash: float = 0.0     # 可用资金
    market_value: float = 0.0       # 持仓市值
    total_profit: float = 0.0       # 总盈亏
    today_profit: float = 0.0       # 今日盈亏


class PositionInfo(BaseModel):
    """持仓明细"""
    symbol: str
    name: str = ""
    quantity: int                   # 持仓数量
    available_qty: int = 0          # 可卖数量
    cost_price: float               # 成本价
    current_price: float            # 现价
    market_value: float             # 市值
    profit: float                   # 盈亏
    profit_pct: float               # 盈亏比例
