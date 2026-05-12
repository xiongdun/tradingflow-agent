# backend/api/routes/features.py
# 特性开关 API — 前端查询哪些功能可用

from __future__ import annotations

from fastapi import APIRouter

from backend.core.feature_flags import get_all_flags, is_enabled

router = APIRouter(prefix="/api/features", tags=["features"])


@router.get("")
async def list_features():
    """列出所有特性开关状态"""
    flags = get_all_flags()
    # 默认始终返回已知的开关（即使未配置也返回默认值）
    defaults = {
        "trading_agent": is_enabled("trading_agent", default=False),
        "multi_round_debate": is_enabled("multi_round_debate", default=False),
        "quant_hybrid": is_enabled("quant_hybrid", default=False),
        "experimental_skills": is_enabled("experimental_skills", default=False),
    }
    return {**defaults, **flags}


@router.get("/{flag_name}")
async def check_feature(flag_name: str):
    """检查单个特性开关状态"""
    return {
        "flag": flag_name,
        "enabled": is_enabled(flag_name),
    }