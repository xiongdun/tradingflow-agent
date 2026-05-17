# backend/skills/registry.py
# 技能注册中心 — 基于装饰器的插件系统，用于注册和管理 Agent 技能

from __future__ import annotations

from typing import Any, Callable, Protocol


class SkillProtocol(Protocol):
    """技能函数标准接口协议 — 所有 @skill 注册的函数应符合此签名"""
    def __call__(self, symbol: str, market: str, **kwargs: Any) -> dict: ...


# 全局技能注册表：{技能名: 技能元数据}
_skills: dict[str, SkillMeta] = {}


class SkillMeta:
    """已注册技能的元数据"""

    def __init__(self, name: str, description: str, markets: list[str],
                 category: str, fn: Callable, params: dict | None = None,
                 depends_on: list[str] | None = None, label: str | None = None):
        self.name = name            # 技能名称
        self.description = description  # 技能描述
        self.markets = markets      # 支持的市场列表
        self.category = category    # 技能类别（fundamental/technical/sentiment 等）
        self.fn = fn                # 技能执行函数
        self.params = params or {}  # 额外参数说明
        self.depends_on = depends_on or []  # 依赖的其他技能名称
        self.label = label or name  # 中文短名称（用于节点显示）

    def execute(self, **kwargs) -> Any:
        """执行技能函数，校验必需参数 symbol 和 market"""
        from backend.core.exceptions import SkillExecutionError
        if "symbol" not in kwargs:
            raise SkillExecutionError(self.name, "缺少必需参数 'symbol'")
        if "market" not in kwargs:
            raise SkillExecutionError(self.name, "缺少必需参数 'market'")
        return self.fn(**kwargs)

    def to_dict(self) -> dict:
        """转换为字典格式（用于 API 返回）"""
        return {
            "name": self.name,
            "description": self.description,
            "markets": self.markets,
            "category": self.category,
            "label": self.label,
            "params": self.params,
            "depends_on": self.depends_on,
        }


def skill(
    name: str,
    description: str,
    markets: list[str] | None = None,
    category: str = "general",
    params: dict | None = None,
    depends_on: list[str] | None = None,
    label: str | None = None,
):
    """装饰器：将函数注册为技能。

    用法示例：
        @skill(
            name="technical_indicators",
            description="计算技术指标",
            markets=["a_share", "us_stock"],
            category="technical",
            depends_on=["kline_data"],
            label="技术指标",
        )
        def get_indicators(symbol: str, market: str, kline_data: dict = None) -> dict:
            ...
    """
    def decorator(fn: Callable) -> Callable:
        meta = SkillMeta(
            name=name,
            description=description,
            markets=markets or ["a_share", "h_stock", "us_stock"],  # 默认支持所有市场
            category=category,
            fn=fn,
            params=params,
            depends_on=depends_on,
            label=label,
        )
        _skills[name] = meta
        fn._skill_meta = meta  # type: ignore[attr-defined]
        return fn
    return decorator


def get_skill(name: str) -> SkillMeta | None:
    """根据名称获取已注册的技能"""
    return _skills.get(name)


def list_skills(market: str | None = None, category: str | None = None) -> list[dict]:
    """列出所有已注册的技能，可按市场或类别过滤"""
    results = []
    for meta in _skills.values():
        if market and market not in meta.markets:
            continue
        if category and meta.category != category:
            continue
        results.append(meta.to_dict())
    return results


def get_skills_by_names(names: list[str]) -> list[SkillMeta]:
    """根据名称列表批量获取技能元数据"""
    return [_skills[name] for name in names if name in _skills]
