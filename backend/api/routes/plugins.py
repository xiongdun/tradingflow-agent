# backend/api/routes/plugins.py
# 插件管理 API — 安装/卸载/启用/禁用/浏览插件

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend.plugins.registry import plugin_registry
from backend.plugins.loader import plugin_loader
from backend.plugins.manifest import PluginType

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


class PluginInstallRequest(BaseModel):
    source: str          # "local" | "git" | "pip" | "url" | "registry"
    url: str = ""
    path: str = ""
    package: str = ""
    version: str = "latest"
    ref: str = "main"
    registry_url: str = ""


@router.get("")
async def list_plugins(plugin_type: str = "", category: str = "", include_disabled: bool = False):
    """列出已安装的插件"""
    pt = PluginType(plugin_type) if plugin_type else None
    plugins = plugin_registry.list_plugins(plugin_type=pt, enabled_only=not include_disabled, category=category or None)
    return [p.model_dump() for p in plugins]


@router.post("/install")
async def install_plugin(req: PluginInstallRequest):
    """安装插件（5 种来源）"""
    try:
        if req.source == "local":
            manifest = plugin_loader.load_from_local(req.path)
        elif req.source == "git":
            manifest = plugin_loader.load_from_git(req.url, req.ref)
        elif req.source == "pip":
            manifest = plugin_loader.load_from_pip(req.package, req.version)
        elif req.source == "registry":
            manifest = plugin_loader.load_from_registry(req.package, req.version, req.registry_url)
        elif req.source == "url":
            manifest = plugin_loader.load_from_url(req.url)
        else:
            return {"error": f"未知来源: {req.source}"}
        return {"status": "ok", "plugin": manifest.model_dump()}
    except Exception as e:
        return {"error": str(e)}


@router.delete("/{name}")
async def uninstall_plugin(name: str):
    """卸载插件"""
    if plugin_loader.uninstall(name):
        return {"status": "ok"}
    return {"error": f"插件不存在: {name}"}


@router.post("/{name}/enable")
async def enable_plugin(name: str):
    if plugin_registry.enable(name):
        return {"status": "ok"}
    return {"error": f"插件不存在: {name}"}


@router.post("/{name}/disable")
async def disable_plugin(name: str):
    if plugin_registry.disable(name):
        return {"status": "ok"}
    return {"error": f"插件不存在: {name}"}


@router.get("/marketplace")
async def search_marketplace(q: str = "", category: str = "", type: str = "", page: int = 1, limit: int = 20):
    """浏览远程插件市场"""
    from backend.plugins.marketplace import marketplace
    return await marketplace.search(query=q, category=category, plugin_type=type, page=page, limit=limit)
