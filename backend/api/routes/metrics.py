# backend/api/routes/metrics.py
# Prometheus 指标端点 — 暴露 /api/metrics 供 Grafana/Prometheus 抓取

from __future__ import annotations

import time

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

_START_TIME = time.time()


def _format_prometheus(name: str, value: float, labels: dict[str, str] | None = None,
                       help_text: str = "") -> str:
    """格式化为 Prometheus exposition 格式"""
    lines = []
    if help_text:
        lines.append(f"# HELP {name} {help_text}")
    lines.append(f"# TYPE {name} gauge")
    if labels:
        label_str = "{" + ",".join(f'{k}="{v}"' for k, v in labels.items()) + "}"
        lines.append(f"{name}{label_str} {value}")
    else:
        lines.append(f"{name} {value}")
    return "\n".join(lines) + "\n"


@router.get("", response_class=PlainTextResponse)
@router.get("/", response_class=PlainTextResponse)
async def get_metrics():
    """Prometheus 标准 /metrics 端点"""
    uptime = time.time() - _START_TIME

    lines = [
        _format_prometheus("tradingflow_uptime_seconds", uptime,
                           help_text="服务运行时长（秒）"),
    ]

    # Token 统计
    try:
        from backend.core.token_tracker import get_stats
        stats = get_stats()
        lines.append(_format_prometheus("tradingflow_llm_calls_total", stats["total_calls"],
                                        help_text="LLM 调用总数"))
        lines.append(_format_prometheus("tradingflow_llm_input_tokens_total", stats["total_input_tokens"],
                                        help_text="LLM 输入 Token 总数"))
        lines.append(_format_prometheus("tradingflow_llm_output_tokens_total", stats["total_output_tokens"],
                                        help_text="LLM 输出 Token 总数"))
        lines.append(_format_prometheus("tradingflow_llm_calls_today", stats["today_calls"],
                                        help_text="今日 LLM 调用次数"))
        lines.append(_format_prometheus("tradingflow_llm_cost_est_usd", stats["cost_est_usd"],
                                        help_text="LLM 估算成本（美元）"))
    except ImportError:
        pass

    # 分析队列统计
    try:
        from backend.core.analysis_service import AnalysisService
        if hasattr(AnalysisService, "_active_analyses"):
            lines.append(_format_prometheus("tradingflow_active_analyses",
                                            len(AnalysisService._active_analyses),
                                            help_text="当前活跃分析数"))
    except (ImportError, AttributeError):
        pass

    return "".join(lines)