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


@router.get("")
async def get_agents():
    """列出所有可用 Agent 及其当前技能配置"""
    from backend.agents.registry import list_agents
    return list_agents()


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
