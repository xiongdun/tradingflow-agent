# backend/agents/registry.py
# Agent 注册中心 — 管理 Agent 注册表和运行时技能覆盖

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.agents.base import BaseAgent

# Agent 注册表
_agents_registry: dict[str, type] = {}

# 运行时技能覆盖
_skill_overrides: dict[str, list[str]] = {}


def agent(name: str, role: str, default_skills: list[str] | None = None, system_prompt: str = ""):
    """装饰器：将 BaseAgent 子类注册到全局注册表"""
    def decorator(cls: type) -> type:
        cls.name = name
        cls.role = role
        cls.default_skills = default_skills or []
        cls.system_prompt = system_prompt
        _agents_registry[role] = cls
        return cls
    return decorator


def get_agent_class(role: str) -> type | None:
    return _agents_registry.get(role)


def list_all_agents() -> list[dict]:
    from backend.skills.registry import list_skills
    all_skills = [s["name"] for s in list_skills()]
    return [
        {
            "role": cls.role,
            "name": cls.name,
            "default_skills": cls.default_skills,
            "current_skills": _skill_overrides.get(cls.role, list(cls.default_skills)),
            "available_skills": all_skills,
        }
        for cls in _agents_registry.values()
    ]


# backward-compatible alias
list_agents = list_all_agents


def get_agent_skills(role: str) -> list[str]:
    cls = _agents_registry.get(role)
    if not cls:
        return []
    return _skill_overrides.get(role, list(cls.default_skills))


def set_agent_skills(role: str, skills: list[str]) -> bool:
    if role not in _agents_registry:
        return False
    _skill_overrides[role] = skills
    return True


def add_agent_skill(role: str, skill_name: str) -> bool:
    if role not in _agents_registry:
        return False
    current = get_agent_skills(role)
    if skill_name not in current:
        current.append(skill_name)
        _skill_overrides[role] = current
    return True


def remove_agent_skill(role: str, skill_name: str) -> bool:
    if role not in _agents_registry:
        return False
    current = get_agent_skills(role)
    if skill_name in current:
        current.remove(skill_name)
        _skill_overrides[role] = current
    return True


def reset_agent_skills(role: str) -> bool:
    if role not in _agents_registry:
        return False
    _skill_overrides.pop(role, None)
    return True
