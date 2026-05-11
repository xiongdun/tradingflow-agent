# backend/repositories/base.py
# 共享连接管理 — 数据库路径、连接池、表初始化

from __future__ import annotations

import queue
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

# 数据库文件路径
_DB_PATH = Path(__file__).parent.parent / "data" / "history.db"

# 记录已初始化的 DB 路径 — 当 _DB_PATH 被测试 patch 改变时自动重新初始化
_initialized_path: str | None = None

# Thread-safe connection pool
_POOL_SIZE = 5
_pool: queue.Queue[sqlite3.Connection] = queue.Queue(maxsize=_POOL_SIZE)
_pool_lock = threading.Lock()
_pool_created = False


def _create_conn() -> sqlite3.Connection:
    """Create a new SQLite connection with WAL + busy_timeout"""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _get_conn() -> sqlite3.Connection:
    """Get a connection from the pool, or create a new one if pool is empty"""
    global _pool_created
    if not _pool_created:
        with _pool_lock:
            if not _pool_created:
                _init_tables(_create_conn())
                _pool_created = True
    try:
        return _pool.get_nowait()
    except queue.Empty:
        return _create_conn()


def _return_conn(conn: sqlite3.Connection) -> None:
    """Return a connection to the pool, or close it if pool is full"""
    try:
        _pool.put_nowait(conn)
    except queue.Full:
        conn.close()


def _init_tables(conn: sqlite3.Connection) -> None:
    """初始化数据库表"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            market TEXT NOT NULL,
            workflow TEXT DEFAULT '',
            agents TEXT DEFAULT '[]',
            opinions TEXT DEFAULT '[]',
            report TEXT DEFAULT '{}',
            markdown TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_history_symbol ON analysis_history(symbol);
        CREATE INDEX IF NOT EXISTS idx_history_market ON analysis_history(market);
        CREATE INDEX IF NOT EXISTS idx_history_created ON analysis_history(created_at);
    """)
    conn.commit()


def _ensure_db() -> sqlite3.Connection:
    """确保数据库已初始化并返回连接（路径变更时自动重新初始化）"""
    global _initialized_path
    conn = _get_conn()
    current = str(_DB_PATH)
    if _initialized_path != current:
        _init_tables(conn)
        _initialized_path = current
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """数据库连接上下文管理器 — 自动归还连接到连接池"""
    conn = _ensure_db()
    try:
        yield conn
    finally:
        _return_conn(conn)
