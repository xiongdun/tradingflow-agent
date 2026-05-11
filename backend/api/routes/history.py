# backend/api/routes/history.py
# 历史记录、回测、报告导出 API 路由

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history")
async def get_history_list(symbol: str = "", market: str = "", limit: int = 20, offset: int = 0):
    """查询分析历史记录列表"""
    from backend.repositories.history import list_history
    records = await list_history(
        symbol=symbol or None,
        market=market or None,
        limit=limit,
        offset=offset,
    )
    return {"records": records, "count": len(records)}


@router.get("/history/{history_id}")
async def get_history_detail(history_id: int):
    """获取单条历史分析记录详情"""
    from backend.repositories.history import get_history
    record = await get_history(history_id)
    if not record:
        return {"error": "Record not found"}
    return record


@router.delete("/history/{history_id}")
async def delete_history_record(history_id: int):
    """删除历史分析记录"""
    from backend.repositories.history import delete_history
    deleted = await delete_history(history_id)
    if not deleted:
        return {"error": "Record not found"}
    return {"status": "ok", "deleted": history_id}


@router.get("/backtest")
async def run_backtest(symbol: str, days: int = 30):
    """回测：统计某股票历史分析中各 Agent 的预测分布"""
    from backend.repositories.history import backtest
    return await backtest(symbol, days)


def _export_response(record: dict, format: str) -> Response:
    from backend.output.report import generate_html_report, generate_text_report

    report = record.get("report", {})
    symbol = record.get("symbol", "report")

    if format == "html":
        content = generate_html_report(report) if report else record.get("markdown", "")
        return Response(content=content, media_type="text/html",
                       headers={"Content-Disposition": f'attachment; filename="{symbol}_report.html"'})
    if format == "txt":
        content = generate_text_report(report) if report else record.get("markdown", "")
        return Response(content=content, media_type="text/plain",
                       headers={"Content-Disposition": f'attachment; filename="{symbol}_report.txt"'})

    content = record.get("markdown", "")
    return Response(content=content, media_type="text/markdown",
                   headers={"Content-Disposition": f'attachment; filename="{symbol}_report.md"'})


@router.get("/export/latest")
async def export_latest_report(format: str = "md"):
    """导出最近一条分析报告为指定格式（md/html/txt）"""
    from backend.repositories.history import get_history, list_history

    records = await list_history(limit=1)
    if not records:
        return {"error": "Record not found"}

    record = await get_history(records[0]["id"])
    if not record:
        return {"error": "Record not found"}
    return _export_response(record, format)


@router.get("/export/{history_id}")
async def export_report(history_id: int, format: str = "md"):
    """导出分析报告为指定格式（md/html/txt）"""
    from backend.repositories.history import get_history

    record = await get_history(history_id)
    if not record:
        return {"error": "Record not found"}
    return _export_response(record, format)
