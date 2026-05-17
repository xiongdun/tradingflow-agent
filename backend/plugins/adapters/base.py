# backend/plugins/adapters/base.py
# 通用节点适配器 — 将外部项目包装为 LangGraph 工作流节点
# 包含全部 6 种内置适配器类型

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


# 全局适配器注册表（外部插件适配器注册到这里）
adapter_registry: dict[str, dict[str, Any]] = {}


class NodeAdapter(ABC):
    """通用节点适配器基类 — 将外部项目包装为 LangGraph 节点"""

    name: str = ""
    description: str = ""
    adapter_type: str = ""

    @abstractmethod
    async def invoke(self, state: dict) -> dict:
        """LangGraph 节点接口 — 输入/输出共享状态"""
        ...

    def input_schema(self) -> dict[str, Any]:
        return {
            "symbol": {"type": "string", "description": "股票代码", "required": True},
            "market": {"type": "string", "description": "市场类型", "required": True},
        }

    def output_schema(self) -> dict[str, Any]:
        return {}

    def get_config_schema(self) -> dict[str, Any]:
        return {}


# ──────────────────── 1. FunctionAdapter ────────────────────

class FunctionAdapter(NodeAdapter):
    """函数适配器 — 包装任何 async def f(state) -> dict 函数为节点"""
    adapter_type = "function"

    def __init__(self, fn: Any = None, name: str = "", description: str = "", config: dict | None = None):
        if config:
            self.name = config.get("name", "function")
            self.description = config.get("description", "")
            self._fn = None
            self._config = config
        else:
            self._fn = fn
            self.name = name or getattr(fn, '__name__', 'function') if fn else "function"
            self.description = description or (getattr(fn, '__doc__', '') or "") if fn else ""
            self._config = {}

    async def invoke(self, state: dict) -> dict:
        import asyncio
        import functools
        fn = self._fn
        if fn is None and self._config.get("module") and self._config.get("function"):
            import importlib
            mod = importlib.import_module(self._config["module"])
            fn = getattr(mod, self._config["function"])
        if fn is None:
            raise ValueError("FunctionAdapter 未配置函数")
        if asyncio.iscoroutinefunction(fn):
            return await fn(state)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, functools.partial(fn, state))


# ──────────────────── 2. HTTPAdapter ────────────────────

class HTTPAdapter(NodeAdapter):
    """HTTP 适配器 — 包装 REST API 为工作流节点"""
    adapter_type = "http"

    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}
        self.name = self._config.get("name", "http_api")
        self.description = self._config.get("description", "HTTP API 适配器")

    async def invoke(self, state: dict) -> dict:
        import httpx
        url = self._config.get("url", "")
        method = self._config.get("method", "POST").upper()
        headers = self._config.get("headers", {})
        timeout = self._config.get("timeout", 30)
        body_map = self._config.get("body_map", {})
        body: dict[str, Any] = {}
        for state_key, body_key in body_map.items():
            if state_key in state:
                body[body_key] = state[state_key]
        if not body:
            body = {"symbol": state.get("symbol", ""), "market": state.get("market", "")}
        url = url.replace("{symbol}", state.get("symbol", "")).replace("{market}", state.get("market", ""))
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method == "GET":
                resp = await client.get(url, headers=headers, params=body)
            else:
                resp = await client.request(method, url, headers=headers, json=body)
            resp.raise_for_status()
        output_key = self._config.get("output_key", "http_result")
        return {output_key: resp.json()}

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "url": {"type": "string", "description": "API URL (支持 {symbol}/{market})", "required": True},
            "method": {"type": "string", "default": "POST", "enum": ["GET", "POST", "PUT"]},
            "headers": {"type": "object"}, "body_map": {"type": "object"},
            "output_key": {"type": "string", "default": "http_result"},
            "timeout": {"type": "integer", "default": 30},
        }


# ──────────────────── 3. ScriptAdapter ────────────────────

class ScriptAdapter(NodeAdapter):
    """脚本适配器 — 包装 Python 脚本为工作流节点"""
    adapter_type = "script"

    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}
        self.name = self._config.get("name", "script")
        self.description = self._config.get("description", "Python 脚本适配器")

    async def invoke(self, state: dict) -> dict:
        import importlib.util
        import asyncio
        import functools
        script_path = self._config.get("script_path", "")
        func_name = self._config.get("function", "run")
        output_key = self._config.get("output_key", "script_result")
        extra_args = self._config.get("args", {})
        spec = importlib.util.spec_from_file_location("_adapted_script", script_path)
        if not spec or not spec.loader:
            raise ValueError(f"无法加载脚本: {script_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = getattr(mod, func_name, None)
        if fn is None:
            raise ValueError(f"脚本 {script_path} 中未找到函数 {func_name}")
        call_args = {**state, **extra_args}
        if asyncio.iscoroutinefunction(fn):
            result = await fn(**call_args)
        else:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, functools.partial(fn, **call_args))
        return {output_key: result}


# ──────────────────── 4. DockerAdapter ────────────────────

class DockerAdapter(NodeAdapter):
    """Docker 适配器 — 包装 Docker 容器为工作流节点"""
    adapter_type = "docker"

    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}
        self.name = self._config.get("name", "docker")
        self.description = self._config.get("description", "Docker 容器适配器")

    async def invoke(self, state: dict) -> dict:
        import asyncio
        import json
        image = self._config.get("image", "")
        output_key = self._config.get("output_key", "docker_result")
        env = self._config.get("env", {})
        timeout = self._config.get("timeout", 120)
        input_data = {"symbol": state.get("symbol", ""), "market": state.get("market", ""), **self._config.get("args", {})}
        cmd = ["docker", "run", "--rm", "--network", "host"]
        for k, v in env.items():
            cmd.extend(["-e", f"{k}={v}"])
        cmd.extend([image, "python", "-c",
            "import json,sys; d=json.loads(sys.stdin.read()); "
            "import importlib; m=importlib.import_module('main'); "
            "f=getattr(m,'run',None); "
            "print(json.dumps(f(**d) if f else {'error':'no run()'}, default=str))"])
        try:
            proc = await asyncio.create_subprocess_exec(*cmd, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await asyncio.wait_for(proc.communicate(input=json.dumps(input_data, default=str).encode()), timeout=timeout)
            if proc.returncode != 0:
                return {output_key: {"error": stderr.decode()[:500]}}
            return {output_key: json.loads(stdout.decode())}
        except asyncio.TimeoutError:
            return {output_key: {"error": f"Docker 超时 ({timeout}s)"}}


# ──────────────────── 5. MCPAdapter ────────────────────

class MCPAdapter(NodeAdapter):
    """MCP 适配器 — 包装 MCP Server 为工作流节点"""
    adapter_type = "mcp"

    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}
        self.name = self._config.get("name", "mcp_server")
        self.description = self._config.get("description", "MCP Server 适配器")

    async def invoke(self, state: dict) -> dict:
        import asyncio
        import json
        command = self._config.get("command", "")
        args = self._config.get("args", [])
        tool_name = self._config.get("tool", "")
        tool_args_map = self._config.get("tool_args", {})
        output_key = self._config.get("output_key", "mcp_result")
        timeout = self._config.get("timeout", 30)
        tool_args = {}
        for state_key, arg_name in tool_args_map.items():
            if state_key in state:
                tool_args[arg_name] = state[state_key]
        if not tool_args:
            tool_args = {"symbol": state.get("symbol", ""), "market": state.get("market", "")}
        init_msg = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"capabilities": {}}})
        call_msg = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": tool_name, "arguments": tool_args}})
        proc = await asyncio.create_subprocess_exec(command, *args, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(input=(init_msg + "\n" + call_msg).encode()), timeout=timeout)
            for line in reversed(stdout.decode().strip().split("\n")):
                try:
                    resp = json.loads(line)
                    if "result" in resp:
                        return {output_key: resp["result"]}
                except json.JSONDecodeError:
                    continue
            return {output_key: {"error": stderr.decode()[:500]}}
        except asyncio.TimeoutError:
            proc.kill()
            return {output_key: {"error": f"MCP 超时 ({timeout}s)"}}


# ──────────────────── 6. LangChainAdapter ────────────────────

class LangChainAdapter(NodeAdapter):
    """LangChain 适配器 — 包装 LangChain Tool 为工作流节点"""
    adapter_type = "langchain"

    def __init__(self, config: dict[str, Any] | None = None):
        self._config = config or {}
        self.name = self._config.get("name", "langchain_tool")
        self.description = self._config.get("description", "LangChain Tool 适配器")
        self._tool = None

    async def invoke(self, state: dict) -> dict:
        tool_class_path = self._config.get("tool_class", "")
        output_key = self._config.get("output_key", "langchain_result")
        if "." in tool_class_path:
            module_path, class_name = tool_class_path.rsplit(".", 1)
            import importlib
            mod = importlib.import_module(module_path)
            self._tool = getattr(mod, class_name)()
        else:
            from langchain_core.tools import tool as langchain_tool
            self._tool = langchain_tool(tool_class_path)
        assert self._tool is not None, "Tool initialization failed"
        input_text = self._config.get("input_template", "{symbol} {market}").format(**state)
        if not input_text.strip():
            input_text = f"{state.get('symbol', '')} {state.get('market', '')}"
        import asyncio
        if hasattr(self._tool, 'ainvoke'):
            result = await self._tool.ainvoke(input_text)
        else:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self._tool.invoke, input_text)
        return {output_key: {"content": str(result)}}


# ──────────────────── 工厂方法 ────────────────────

_BUILTIN_ADAPTERS: dict[str, type[NodeAdapter]] = {
    "function": FunctionAdapter,
    "http": HTTPAdapter,
    "script": ScriptAdapter,
    "docker": DockerAdapter,
    "mcp": MCPAdapter,
    "langchain": LangChainAdapter,
}


def get_adapter_class(adapter_type: str) -> type[NodeAdapter] | None:
    """根据类型获取适配器类"""
    if adapter_type in _BUILTIN_ADAPTERS:
        return _BUILTIN_ADAPTERS[adapter_type]
    entry = adapter_registry.get(adapter_type)
    if entry and "class" in entry:
        return entry["class"]
    return None


def create_adapter(adapter_type: str, config: dict[str, Any] | None = None) -> NodeAdapter:
    """工厂方法 — 根据类型和配置创建适配器实例"""
    cls = get_adapter_class(adapter_type)
    if cls is None:
        raise ValueError(f"未知的适配器类型: {adapter_type}")
    return cls(config=config)  # type: ignore[call-arg]


def list_adapter_types() -> list[dict[str, Any]]:
    """列出所有可用的适配器类型"""
    result = [
        {"type": "function", "name": "函数适配器", "description": "包装任何 Python 函数为节点"},
        {"type": "http", "name": "HTTP 适配器", "description": "包装 REST API 为节点"},
        {"type": "script", "name": "脚本适配器", "description": "包装 Python 脚本为节点"},
        {"type": "docker", "name": "Docker 适配器", "description": "包装 Docker 容器为节点"},
        {"type": "mcp", "name": "MCP 适配器", "description": "包装 MCP Server 为节点"},
        {"type": "langchain", "name": "LangChain 适配器", "description": "包装 LangChain Tool 为节点"},
    ]
    for name, entry in adapter_registry.items():
        manifest = entry.get("manifest")
        if manifest:
            result.append({"type": name, "name": manifest.description.split("—")[0] if manifest.description else name, "description": manifest.description, "source": "plugin"})
    return result
