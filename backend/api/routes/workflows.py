# backend/api/routes/workflows.py
# 工作流管理 API 路由

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.graph import TEMPLATES_DIR

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


class WorkflowSave(BaseModel):
    """工作流保存请求模型"""
    name: str
    definition: dict[str, Any]


@router.get("")
async def list_workflows():
    """列出所有可用的工作流模板"""
    workflows = []
    for f in TEMPLATES_DIR.glob("*.json"):
        defn = json.loads(f.read_text(encoding="utf-8"))
        mode = defn.get("mode", "parallel")

        agents_raw = defn.get("agents", [])
        if mode == "conditional":
            agent_roles = []
            for stage in defn.get("stages", []):
                agent_roles.extend(stage.get("agents", []))
        elif agents_raw and isinstance(agents_raw[0], str):
            agent_roles = agents_raw
        else:
            agent_roles = [a["role"] for a in agents_raw]

        workflows.append({
            "id": f.stem,
            "name": defn.get("name", f.stem),
            "description": defn.get("description", ""),
            "mode": mode,
            "agents": agent_roles,
            "version": defn.get("version"),
        })
    return workflows


@router.post("")
async def save_workflow(req: WorkflowSave):
    """保存工作流定义为 JSON 模板文件"""
    safe_name = Path(req.name.replace(" ", "_")).name
    file_path = TEMPLATES_DIR / f"{safe_name}.json"
    # 自动添加版本号（如果未提供）
    definition = dict(req.definition)
    if "version" not in definition:
        definition["version"] = 1
    file_path.write_text(
        json.dumps(definition, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"status": "ok", "id": safe_name, "path": str(file_path)}
