# backend/api/routes/schedules.py
# 定时任务管理 API 路由

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


class ScheduleCreate(BaseModel):
    symbol: str
    market: str = "a_share"
    workflow: str = "deep_analysis"
    schedule_type: str = "daily"
    schedule_time: str = "09:00"
    interval_minutes: int = 60


class ScheduleUpdate(BaseModel):
    enabled: int | None = None
    schedule_time: str | None = None
    interval_minutes: int | None = None
    workflow: str | None = None


@router.get("")
async def get_schedules():
    """获取定时任务列表"""
    from backend.core.scheduler import list_tasks
    return await list_tasks()


@router.post("")
async def create_schedule(req: ScheduleCreate):
    """创建定时任务"""
    from backend.core.scheduler import create_task
    task_id = await create_task(
        symbol=req.symbol, market=req.market, workflow=req.workflow,
        schedule_type=req.schedule_type, schedule_time=req.schedule_time,
        interval_minutes=req.interval_minutes,
    )
    return {"status": "ok", "id": task_id}


@router.put("/{task_id}")
async def update_schedule(task_id: int, req: ScheduleUpdate):
    """更新定时任务"""
    from backend.core.scheduler import update_task
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    updated = await update_task(task_id, **kwargs)
    if not updated:
        return {"error": "Task not found"}
    return {"status": "ok"}


@router.delete("/{task_id}")
async def delete_schedule(task_id: int):
    """删除定时任务"""
    from backend.core.scheduler import delete_task
    deleted = await delete_task(task_id)
    if not deleted:
        return {"error": "Task not found"}
    return {"status": "ok", "deleted": task_id}
