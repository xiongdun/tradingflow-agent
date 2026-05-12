# backend/core/limiter.py
# 共享限流器 — 供 main.py 和各个 APIRouter 使用，避免循环导入

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])