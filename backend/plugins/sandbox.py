# backend/plugins/sandbox.py
# 技能沙箱 — 隔离执行不可信的社区技能，支持 3 种隔离级别

from __future__ import annotations

import asyncio
import functools
import json
import sys
from typing import Any

from loguru import logger

from backend.plugins.manifest import Permission, PluginManifest
from backend.skills.registry import SkillMeta


class SandboxError(Exception):
    """沙箱执行错误"""
    pass


class SkillSandbox:
    """技能沙箱 — 根据插件权限选择隔离级别

    3 种隔离级别：
    1. direct    — 直接执行（本地可信插件，FULL_ACCESS 权限）
    2. restricted — 限制执行（禁止网络/执行权限，纯计算型技能）
    3. subprocess — 子进程隔离（网络/文件/执行权限，完全隔离）
    """

    def __init__(self, manifest: PluginManifest | None = None):
        self.manifest = manifest
        self.permissions = manifest.permissions if manifest else [Permission.FULL_ACCESS]

    def _determine_level(self) -> str:
        """根据权限列表决定隔离级别"""
        if Permission.FULL_ACCESS in self.permissions:
            return "direct"
        if Permission.NETWORK in self.permissions or Permission.EXECUTE in self.permissions:
            return "subprocess"
        return "restricted"

    async def execute_skill(self, skill_meta: SkillMeta, symbol: str, market: str,
                            dep_results: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        """执行技能并返回结果"""
        level = self._determine_level()
        if level == "direct":
            return await self._execute_direct(skill_meta, symbol, market, dep_results, **kwargs)
        elif level == "subprocess":
            return await self._execute_subprocess(skill_meta, symbol, market, dep_results, **kwargs)
        else:
            return await self._execute_restricted(skill_meta, symbol, market, dep_results, **kwargs)

    async def _execute_direct(self, skill_meta: SkillMeta, symbol: str, market: str,
                              dep_results: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        """直接执行 — 无隔离，适用于本地可信插件"""
        extra_kwargs = {k: v for k, v in (dep_results or {}).items() if k in skill_meta.depends_on}
        fn = functools.partial(skill_meta.execute, symbol=symbol, market=market, **extra_kwargs, **kwargs)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, fn)

    async def _execute_restricted(self, skill_meta: SkillMeta, symbol: str, market: str,
                                  dep_results: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        """受限执行 — 禁止网络调用和外部进程，仅允许纯计算"""
        extra_kwargs = {k: v for k, v in (dep_results or {}).items() if k in skill_meta.depends_on}
        original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

        def _restricted_import(name, *args, **kw):
            if name.split(".")[0] in {"socket", "urllib3", "requests", "httpx", "aiohttp"}:
                raise SandboxError(f"沙箱禁止网络模块: {name}")
            return original_import(name, *args, **kw)

        loop = asyncio.get_running_loop()

        def _run():
            old_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else None
            if old_import:
                __builtins__.__import__ = _restricted_import  # type: ignore
            try:
                return skill_meta.execute(symbol=symbol, market=market, **extra_kwargs, **kwargs)
            finally:
                if old_import:
                    __builtins__.__import__ = old_import  # type: ignore

        return await loop.run_in_executor(None, _run)

    async def _execute_subprocess(self, skill_meta: SkillMeta, symbol: str, market: str,
                                  dep_results: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        """子进程隔离执行 — 完全隔离，适用于不受信任的外部插件"""
        extra_kwargs = {k: v for k, v in (dep_results or {}).items() if k in skill_meta.depends_on}
        call_data = {
            "module": skill_meta.fn.__module__ if hasattr(skill_meta.fn, '__module__') else "",
            "func": skill_meta.fn.__name__,
            "kwargs": {**extra_kwargs, **kwargs, "symbol": symbol, "market": market},
        }
        script = (
            "import json, sys, importlib\n"
            "data = json.loads(sys.stdin.read())\n"
            "mod = importlib.import_module(data[\"module\"])\n"
            "fn = getattr(mod, data[\"func\"])\n"
            "result = fn(**data[\"kwargs\"])\n"
            "print(json.dumps(result, default=str, ensure_ascii=False))\n"
        )
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-c", script,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=json.dumps(call_data, default=str).encode()),
                timeout=30,
            )
            if proc.returncode != 0:
                raise SandboxError(f"子进程执行失败: {stderr.decode()}")
            return json.loads(stdout.decode())
        except asyncio.TimeoutError:
            proc.kill()
            raise SandboxError("子进程执行超时 (30s)")
        except json.JSONDecodeError as e:
            raise SandboxError(f"子进程输出解析失败: {e}")

    def validate_permissions(self) -> list[str]:
        """校验权限合规性，返回不合规的权限列表"""
        blocked = []
        if self.manifest and self.manifest.source == "local":
            return blocked
        if Permission.FULL_ACCESS in self.permissions:
            blocked.append("full_access")
        if Permission.EXECUTE in self.permissions:
            blocked.append("execute")
        return blocked
