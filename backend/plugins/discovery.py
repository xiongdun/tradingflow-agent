# backend/plugins/discovery.py
# 插件发现 — 扫描已安装插件目录，自动加载 manifest 并注册

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

from loguru import logger

from backend.plugins.manifest import PluginManifest, PluginType, PLUGINS_DIR
from backend.plugins.registry import plugin_registry

# 使用共享常量
_PLUGINS_DIR = PLUGINS_DIR


def discover_plugins() -> int:
    """扫描 plugins/ 目录下所有含 manifest.json 的子目录，自动注册。

    返回新发现的插件数量。
    """
    if not _PLUGINS_DIR.exists():
        return 0

    plugin_registry.load_from_disk()
    discovered = 0

    for child in sorted(_PLUGINS_DIR.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        manifest_path = child / "manifest.json"
        if not manifest_path.exists():
            continue
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = PluginManifest(**data)
        except Exception as e:
            logger.warning(f"[plugin-discover] 跳过无效插件 {child.name}: {e}")
            continue

        if plugin_registry.is_installed(manifest.name):
            existing = plugin_registry.get(manifest.name)
            if existing and existing.installed_path:
                continue

        manifest.installed_path = str(child)
        if not manifest.source:
            manifest.source = "local"
        plugin_registry.register(manifest)
        discovered += 1
        logger.info(f"[plugin-discover] 发现插件: {manifest.name} v{manifest.version} ({manifest.type})")

    _import_plugin_modules()
    if discovered > 0:
        logger.info(f"[plugin-discover] 新发现 {discovered} 个插件")
    return discovered


def _import_plugin_modules() -> None:
    """导入已注册插件的入口模块，触发装饰器注册"""
    for manifest in plugin_registry.list_plugins(enabled_only=True):
        if not manifest.entry_point:
            continue
        module_name = manifest.entry_point.split(":")[0]
        try:
            if manifest.installed_path:
                parent = str(Path(manifest.installed_path).parent)
                if parent not in sys.path:
                    sys.path.insert(0, parent)
            importlib.import_module(module_name)
        except ImportError as e:
            logger.warning(f"[plugin-discover] 导入插件 {manifest.name} 失败: {e}")
        except Exception as e:
            logger.warning(f"[plugin-discover] 插件 {manifest.name} 加载异常: {e}")


def discover_skill_plugins() -> list[PluginManifest]:
    """仅发现技能类型插件"""
    discover_plugins()
    return plugin_registry.list_plugins(plugin_type=PluginType.SKILL)


def discover_adapter_plugins() -> list[PluginManifest]:
    """仅发现适配器类型插件"""
    discover_plugins()
    return plugin_registry.list_plugins(plugin_type=PluginType.ADAPTER)


def register_plugin_skills() -> int:
    """将插件技能注册到现有的 SkillMeta 注册表"""
    from backend.skills.registry import _skills

    count = 0
    for manifest in plugin_registry.list_plugins(plugin_type=PluginType.SKILL):
        if not manifest.entry_point or manifest.name in _skills:
            continue
        module_name, _, func_name = manifest.entry_point.partition(":")
        if not func_name:
            func_name = "run"
        try:
            mod = importlib.import_module(module_name)
            fn = getattr(mod, func_name)
            from backend.skills.registry import SkillMeta
            meta = SkillMeta(
                name=manifest.name,
                description=manifest.description,
                markets=manifest.markets,
                category=manifest.category,
                fn=fn,
                params={k: {"type": v.type, "description": v.description}
                        for k, v in manifest.params.items()},
                depends_on=manifest.dependencies,
                label=manifest.description.split("—")[0][:20] if manifest.description else manifest.name,
            )
            _skills[manifest.name] = meta
            count += 1
            logger.info(f"[plugin-skill] 注册外部技能: {manifest.name}")
        except Exception as e:
            logger.warning(f"[plugin-skill] 注册技能 {manifest.name} 失败: {e}")
    return count


def register_plugin_adapters() -> int:
    """将插件适配器注册到适配器注册表"""
    from backend.plugins.adapters.base import adapter_registry

    count = 0
    for manifest in plugin_registry.list_plugins(plugin_type=PluginType.ADAPTER):
        if manifest.name in adapter_registry or not manifest.entry_point:
            continue
        module_name, _, class_name = manifest.entry_point.partition(":")
        if not class_name:
            class_name = "Adapter"
        try:
            mod = importlib.import_module(module_name)
            cls = getattr(mod, class_name)
            adapter_registry[manifest.name] = {"class": cls, "manifest": manifest}
            count += 1
            logger.info(f"[plugin-adapter] 注册外部适配器: {manifest.name}")
        except Exception as e:
            logger.warning(f"[plugin-adapter] 注册适配器 {manifest.name} 失败: {e}")
    return count
