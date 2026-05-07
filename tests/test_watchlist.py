# tests/test_watchlist.py
# 自选股模块测试 — 添加、列表、删除、去重

from __future__ import annotations

import pytest


class TestWatchlist:
    @pytest.mark.asyncio
    async def test_add_and_list(self, patch_db_path):
        from backend.core.watchlist import add_to_watchlist, list_watchlist

        item_id = await add_to_watchlist("600519", "a_share", "贵州茅台")
        assert item_id > 0

        items = await list_watchlist()
        assert len(items) >= 1
        assert items[0]["symbol"] == "600519"

    @pytest.mark.asyncio
    async def test_duplicate_ignored(self, patch_db_path):
        from backend.core.watchlist import add_to_watchlist, list_watchlist

        await add_to_watchlist("AAPL", "us_stock", "Apple")
        await add_to_watchlist("AAPL", "us_stock", "Apple Dup")

        items = await list_watchlist()
        aapl_items = [i for i in items if i["symbol"] == "AAPL"]
        assert len(aapl_items) == 1

    @pytest.mark.asyncio
    async def test_delete(self, patch_db_path):
        from backend.core.watchlist import add_to_watchlist, list_watchlist, remove_from_watchlist

        item_id = await add_to_watchlist("TSLA", "us_stock", "Tesla")
        result = await remove_from_watchlist(item_id)
        assert result is True

        items = await list_watchlist()
        assert all(i["symbol"] != "TSLA" for i in items)

    @pytest.mark.asyncio
    async def test_list_by_group(self, patch_db_path):
        from backend.core.watchlist import add_to_watchlist, list_watchlist

        await add_to_watchlist("AAA", "a_share", name="A", group_name="tech")
        await add_to_watchlist("BBB", "a_share", name="B", group_name="finance")

        tech = await list_watchlist(group_name="tech")
        assert len(tech) >= 1
        assert all(i["group_name"] == "tech" for i in tech)
