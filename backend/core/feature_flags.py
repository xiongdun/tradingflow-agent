# backend/core/feature_flags.py
# 轻量特性开关系统 — 从 .env 读取 FEATURE_*=true/false，支持运行时查询和 Agent/Skill 实验性标记

from __future__ import annotations

import os
from functools import wraps
from typing import Callable

FEATURE_PREFIX = "FEATURE_"


def is_enabled(flag_name: str, default: bool = False) -> bool:
    """检查特性开关是否启用，读取环境变量 FEATURE_{flag_name}"""
    raw = os.getenv(f"{FEATURE_PREFIX}{flag_name.upper()}", str(default).lower())
    return raw.lower() in ("1", "true", "yes", "on")


def get_all_flags() -> dict[str, bool]:
    """获取所有已配置的特性开关"""
    flags: dict[str, bool] = {}
    for key, value in os.environ.items():
        if key.startswith(FEATURE_PREFIX) and not key.startswith(f"{FEATURE_PREFIX}_"):
            name = key[len(FEATURE_PREFIX):].lower()
            flags[name] = value.lower() in ("1", "true", "yes", "on")
    return flags


def experimental(flag_name: str | None = None):
    """装饰器：标记 Agent 或 Skill 为实验性，受特性开关控制

    用法:
        @experimental("trading_agent")
        class TradingAgent(BaseAgent):
            ...

    开关: FEATURE_TRADING_AGENT=true 才启用

    agent_metadata 中会添加 {"experimental": True, "feature_flag": "trading_agent"}
    """
    def decorator(cls_or_func: type | Callable):
        name = flag_name or cls_or_func.__name__.lower()
        meta = getattr(cls_or_func, "_experimental_meta", {})
        meta["experimental"] = True
        meta["feature_flag"] = name
        setattr(cls_or_func, "_experimental_meta", meta)

        @wraps(cls_or_func)
        def wrapper(*args, **kwargs):
            if not is_enabled(name):
                from loguru import logger
                logger.warning(f"Experimental feature '{name}' is disabled, skipping {cls_or_func.__name__}")
                return None
            return cls_or_func(*args, **kwargs)

        wrapper._experimental_meta = meta
        return wrapper
    return decorator