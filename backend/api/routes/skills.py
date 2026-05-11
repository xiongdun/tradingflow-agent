# backend/api/routes/skills.py
# 技能管理 API 路由

from __future__ import annotations

from fastapi import APIRouter, Request, UploadFile
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["skills"])


class SkillCreate(BaseModel):
    name: str
    description: str
    label: str = ""
    category: str = "general"
    markets: list[str] = []
    params: dict[str, str] = {}
    depends_on: list[str] = []


class SkillUpdate(BaseModel):
    description: str | None = None
    label: str | None = None
    category: str | None = None
    markets: list[str] | None = None


class SkillInstallRequest(BaseModel):
    url: str


@router.get("/skills")
async def get_skills(request: Request, market: str = "", category: str = ""):
    from backend.skills.registry import list_skills
    from backend.core.custom_store import get_all_custom_skills
    result = list_skills(market=market or None, category=category or None)
    for name, cfg in get_all_custom_skills().items():
        result.append({
            "name": name,
            "description": cfg.get("description", ""),
            "markets": cfg.get("markets", []),
            "category": cfg.get("category", "general"),
            "label": cfg.get("label", name),
            "params": cfg.get("params", {}),
            "depends_on": cfg.get("depends_on", []),
            "_custom": True,
        })
    return result


@router.post("/skills")
async def create_skill(request: Request, req: SkillCreate):
    from backend.core.custom_store import save_custom_skill
    save_custom_skill(req.name, {
        "name": req.name,
        "description": req.description,
        "label": req.label,
        "category": req.category,
        "markets": req.markets,
        "params": req.params,
        "depends_on": req.depends_on,
    })
    return {"status": "ok", "name": req.name}


@router.patch("/skills/{name}")
async def update_skill(request: Request, name: str, req: SkillUpdate):
    from backend.core.custom_store import update_custom_skill
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        return {"error": "No fields to update"}
    if update_custom_skill(name, updates):
        return {"status": "ok", "name": name}
    return {"error": f"Skill not found: {name}"}


@router.delete("/skills/{name}")
async def delete_skill(request: Request, name: str):
    from backend.core.custom_store import delete_custom_skill
    if delete_custom_skill(name):
        return {"status": "ok", "name": name}
    return {"error": f"Skill not found: {name}"}


@router.post("/skills/install")
async def install_skill_from_url(request: Request, req: SkillInstallRequest):
    from backend.core.skill_manager import install_skill_from_url as _install
    try:
        result = _install(req.url)
        return {"status": "ok", "skill": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/skills/install/upload")
async def install_skill_upload(request: Request, file: UploadFile):
    from backend.core.skill_manager import install_skill_from_content as _install
    try:
        content = (await file.read()).decode("utf-8")
        result = _install(content, filename=file.filename or "SKILL.md")
        return {"status": "ok", "skill": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/skills/{name}/uninstall")
async def uninstall_skill_endpoint(request: Request, name: str):
    from backend.core.skill_manager import uninstall_skill
    if uninstall_skill(name):
        return {"status": "ok", "name": name}
    return {"error": f"无法卸载技能: {name}（可能不是通过 SKILL.md 安装的）"}


@router.get("/skills/installed")
async def list_installed_skills(request: Request):
    from backend.core.skill_manager import list_installed_skill_files
    return list_installed_skill_files()