# backend/core/discovery.py
# 自动发现模块 — 扫描 skills/、data/、agents/ 目录，触发装饰器注册
# 消除 CLI 和 API 各自重复维护显式导入的问题

from __future__ import annotations

import importlib
import pkgutil


def auto_discover() -> None:
    """自动发现并导入所有插件模块，触发 @skill/@provider/@agent 装饰器注册。

    调用时机：
    - CLI 入口（cli.py）：每个命令执行前
    - API 入口（main.py）：应用启动时
    - 测试 fixtures：需要注册表 populated 时

    幂等：重复调用无副作用（Python import 缓存）。
    """
    # Auto-import all skill modules → 触发 @skill 装饰器
    import backend.skills as skills_pkg
    for _, name, _ in pkgutil.iter_modules(skills_pkg.__path__):
        if name != "registry":
            importlib.import_module(f"backend.skills.{name}")

    # Auto-import all data provider modules → 触发 @provider 装饰器
    import backend.data as data_pkg
    for _, name, _ in pkgutil.iter_modules(data_pkg.__path__):
        if name not in ("provider", "factory", "fallback_provider", "__init__"):
            importlib.import_module(f"backend.data.{name}")

    # Auto-import all agent modules → 触发 @agent 装饰器
    import backend.agents as agents_pkg
    for _, name, _ in pkgutil.iter_modules(agents_pkg.__path__):
        if name not in ("registry", "base", "generic", "__init__", "models"):
            importlib.import_module(f"backend.agents.{name}")

    # Discover and register external plugins (skills + adapters from plugins/ directory)
    try:
        from backend.plugins.discovery import discover_plugins, register_plugin_skills, register_plugin_adapters
        discover_plugins()
        register_plugin_skills()
        register_plugin_adapters()
    except Exception:
        pass  # 插件系统不可用时静默跳过
