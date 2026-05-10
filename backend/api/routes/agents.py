# backend/api/routes/agents.py
# Agent 管理 API 路由

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentSkillsUpdate(BaseModel):
    """Agent 技能批量更新模型"""
    skills: list[str]


class AgentSkillAction(BaseModel):
    """Agent 技能单个操作模型"""
    skill: str


class AgentCreate(BaseModel):
    """新建自定义 Agent 模型"""
    name: str
    role: str
    extra_prompt: str = ""
    default_skills: list[str] = []


class AgentUpdate(BaseModel):
    """更新 Agent 信息模型"""
    name: str | None = None
    extra_prompt: str | None = None


@router.get("")
async def get_agents():
    """列出所有可用 Agent（内置 + 自定义）及其当前技能配置"""
    from backend.agents.registry import list_agents
    from backend.core.custom_store import get_all_custom_agents
    agents = list_agents()
    # 追加自定义 Agent
    for role, cfg in get_all_custom_agents().items():
        agents.append({
            "role": role,
            "name": cfg.get("name", role),
            "default_skills": cfg.get("default_skills", []),
            "current_skills": cfg.get("default_skills", []),
            "available_skills": [],
            "_custom": True,
        })
    return agents


@router.post("")
async def create_agent(req: AgentCreate):
    """创建自定义 Agent"""
    from backend.core.custom_store import save_custom_agent
    save_custom_agent(req.role, {
        "name": req.name,
        "role": req.role,
        "extra_prompt": req.extra_prompt,
        "default_skills": req.default_skills,
    })
    return {"status": "ok", "role": req.role}


@router.patch("/{role}")
async def update_agent(role: str, req: AgentUpdate):
    """更新 Agent 信息（名称、额外提示词）"""
    from backend.agents.registry import get_agent_class
    from backend.core.custom_store import get_custom_agent, save_custom_agent
    cls = get_agent_class(role)
    if cls:
        if req.extra_prompt is not None:
            save_custom_agent(f"_override_{role}", {
                "name": req.name or cls.name,
                "role": role,
                "extra_prompt": req.extra_prompt,
            })
        return {"status": "ok", "role": role}
    existing = get_custom_agent(role)
    if existing:
        if req.name is not None:
            existing["name"] = req.name
        if req.extra_prompt is not None:
            existing["extra_prompt"] = req.extra_prompt
        save_custom_agent(role, existing)
        return {"status": "ok", "role": role}
    return {"error": f"Agent not found: {role}"}


@router.delete("/{role}")
async def delete_agent(role: str):
    """删除自定义 Agent（内置 Agent 不可删除）"""
    from backend.agents.registry import get_agent_class
    from backend.core.custom_store import delete_custom_agent
    if get_agent_class(role):
        return {"error": "Cannot delete built-in agent"}
    if delete_custom_agent(role):
        return {"status": "ok", "role": role}
    return {"error": f"Agent not found: {role}"}


@router.get("/{role}/skills")
async def get_agent_skills(role: str):
    """获取指定 Agent 的当前技能列表"""
    from backend.agents.registry import get_agent_skills, get_agent_class
    if not get_agent_class(role):
        return {"error": f"Agent not found: {role}"}
    return {"role": role, "skills": get_agent_skills(role)}


@router.put("/{role}/skills")
async def set_agent_skills(role: str, req: AgentSkillsUpdate):
    """批量替换 Agent 的技能列表"""
    from backend.agents.registry import set_agent_skills
    if not set_agent_skills(role, req.skills):
        return {"error": f"Agent not found: {role}"}
    return {"status": "ok", "role": role, "skills": req.skills}


@router.post("/{role}/skills/add")
async def add_agent_skill(role: str, req: AgentSkillAction):
    """为 Agent 添加单个技能"""
    from backend.agents.registry import add_agent_skill, get_agent_skills
    if not add_agent_skill(role, req.skill):
        return {"error": f"Agent not found: {role}"}
    return {"status": "ok", "role": role, "skills": get_agent_skills(role)}


@router.post("/{role}/skills/remove")
async def remove_agent_skill(role: str, req: AgentSkillAction):
    """移除 Agent 的单个技能"""
    from backend.agents.registry import remove_agent_skill, get_agent_skills
    if not remove_agent_skill(role, req.skill):
        return {"error": f"Agent not found or skill not present: {role}/{req.skill}"}
    return {"status": "ok", "role": role, "skills": get_agent_skills(role)}


@router.post("/{role}/skills/reset")
async def reset_agent_skills(role: str):
    """将 Agent 的技能重置为默认配置"""
    from backend.agents.registry import reset_agent_skills, get_agent_skills
    if not reset_agent_skills(role):
        return {"error": f"Agent not found: {role}"}
    return {"status": "ok", "role": role, "skills": get_agent_skills(role)}
