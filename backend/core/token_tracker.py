# backend/core/token_tracker.py
# LLM Token 用量追踪 — 记录每次 LLM 调用的 token 消耗，支持配额告警

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class TokenStats:
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_calls: int = 0
    last_call_time: float = 0.0
    daily_calls: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))
    daily_input_tokens: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))
    daily_output_tokens: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))


_stats = TokenStats()
_lock = threading.Lock()


def record_tokens(input_tokens: int = 0, output_tokens: int = 0) -> None:
    """记录一次 LLM 调用的 token 消耗（线程安全）"""
    today = time.strftime("%Y-%m-%d")
    with _lock:
        _stats.total_input_tokens += input_tokens
        _stats.total_output_tokens += output_tokens
        _stats.total_calls += 1
        _stats.last_call_time = time.time()
        _stats.daily_calls[today] += 1
        _stats.daily_input_tokens[today] += input_tokens
        _stats.daily_output_tokens[today] += output_tokens


def extract_token_usage(response_metadata: dict | None) -> tuple[int, int]:
    """从 LLM response_metadata 中提取 token 用量"""
    if not response_metadata:
        return 0, 0
    usage = response_metadata.get("token_usage", {})
    if not usage and "usage" in response_metadata:
        usage = response_metadata["usage"]
    return (
        usage.get("input_tokens", usage.get("prompt_tokens", 0)),
        usage.get("output_tokens", usage.get("completion_tokens", 0)),
    )


def get_stats() -> dict:
    """获取 Token 使用统计"""
    today = time.strftime("%Y-%m-%d")
    with _lock:
        return {
            "total_calls": _stats.total_calls,
            "total_input_tokens": _stats.total_input_tokens,
            "total_output_tokens": _stats.total_output_tokens,
            "total_tokens": _stats.total_input_tokens + _stats.total_output_tokens,
            "last_call_time": _stats.last_call_time,
            "today_calls": _stats.daily_calls.get(today, 0),
            "today_input_tokens": _stats.daily_input_tokens.get(today, 0),
            "today_output_tokens": _stats.daily_output_tokens.get(today, 0),
            "cost_est_usd": _estimate_cost(
                _stats.total_input_tokens, _stats.total_output_tokens
            ),
        }


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """估算 LLM 调用成本（基于 DeepSeek 标准定价）"""
    return (input_tokens * 0.14 + output_tokens * 0.28) / 1_000_000


def check_daily_budget(max_daily_calls: int = 500) -> bool:
    """检查是否超过每日 API 调用预算"""
    today = time.strftime("%Y-%m-%d")
    with _lock:
        return _stats.daily_calls.get(today, 0) < max_daily_calls