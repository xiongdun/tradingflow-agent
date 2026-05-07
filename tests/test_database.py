# tests/test_database.py
# 数据库模块测试 — CRUD + 回测

from __future__ import annotations

import pytest


class TestDatabase:
    @pytest.mark.asyncio
    async def test_save_and_list(self, patch_db_path):
        from backend.core.database import save_analysis, list_history

        await save_analysis(
            symbol="TEST", market="a_share", workflow="deep_analysis",
            agents=["fundamental", "technical"],
            opinions=[{"agent_name": "Fund", "stance": "bullish", "confidence": 0.8}],
            report={"overall_stance": "bullish", "overall_confidence": 0.8},
            markdown="# Test Report",
        )
        records = await list_history()
        assert len(records) >= 1
        assert records[0]["symbol"] == "TEST"

    @pytest.mark.asyncio
    async def test_get_history_detail(self, patch_db_path):
        from backend.core.database import save_analysis, get_history, list_history

        await save_analysis(
            symbol="DETAIL", market="us_stock", workflow="quick_scan",
            agents=["technical"], opinions=[], report={}, markdown="test",
        )
        records = await list_history()
        detail = await get_history(records[0]["id"])
        assert detail is not None
        assert detail["symbol"] == "DETAIL"

    @pytest.mark.asyncio
    async def test_delete_history(self, patch_db_path):
        from backend.core.database import save_analysis, list_history, delete_history

        await save_analysis(
            symbol="DEL", market="a_share", workflow="test",
            agents=[], opinions=[], report={}, markdown="",
        )
        records = await list_history()
        assert len(records) >= 1
        result = await delete_history(records[0]["id"])
        assert result is True

    @pytest.mark.asyncio
    async def test_backtest_empty(self, patch_db_path):
        from backend.core.database import backtest

        result = await backtest(symbol="EMPTY", days=30)
        assert result["records"] == 0
