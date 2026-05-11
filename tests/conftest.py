# tests/conftest.py
# pytest fixtures — 临时数据库、缓存目录隔离

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def tmp_db(tmp_path: Path):
    """创建临时 SQLite 数据库，返回连接工厂"""
    db_path = tmp_path / "test_history.db"

    def _get_conn():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn

    return _get_conn


@pytest.fixture
def tmp_cache_dir(tmp_path: Path):
    """创建临时缓存目录"""
    cache_dir = tmp_path / ".cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def patch_db_path(tmp_path: Path):
    """将数据库 _DB_PATH 指向临时目录，同时重置连接池防止跨测试连接污染"""
    db_path = tmp_path / "history.db"
    import backend.repositories.base as base_mod
    with patch.object(base_mod, "_DB_PATH", db_path):
        base_mod._pool_created = False
        while not base_mod._pool.empty():
            try:
                c = base_mod._pool.get_nowait()
                c.close()
            except Exception:
                break
        base_mod._initialized_path = None

        from backend.repositories.base import _ensure_db
        conn = _ensure_db()
        conn.close()
        yield db_path


@pytest.fixture
def patch_cache_dir(tmp_cache_dir: Path):
    """将 cache.py 的 _CACHE_DIR 指向临时目录"""
    with patch("backend.core.cache._CACHE_DIR", tmp_cache_dir):
        yield tmp_cache_dir
