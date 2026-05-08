# backend/core/analysis_service.py
# 分析执行服务 — 统一 REST/WS/CLI/调度器的分析逻辑，消除重复

from __future__ import annotations

import json
from typing import Any, Callable, Awaitable

from loguru import logger

from backend.graph import TEMPLATES_DIR
from backend.output.report import generate_markdown_report

# 状态回调类型：(status, agent_role, agent_name, extra) -> None
StatusCallback = Callable[[str, str, str, dict[str, Any]], Awaitable[None]] | None


class AnalysisService:
    """统一分析执行服务"""

    @staticmethod
    async def run(symbol: str, market: str, workflow_def: dict[str, Any],
                  status_callback: StatusCallback = None) -> dict[str, Any]:
        """提取工作流中参与的 Agent 角色，兼容多种模板格式。"""
        mode = workflow_def.get("mode", "parallel")
        if mode == "conditional":
            roles: list[str] = []
            for stage in workflow_def.get("stages", []):
                for role in stage.get("agents", []):
                    if role not in roles:
                        roles.append(role)
            return roles

        agents_raw = workflow_def.get("agents", [])
        if agents_raw and isinstance(agents_raw[0], str):
            return list(agents_raw)
        return [
            agent.get("role", "")
            for agent in agents_raw
            if isinstance(agent, dict) and agent.get("role")
        ]

    @staticmethod
    async def run(symbol: str, market: str, workflow_def: dict[str, Any]) -> dict[str, Any]:
        """执行分析并返回结果（不持久化）

        Args:
            status_callback: 可选的异步回调，用于报告 agent 执行进度
                签名: async def callback(status, agent_role, agent_name, extra)
                status: "running" | "skill_done" | "done" | "error"
        """
        from backend.graph.builder import build_from_json
        from backend.core.exceptions import AnalysisError

        try:
            graph = build_from_json(workflow_def)
        except Exception as e:
            raise AnalysisError(symbol, f"工作流构建失败: {e}") from e

        try:
            result = await graph.ainvoke({
                "symbol": symbol,
                "market": market,
                "opinions": [],
                "final_report": None,
                "workflow_name": workflow_def.get("name", ""),
                "status": "running",
                "error": None,
                "round": 0,
                "selected_agents": [],
                "status_callback": status_callback,
            })
        except Exception as e:
            raise AnalysisError(symbol, str(e)) from e

        final_report = result.get("final_report", {})
        opinions = result.get("opinions", [])
        md = generate_markdown_report(final_report) if final_report else ""
        return {"report": final_report, "opinions": opinions, "markdown": md}

    @staticmethod
    async def run_and_save(symbol: str, market: str, workflow_def: dict[str, Any],
                           status_callback: StatusCallback = None) -> dict[str, Any]:
        """执行分析 + 持久化到数据库"""
        result = await AnalysisService.run(symbol, market, workflow_def, status_callback=status_callback)
        try:
            from backend.repositories.history import save_analysis
            await save_analysis(
                symbol=symbol,
                market=market,
                workflow=workflow_def.get("name", ""),
                agents=AnalysisService.workflow_agents(workflow_def),
                opinions=result["opinions"],
                report=result["report"],
                markdown=result["markdown"],
            )
        except Exception as e:
            logger.warning(f"Failed to save analysis: {e}")
        return result

    @staticmethod
    def load_workflow(workflow_name: str) -> dict[str, Any] | None:
        """从模板目录加载工作流定义"""
        template_path = TEMPLATES_DIR / f"{workflow_name}.json"
        if not template_path.exists():
            return None
        return json.loads(template_path.read_text(encoding="utf-8"))
