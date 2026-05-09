# backend/plugins/marketplace.py
# 远程技能注册中心 — 浏览、搜索和安装社区贡献的插件

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from backend.plugins.manifest import PluginManifest
from backend.plugins.registry import plugin_registry


class PluginListing:
    """远程注册中心中的插件条目"""
    def __init__(self, data: dict[str, Any]):
        self.name: str = data.get("name", "")
        self.version: str = data.get("version", "")
        self.description: str = data.get("description", "")
        self.author: str = data.get("author", "")
        self.category: str = data.get("category", "")
        self.downloads: int = data.get("downloads", 0)
        self.rating: float = data.get("rating", 0.0)
        self.type: str = data.get("type", "skill")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name, "version": self.version, "description": self.description,
            "author": self.author, "category": self.category, "downloads": self.downloads,
            "rating": self.rating, "type": self.type,
        }


class SkillMarketplace:
    """远程技能注册中心客户端

    默认注册中心: https://plugins.tradingflow.dev
    可通过 Settings.marketplace_url 配置。
    """

    def __init__(self, base_url: str = "") -> None:
        self._base_url = base_url or "https://plugins.tradingflow.dev"
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(timeout=30, follow_redirects=True)
        return self._client

    def _api(self, path: str) -> str:
        return f"{self._base_url.rstrip('/')}{path}"

    async def search(self, query: str = "", category: str = "",
                     plugin_type: str = "", page: int = 1, limit: int = 20) -> dict[str, Any]:
        """搜索远程注册中心的插件"""
        params: dict[str, Any] = {"page": page, "limit": limit}
        if query:
            params["q"] = query
        if category:
            params["category"] = category
        if plugin_type:
            params["type"] = plugin_type
        try:
            client = self._get_client()
            resp = client.get(self._api("/api/plugins/search"), params=params)
            resp.raise_for_status()
            data = resp.json()
            listings = [PluginListing(item) for item in data.get("plugins", [])]
            return {"plugins": [l.to_dict() for l in listings], "total": data.get("total", 0), "page": page, "limit": limit}
        except httpx.HTTPError as e:
            logger.warning(f"[marketplace] 搜索失败: {e}")
            return {"plugins": [], "total": 0, "page": page, "limit": limit, "error": str(e)}

    async def get_plugin_info(self, name: str) -> dict[str, Any] | None:
        """获取插件详细信息"""
        try:
            client = self._get_client()
            resp = client.get(self._api(f"/api/plugins/{name}"))
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.warning(f"[marketplace] 获取插件信息失败: {e}")
            return None

    async def get_versions(self, name: str) -> list[str]:
        """获取插件所有可用版本"""
        try:
            client = self._get_client()
            resp = client.get(self._api(f"/api/plugins/{name}/versions"))
            resp.raise_for_status()
            return resp.json().get("versions", [])
        except httpx.HTTPError:
            return []

    async def install(self, name: str, version: str = "latest") -> PluginManifest | None:
        """从远程注册中心安装插件"""
        from backend.plugins.loader import plugin_loader
        try:
            manifest = plugin_loader.load_from_registry(name, version, self._base_url)
            return manifest
        except Exception as e:
            logger.error(f"[marketplace] 安装插件 {name} 失败: {e}")
            return None

    async def get_categories(self) -> list[dict[str, Any]]:
        """获取所有可用的插件类别"""
        try:
            client = self._get_client()
            resp = client.get(self._api("/api/categories"))
            resp.raise_for_status()
            return resp.json().get("categories", [])
        except httpx.HTTPError:
            return []

    def is_installed(self, name: str) -> bool:
        """检查插件是否已本地安装"""
        return plugin_registry.is_installed(name)

    def close(self) -> None:
        if self._client and not self._client.is_closed:
            self._client.close()


# 全局单例
marketplace = SkillMarketplace()
