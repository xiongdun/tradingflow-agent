# backend/core/cache.py
# 磁盘 TTL 缓存层 — 为数据源调用提供基于文件的缓存，减少重复 API 请求

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any, Callable

from loguru import logger

# 缓存目录
_CACHE_DIR = Path(__file__).parent.parent / ".cache"

# 默认 TTL（秒）
DEFAULT_TTL = 300

# 按缓存 key 分片的锁，避免并发读写同一文件
_locks: dict[str, threading.Lock] = {}
_locks_lock = threading.Lock()


def _get_lock(key: str) -> threading.Lock:
    """获取指定缓存 key 的文件锁（惰性创建，线程安全）"""
    if key not in _locks:
        with _locks_lock:
            if key not in _locks:
                _locks[key] = threading.Lock()
    return _locks[key]

# 各数据方法的 TTL 策略
TTL_CONFIG: dict[str, int] = {
    "get_realtime_quote": 60,
    "get_kline": 300,
    "get_stock_info": 86400,
    "get_financial_data": 3600,
    "search_stock": 3600,
    "news": 300,
    "sentiment": 300,
}


def _ensure_cache_dir() -> Path:
    """确保缓存目录存在"""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR


def _cache_key(method: str, *args: Any, **kwargs: Any) -> str:
    """生成缓存 key：{method}:{args_hash}"""
    raw = f"{method}:{args}:{sorted(kwargs.items())}"
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_path(key: str) -> Path:
    """缓存文件路径"""
    return _ensure_cache_dir() / f"{key}.json"


def cached_call(method: str, fn: Callable, *args: Any, **kwargs: Any) -> Any:
    """带 TTL 缓存的函数调用（线程安全）。

    先检查缓存是否命中且未过期，命中则直接返回缓存值；
    未命中则调用 fn，成功后写入缓存。
    使用 per-key 锁防止并发读写同一缓存文件。

    Args:
        method: 方法名（用于查 TTL 策略和生成 key）
        fn: 实际执行的函数
        *args, **kwargs: 传给 fn 的参数

    Returns:
        fn 的返回值（来自缓存或实时调用）
    """
    ttl = TTL_CONFIG.get(method, DEFAULT_TTL)
    key = _cache_key(method, *args, **kwargs)
    path = _cache_path(key)
    lock = _get_lock(key)

    with lock:
        # 尝试读取缓存
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("expire_at", 0) > time.time():
                    logger.debug(f"[cache] HIT: {method} (ttl={ttl}s)")
                    return data["value"]
                else:
                    logger.debug(f"[cache] EXPIRED: {method}")
                    path.unlink(missing_ok=True)
            except Exception:
                path.unlink(missing_ok=True)

        # 缓存未命中，调用实际函数
        logger.debug(f"[cache] MISS: {method}")
        result = fn(*args, **kwargs)

        # 写入缓存（仅成功结果才缓存）
        try:
            cache_data = {
                "expire_at": time.time() + ttl,
                "method": method,
                "value": result,
            }
            path.write_text(
                json.dumps(cache_data, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"[cache] Failed to write cache for {method}: {e}")

    return result


def clear_cache(method: str | None = None) -> int:
    """清除缓存。指定 method 则只清除该方法的缓存，否则清除全部。

    Returns:
        清除的缓存文件数
    """
    cache_dir = _ensure_cache_dir()
    count = 0
    for f in cache_dir.glob("*.json"):
        file_key = f.stem
        lock = _get_lock(file_key)
        with lock:
            if method:
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if data.get("method") == method:
                        f.unlink()
                        count += 1
                except Exception:
                    f.unlink()
                    count += 1
            else:
                f.unlink()
                count += 1
    return count
