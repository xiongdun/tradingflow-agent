# backend/plugins/registry.py
# 插件注册中心 — 管理已安装插件的注册、启用/禁用、持久化

from __future__ import annotations

import json

from loguru import logger

from backend.plugins.manifest import PluginManifest, PluginType, PLUGINS_DIR

# 使用共享常量
_PLUGINS_DIR = PLUGINS_DIR
_INSTALLED_FILE = _PLUGINS_DIR / "installed.json"


class PluginRegistry:
    """全局插件注册中心 — 管理所有已安装插件的元数据"""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginManifest] = {}  # name -> manifest
        self._loaded = False

    def _ensure_dir(self) -> None:
        """确保插件存储目录存在"""
        _PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

    def load_from_disk(self) -> None:
        """从磁盘加载已安装插件列表"""
        if self._loaded:
            return
        self._ensure_dir()
        if _INSTALLED_FILE.exists():
            try:
                data = json.loads(_INSTALLED_FILE.read_text(encoding="utf-8"))
                for item in data.get("plugins", []):
                    manifest = PluginManifest(**item)
                    self._plugins[manifest.name] = manifest
                logger.info(f"[plugin] Loaded {len(self._plugins)} installed plugins")
            except Exception as e:
                logger.warning(f"[plugin] Failed to load installed plugins: {e}")
        self._loaded = True

    def save_to_disk(self) -> None:
        """将已安装插件列表持久化到磁盘"""
        self._ensure_dir()
        data = {"plugins": [p.model_dump() for p in self._plugins.values()]}
        _INSTALLED_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def register(self, manifest: PluginManifest) -> bool:
        """注册一个插件，返回是否成功（重名返回 False）"""
        self.load_from_disk()
        if manifest.name in self._plugins:
            existing = self._plugins[manifest.name]
            if existing.version == manifest.version:
                return False  # 同版本重复注册
            logger.info(f"[plugin] Upgrading {manifest.name}: {existing.version} -> {manifest.version}")
        self._plugins[manifest.name] = manifest
        self.save_to_disk()
        logger.info(f"[plugin] Registered: {manifest.name} v{manifest.version} ({manifest.type})")
        return True

    def unregister(self, name: str) -> bool:
        """卸载插件"""
        self.load_from_disk()
        if name not in self._plugins:
            return False
        manifest = self._plugins.pop(name)
        self.save_to_disk()
        logger.info(f"[plugin] Unregistered: {name} v{manifest.version}")
        return True

    def get(self, name: str) -> PluginManifest | None:
        """获取已注册的插件"""
        self.load_from_disk()
        return self._plugins.get(name)

    def list_plugins(
        self,
        plugin_type: PluginType | None = None,
        enabled_only: bool = True,
        category: str | None = None,
    ) -> list[PluginManifest]:
        """列出已注册的插件，支持按类型和类别过滤"""
        self.load_from_disk()
        results = []
        for manifest in self._plugins.values():
            if enabled_only and not manifest.enabled:
                continue
            if plugin_type and manifest.type != plugin_type:
                continue
            if category and manifest.category != category:
                continue
            results.append(manifest)
        return results

    def enable(self, name: str) -> bool:
        """启用插件"""
        self.load_from_disk()
        manifest = self._plugins.get(name)
        if not manifest:
            return False
        manifest.enabled = True
        self.save_to_disk()
        return True

    def disable(self, name: str) -> bool:
        """禁用插件"""
        self.load_from_disk()
        manifest = self._plugins.get(name)
        if not manifest:
            return False
        manifest.enabled = False
        self.save_to_disk()
        return True

    def is_installed(self, name: str) -> bool:
        """检查插件是否已安装"""
        self.load_from_disk()
        return name in self._plugins

    def get_by_type(self, plugin_type: PluginType) -> dict[str, PluginManifest]:
        """获取指定类型的所有插件"""
        self.load_from_disk()
        return {n: m for n, m in self._plugins.items() if m.type == plugin_type}


# 全局单例
plugin_registry = PluginRegistry()
