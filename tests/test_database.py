# tests/test_database.py
# 数据库连接池模块测试 — 连接获取、复用、表格初始化

from __future__ import annotations


class TestDatabaseConnectionPool:
    def test_get_db_returns_connection(self, patch_db_path):
        from backend.repositories.base import get_db
        with get_db() as conn:
            cursor = conn.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1

    def test_connection_pool_reuse(self, patch_db_path):
        from backend.repositories.base import get_db
        with get_db() as conn1:
            conn1.execute("CREATE TABLE IF NOT EXISTS _test_pool (id INTEGER)")
            conn1.commit()
        with get_db() as conn2:
            conn2.execute("DROP TABLE IF EXISTS _test_pool")
            conn2.commit()

    def test_table_initialization(self, patch_db_path):
        from backend.repositories.base import get_db
        with get_db() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]
            assert "analysis_history" in table_names

    def test_wal_mode_enabled(self, patch_db_path):
        from backend.repositories.base import get_db
        with get_db() as conn:
            journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert journal_mode.lower() == "wal"