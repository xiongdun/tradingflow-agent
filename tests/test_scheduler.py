# tests/test_scheduler.py
# 定时任务调度器测试 — CRUD 操作、触发逻辑

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest


@pytest.fixture
def patch_scheduler_db(tmp_path):
    """将 scheduler 的数据库指向临时目录，使用内存模式避免线程问题"""
    db_path = tmp_path / "history.db"
    with patch("backend.repositories.base._DB_PATH", db_path):
        # 重置连接池状态
        import backend.repositories.base as base
        base._pool_created = False
        while not base._pool.empty():
            try:
                base._pool.get_nowait()
            except Exception:
                break
        base._initialized_path = None

        from backend.repositories.base import _ensure_db
        conn = _ensure_db()
        conn.close()

        # 确保 scheduler 的表也被初始化
        from backend.core.scheduler import _init_schedule_table
        _init_schedule_table()
        yield db_path


class TestSchedulerCRUD:
    """测试定时任务的创建、列表、更新、删除"""

    @pytest.mark.asyncio
    async def test_create_and_list(self, patch_scheduler_db):
        from backend.core.scheduler import _create_sync, _list_sync
        task_id = _create_sync(
            symbol="600519", market="a_share", workflow="deep_analysis",
            schedule_type="daily", schedule_time="09:00", interval_minutes=60,
        )
        assert task_id > 0
        tasks = _list_sync()
        assert len(tasks) >= 1
        found = [t for t in tasks if t["id"] == task_id]
        assert len(found) == 1
        assert found[0]["symbol"] == "600519"

    @pytest.mark.asyncio
    async def test_update_task(self, patch_scheduler_db):
        from backend.core.scheduler import _create_sync, _update_sync
        task_id = _create_sync(symbol="AAPL", market="us_stock", workflow="deep_analysis",
                               schedule_type="daily", schedule_time="09:00", interval_minutes=60)
        ok = _update_sync(task_id, enabled=0)
        assert ok is True

    @pytest.mark.asyncio
    async def test_delete_task(self, patch_scheduler_db):
        from backend.core.scheduler import _create_sync, _delete_sync
        task_id = _create_sync(symbol="00700", market="h_stock", workflow="deep_analysis",
                               schedule_type="daily", schedule_time="09:00", interval_minutes=60)
        ok = _delete_sync(task_id)
        assert ok is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, patch_scheduler_db):
        from backend.core.scheduler import _delete_sync
        ok = _delete_sync(99999)
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
