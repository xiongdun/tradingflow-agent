# backend/core/watchlist.py
# 自选股/关注列表 — SQLite 存储用户关注的股票

from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.repositories.base import _ensure_db


def _add_sync(symbol: str, market: str, name: str, group_name: str) -> int:
    conn = _ensure_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                market TEXT NOT NULL,
                name TEXT DEFAULT '',
                group_name TEXT DEFAULT 'default',
                added_at TEXT NOT NULL,
                UNIQUE(symbol, market)
            )
        """)
        cursor = conn.execute(
            "INSERT OR IGNORE INTO watchlist (symbol, market, name, group_name, added_at) VALUES (?, ?, ?, ?, ?)",
            (symbol, market, name, group_name, datetime.now().isoformat()),
        )
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def _list_sync(group_name: str | None = None) -> list[dict[str, Any]]:
    conn = _ensure_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                market TEXT NOT NULL,
                name TEXT DEFAULT '',
                group_name TEXT DEFAULT 'default',
                added_at TEXT NOT NULL,
                UNIQUE(symbol, market)
            )
        """)
        query = "SELECT * FROM watchlist"
        params: list[Any] = []
        if group_name:
            query += " WHERE group_name = ?"
            params.append(group_name)
        query += " ORDER BY added_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [
            {"id": r["id"], "symbol": r["symbol"], "market": r["market"],
             "name": r["name"], "group_name": r["group_name"], "added_at": r["added_at"]}
            for r in rows
        ]
    finally:
        conn.close()


def _delete_sync(item_id: int) -> bool:
    conn = _ensure_db()
    try:
        cursor = conn.execute("DELETE FROM watchlist WHERE id = ?", (item_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


async def add_to_watchlist(symbol: str, market: str, name: str = "", group_name: str = "default") -> int:
    return await asyncio.to_thread(_add_sync, symbol, market, name, group_name)


async def list_watchlist(group_name: str | None = None) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_list_sync, group_name)


async def remove_from_watchlist(item_id: int) -> bool:
    return await asyncio.to_thread(_delete_sync, item_id)
