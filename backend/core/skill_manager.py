# backend/core/skill_manager.py
# SKILL.md 安装管理器 — 解析、安装、卸载从网上下载的 SKILL.md 技能文件

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from loguru import logger

# 技能文件存储目录
SKILLS_DIR = Path(__file__).resolve().parent.parent / "data" / "skills"


def _ensure_dir():
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)


def parse_skill_md(content: str) -> dict[str, Any]:
    """解析 SKILL.md 的 YAML frontmatter + markdown 正文

    格式：
        ---
        name: my_skill
        description: 技能描述
        label: 中文名
        category: fundamental
        markets: a_share, h_stock
        ---
        # 技能标题
        （markdown 正文）
    """
    result: dict[str, Any] = {
        "name": "",
        "description": "",
        "label": "",
        "category": "general",
        "markets": ["a_share", "h_stock", "us_stock"],
        "content": "",
    }

    # 提取 YAML frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        result["content"] = fm_match.group(2).strip()
        # 简易 YAML 解析（避免引入 pyyaml 依赖）
        for line in fm_text.split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip()
            if key == "name":
                result["name"] = val
            elif key == "description":
                result["description"] = val
            elif key == "label":
                result["label"] = val
            elif key == "category":
                result["category"] = val
            elif key == "markets":
                result["markets"] = [m.strip() for m in val.split(",") if m.strip()]
    else:
        # 无 frontmatter，尝试从第一行提取 name
        result["content"] = content.strip()
        first_line = content.strip().split("\n")[0].lstrip("# ").strip()
        if first_line:
            result["name"] = re.sub(r"[^a-zA-Z0-9_]", "_", first_line.lower())[:40]
            result["label"] = first_line
            result["description"] = first_line

    return result


def install_skill_from_url(url: str) -> dict[str, Any]:
    """从 URL 下载 SKILL.md 并安装"""
    import httpx

    _ensure_dir()
    try:
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        raise ValueError(f"下载失败: {e}")

    content = resp.text
    return install_skill_from_content(content, filename=url.split("/")[-1] or "SKILL.md")


def install_skill_from_content(content: str, filename: str = "SKILL.md") -> dict[str, Any]:
    """从文件内容安装 SKILL.md 技能"""
    from backend.core.custom_store import save_custom_skill

    _ensure_dir()
    meta = parse_skill_md(content)
    if not meta["name"]:
        raise ValueError("无法从 SKILL.md 中提取技能名称（需要 YAML frontmatter 中的 name 字段）")

    name = meta["name"]

    # 检查是否与内置技能冲突
    from backend.skills.registry import _skills
    if name in _skills:
        raise ValueError(f"技能名称 '{name}' 与内置技能冲突")

    # 保存 SKILL.md 文件
    skill_dir = SKILLS_DIR / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")

    # 注册到 custom_skills.json
    save_custom_skill(name, {
        "name": name,
        "description": meta["description"],
        "label": meta["label"] or name,
        "category": meta["category"],
        "markets": meta["markets"],
        "params": {},
        "depends_on": [],
        "_source": "skill_md",
        "_file_path": str(skill_dir / "SKILL.md"),
    })

    logger.info(f"[skill] Installed SKILL.md: {name}")
    return {
        "name": name,
        "description": meta["description"],
        "label": meta["label"],
        "category": meta["category"],
        "markets": meta["markets"],
    }


def uninstall_skill(name: str) -> bool:
    """卸载已安装的 SKILL.md 技能"""
    from backend.core.custom_store import get_custom_skill, delete_custom_skill

    skill = get_custom_skill(name)
    if not skill:
        return False

    # 只允许卸载通过 SKILL.md 安装的技能
    if skill.get("_source") != "skill_md":
        return False

    # 删除文件
    file_path = skill.get("_file_path")
    if file_path:
        p = Path(file_path)
        if p.exists():
            p.unlink()
        # 删除空目录
        if p.parent.exists() and not any(p.parent.iterdir()):
            p.parent.rmdir()

    # 从 custom_skills.json 移除
    delete_custom_skill(name)
    logger.info(f"[skill] Uninstalled SKILL.md: {name}")
    return True


def list_installed_skill_files() -> list[dict[str, Any]]:
    """列出所有通过 SKILL.md 安装的技能"""
    from backend.core.custom_store import get_all_custom_skills

    result = []
    for name, cfg in get_all_custom_skills().items():
        if cfg.get("_source") == "skill_md":
            result.append({
                "name": name,
                "description": cfg.get("description", ""),
                "label": cfg.get("label", name),
                "category": cfg.get("category", "general"),
                "markets": cfg.get("markets", []),
                "_file_path": cfg.get("_file_path", ""),
            })
    return result
