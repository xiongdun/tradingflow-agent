# backend/core/config_writer.py
# 配置写入模块 — .env 文件读写（与 Settings 读取分离）

from __future__ import annotations

from backend.core.config import ENV_FILE, PROJECT_ROOT


def update_setting(key: str, value: str) -> None:
    """更新 .env 文件中的单个配置项"""
    if not ENV_FILE.exists():
        example = PROJECT_ROOT / ".env.example"
        if example.exists():
            ENV_FILE.write_text(example.read_text())
        else:
            ENV_FILE.touch()

    lines = ENV_FILE.read_text().splitlines()
    found = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n")


def update_settings(updates: dict[str, str]) -> None:
    """批量更新 .env 文件中的多个配置项（单次读写）"""
    if not updates:
        return
    if not ENV_FILE.exists():
        example = PROJECT_ROOT / ".env.example"
        if example.exists():
            ENV_FILE.write_text(example.read_text())
        else:
            ENV_FILE.touch()

    lines = ENV_FILE.read_text().splitlines()
    new_lines = []
    remaining = dict(updates)
    for line in lines:
        key = line.split("=", 1)[0] if "=" in line else ""
        if key in remaining:
            new_lines.append(f"{key}={remaining.pop(key)}")
        else:
            new_lines.append(line)
    for key, value in remaining.items():
        new_lines.append(f"{key}={value}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n")
