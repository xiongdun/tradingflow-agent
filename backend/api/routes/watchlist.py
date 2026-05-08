# backend/api/routes/watchlist.py
# 自选股/关注列表 API 路由

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


class WatchlistAdd(BaseModel):
    symbol: str
    market: str = "a_share"
    name: str = ""
    group_name: str = "default"


@router.get("")
async def get_watchlist(group: str = ""):
    """获取关注列表"""
    from backend.core.watchlist import list_watchlist
    items = await list_watchlist(group or None)
    return {"items": items, "count": len(items)}


@router.post("")
async def add_watchlist(req: WatchlistAdd):
    """添加股票到关注列表"""
    from backend.core.watchlist import add_to_watchlist
    item_id = await add_to_watchlist(req.symbol, req.market, req.name, req.group_name)
    return {"status": "ok", "id": item_id}


@router.delete("/{item_id}")
async def delete_watchlist(item_id: int):
    """从关注列表删除"""
    from backend.core.watchlist import remove_from_watchlist
    deleted = await remove_from_watchlist(item_id)
    if not deleted:
        return {"error": "Item not found"}
    return {"status": "ok", "deleted": item_id}


@router.post("/batch-analyze")
async def batch_analyze():
    """批量分析自选股列表中的所有股票"""
    from backend.core.analysis_service import AnalysisService
    from backend.core.watchlist import list_watchlist

    items = await list_watchlist()
    if not items:
        return {"status": "ok", "message": "Watchlist is empty", "results": []}

    workflow_def = AnalysisService.load_workflow("quick_scan") or {"name": "quick_scan", "agents": [{"role": "fundamental"}, {"role": "technical"}]}
    results = []
    for item in items:
        try:
            await AnalysisService.run_and_save(item["symbol"], item.get("market", "a_share"), workflow_def)
            results.append({"symbol": item["symbol"], "status": "completed"})
        except Exception as e:
            results.append({"symbol": item["symbol"], "status": "error", "error": str(e)})

    return {"status": "ok", "total": len(items), "results": results}
