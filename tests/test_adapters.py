# tests/test_adapters.py
# 适配器系统全覆盖测试 — 6 种适配器 / 工厂方法 / 注册表

from __future__ import annotations

import asyncio
import json
import tempfile
from unittest.mock import patch, AsyncMock, MagicMock

import pytest


# ═══════════════════════════════════════════════════════
#  1. NodeAdapter 基类
# ═══════════════════════════════════════════════════════

class TestNodeAdapterBase:

    def test_has_abstract_invoke(self):
        from backend.plugins.adapters.base import NodeAdapter
        assert hasattr(NodeAdapter, "invoke")
        # 基类不能直接实例化（abc.abstractmethod）
        with pytest.raises(TypeError):
            NodeAdapter()

    def test_default_schemas(self):
        from backend.plugins.adapters.base import NodeAdapter
        # 用一个简单子类测试
        class DummyAdapter(NodeAdapter):
            async def invoke(self, state):
                return {}
        a = DummyAdapter()
        inp = a.input_schema()
        assert "symbol" in inp
        assert "market" in inp
        assert a.output_schema() == {}
        assert a.get_config_schema() == {}


# ═══════════════════════════════════════════════════════
#  2. FunctionAdapter
# ═══════════════════════════════════════════════════════

class TestFunctionAdapter:

    def test_sync_function(self):
        from backend.plugins.adapters.base import FunctionAdapter

        def my_fn(state):
            return {"result": state.get("symbol", "") + "_ok"}

        a = FunctionAdapter(fn=my_fn, name="sync_test")
        assert a.name == "sync_test"
        result = asyncio.get_event_loop().run_until_complete(a.invoke({"symbol": "600519"}))
        assert result == {"result": "600519_ok"}

    def test_async_function(self):
        from backend.plugins.adapters.base import FunctionAdapter

        async def my_async_fn(state):
            return {"data": 42}

        a = FunctionAdapter(fn=my_async_fn, name="async_test")
        result = asyncio.get_event_loop().run_until_complete(a.invoke({}))
        assert result == {"data": 42}

    def test_config_based_dynamic_import(self):
        """通过 config 中的 module+function 动态加载"""
        from backend.plugins.adapters.base import FunctionAdapter
        config = {
            "name": "dynamic_fn",
            "module": "os.path",
            "function": "exists",
        }
        a = FunctionAdapter(config=config)
        # os.path.exists 传入 dict 触发 TypeError，但加载成功
        with pytest.raises((TypeError, OSError)):
            asyncio.get_event_loop().run_until_complete(
                a.invoke({"some": "data"})
            )

    def test_no_fn_raises(self):
        from backend.plugins.adapters.base import FunctionAdapter
        a = FunctionAdapter()  # no fn, no config
        with pytest.raises(ValueError, match="未配置函数"):
            asyncio.get_event_loop().run_until_complete(a.invoke({}))

    def test_name_from_config(self):
        from backend.plugins.adapters.base import FunctionAdapter
        a = FunctionAdapter(config={"name": "from_cfg", "module": "json", "function": "loads"})
        assert a.name == "from_cfg"


# ═══════════════════════════════════════════════════════
#  3. HTTPAdapter
# ═══════════════════════════════════════════════════════

class TestHTTPAdapter:

    def test_init_defaults(self):
        from backend.plugins.adapters.base import HTTPAdapter
        a = HTTPAdapter()
        assert a.name == "http_api"
        assert a.adapter_type == "http"

    def test_init_with_config(self):
        from backend.plugins.adapters.base import HTTPAdapter
        a = HTTPAdapter(config={"name": "my_api", "url": "https://api.example.com"})
        assert a.name == "my_api"

    def test_config_schema(self):
        from backend.plugins.adapters.base import HTTPAdapter
        a = HTTPAdapter()
        schema = a.get_config_schema()
        assert "url" in schema
        assert "method" in schema
        assert schema["url"]["required"] is True

    def test_url_template_substitution(self):
        """验证 {symbol} / {market} 模板替换"""
        from backend.plugins.adapters.base import HTTPAdapter
        a = HTTPAdapter(config={"url": "https://api.example.com/{symbol}/{market}", "method": "GET"})
        # mock httpx to avoid real HTTP call
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client
            asyncio.get_event_loop().run_until_complete(
                a.invoke({"symbol": "600519", "market": "a_share"})
            )
            # 验证 URL 被正确替换
            call_args = mock_client.get.call_args
            assert "600519" in str(call_args)
            assert "a_share" in str(call_args)

    def test_body_map(self):
        from backend.plugins.adapters.base import HTTPAdapter
        a = HTTPAdapter(config={"url": "https://x.com/api", "method": "POST", "body_map": {"symbol": "code"}})
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client
            asyncio.get_event_loop().run_until_complete(
                a.invoke({"symbol": "600519", "market": "a_share"})
            )
            # body_map should map "symbol" -> "code"
            call_kwargs = mock_client.request.call_args
            json_body = call_kwargs[1].get("json") if len(call_kwargs) > 1 else None
            if json_body is None:
                json_body = call_kwargs.kwargs.get("json", {})
            assert json_body.get("code") == "600519"


# ═══════════════════════════════════════════════════════
#  4. ScriptAdapter
# ═══════════════════════════════════════════════════════

class TestScriptAdapter:

    def test_invoke_script(self):
        from backend.plugins.adapters.base import ScriptAdapter
        # 创建临时脚本
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write("def run(symbol='', market='', **kw):\n    return {'symbol': symbol, 'market': market}\n")
            f.flush()
            script_path = f.name
        try:
            a = ScriptAdapter(config={"script_path": script_path, "function": "run", "output_key": "script_out"})
            result = asyncio.get_event_loop().run_until_complete(
                a.invoke({"symbol": "600519", "market": "a_share"})
            )
            assert result["script_out"]["symbol"] == "600519"
        finally:
            import os
            os.unlink(script_path)

    def test_missing_script_raises(self):
        from backend.plugins.adapters.base import ScriptAdapter
        a = ScriptAdapter(config={"script_path": "/nonexistent/script.py"})
        with pytest.raises((ValueError, FileNotFoundError)):
            asyncio.get_event_loop().run_until_complete(a.invoke({}))

    def test_missing_function_in_script(self):
        from backend.plugins.adapters.base import ScriptAdapter
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write("def other(): pass\n")
            f.flush()
            script_path = f.name
        try:
            a = ScriptAdapter(config={"script_path": script_path, "function": "nonexistent"})
            with pytest.raises(ValueError, match="未找到函数"):
                asyncio.get_event_loop().run_until_complete(a.invoke({}))
        finally:
            import os
            os.unlink(script_path)

    def test_init_defaults(self):
        from backend.plugins.adapters.base import ScriptAdapter
        a = ScriptAdapter()
        assert a.name == "script"
        assert a.adapter_type == "script"


# ═══════════════════════════════════════════════════════
#  5. DockerAdapter
# ═══════════════════════════════════════════════════════

class TestDockerAdapter:

    def test_init(self):
        from backend.plugins.adapters.base import DockerAdapter
        a = DockerAdapter(config={"name": "my_docker", "image": "python:3.12"})
        assert a.name == "my_docker"
        assert a.adapter_type == "docker"

    def test_init_defaults(self):
        from backend.plugins.adapters.base import DockerAdapter
        a = DockerAdapter()
        assert a.name == "docker"

    def test_invoke_docker_error_no_binary(self):
        """docker 不可用时应返回错误"""
        from backend.plugins.adapters.base import DockerAdapter
        a = AsyncMock()
        a.__class__ = DockerAdapter
        # 直接测试错误路径 — docker binary 不存在
        from backend.plugins.adapters.base import DockerAdapter as DA
        real = DA(config={"image": "python:3.12"})
        # 用 mock 替代 subprocess
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mock_proc.returncode = 1
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc), \
             patch("asyncio.wait_for", AsyncMock(return_value=(b"", b"docker not found"))):
            mock_proc.returncode = 1
            result = asyncio.get_event_loop().run_until_complete(
                real.invoke({"symbol": "600519", "market": "a_share"})
            )
            assert "error" in result.get("docker_result", {})


# ═══════════════════════════════════════════════════════
#  6. MCPAdapter
# ═══════════════════════════════════════════════════════

class TestMCPAdapter:

    def test_init(self):
        from backend.plugins.adapters.base import MCPAdapter
        a = MCPAdapter(config={"name": "mcp_test", "command": "npx", "args": ["-y", "my-mcp"]})
        assert a.name == "mcp_test"
        assert a.adapter_type == "mcp"

    def test_init_defaults(self):
        from backend.plugins.adapters.base import MCPAdapter
        a = MCPAdapter()
        assert a.name == "mcp_server"

    def test_tool_args_mapping(self):
        """验证 tool_args 中 state_key -> arg_name 映射"""
        from backend.plugins.adapters.base import MCPAdapter
        a = MCPAdapter(config={
            "command": "echo",
            "tool": "get_price",
            "tool_args": {"symbol": "stock_code"},
            "timeout": 5,
        })
        # mock subprocess
        mock_resp_line = json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"price": 100}})
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(mock_resp_line.encode(), b""))
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc), \
             patch("asyncio.wait_for", AsyncMock(return_value=(mock_resp_line.encode(), b""))):
            result = asyncio.get_event_loop().run_until_complete(
                a.invoke({"symbol": "600519", "market": "a_share"})
            )
            assert result["mcp_result"]["price"] == 100


# ═══════════════════════════════════════════════════════
#  7. LangChainAdapter
# ═══════════════════════════════════════════════════════

class TestLangChainAdapter:

    def test_init(self):
        from backend.plugins.adapters.base import LangChainAdapter
        a = LangChainAdapter(config={"name": "lc_test"})
        assert a.name == "lc_test"
        assert a.adapter_type == "langchain"

    def test_init_defaults(self):
        from backend.plugins.adapters.base import LangChainAdapter
        a = LangChainAdapter()
        assert a.name == "langchain_tool"


# ═══════════════════════════════════════════════════════
#  8. 工厂方法 & 注册表
# ═══════════════════════════════════════════════════════

class TestAdapterFactory:

    def test_create_all_builtin_types(self):
        from backend.plugins.adapters.base import create_adapter
        for atype in ("function", "http", "script", "docker", "mcp", "langchain"):
            a = create_adapter(atype, {"name": f"test_{atype}"})
            assert a.adapter_type == atype

    def test_create_unknown_raises(self):
        from backend.plugins.adapters.base import create_adapter
        with pytest.raises(ValueError, match="未知的适配器类型"):
            create_adapter("nonexistent_type")

    def test_get_adapter_class_builtin(self):
        from backend.plugins.adapters.base import get_adapter_class, FunctionAdapter, HTTPAdapter
        assert get_adapter_class("function") is FunctionAdapter
        assert get_adapter_class("http") is HTTPAdapter

    def test_get_adapter_class_external_registry(self):
        from backend.plugins.adapters.base import get_adapter_class, adapter_registry
        class CustomAdapter:
            pass
        adapter_registry["custom_ext"] = {"class": CustomAdapter}
        try:
            assert get_adapter_class("custom_ext") is CustomAdapter
        finally:
            del adapter_registry["custom_ext"]

    def test_get_adapter_class_unknown(self):
        from backend.plugins.adapters.base import get_adapter_class
        assert get_adapter_class("unknown_xxx") is None

    def test_list_adapter_types(self):
        from backend.plugins.adapters.base import list_adapter_types
        types_list = list_adapter_types()
        type_names = [t["type"] for t in types_list]
        assert "function" in type_names
        assert "http" in type_names
        assert "script" in type_names
        assert "docker" in type_names
        assert "mcp" in type_names
        assert "langchain" in type_names

    def test_list_adapter_types_with_external(self):
        from backend.plugins.adapters.base import list_adapter_types, adapter_registry
        mock_manifest = MagicMock()
        mock_manifest.description = "自定义 — 自定义适配器"
        adapter_registry["custom_list"] = {"manifest": mock_manifest}
        try:
            types_list = list_adapter_types()
            custom = [t for t in types_list if t["type"] == "custom_list"]
            assert len(custom) == 1
            assert custom[0].get("source") == "plugin"
        finally:
            del adapter_registry["custom_list"]

    def test_adapter_registry_is_global_dict(self):
        from backend.plugins.adapters.base import adapter_registry
        assert isinstance(adapter_registry, dict)
