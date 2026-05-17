# backend/skills/trade_execute.py
# 交易执行技能 — 创建交易订单（模拟/实盘）

from __future__ import annotations

from typing import Any

from backend.skills.registry import skill


@skill(
    name="trade_execute",
    description="创建交易订单（买入/卖出），支持模拟和实盘交易。需要实时行情数据输入。",
    markets=["a_share", "h_stock", "us_stock", "bond", "futures", "crypto"],
    category="trading",
    label="交易执行",
    params={
        "symbol": "股票代码",
        "side": "buy/sell",
        "price": "委托价格（0=市价）",
        "quantity": "委托数量（股）",
    },
    depends_on=["trade_signal"],
)
def execute_trade(symbol: str, market: str, **kwargs: Any) -> dict[str, Any]:
    """
    创建交易订单。

    参数通过 kwargs 传入：
    - side: "buy" 或 "sell"
    - price: 委托价格（0 表示市价）
    - quantity: 委托数量（股）
    - trade_signal: trade_signal 技能的结果（含实时行情）
    """
    side = kwargs.get("side", "buy")
    price = float(kwargs.get("price", 0))
    quantity = int(kwargs.get("quantity", 0))

    # 如果没有指定价格，尝试从 trade_signal 结果中获取实时价
    trade_signal_data = kwargs.get("trade_signal", {})
    if price <= 0 and isinstance(trade_signal_data, dict):
        quote = trade_signal_data.get("quote", {})
        price = float(quote.get("price", 0) or quote.get("latest_price", 0))

    if price <= 0:
        return {"error": "无法获取委托价格，请指定 price 参数"}
    if quantity <= 0:
        return {"error": "委托数量必须大于 0"}
    if side not in ("buy", "sell"):
        return {"error": f"无效的交易方向: {side}，必须是 buy 或 sell"}

    # 创建订单（通过交易执行器）
    try:
        from backend.trading.executor import get_executor

        executor = get_executor()
        import asyncio

        try:
            asyncio.get_running_loop()
            # 在已有事件循环中运行协程 — 用线程池避免死锁
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, executor.create_order(
                    symbol=symbol,
                    market=market,
                    side=side,
                    price=price,
                    quantity=quantity,
                ))
                order = future.result(timeout=10)
        except RuntimeError:
            # 没有运行中的事件循环，直接运行
            order = asyncio.run(executor.create_order(
                symbol=symbol,
                market=market,
                side=side,
                price=price,
                quantity=quantity,
            ))

        return {
            "order_id": order.id,
            "symbol": order.symbol,
            "side": order.side.value,
            "price": order.price,
            "quantity": order.quantity,
            "total_amount": order.total_amount,
            "status": order.status.value,
            "confirm_required": executor.confirm_required,
            "message": f"订单已创建: {'买入' if side == 'buy' else '卖出'} {symbol} {quantity}股 @ ¥{price:.2f}",
        }
    except Exception as e:
        return {"error": f"创建订单失败: {e}"}
