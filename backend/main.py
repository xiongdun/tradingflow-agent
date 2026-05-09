# backend/main.py
# FastAPI 应用入口 — 提供 REST API 和 WebSocket 实时分析服务

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger

from backend.core.config import load_settings
from backend.core.config_writer import update_setting


# ──────────────────────────── 结构化日志 ────────────────────────────

_LOG_DIR = Path(__file__).parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# 移除 loguru 默认 handler，添加结构化配置
logger.remove()
# 开发模式：彩色人类可读格式
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | {message}",
    level="DEBUG",
    colorize=True,
)
# 生产模式：JSON 格式文件（按天轮转，保留 30 天）
logger.add(
    _LOG_DIR / "app_{time:YYYY-MM-DD}.jsonl",
    format="{message}",
    level="INFO",
    rotation="00:00",
    retention="30 days",
    serialize=True,
    encoding="utf-8",
)


# ──────────────────────────── 自动发现 ────────────────────────────

from backend.core.discovery import auto_discover
auto_discover()


# ──────────────────────────── 应用初始化 ────────────────────────────

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="TradingFlow Agent",
    description="AI 多智能体股票分析系统 API",
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────── 注册路由 ────────────────────────────

from backend.api.routes.market_data import router as market_router
from backend.api.routes.agents import router as agents_router
from backend.api.routes.workflows import router as workflows_router
from backend.api.routes.data_sources import router as data_sources_router
from backend.api.routes.history import router as history_router
from backend.api.routes.watchlist import router as watchlist_router
from backend.api.routes.schedules import router as schedules_router
from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.plugins import router as plugins_router
from backend.api.routes.adapters import router as adapters_router

app.include_router(market_router)
app.include_router(agents_router)
app.include_router(workflows_router)
app.include_router(data_sources_router)
app.include_router(history_router)
app.include_router(watchlist_router)
app.include_router(schedules_router)
app.include_router(analysis_router)
app.include_router(plugins_router)
app.include_router(adapters_router)


# ──────────────────────────── 请求/响应模型 ────────────────────────────

class ConfigUpdate(BaseModel):
    """配置更新请求模型"""
    key: str
    value: str


# ──────────────────────────── 通用端点 ────────────────────────────

@app.get("/api/health")
@limiter.exempt
async def health():
    """健康检查端点"""
    return {"status": "ok"}


@app.get("/api/skills")
@limiter.limit("60/minute")
async def get_skills(request: Request, market: str = "", category: str = ""):
    """列出所有可用技能，支持按市场和类别过滤"""
    from backend.skills.registry import list_skills
    return list_skills(market=market or None, category=category or None)


@app.get("/api/config")
@limiter.limit("30/minute")
async def get_config(request: Request):
    """获取当前系统配置（API Key 脱敏显示）"""
    settings = load_settings()
    data = settings.model_dump()
    if data.get("llm_api_key"):
        key = data["llm_api_key"]
        data["llm_api_key"] = key[:4] + "****" + key[-4:] if len(key) > 8 else "****"
    return data


# 配置项白名单 — 防止写入任意 .env 字段
_CONFIG_WHITELIST = {
    "llm_provider", "llm_model", "llm_base_url", "llm_temperature", "llm_max_tokens",
    "default_market", "analysis_timeout", "api_host", "api_port",
    "log_level", "color_scheme", "language", "provider_priority",
}


@app.post("/api/config")
@limiter.limit("10/minute")
async def update_config(request: Request, req: ConfigUpdate):
    """更新单个配置项（白名单校验）"""
    if req.key not in _CONFIG_WHITELIST:
        return {"error": f"不允许修改配置项: {req.key}"}
    update_setting(req.key, req.value)
    return {"status": "ok", "key": req.key, "value": req.value}


@app.get("/api/locale/{lang}")
async def get_locale(lang: str):
    """获取指定语言的翻译包"""
    from backend.core.locale import REPORT_LOCALE
    return REPORT_LOCALE.get(lang, REPORT_LOCALE["zh"])


# ──────────────────────────── 启动/关闭事件 ────────────────────────────

@app.on_event("startup")
async def startup():
    """应用启动时初始化调度器"""
    from backend.core.scheduler import start_scheduler
    start_scheduler()


@app.on_event("shutdown")
async def shutdown():
    """应用关闭时停止调度器"""
    from backend.core.scheduler import stop_scheduler
    stop_scheduler()
