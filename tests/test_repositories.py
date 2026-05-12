# tests/test_repositories.py
# 数据访问层测试 — history CRUD + 回测统计

from __future__ import annotations

import pytest


class TestHistoryRepository:
    """测试分析历史记录仓库"""

    @pytest.mark.asyncio
    async def test_save_and_get(self, patch_db_path):
        from backend.repositories.history import save_analysis, get_history, list_history

        history_id = await save_analysis(
            symbol="TEST001",
            market="a_share",
            workflow="deep_analysis",
            agents=["fundamental", "technical"],
            opinions=[{"agent_role": "fundamental", "stance": "bullish"}],
            report={"overall_stance": "bullish"},
            markdown="# Test",
        )
        assert history_id > 0

        records = await list_history()
        assert any(r["symbol"] == "TEST001" for r in records)

        detail = await get_history(history_id)
        assert detail is not None
        assert detail["symbol"] == "TEST001"
        assert detail["market"] == "a_share"
        assert len(detail["agents"]) == 2

    @pytest.mark.asyncio
    async def test_list_with_filter(self, patch_db_path):
        from backend.repositories.history import save_analysis, list_history

        await save_analysis("AAA", "a_share", "test", [], [], {}, "")
        await save_analysis("BBB", "us_stock", "test", [], [], {}, "")

        all_records = await list_history()
        assert len(all_records) >= 2

        a_share_records = await list_history(symbol="AAA")
        assert all(r["symbol"] == "AAA" for r in a_share_records)

        us_records = await list_history(market="us_stock")
        assert all(r["market"] == "us_stock" for r in us_records)

    @pytest.mark.asyncio
    async def test_list_pagination(self, patch_db_path):
        from backend.repositories.history import save_analysis, list_history

        for i in range(5):
            await save_analysis(f"PAGE{i}", "a_share", "test", [], [], {}, "")

        page1 = await list_history(limit=2, offset=0)
        assert len(page1) == 2

        page2 = await list_history(limit=2, offset=2)
        assert len(page2) == 2

    @pytest.mark.asyncio
    async def test_delete_history(self, patch_db_path):
        from backend.repositories.history import save_analysis, delete_history, get_history

        history_id = await save_analysis("DEL", "a_share", "test", [], [], {}, "")
        result = await delete_history(history_id)
        assert result is True

        detail = await get_history(history_id)
        assert detail is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, patch_db_path):
        from backend.repositories.history import delete_history
        result = await delete_history(99999)
        assert result is False


class TestBacktest:
    """测试回测功能"""

    @pytest.mark.asyncio
    async def test_backtest_empty(self, patch_db_path):
        from backend.repositories.history import backtest
        result = await backtest("NO_HISTORY", days=30)
        assert result["records"] == 0
        assert result["symbol"] == "NO_HISTORY"

    @pytest.mark.asyncio
    async def test_backtest_with_data(self, patch_db_path):
        from backend.repositories.history import save_analysis, backtest

        await save_analysis(
            symbol="BT001",
            market="a_share",
            workflow="deep_analysis",
            agents=["fundamental"],
            opinions=[
                {"agent_role": "fundamental", "agent_name": "基本面", "stance": "bullish", "confidence": 0.8}
            ],
            report={},
            markdown="",
        )

        result = await backtest("BT001", days=30)
        assert result["records"] >= 1
        assert result["total_predictions"] >= 1
        assert "agent_stats" in result
        assert "fundamental" in result["agent_stats"]
        stats = result["agent_stats"]["fundamental"]
        assert stats["total"] >= 1
        assert "stances" in stats
        assert stats["stances"]["bullish"] >= 1


class TestDBRollback:
    """测试 get_db() 异常时自动回滚 — 防止脏连接污染连接池"""

    def test_rollback_on_error(self, patch_db_path):
        """当 with 块内抛出异常时，连接必须调用 rollback()"""
        import sqlite3
        from unittest.mock import MagicMock, patch as mock_patch

        mock_conn = MagicMock(spec=sqlite3.Connection)
        mock_conn.row_factory = sqlite3.Row

        return_spy = MagicMock()

        with mock_patch("backend.repositories.base._ensure_db", return_value=mock_conn), \
             mock_patch("backend.repositories.base._return_conn", return_spy):
            from backend.repositories.base import get_db
            try:
                with get_db() as conn:
                    raise ValueError("模拟数据库操作异常")
            except ValueError:
                pass

        mock_conn.rollback.assert_called_once()

    def test_normal_flow_no_rollback(self, patch_db_path):
        """正常流程不触发 rollback，连接归还池"""
        import sqlite3
        from unittest.mock import MagicMock, patch as mock_patch

        mock_conn = MagicMock(spec=sqlite3.Connection)
        mock_conn.row_factory = sqlite3.Row

        return_spy = MagicMock()

        with mock_patch("backend.repositories.base._ensure_db", return_value=mock_conn), \
             mock_patch("backend.repositories.base._return_conn", return_spy):
            from backend.repositories.base import get_db
            with get_db() as conn:
                conn.execute("SELECT 1")

        mock_conn.rollback.assert_not_called()
        return_spy.assert_called_once()
