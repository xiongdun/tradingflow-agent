# backend/repositories/history.py
# 分析历史记录 CRUD — 同步实现 + 异步公共接口

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from loguru import logger


# ──────────────────────────── 同步 CRUD ────────────────────────────


def _save_sync(
    symbol: str,
    market: str,
    workflow: str,
    agents: list[str],
    opinions: list[dict],
    report: dict | None,
    markdown: str,
) -> int:
    from backend.repositories.base import get_db
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO analysis_history
               (symbol, market, workflow, agents, opinions, report, markdown, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                symbol,
                market,
                workflow,
                json.dumps(agents, ensure_ascii=False),
                json.dumps(opinions, ensure_ascii=False, default=str),
                json.dumps(report or {}, ensure_ascii=False, default=str),
                markdown,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0


def _list_sync(
    symbol: str | None = None,
    market: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    from backend.repositories.base import get_db
    with get_db() as conn:
        query = "SELECT * FROM analysis_history WHERE 1=1"
        params: list[Any] = []
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if market:
            query += " AND market = ?"
            params.append(market)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        return [
            {
                "id": r["id"],
                "symbol": r["symbol"],
                "market": r["market"],
                "workflow": r["workflow"],
                "agents": json.loads(r["agents"]),
                "opinions_count": len(json.loads(r["opinions"])),
                "created_at": r["created_at"],
            }
            for r in rows
        ]


def _get_sync(history_id: int) -> dict[str, Any] | None:
    from backend.repositories.base import get_db
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM analysis_history WHERE id = ?", (history_id,)
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "symbol": row["symbol"],
            "market": row["market"],
            "workflow": row["workflow"],
            "agents": json.loads(row["agents"]),
            "opinions": json.loads(row["opinions"]),
            "report": json.loads(row["report"]),
            "markdown": row["markdown"],
            "created_at": row["created_at"],
        }


def _delete_sync(history_id: int) -> bool:
    from backend.repositories.base import get_db
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM analysis_history WHERE id = ?", (history_id,)
        )
        conn.commit()
        return cursor.rowcount > 0


def _backtest_sync(symbol: str, days: int = 30) -> dict[str, Any]:
    from backend.repositories.base import get_db
    with get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM analysis_history
               WHERE symbol = ?
               AND created_at >= datetime('now', ?)
               ORDER BY created_at ASC""",
            (symbol, f"-{days} days"),
        ).fetchall()

        if not rows:
            return {"symbol": symbol, "days": days, "records": 0, "summary": "无历史分析记录"}

        predictions = []
        for row in rows:
            opinions = json.loads(row["opinions"])
            created = row["created_at"]
            for op in opinions:
                predictions.append({
                    "date": created,
                    "agent_role": op.get("agent_role", ""),
                    "agent_name": op.get("agent_name", ""),
                    "stance": op.get("stance", "neutral"),
                    "confidence": op.get("confidence", 0),
                })

        agent_stats: dict[str, dict] = {}
        for pred in predictions:
            role = pred["agent_role"]
            if role not in agent_stats:
                agent_stats[role] = {"name": pred["agent_name"], "total": 0, "stances": {}}
            agent_stats[role]["total"] += 1
            stance = pred["stance"]
            agent_stats[role]["stances"][stance] = agent_stats[role]["stances"].get(stance, 0) + 1

        return {
            "symbol": symbol,
            "days": days,
            "records": len(rows),
            "total_predictions": len(predictions),
            "agent_stats": agent_stats,
        }


# ──────────────────────────── 异步公共接口 ────────────────────────────


async def save_analysis(
    symbol: str,
    market: str,
    workflow: str,
    agents: list[str],
    opinions: list[dict],
    report: dict | None,
    markdown: str,
) -> int:
    return await asyncio.to_thread(
        _save_sync, symbol, market, workflow, agents, opinions, report, markdown
    )


async def list_history(
    symbol: str | None = None,
    market: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_list_sync, symbol, market, limit, offset)


async def get_history(history_id: int) -> dict[str, Any] | None:
    return await asyncio.to_thread(_get_sync, history_id)


async def delete_history(history_id: int) -> bool:
    return await asyncio.to_thread(_delete_sync, history_id)


async def backtest(symbol: str, days: int = 30) -> dict[str, Any]:
    return await asyncio.to_thread(_backtest_sync, symbol, days)