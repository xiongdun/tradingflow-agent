# tests/test_cache.py
# 缓存模块测试 — 命中、过期、清除

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch



class TestCacheKey:
    def test_deterministic(self):
        from backend.core.cache import _cache_key
        k1 = _cache_key("test", "a", 1)
        k2 = _cache_key("test", "a", 1)
        assert k1 == k2

    def test_different_args_different_key(self):
        from backend.core.cache import _cache_key
        k1 = _cache_key("test", "a")
        k2 = _cache_key("test", "b")
        assert k1 != k2


class TestCachedCall:
    def test_miss_then_hit(self, tmp_path: Path):
        from backend.core.cache import cached_call
        cache_dir = tmp_path / ".cache"
        cache_dir.mkdir()

        with patch("backend.core.cache._CACHE_DIR", cache_dir):
            def fn():
                return {"data": 42}
            result1 = cached_call("test_method", fn)
            assert result1 == {"data": 42}
            result2 = cached_call("test_method", fn)
            assert result2 == {"data": 42}

    def test_expired_cache(self, tmp_path: Path):
        from backend.core.cache import cached_call, _cache_key, _cache_path
        cache_dir = tmp_path / ".cache"
        cache_dir.mkdir()

        with patch("backend.core.cache._CACHE_DIR", cache_dir):
            call_count = 0
            def fn():
                nonlocal call_count
                call_count += 1
                return call_count

            result1 = cached_call("test_expire", fn)
            assert result1 == 1

            key = _cache_key("test_expire")
            path = _cache_path(key)
            data = json.loads(path.read_text())
            data["expire_at"] = time.time() - 10
            path.write_text(json.dumps(data))

            result2 = cached_call("test_expire", fn)
            assert result2 == 2

    def test_clear_all(self, tmp_path: Path):
        from backend.core.cache import cached_call, clear_cache
        cache_dir = tmp_path / ".cache"
        cache_dir.mkdir()

        with patch("backend.core.cache._CACHE_DIR", cache_dir):
            cached_call("m1", lambda: "a")
            cached_call("m2", lambda: "b")
            assert len(list(cache_dir.glob("*.json"))) == 2
            count = clear_cache()
            assert count == 2
            assert len(list(cache_dir.glob("*.json"))) == 0

    def test_clear_by_method(self, tmp_path: Path):
        from backend.core.cache import cached_call, clear_cache
        cache_dir = tmp_path / ".cache"
        cache_dir.mkdir()

        with patch("backend.core.cache._CACHE_DIR", cache_dir):
            cached_call("m1", lambda: "a")
            cached_call("m2", lambda: "b")
            count = clear_cache(method="m1")
            assert count == 1
            assert len(list(cache_dir.glob("*.json"))) == 1
