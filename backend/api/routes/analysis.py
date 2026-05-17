# backend/api/routes/analysis.py
# 股票分析 API 路由（REST + WebSocket）

from __future__ import annotations

import json
from datetime import datetime, date
from typing import Any

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.core.limiter import limiter

router = APIRouter(tags=["analysis"])


def _ws_json_encoder(obj: Any) -> Any:
    """WebSocket JSON 序列化器 — 处理 datetime、set、bytes 等不可序列化类型"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


async def _send_ws(ws: WebSocket, data: dict) -> None:
    """安全发送 WebSocket JSON 消息 — 自动处理不可序列化类型"""
    text = json.dumps(data, default=_ws_json_encoder, ensure_ascii=False)
    await ws.send_text(text)


class AnalyzeRequest(BaseModel):
    """股票分析请求模型"""
    symbol: str
    market: str = "a_share"
    workflow: str = "deep_analysis"
    agents: list[str] | None = None


@router.post("/api/analyze")
@limiter.limit("10/minute")
async def run_analysis(req: AnalyzeRequest, request: Request):
    """运行股票分析，返回完整分析报告（REST 同步模式）"""
    from backend.core.analysis_service import AnalysisService

    if req.agents:
        workflow_def: dict[str, Any] | None = {"name": "custom", "agents": [{"role": r} for r in req.agents]}
    else:
        workflow_def = AnalysisService.load_workflow(req.workflow)
        if not workflow_def:
            return JSONResponse(
                status_code=404,
                content={"error": f"Workflow template not found: {req.workflow}"},
            )

    assert workflow_def is not None  # verified above
    try:
        result = await AnalysisService.run_and_save(req.symbol, req.market, workflow_def)
        return {"status": "completed", "report": result["report"], "markdown": result["markdown"]}
    except Exception as e:
        from loguru import logger
        logger.error(f"Analysis failed for {req.symbol}: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)},
        )


# ──────────────────────────── WebSocket 实时分析 ────────────────────────────

class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws/analyze")
async def ws_analyze(ws: WebSocket):
    """WebSocket 实时分析端点

    消息协议：
    - 客户端发送: {symbol, market, workflow, agents}
    - 服务端推送:
      - {type: "status", status: "started"|"running"|"completed"}
      - {type: "opinion", data: {...}}
      - {type: "report", data: {...}, markdown: "..."}
      - {type: "error", message: "..."}
    """
    from backend.core.analysis_service import AnalysisService

    await manager.connect(ws)
    # 防止同一连接并发执行多次分析（导致重复保存历史记录）
    _analysis_running = False
    try:
        while True:
            data = await ws.receive_json()

            # 如果已有分析在运行，拒绝新请求
            if _analysis_running:
                await _send_ws(ws, {"type": "error", "message": "已有分析正在运行，请等待完成"})
                continue

            symbol = data.get("symbol", "")
            market = data.get("market", "a_share")
            workflow_name = data.get("workflow", "deep_analysis")
            agent_list = data.get("agents")
            agent_infos = data.get("agent_infos")

            if agent_list:
                info_map = {
                    ai["role"]: ai
                    for ai in (agent_infos or [])
                    if isinstance(ai, dict) and "role" in ai
                }
                agents_def = []
                for r in agent_list:
                    entry = {"role": r}
                    info = info_map.get(r, {})
                    for key in ("name", "skills", "extra_prompt", "system_prompt"):
                        if info.get(key):
                            entry[key] = info[key]
                    agents_def.append(entry)
                workflow_def: dict[str, Any] | None = {"name": "custom", "agents": agents_def}
            else:
                workflow_def = AnalysisService.load_workflow(workflow_name)
                if not workflow_def:
                    await _send_ws(ws, {"type": "error", "message": f"Template not found: {workflow_name}"})
                    continue

            assert workflow_def is not None  # guarded above
            _analysis_running = True
            await _send_ws(ws, {"type": "status", "status": "started", "workflow": workflow_def.get("name")})
            await _send_ws(ws, {
                "type": "status",
                "status": "running",
                "agents": AnalysisService.workflow_agents(workflow_def),
            })

            # 创建状态回调 — 将 agent 进度实时推送到 WebSocket
            async def status_callback(status: str, agent_role: str, agent_name: str, extra: dict):
                msg = {"type": "agent_status", "status": status, "agent_role": agent_role, "agent_name": agent_name}
                msg.update(extra)
                await _send_ws(ws, msg)

            try:
                result = await AnalysisService.run_and_save(symbol, market, workflow_def, status_callback=status_callback)

                for op in result["opinions"]:
                    await _send_ws(ws, {"type": "opinion", "data": op})

                await _send_ws(ws, {"type": "report", "data": result["report"], "markdown": result["markdown"]})
                await _send_ws(ws, {"type": "status", "status": "completed"})

            except Exception as e:
                from loguru import logger
                logger.error(f"WS analysis failed for {symbol}: {e}")
                await _send_ws(ws, {"type": "error", "message": str(e)})
            finally:
                _analysis_running = False

    except WebSocketDisconnect:
        manager.disconnect(ws)
