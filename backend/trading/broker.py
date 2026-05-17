# backend/trading/broker.py
# 券商接口 — 抽象基类 + EasyTrader 实盘 + 模拟交易

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from .models import AccountInfo, PositionInfo

logger = logging.getLogger(__name__)


class BaseBroker(ABC):
    """券商接口抽象基类"""

    name: str = "base"

    @abstractmethod
    async def connect(self, account: str = "", password: str = "", **kwargs: Any) -> bool:
        """连接券商客户端，返回是否成功"""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        ...

    @abstractmethod
    async def get_balance(self) -> AccountInfo:
        """获取账户余额"""
        ...

    @abstractmethod
    async def get_positions(self) -> list[PositionInfo]:
        """获取持仓列表"""
        ...

    @abstractmethod
    async def buy(self, symbol: str, price: float, quantity: int) -> str:
        """买入，返回券商订单号"""
        ...

    @abstractmethod
    async def sell(self, symbol: str, price: float, quantity: int) -> str:
        """卖出，返回券商订单号"""
        ...

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> bool:
        """撤单"""
        ...

    @abstractmethod
    async def is_connected(self) -> bool:
        """是否已连接"""
        ...


class EasyTraderBroker(BaseBroker):
    """基于 easytrader 的实盘券商接口（需要本地通达信/同花顺客户端）"""

    name = "easytrader"

    def __init__(self) -> None:
        self._user: Any = None
        self._connected = False

    async def connect(self, account: str = "", password: str = "", **kwargs: Any) -> bool:
        """连接券商客户端"""
        broker = kwargs.get("broker", "ths")  # ths=同花顺, ht=通达信
        try:
            import easytrader  # type: ignore[import-untyped]

            def _do_connect() -> Any:
                user = easytrader.use(broker)
                user.connect(account)
                return user

            self._user = await asyncio.to_thread(_do_connect)
            self._connected = True
            logger.info("[broker] easytrader 已连接 (broker=%s)", broker)
            return True
        except ImportError:
            logger.error("[broker] easytrader 未安装，请执行: pip install easytrader")
            return False
        except Exception as e:
            logger.error("[broker] 连接失败: %s", e)
            return False

    async def disconnect(self) -> None:
        self._user = None
        self._connected = False

    async def get_balance(self) -> AccountInfo:
        self._ensure_connected()
        assert self._user is not None

        def _query() -> dict[str, Any]:
            return self._user.balance  # type: ignore[no-any-return]

        bal = await asyncio.to_thread(_query)
        return AccountInfo(
            total_assets=float(bal.get("总资产", 0)),
            available_cash=float(bal.get("可用金额", 0)),
            market_value=float(bal.get("市值", 0)),
            total_profit=float(bal.get("盈亏", 0)),
        )

    async def get_positions(self) -> list[PositionInfo]:
        self._ensure_connected()
        assert self._user is not None

        def _query() -> list[dict[str, Any]]:
            return self._user.position  # type: ignore[no-any-return]

        raw = await asyncio.to_thread(_query)
        positions = []
        for p in raw:
            positions.append(PositionInfo(
                symbol=str(p.get("证券代码", "")),
                name=str(p.get("证券名称", "")),
                quantity=int(p.get("股票余额", 0)),
                available_qty=int(p.get("可用余额", 0)),
                cost_price=float(p.get("成本价", 0)),
                current_price=float(p.get("市价", 0)),
                market_value=float(p.get("市值", 0)),
                profit=float(p.get("盈亏", 0)),
                profit_pct=float(p.get("盈亏比例", 0)),
            ))
        return positions

    async def buy(self, symbol: str, price: float, quantity: int) -> str:
        self._ensure_connected()
        assert self._user is not None

        def _submit() -> str:
            result = self._user.buy(symbol, price=price, amount=quantity)
            return str(result.get("entrust_no", ""))

        return await asyncio.to_thread(_submit)

    async def sell(self, symbol: str, price: float, quantity: int) -> str:
        self._ensure_connected()
        assert self._user is not None

        def _submit() -> str:
            result = self._user.sell(symbol, price=price, amount=quantity)
            return str(result.get("entrust_no", ""))

        return await asyncio.to_thread(_submit)

    async def cancel_order(self, broker_order_id: str) -> bool:
        self._ensure_connected()
        assert self._user is not None

        def _cancel() -> bool:
            self._user.cancel_entrust(broker_order_id)
            return True

        try:
            return await asyncio.to_thread(_cancel)
        except Exception as e:
            logger.error("[broker] 撤单失败: %s", e)
            return False

    async def is_connected(self) -> bool:
        return self._connected

    def _ensure_connected(self) -> None:
        if not self._connected:
            raise RuntimeError("券商未连接，请先调用 connect()")


class SimulatedBroker(BaseBroker):
    """模拟交易 — 内存账户，用于测试和默认模式"""

    name = "simulated"

    def __init__(self, initial_cash: float = 1_000_000) -> None:
        self._cash = initial_cash
        self._initial_cash = initial_cash
        self._positions: dict[str, _SimPosition] = {}
        self._connected = True
        self._order_counter = 0

    async def connect(self, account: str = "", password: str = "", **kwargs: Any) -> bool:
        self._connected = True
        logger.info("[broker] 模拟交易已就绪 (初始资金: ¥%.0f)", self._initial_cash)
        return True

    async def disconnect(self) -> None:
        pass

    async def get_balance(self) -> AccountInfo:
        market_value = sum(p.quantity * p.current_price for p in self._positions.values())
        total = self._cash + market_value
        return AccountInfo(
            total_assets=total,
            available_cash=self._cash,
            market_value=market_value,
            total_profit=total - self._initial_cash,
        )

    async def get_positions(self) -> list[PositionInfo]:
        return [
            PositionInfo(
                symbol=p.symbol,
                name=p.name,
                quantity=p.quantity,
                available_qty=p.quantity,
                cost_price=p.cost_price,
                current_price=p.current_price,
                market_value=p.quantity * p.current_price,
                profit=(p.current_price - p.cost_price) * p.quantity,
                profit_pct=(p.current_price / p.cost_price - 1) * 100 if p.cost_price else 0,
            )
            for p in self._positions.values()
        ]

    async def buy(self, symbol: str, price: float, quantity: int) -> str:
        cost = price * quantity
        if cost > self._cash:
            raise ValueError(f"余额不足: 需要 ¥{cost:.2f}，可用 ¥{self._cash:.2f}")

        self._cash -= cost
        pos = self._positions.get(symbol)
        if pos:
            total_qty = pos.quantity + quantity
            pos.cost_price = (pos.cost_price * pos.quantity + price * quantity) / total_qty
            pos.quantity = total_qty
            pos.current_price = price
        else:
            self._positions[symbol] = _SimPosition(
                symbol=symbol, name=symbol,
                quantity=quantity, cost_price=price, current_price=price,
            )
        self._order_counter += 1
        oid = f"SIM-{self._order_counter:06d}"
        logger.info("[broker] 模拟买入 %s %d股 @ ¥%.2f → %s", symbol, quantity, price, oid)
        return oid

    async def sell(self, symbol: str, price: float, quantity: int) -> str:
        pos = self._positions.get(symbol)
        if not pos or pos.quantity < quantity:
            avail = pos.quantity if pos else 0
            raise ValueError(f"持仓不足: {symbol} 可卖 {avail} 股，要求 {quantity} 股")

        self._cash += price * quantity
        pos.quantity -= quantity
        if pos.quantity == 0:
            del self._positions[symbol]
        self._order_counter += 1
        oid = f"SIM-{self._order_counter:06d}"
        logger.info("[broker] 模拟卖出 %s %d股 @ ¥%.2f → %s", symbol, quantity, price, oid)
        return oid

    async def cancel_order(self, broker_order_id: str) -> bool:
        return True  # 模拟模式直接成功

    async def is_connected(self) -> bool:
        return self._connected


class _SimPosition:
    """模拟持仓内部数据结构"""
    __slots__ = ("symbol", "name", "quantity", "cost_price", "current_price")

    def __init__(self, symbol: str, name: str, quantity: int, cost_price: float, current_price: float) -> None:
        self.symbol = symbol
        self.name = name
        self.quantity = quantity
        self.cost_price = cost_price
        self.current_price = current_price


def create_broker(broker_type: str = "simulated", **kwargs: Any) -> BaseBroker:
    """工厂函数：根据类型创建券商实例"""
    if broker_type == "easytrader":
        return EasyTraderBroker()
    return SimulatedBroker(**kwargs)
