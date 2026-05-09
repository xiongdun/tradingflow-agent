# backend/api/routes/adapters.py
# 适配器管理 API — 列出/注册/测试外部项目适配器

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/adapters", tags=["adapters"])


class AdapterRegisterRequest(BaseModel):
    name: str
    adapter_type: str
    description: str = ""
    config: dict = {}
    input_fields: list[str] = []
    output_fields: list[str] = []


@router.get("")
async def list_adapter_types():
    """列出所有可用的适配器类型（内置 + 插件）"""
    from backend.plugins.adapters.base import list_adapter_types
    return list_adapter_types()


@router.post("")
async def register_adapter(req: AdapterRegisterRequest):
    """注册新的外部项目为工作流节点"""
    from backend.plugins.adapters.base import create_adapter, adapter_registry
    from backend.plugins.manifest import PluginManifest, PluginType
    from backend.plugins.registry import plugin_registry

    try:
        adapter = create_adapter(req.adapter_type, req.config)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    adapter_registry[req.name] = {"class": type(adapter), "config": req.config}
    manifest = PluginManifest(
        name=req.name, type=PluginType.ADAPTER,
        description=req.description or f"{req.adapter_type} 适配器",
        adapter_type=req.adapter_type, adapter_config=req.config,
        input_schema={f: {"type": "string"} for f in req.input_fields},
        output_schema={f: {"type": "string"} for f in req.output_fields},
    )
    plugin_registry.register(manifest)
    return {"status": "ok", "adapter": req.name, "type": req.adapter_type}


@router.get("/{name}/schema")
async def get_adapter_schema(name: str):
    """获取适配器的输入输出 schema"""
    from backend.plugins.adapters.base import adapter_registry
    entry = adapter_registry.get(name)
    if not entry:
        raise HTTPException(status_code=404, detail=f"适配器不存在: {name}")
    cls = entry.get("class")
    if cls:
        instance = cls(config=entry.get("config"))
        return {"input": instance.input_schema(), "output": instance.output_schema(), "config": instance.get_config_schema()}
    raise HTTPException(status_code=500, detail="无法获取 schema")


@router.post("/{name}/test")
async def test_adapter(name: str):
    """测试适配器连接（使用示例股票代码）"""
    from backend.plugins.adapters.base import adapter_registry
    entry = adapter_registry.get(name)
    if not entry:
        raise HTTPException(status_code=404, detail=f"适配器不存在: {name}")
    cls = entry.get("class")
    if not cls:
        raise HTTPException(status_code=500, detail="无法测试适配器：缺少类定义")
    try:
        instance = cls(config=entry.get("config", {}))
        result = await instance.invoke({"symbol": "600519", "market": "a_share"})
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"适配器测试失败: {e}")
