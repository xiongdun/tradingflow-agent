# tests/test_scheduler.py
# 定时任务调度器测试 — CRUD 操作、触发逻辑

from __future__ import annotations

import asyncio

import pytest


@pytest.fixture
def patch_scheduler_db(tmp_path):
    """将 scheduler 的数据库指向临时目录"""
    from unittest.mock import patch
    with patch("backend.repositories.base._DB_PATH", tmp_path / "history.db"):
        from backend.repositories.base import _ensure_db
        _ensure_db()
        # 确保 scheduler 的表也被初始化
        from backend.core.scheduler import _init_schedule_table
        _init_schedule_table()
        yield tmp_path


class TestSchedulerCRUD:
    """测试定时任务的创建、列表、更新、删除"""

    @pytest.mark.asyncio
    async def test_create_and_list(self, patch_scheduler_db):
        from backend.core.scheduler import create_task, list_tasks
        task_id = await create_task(
            symbol="600519", market="a_share", workflow="deep_analysis",
            schedule_type="daily", schedule_time="09:00",
        )
        assert task_id > 0
        tasks = await list_tasks()
        assert len(tasks) >= 1
        found = [t for t in tasks if t["id"] == task_id]
        assert len(found) == 1
        assert found[0]["symbol"] == "600519"

    @pytest.mark.asyncio
    async def test_update_task(self, patch_scheduler_db):
        from backend.core.scheduler import create_task, update_task
        task_id = await create_task(symbol="AAPL", market="us_stock")
        ok = await update_task(task_id, enabled=0)
        assert ok is True

    @pytest.mark.asyncio
    async def test_delete_task(self, patch_scheduler_db):
        from backend.core.scheduler import create_task, delete_task
        task_id = await create_task(symbol="00700", market="h_stock")
        ok = await delete_task(task_id)
        assert ok is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, patch_scheduler_db):
        from backend.core.scheduler import delete_task
        ok = await delete_task(99999)
        assert ok is False


class TestSchedulerCalc:
    """测试下次执行时间计算"""

    def test_daily_next_run(self):
        from backend.core.scheduler import _calc_next_run
        result = _calc_next_run("daily", "09:00", 60)
        assert result is not None
        assert "T09:00" in result

    def test_interval_next_run(self):
        from backend.core.scheduler import _calc_next_run
        result = _calc_next_run("interval", "09:00", 30)
        assert result is not None

    def test_once_next_run(self):
        from backend.core.scheduler import _calc_next_run
        result = _calc_next_run("once", "14:30", 60)
        assert result is not None
        assert "T14:30" in result
