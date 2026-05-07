# backend/core/scheduler.py
# 轻量定时任务调度器 — 基于 asyncio 实现定时自动分析

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from loguru import logger

import backend.repositories.base as _base
from backend.repositories.base import get_db

_running = False
_task: asyncio.Task | None = None

# 记录所有已初始化调度表的 DB 路径 — 测试中每个 fixture 有不同临时路径
_schedule_initialized_paths: set[str] = set()


def _init_schedule_table() -> None:
    current = str(_base._DB_PATH)
    if current in _schedule_initialized_paths:
        return
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                market TEXT NOT NULL DEFAULT 'a_share',
                workflow TEXT DEFAULT 'deep_analysis',
                schedule_type TEXT NOT NULL DEFAULT 'daily',
                schedule_time TEXT DEFAULT '09:00',
                interval_minutes INTEGER DEFAULT 60,
                enabled INTEGER DEFAULT 1,
                last_run TEXT,
                next_run TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
    _schedule_initialized_paths.add(current)


def _calc_next_run(schedule_type: str, schedule_time: str, interval_minutes: int) -> str:
    now = datetime.now()
    if schedule_type in ("daily", "once"):
        parts = schedule_time.split(":")
        hour, minute = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        next_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_dt <= now:
            next_dt += timedelta(days=1)
        return next_dt.isoformat()
    elif schedule_type == "interval":
        return (now + timedelta(minutes=interval_minutes)).isoformat()
    return (now + timedelta(hours=1)).isoformat()


def _create_sync(
    symbol: str, market: str, workflow: str,
    schedule_type: str, schedule_time: str, interval_minutes: int,
) -> int:
    _init_schedule_table()
    with get_db() as conn:
        next_run = _calc_next_run(schedule_type, schedule_time, interval_minutes)
        cursor = conn.execute(
            """INSERT INTO scheduled_tasks
               (symbol, market, workflow, schedule_type, schedule_time, interval_minutes, next_run, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (symbol, market, workflow, schedule_type, schedule_time, interval_minutes, next_run, datetime.now().isoformat()),
        )
        conn.commit()
        return cursor.lastrowid or 0


def _list_sync() -> list[dict[str, Any]]:
    _init_schedule_table()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM scheduled_tasks ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def _update_sync(task_id: int, **kwargs: Any) -> bool:
    _init_schedule_table()
    with get_db() as conn:
        sets, params = [], []
        for k, v in kwargs.items():
            if k in ("enabled", "schedule_time", "interval_minutes", "workflow"):
                sets.append(f"{k} = ?")
                params.append(v)
        if not sets:
            return False
        params.append(task_id)
        cursor = conn.execute(f"UPDATE scheduled_tasks SET {', '.join(sets)} WHERE id = ?", params)
        conn.commit()
        return cursor.rowcount > 0


def _delete_sync(task_id: int) -> bool:
    _init_schedule_table()
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM scheduled_tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0


def _get_due_tasks() -> list[dict[str, Any]]:
    _init_schedule_table()
    with get_db() as conn:
        now = datetime.now().isoformat()
        rows = conn.execute(
            "SELECT * FROM scheduled_tasks WHERE enabled = 1 AND next_run <= ?", (now,)
        ).fetchall()
        return [dict(r) for r in rows]


def _mark_run(task_id: int, schedule_type: str, schedule_time: str, interval_minutes: int) -> None:
    _init_schedule_table()
    with get_db() as conn:
        now = datetime.now().isoformat()
        if schedule_type == "once":
            conn.execute("UPDATE scheduled_tasks SET last_run = ?, enabled = 0 WHERE id = ?", (now, task_id))
        else:
            next_run = _calc_next_run(schedule_type, schedule_time, interval_minutes)
            conn.execute("UPDATE scheduled_tasks SET last_run = ?, next_run = ? WHERE id = ?", (now, next_run, task_id))
        conn.commit()


async def _run_analysis(task: dict[str, Any]) -> None:
    try:
        from backend.core.analysis_service import AnalysisService
        workflow = task.get("workflow", "deep_analysis")
        workflow_def = AnalysisService.load_workflow(workflow)
        if not workflow_def:
            workflow_def = {"name": "custom", "agents": [{"role": "fundamental"}, {"role": "technical"}]}
        await AnalysisService.run_and_save(task["symbol"], task.get("market", "a_share"), workflow_def)
        logger.info(f"[scheduler] 定时分析完成: {task['symbol']}")
    except Exception as e:
        logger.error(f"[scheduler] 定时分析失败: {task['symbol']} - {e}")


async def _scheduler_loop() -> None:
    while _running:
        try:
            for task in _get_due_tasks():
                logger.info(f"[scheduler] 触发: {task['symbol']} ({task['schedule_type']})")
                asyncio.create_task(_run_analysis(task))
                _mark_run(task["id"], task["schedule_type"], task["schedule_time"], task.get("interval_minutes", 60))
        except Exception as e:
            logger.error(f"[scheduler] 异常: {e}")
        await asyncio.sleep(30)


def start_scheduler() -> None:
    global _running, _task
    if _running:
        return
    _running = True
    _init_schedule_table()
    _task = asyncio.create_task(_scheduler_loop())
    logger.info("[scheduler] 调度器已启动")


def stop_scheduler() -> None:
    global _running, _task
    _running = False
    if _task:
        _task.cancel()
        _task = None


async def create_task(
    symbol: str, market: str = "a_share", workflow: str = "deep_analysis",
    schedule_type: str = "daily", schedule_time: str = "09:00", interval_minutes: int = 60,
) -> int:
    return await asyncio.to_thread(
        _create_sync, symbol, market, workflow, schedule_type, schedule_time, interval_minutes
    )


async def list_tasks() -> list[dict[str, Any]]:
    return await asyncio.to_thread(_list_sync)


async def update_task(task_id: int, **kwargs: Any) -> bool:
    return await asyncio.to_thread(_update_sync, task_id, **kwargs)


async def delete_task(task_id: int) -> bool:
    return await asyncio.to_thread(_delete_sync, task_id)
