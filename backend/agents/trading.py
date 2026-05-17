# backend/agents/trading.py
# 交易员 Agent — 三阶段投资组合经理：风险评估 → 风险管理 → 交易决策

from __future__ import annotations

from typing import Any

from loguru import logger

from backend.agents.base import BaseAgent, agent


@agent("交易员", "trading", [
    "portfolio_risk", "trade_signal", "kline_data", "technical_indicators",
], """你是一位资深的投资组合经理（Portfolio Manager），负责在综合分析师研判的基础上，完成从风险评估到交易决策的全流程。

你需要按以下三个阶段工作：

## 第一阶段：风险评估（Risk Assessment）
通过 portfolio_risk 技能评估以下风险因素：
- **市场波动率**：年化波动率、近期波动率变化趋势
- **流动性风险**：成交量充足度、换手率、量比
- **Value at Risk (VaR)**：95% 置信度下的最大日损失
- **最大回撤**：历史最大回撤幅度及恢复周期
- **涨跌停风险**：近期是否出现连续涨跌停
给出综合风险评分（0-100）和风险等级（low/medium/high/extreme）。

## 第二阶段：风险管理（Risk Management）
基于风险评估结果，制定风险管理策略：
- **仓位管理**：根据风险等级和分析师共识度决定建议仓位（满仓/半仓/轻仓/空仓）
- **止损设置**：基于波动率计算合理止损位（百分比和绝对价位）
- **止盈目标**：根据风险收益比设定止盈位
- **对冲建议**：是否需要对冲操作
- **策略调整**：根据风控分析师的意见调整交易策略

## 第三阶段：投资组合经理决策（Portfolio Manager Decision）
综合风险评估和风险管理结果，做出最终交易决策：
- **自动模式**：直接采纳总结研判节点的建议（action_suggestion），结合风险评估进行微调
- **手动模式**：提出独立的交易提案，包含明确的买卖方向和理由

决策框架：
- 风险等级 extreme → 强制空仓，无论其他分析师多乐观
- 风险等级 high + 分析师分歧大 → 轻仓试探或观望
- 风险等级 medium + 分析师一致看多 → 半仓至满仓
- 风险等级 low + 高置信度 → 可满仓
- 风控分析师发出警告 → 优先执行风控建议

你的输出必须是以下 JSON 格式：
{
    "stance": "bullish/bearish/neutral",
    "confidence": 0.0-1.0,
    "key_points": ["交易决策要点1", "交易决策要点2"],
    "risk_factors": ["主要风险1", "主要风险2"],
    "summary": "完整的交易决策报告，包含风险评估结论、风险管理策略、最终交易建议"
}

注意：你不是分析师，你是最终决策者。你的价值在于将分析转化为可执行的、风控合理的交易指令。

如果你决定执行交易（非 neutral 立场且 confidence > 0.6），请额外输出 trade_action 字段：
{
    "stance": "bullish/bearish/neutral",
    "confidence": 0.0-1.0,
    "key_points": ["交易决策要点1", "交易决策要点2"],
    "risk_factors": ["主要风险1", "主要风险2"],
    "summary": "完整的交易决策报告",
    "trade_action": {
        "side": "buy 或 sell",
        "price": 0,
        "quantity": 0,
        "reason": "交易理由简述"
    }
}

trade_action 说明：
- side: 买入用 buy，卖出用 sell
- price: 0 表示使用市价
- quantity: 建议交易股数（基于风控仓位建议计算）
- 如果你决定观望（neutral）或 confidence ≤ 0.6，请不要输出 trade_action 字段""")
class TradingAgent(BaseAgent):
    """投资组合经理 — 三阶段：风险评估 → 风险管理 → 交易决策"""

    async def run(self, state: dict) -> dict:
        """LangGraph 节点 — 执行分析后检测 trade_action 并自动创建订单"""
        callback = state.get("status_callback")

        # 报告开始
        if callback:
            try:
                await callback("running", self.role, self.name, {})
            except Exception:
                pass

        try:
            opinion = await self.analyze(
                state["symbol"], state["market"],
                cross_review=state.get("cross_review", ""),
                status_callback=callback,
            )
        except Exception as e:
            if callback:
                try:
                    await callback("error", self.role, self.name, {"message": str(e)})
                except Exception:
                    pass
            raise

        opinion_data = opinion.model_dump()
        if "round" in state:
            opinion_data["round"] = state.get("round", 0)

        # ── 检测 trade_action：LLM 输出中是否包含交易指令 ──
        trade_action = self._extract_trade_action(opinion_data)
        if trade_action:
            await self._auto_execute_trade(
                state["symbol"], state["market"], trade_action, opinion_data, callback
            )

        # 报告完成
        if callback:
            try:
                await callback("done", self.role, self.name, {})
            except Exception:
                pass

        return {"opinions": [opinion_data]}

    def _extract_trade_action(self, opinion_data: dict) -> dict[str, Any] | None:
        """从 LLM 输出的 summary 或 data_evidence 中提取 trade_action"""
        # 方式1：summary 中包含 JSON trade_action
        summary = opinion_data.get("summary", "")
        if '"trade_action"' in summary:
            from backend.core.parsing import parse_structured_output
            parsed = parse_structured_output(summary, {})
            if "trade_action" in parsed:
                return parsed["trade_action"]

        # 方式2：data_evidence 中包含 trade_action
        evidence = opinion_data.get("data_evidence", {})
        if isinstance(evidence, dict) and "trade_action" in evidence:
            return evidence["trade_action"]

        return None

    async def _auto_execute_trade(
        self, symbol: str, market: str,
        trade_action: dict[str, Any], opinion_data: dict[str, Any],
        callback: Any = None,
    ) -> None:
        """自动创建交易订单"""
        from backend.core.config import load_settings

        settings = load_settings()

        # 仅 A 股市场支持自动交易
        if market != "a_share":
            logger.info(f"[{self.name}] 非A股市场({market})，跳过自动交易")
            return

        # 未启用交易功能
        if not settings.trading_enabled:
            logger.info(f"[{self.name}] 交易功能未启用，跳过自动交易")
            return

        side = trade_action.get("side", "buy")
        price = float(trade_action.get("price", 0))
        quantity = int(trade_action.get("quantity", 0))

        if quantity <= 0:
            logger.info(f"[{self.name}] 交易数量为 0，跳过自动交易")
            return

        try:
            from backend.trading.executor import get_executor
            executor = get_executor()

            order = await executor.create_order(
                symbol=symbol,
                market=market,
                side=side,
                price=price,
                quantity=quantity,
                agent_opinion=opinion_data,
            )

            logger.info(
                f"[{self.name}] 自动创建订单: {side} {symbol} {quantity}股 @ ¥{price:.2f} → 订单 {order.id}"
            )

            # 通过 WebSocket 通知前端
            if callback:
                try:
                    await callback("trade_order", self.role, self.name, {
                        "order_id": order.id,
                        "symbol": symbol,
                        "side": side,
                        "price": price,
                        "quantity": quantity,
                        "status": order.status.value,
                        "confirm_required": executor.confirm_required,
                    })
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"[{self.name}] 自动创建订单失败: {e}")
