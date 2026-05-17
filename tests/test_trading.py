# tests/test_trading.py
# 交易模块测试 — 模拟交易、订单生命周期、风控检查

from __future__ import annotations

import asyncio
import pytest

from backend.trading.models import (
    AccountInfo, OrderSide, OrderStatus, PositionInfo, TradeOrder,
)
from backend.trading.broker import SimulatedBroker, create_broker
from backend.trading.executor import TradeExecutor, reset_executor


# ─── Broker 测试 ───

class TestSimulatedBroker:
    """模拟券商测试"""

    @pytest.fixture
    def broker(self):
        return SimulatedBroker(initial_cash=1_000_000)

    @pytest.mark.asyncio
    async def test_initial_balance(self, broker: SimulatedBroker):
        bal = await broker.get_balance()
        assert bal.total_assets == 1_000_000
        assert bal.available_cash == 1_000_000
        assert bal.market_value == 0

    @pytest.mark.asyncio
    async def test_buy(self, broker: SimulatedBroker):
        oid = await broker.buy("600519", 1500.0, 100)
        assert oid.startswith("SIM-")

        bal = await broker.get_balance()
        assert bal.available_cash == 1_000_000 - 150_000
        assert bal.market_value == 150_000

        positions = await broker.get_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "600519"
        assert positions[0].quantity == 100

    @pytest.mark.asyncio
    async def test_buy_insufficient_cash(self, broker: SimulatedBroker):
        with pytest.raises(ValueError, match="余额不足"):
            await broker.buy("600519", 1500.0, 1000)

    @pytest.mark.asyncio
    async def test_sell(self, broker: SimulatedBroker):
        await broker.buy("600519", 1500.0, 100)
        oid = await broker.sell("600519", 1600.0, 50)
        assert oid.startswith("SIM-")

        positions = await broker.get_positions()
        assert len(positions) == 1
        assert positions[0].quantity == 50

    @pytest.mark.asyncio
    async def test_sell_all(self, broker: SimulatedBroker):
        await broker.buy("600519", 1500.0, 100)
        await broker.sell("600519", 1600.0, 100)

        positions = await broker.get_positions()
        assert len(positions) == 0

    @pytest.mark.asyncio
    async def test_sell_insufficient_position(self, broker: SimulatedBroker):
        with pytest.raises(ValueError, match="持仓不足"):
            await broker.sell("600519", 1500.0, 100)

    @pytest.mark.asyncio
    async def test_connect(self, broker: SimulatedBroker):
        assert await broker.connect() is True
        assert await broker.is_connected() is True


def test_create_broker_factory():
    """工厂函数测试"""
    broker = create_broker("simulated")
    assert isinstance(broker, SimulatedBroker)

    broker = create_broker("easytrader")
    assert broker.name == "easytrader"


# ─── TradeExecutor 测试 ───

class TestTradeExecutor:
    """交易执行器测试"""

    @pytest.fixture
    def executor(self):
        reset_executor()
        ex = TradeExecutor(
            broker_type="simulated",
            max_amount=100_000,
            max_position_pct=0.3,
            confirm_required=True,
        )
        asyncio.get_event_loop().run_until_complete(ex.connect())
        return ex

    @pytest.mark.asyncio
    async def test_create_order(self, executor: TradeExecutor):
        order = await executor.create_order(
            symbol="600036", market="a_share",
            side="buy", price=35.0, quantity=100,
        )
        assert order.status == OrderStatus.PENDING
        assert order.symbol == "600036"
        assert order.total_amount == 3500.0

    @pytest.mark.asyncio
    async def test_create_order_exceeds_max_amount(self, executor: TradeExecutor):
        with pytest.raises(ValueError, match="超过限额"):
            await executor.create_order(
                symbol="600519", market="a_share",
                side="buy", price=1500.0, quantity=100,
            )

    @pytest.mark.asyncio
    async def test_confirm_and_submit(self, executor: TradeExecutor):
        order = await executor.create_order(
            symbol="600036", market="a_share",
            side="buy", price=35.0, quantity=100,
        )
        assert order.status == OrderStatus.PENDING

        confirmed = await executor.confirm_order(order.id)
        assert confirmed.status == OrderStatus.SUBMITTED  # confirm 自动提交

    @pytest.mark.asyncio
    async def test_cancel_order(self, executor: TradeExecutor):
        order = await executor.create_order(
            symbol="600036", market="a_share",
            side="buy", price=35.0, quantity=100,
        )
        cancelled = await executor.cancel_order(order.id)
        assert cancelled.status == OrderStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_get_account(self, executor: TradeExecutor):
        acc = await executor.get_account()
        assert acc.total_assets == 1_000_000

    @pytest.mark.asyncio
    async def test_get_orders(self, executor: TradeExecutor):
        await executor.create_order(
            symbol="600036", market="a_share",
            side="buy", price=35.0, quantity=100,
        )
        orders = executor.get_orders()
        assert len(orders) == 1

        pending = executor.get_orders(status="pending")
        assert len(pending) == 1

    def test_mode(self, executor: TradeExecutor):
        assert executor.mode == "simulated"

    def test_status(self, executor: TradeExecutor):
        status = executor.get_status()
        assert status["mode"] == "simulated"
        assert status["connected"] is True
        assert status["confirm_required"] is True


# ─── 模型测试 ───

class TestModels:
    """Pydantic 模型测试"""

    def test_trade_order_total_amount(self):
        order = TradeOrder(
            symbol="600519", market="a_share",
            side=OrderSide.BUY, price=1500.0, quantity=100,
        )
        assert order.total_amount == 150_000
        assert order.status == OrderStatus.PENDING

    def test_account_info_defaults(self):
        acc = AccountInfo()
        assert acc.total_assets == 0
        assert acc.available_cash == 0

    def test_position_info(self):
        pos = PositionInfo(
            symbol="600519", quantity=100,
            cost_price=1500.0, current_price=1600.0,
            market_value=160_000, profit=10_000,
            profit_pct=6.67,
        )
        assert pos.symbol == "600519"
