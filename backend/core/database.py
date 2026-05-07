# backend/core/database.py
# 向后兼容 re-export 层 — 实际实现已迁移到 backend/repositories/
from backend.repositories.base import _DB_PATH, _get_conn, _init_tables, _ensure_db
from backend.repositories.history import (
    save_analysis, list_history, get_history, delete_history, backtest,
    _save_sync, _list_sync, _get_sync, _delete_sync, _backtest_sync,
)
