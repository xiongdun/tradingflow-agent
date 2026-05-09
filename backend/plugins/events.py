# backend/plugins/events.py
# 事件总线 — 发布/订阅模式，支持市场事件驱动工作流触发

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable, Awaitable

from loguru import logger

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class Event:
    """事件对象"""
    def __init__(self, event_type: str, data: dict[str, Any], source: str = ""):
        self.type = event_type
        self.data = data
        self.source = source
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "data": self.data, "source": self.source, "timestamp": self.timestamp}


class EventBus:
    """事件总线 — 发布/订阅模式

    事件类型：price_alert / indicator_signal / news_event / workflow_complete / plugin_installed / custom
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self._triggers: list[EventTrigger] = []
        self._history: list[dict[str, Any]] = []
        self._max_history = 1000

    def on(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: EventHandler) -> None:
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]

    async def emit(self, event: Event) -> None:
        logger.info(f"[event] {event.type}: {json.dumps(event.data, default=str, ensure_ascii=False)[:200]}")
        self._history.append(event.to_dict())
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        handlers = self._handlers.get(event.type, []) + self._handlers.get("*", [])
        for handler in handlers:
            try:
                await handler(event.data)
            except Exception as e:
                logger.error(f"[event] 处理器异常: {event.type} -> {e}")
        for trigger in self._triggers:
            if trigger.matches(event):
                await trigger.execute(event)

    def add_trigger(self, trigger: EventTrigger) -> None:
        self._triggers.append(trigger)

    def remove_trigger(self, trigger_id: str) -> bool:
        before = len(self._triggers)
        self._triggers = [t for t in self._triggers if t.id != trigger_id]
        return len(self._triggers) < before

    def list_triggers(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._triggers]

    def get_history(self, event_type: str = "", limit: int = 50) -> list[dict[str, Any]]:
        history = self._history
        if event_type:
            history = [e for e in history if e.get("type") == event_type]
        return history[-limit:]


class EventTrigger:
    """事件触发器 — 监听特定事件并自动执行工作流"""

    def __init__(self, trigger_id: str, event_type: str, condition: dict[str, Any],
                 workflow_name: str, params: dict[str, Any] | None = None):
        self.id = trigger_id
        self.event_type = event_type
        self.condition = condition
        self.workflow_name = workflow_name
        self.params = params or {}
        self.enabled = True
        self.last_triggered: str | None = None
        self.trigger_count = 0

    def matches(self, event: Event) -> bool:
        if not self.enabled or event.type != self.event_type:
            return False
        for key, expected in self.condition.items():
            actual = event.data.get(key)
            if isinstance(expected, dict):
                op, val = expected.get("op", "eq"), expected.get("value")
                if op == "gt" and not (actual is not None and actual > val):
                    return False
                if op == "lt" and not (actual is not None and actual < val):
                    return False
                if op == "eq" and actual != val:
                    return False
                if op == "contains" and not (isinstance(actual, str) and str(val) in actual):
                    return False
            elif actual != expected:
                return False
        return True

    async def execute(self, event: Event) -> None:
        from backend.core.analysis_service import AnalysisService
        self.last_triggered = datetime.now().isoformat()
        self.trigger_count += 1
        logger.info(f"[trigger] {self.id}: 触发工作流 {self.workflow_name}")
        try:
            workflow_def = AnalysisService.load_workflow(self.workflow_name)
            if not workflow_def:
                logger.warning(f"[trigger] 工作流模板不存在: {self.workflow_name}")
                return
            symbol = self.params.get("symbol") or event.data.get("symbol", "")
            market = self.params.get("market") or event.data.get("market", "a_share")
            if symbol:
                await AnalysisService.run_and_save(symbol, market, workflow_def)
        except Exception as e:
            logger.error(f"[trigger] 工作流执行失败: {e}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "event_type": self.event_type, "condition": self.condition,
            "workflow_name": self.workflow_name, "params": self.params,
            "enabled": self.enabled, "last_triggered": self.last_triggered, "trigger_count": self.trigger_count,
        }


def create_price_alert(trigger_id: str, symbol: str, condition: str, workflow_name: str, **kwargs: Any) -> EventTrigger:
    """创建价格警报触发器

    Args:
        trigger_id: 触发器唯一标识
        symbol: 股票代码
        condition: 条件表达式，格式 "操作符:阈值"，支持 gt/lt/eq（如 "gt:100", "lt:50"）
        workflow_name: 触发时执行的工作流名称
        **kwargs: 附加参数
    """
    parts = condition.split(":")
    op = parts[0] if len(parts) > 1 else "gt"
    try:
        value = float(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        logger.warning(f"[trigger] 无效的价格条件格式: {condition}，使用默认值 gt:0")
        op, value = "gt", 0
    return EventTrigger(trigger_id=trigger_id, event_type="price_alert",
                        condition={"symbol": symbol, "price": {"op": op, "value": value}},
                        workflow_name=workflow_name, params={"symbol": symbol, **kwargs})


def create_indicator_signal(trigger_id: str, symbol: str, indicator: str, signal: str, workflow_name: str, **kwargs: Any) -> EventTrigger:
    """创建技术指标信号触发器"""
    return EventTrigger(trigger_id=trigger_id, event_type="indicator_signal",
                        condition={"symbol": symbol, "indicator": indicator, "signal": signal},
                        workflow_name=workflow_name, params={"symbol": symbol, **kwargs})


def create_news_trigger(trigger_id: str, keywords: list[str], workflow_name: str, **kwargs: Any) -> EventTrigger:
    """创建新闻事件触发器"""
    return EventTrigger(trigger_id=trigger_id, event_type="news_event",
                        condition={"keywords": keywords}, workflow_name=workflow_name, params=kwargs)


# 全局事件总线
event_bus = EventBus()
