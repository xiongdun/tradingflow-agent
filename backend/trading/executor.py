# backend/trading/executor.py
# 交易执行器 — 订单生命周期管理、风控检查、模拟/实盘下单

from __future__ import annotations

import logging
from typing import Any

from .broker import BaseBroker, create_broker
from .models import AccountInfo, OrderSide, OrderStatus, PositionInfo, TradeOrder

logger = logging.getLogger(__name__)

# 全局执行器实例
_executor: TradeExecutor | None = None


def get_executor() -> TradeExecutor:
    """获取全局交易执行器单例"""
    global _executor
    if _executor is None:
        from backend.core.config import load_settings

        settings = load_settings()
        _executor = TradeExecutor(
            broker_type=settings.broker_type,
            max_amount=settings.trade_max_amount,
            max_position_pct=settings.trade_max_position_pct,
            confirm_required=settings.trade_confirm_required,
        )
    return _executor


def reset_executor() -> None:
    """重置全局执行器（用于测试或重新配置）"""
    global _executor
    _executor = None


class TradeExecutor:
    """交易执行器 — 管理订单从创建到成交的完整生命周期"""

    def __init__(
        self,
        broker_type: str = "simulated",
        max_amount: float = 100_000,
        max_position_pct: float = 0.3,
        confirm_required: bool = True,
    ) -> None:
        self.broker: BaseBroker = create_broker(broker_type)
        self.max_amount = max_amount
        self.max_position_pct = max_position_pct
        self.confirm_required = confirm_required
        self.orders: dict[str, TradeOrder] = {}
        self._connected = False

    async def connect(self, account: str = "", password: str = "", **kwargs: Any) -> bool:
        """连接券商"""
        self._connected = await self.broker.connect(account, password, **kwargs)
        return self._connected

    async def disconnect(self) -> None:
        await self.broker.disconnect()
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def mode(self) -> str:
        return self.broker.name

    def get_status(self) -> dict[str, Any]:
        return {
            "mode": self.broker.name,
            "connected": self._connected,
            "confirm_required": self.confirm_required,
            "max_amount": self.max_amount,
            "max_position_pct": self.max_position_pct,
            "total_orders": len(self.orders),
            "pending_orders": sum(1 for o in self.orders.values() if o.status == OrderStatus.PENDING),
        }

    async def create_order(
        self,
        symbol: str,
        market: str,
        side: str,
        price: float,
        quantity: int,
        agent_opinion: dict[str, Any] | None = None,
    ) -> TradeOrder:
        """
        创建交易订单
        - 风控检查（金额限制、持仓比例）
        - 无需确认时直接提交（模拟模式）
        - 需要确认时等待用户确认
        """
        # 风控：单笔金额限制
        amount = price * quantity
        if amount > self.max_amount:
            raise ValueError(
                f"单笔金额 ¥{amount:,.2f} 超过限额 ¥{self.max_amount:,.2f}"
            )

        # 风控：持仓比例检查（买入时）
        if side == "buy" and self._connected:
            try:
                bal = await self.broker.get_balance()
                if bal.total_assets > 0:
                    _ = bal.market_value / bal.total_assets
                    new_pct = (bal.market_value + amount) / (bal.total_assets + amount)
                    if new_pct > self.max_position_pct:
                        raise ValueError(
                            f"买入后持仓比例 {new_pct:.1%} 超过限额 {self.max_position_pct:.1%}"
                        )
            except Exception:
                pass  # 模拟模式或查询失败时跳过

        order = TradeOrder(
            symbol=symbol,
            market=market,
            side=OrderSide(side),  # type: ignore[arg-type]
            price=price,
            quantity=quantity,
            agent_opinion=agent_opinion,
        )
        self.orders[order.id] = order

        logger.info(
            "[executor] 创建订单 %s: %s %s %d股 @ ¥%.2f (金额 ¥%.2f)",
            order.id, side, symbol, quantity, price, amount,
        )

        # 不需要确认时自动提交
        if not self.confirm_required:
            await self.submit_order(order.id)

        return order

    async def confirm_order(self, order_id: str) -> TradeOrder:
        """用户确认订单 → 自动提交"""
        order = self._get_order(order_id)
        if order.status != OrderStatus.PENDING:
            raise ValueError(f"订单 {order_id} 状态为 {order.status.value}，无法确认")
        order.confirmed_by_user = True
        order.status = OrderStatus.CONFIRMED
        order.updated_at = __import__("datetime").datetime.now().isoformat()
        await self.submit_order(order_id)
        return order

    async def submit_order(self, order_id: str) -> TradeOrder:
        """提交订单到券商"""
        order = self._get_order(order_id)
        if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            raise ValueError(f"订单 {order_id} 状态为 {order.status.value}，无法提交")

        if not self._connected:
            order.status = OrderStatus.REJECTED
            order.note = "券商未连接"
            return order

        try:
            if order.side == OrderSide.BUY:
                broker_id = await self.broker.buy(order.symbol, order.price, order.quantity)
            else:
                broker_id = await self.broker.sell(order.symbol, order.price, order.quantity)

            order.broker_order_id = broker_id
            order.status = OrderStatus.SUBMITTED
            order.note = ""
            logger.info("[executor] 订单 %s 已提交 → 券商单号 %s", order_id, broker_id)
        except Exception as e:
            order.status = OrderStatus.REJECTED
            order.note = str(e)
            logger.error("[executor] 订单 %s 提交失败: %s", order_id, e)

        order.updated_at = __import__("datetime").datetime.now().isoformat()
        return order

    async def cancel_order(self, order_id: str) -> TradeOrder:
        """取消订单"""
        order = self._get_order(order_id)
        if order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED):
            raise ValueError(f"订单 {order_id} 状态为 {order.status.value}，无法取消")

        if order.broker_order_id and self._connected:
            await self.broker.cancel_order(order.broker_order_id)

        order.status = OrderStatus.CANCELLED
        order.updated_at = __import__("datetime").datetime.now().isoformat()
        return order

    async def get_account(self) -> AccountInfo:
        if self._connected:
            return await self.broker.get_balance()
        return AccountInfo()

    async def get_positions(self) -> list[PositionInfo]:
        if self._connected:
            return await self.broker.get_positions()
        return []

    def get_orders(self, status: str | None = None) -> list[TradeOrder]:
        orders = list(self.orders.values())
        if status:
            orders = [o for o in orders if o.status.value == status]
        return sorted(orders, key=lambda o: o.created_at, reverse=True)

    def _get_order(self, order_id: str) -> TradeOrder:
        order = self.orders.get(order_id)
        if not order:
            raise ValueError(f"订单不存在: {order_id}")
        return order
