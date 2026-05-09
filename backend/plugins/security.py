# backend/plugins/security.py
# 安全治理 — 插件权限校验、审计日志、LLM 预算控制

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

from backend.plugins.manifest import Permission, PluginManifest

_AUDIT_DIR = Path(__file__).parent.parent / "data" / "plugins" / "audit"


class PermissionChecker:
    """插件权限校验器"""
    TRUSTED_PERMISSIONS = {Permission.FULL_ACCESS, Permission.NETWORK, Permission.DATA_READ,
                           Permission.DATA_WRITE, Permission.EXECUTE, Permission.LLM_CALL}

    def check(self, manifest: PluginManifest) -> list[str]:
        """校验权限合规性，返回警告列表"""
        warnings = []
        is_local = manifest.source == "local"
        if not is_local and Permission.FULL_ACCESS in manifest.permissions:
            warnings.append(f"插件 {manifest.name} 请求 FULL_ACCESS 权限，非本地插件不允许")
        if not is_local and Permission.EXECUTE in manifest.permissions:
            warnings.append(f"插件 {manifest.name} 请求 EXECUTE 权限，非本地插件不允许")
        for perm in manifest.permissions:
            if perm not in self.TRUSTED_PERMISSIONS:
                warnings.append(f"插件 {manifest.name} 请求未知权限: {perm}")
        return warnings

    def validate_for_execution(self, manifest: PluginManifest) -> bool:
        if manifest.source == "local":
            return True
        if Permission.FULL_ACCESS in manifest.permissions:
            logger.warning(f"[security] 拒绝执行: {manifest.name} (非本地插件请求 FULL_ACCESS)")
            return False
        return True


class AuditLog:
    """插件审计日志 — 记录所有插件的执行行为"""

    def __init__(self) -> None:
        _AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    def _log_file(self) -> Path:
        return _AUDIT_DIR / f"audit_{datetime.now().strftime('%Y-%m-%d')}.jsonl"

    def _write(self, entry: dict[str, Any]) -> None:
        try:
            with open(self._log_file(), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        except Exception as e:
            logger.warning(f"[audit] 写入审计日志失败: {e}")

    def log_execution(self, plugin: str, action: str, result: str, details: dict[str, Any] | None = None) -> None:
        self._write({"timestamp": datetime.now().isoformat(), "plugin": plugin, "action": action, "result": result, "details": details or {}})

    def log_permission_request(self, plugin: str, permission: str, granted: bool) -> None:
        self._write({"timestamp": datetime.now().isoformat(), "plugin": plugin, "action": "permission_request", "permission": permission, "granted": granted})

    def log_install(self, plugin: str, version: str, source: str) -> None:
        self._write({"timestamp": datetime.now().isoformat(), "plugin": plugin, "action": "install", "version": version, "source": source})

    def log_uninstall(self, plugin: str) -> None:
        self._write({"timestamp": datetime.now().isoformat(), "plugin": plugin, "action": "uninstall"})

    def get_audit_trail(self, plugin: str = "", limit: int = 100) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for log_file in sorted(_AUDIT_DIR.glob("audit_*.jsonl"), reverse=True):
            try:
                for line in reversed(log_file.read_text(encoding="utf-8").strip().split("\n")):
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    if plugin and entry.get("plugin") != plugin:
                        continue
                    entries.append(entry)
                    if len(entries) >= limit:
                        return entries
            except Exception:
                continue
        return entries

    def cleanup(self, keep_days: int = 30) -> int:
        cutoff = datetime.now() - timedelta(days=keep_days)
        removed = 0
        for log_file in _AUDIT_DIR.glob("audit_*.jsonl"):
            try:
                file_date = datetime.strptime(log_file.stem.replace("audit_", ""), "%Y-%m-%d")
                if file_date < cutoff:
                    log_file.unlink()
                    removed += 1
            except Exception:
                continue
        return removed


class LLMBudgetGuard:
    """LLM 调用预算控制 — 防止社区插件滥用 LLM API"""

    def __init__(self, max_tokens_per_call: int = 4096, max_calls_per_minute: int = 60,
                 max_cost_per_day: float = 10.0):
        self.max_tokens_per_call = max_tokens_per_call
        self.max_calls_per_minute = max_calls_per_minute
        self.max_cost_per_day = max_cost_per_day
        self._call_times: list[float] = []
        self._daily_tokens: int = 0
        self._daily_cost: float = 0.0

    def check_rate_limit(self) -> bool:
        import time
        now = time.time()
        self._call_times = [t for t in self._call_times if now - t < 60]
        if len(self._call_times) >= self.max_calls_per_minute:
            logger.warning(f"[budget] LLM 调用频率超限: {len(self._call_times)}/{self.max_calls_per_minute}/min")
            return False
        self._call_times.append(now)
        return True

    def check_budget(self) -> bool:
        if self._daily_cost >= self.max_cost_per_day:
            logger.warning(f"[budget] 每日 LLM 预算超限: ${self._daily_cost:.2f}/${self.max_cost_per_day:.2f}")
            return False
        return True

    def record_usage(self, tokens: int, cost: float = 0.0) -> None:
        self._daily_tokens += tokens
        self._daily_cost += cost

    def get_usage(self) -> dict[str, Any]:
        return {"calls_this_minute": len(self._call_times), "max_calls_per_minute": self.max_calls_per_minute,
                "daily_tokens": self._daily_tokens, "daily_cost": round(self._daily_cost, 4), "max_cost_per_day": self.max_cost_per_day}

    def reset_daily(self) -> None:
        self._daily_tokens = 0
        self._daily_cost = 0.0


# 全局实例
permission_checker = PermissionChecker()
audit_log = AuditLog()
llm_budget_guard = LLMBudgetGuard()
