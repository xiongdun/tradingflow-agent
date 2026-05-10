# backend/core/custom_store.py
# 自定义 Agent / Skill 持久化存储 — JSON 文件存储用户创建的自定义配置

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# 存储目录（backend/data/）
_STORE_DIR = Path(__file__).resolve().parent.parent / "data"
_AGENTS_FILE = _STORE_DIR / "custom_agents.json"
_SKILLS_FILE = _STORE_DIR / "custom_skills.json"


def _ensure_dir():
    _STORE_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> dict:
    _ensure_dir()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_json(path: Path, data: dict):
    _ensure_dir()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ─── Custom Agents ───

def get_all_custom_agents() -> dict[str, dict[str, Any]]:
    return _load_json(_AGENTS_FILE)


def get_custom_agent(role: str) -> dict[str, Any] | None:
    return get_all_custom_agents().get(role)


def save_custom_agent(role: str, data: dict[str, Any]):
    agents = get_all_custom_agents()
    agents[role] = data
    _save_json(_AGENTS_FILE, agents)


def delete_custom_agent(role: str) -> bool:
    agents = get_all_custom_agents()
    if role in agents:
        del agents[role]
        _save_json(_AGENTS_FILE, agents)
        return True
    return False


# ─── Custom Skills ───

def get_all_custom_skills() -> dict[str, dict[str, Any]]:
    return _load_json(_SKILLS_FILE)


def get_custom_skill(name: str) -> dict[str, Any] | None:
    return get_all_custom_skills().get(name)


def save_custom_skill(name: str, data: dict[str, Any]):
    skills = get_all_custom_skills()
    skills[name] = data
    _save_json(_SKILLS_FILE, skills)


def update_custom_skill(name: str, updates: dict[str, Any]) -> bool:
    skills = get_all_custom_skills()
    if name not in skills:
        return False
    skills[name].update(updates)
    _save_json(_SKILLS_FILE, skills)
    return True


def delete_custom_skill(name: str) -> bool:
    skills = get_all_custom_skills()
    if name in skills:
        del skills[name]
        _save_json(_SKILLS_FILE, skills)
        return True
    return False
