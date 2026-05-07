# backend/api/routes/history.py
# 历史记录、回测、报告导出 API 路由

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history")
async def get_history_list(symbol: str = "", market: str = "", limit: int = 20, offset: int = 0):
    """查询分析历史记录列表"""
    from backend.core.database import list_history
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
    from backend.core.database import get_history
    record = await get_history(history_id)
    if not record:
        return {"error": "Record not found"}
    return record


@router.delete("/history/{history_id}")
async def delete_history_record(history_id: int):
    """删除历史分析记录"""
    from backend.core.database import delete_history
    deleted = await delete_history(history_id)
    if not deleted:
        return {"error": "Record not found"}
    return {"status": "ok", "deleted": history_id}


@router.get("/backtest")
async def run_backtest(symbol: str, days: int = 30):
    """回测：统计某股票历史分析中各 Agent 的预测分布"""
    from backend.core.database import backtest
    return await backtest(symbol, days)


@router.get("/export/{history_id}")
async def export_report(history_id: int, format: str = "md"):
    """导出分析报告为指定格式（md/html/txt）"""
    from backend.core.database import get_history
    from backend.output.report import generate_html_report, generate_text_report

    record = await get_history(history_id)
    if not record:
        return {"error": "Record not found"}

    report = record.get("report", {})
    symbol = record.get("symbol", "report")

    if format == "html":
        content = generate_html_report(report) if report else record.get("markdown", "")
        return Response(content=content, media_type="text/html",
                       headers={"Content-Disposition": f'attachment; filename="{symbol}_report.html"'})
    elif format == "txt":
        content = generate_text_report(report) if report else record.get("markdown", "")
        return Response(content=content, media_type="text/plain",
                       headers={"Content-Disposition": f'attachment; filename="{symbol}_report.txt"'})
    else:  # md
        content = record.get("markdown", "")
        return Response(content=content, media_type="text/markdown",
                       headers={"Content-Disposition": f'attachment; filename="{symbol}_report.md"'})
