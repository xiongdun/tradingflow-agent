# backend/api/routes/data_sources.py
# 数据源管理 API 路由

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/providers", tags=["providers"])


class ProviderPriorityUpdate(BaseModel):
    """数据源优先级更新请求"""
    market: str
    providers: list[str]


@router.get("")
async def get_providers():
    """获取各市场的数据源优先级配置"""
    from backend.data.factory import get_provider_info
    return get_provider_info()


@router.put("")
async def update_providers(req: ProviderPriorityUpdate):
    """更新指定市场的数据源优先级"""
    from backend.data.factory import set_provider_priority
    if not set_provider_priority(req.market, req.providers):
        return {"error": f"Unknown market: {req.market}"}
    return {"status": "ok", "market": req.market, "providers": req.providers}


@router.post("/reset")
async def reset_providers(market: str = ""):
    """重置数据提供者缓存（可选指定市场）"""
    from backend.data.factory import reset_provider
    reset_provider(market or None)
    return {"status": "ok"}
