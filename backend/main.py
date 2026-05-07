# backend/main.py
# FastAPI 应用入口 — 提供 REST API 和 WebSocket 实时分析服务

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core.config import load_settings
from backend.core.config_writer import update_setting


# ──────────────────────────── 自动发现 ────────────────────────────

from backend.core.discovery import auto_discover
auto_discover()


# ──────────────────────────── 应用初始化 ────────────────────────────

app = FastAPI(
    title="TradingFlow Agent",
    description="AI 多智能体股票分析系统 API",
    version="0.1.0",
)

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

app.include_router(market_router)
app.include_router(agents_router)
app.include_router(workflows_router)
app.include_router(data_sources_router)
app.include_router(history_router)
app.include_router(watchlist_router)
app.include_router(schedules_router)
app.include_router(analysis_router)


# ──────────────────────────── 请求/响应模型 ────────────────────────────

class ConfigUpdate(BaseModel):
    """配置更新请求模型"""
    key: str
    value: str


# ──────────────────────────── 通用端点 ────────────────────────────

@app.get("/api/health")
async def health():
    """健康检查端点"""
    return {"status": "ok"}


@app.get("/api/skills")
async def get_skills(market: str = "", category: str = ""):
    """列出所有可用技能，支持按市场和类别过滤"""
    from backend.skills.registry import list_skills
    return list_skills(market=market or None, category=category or None)


@app.get("/api/config")
async def get_config():
    """获取当前系统配置（API Key 脱敏显示）"""
    settings = load_settings()
    data = settings.model_dump()
    if data.get("llm_api_key"):
        key = data["llm_api_key"]
        data["llm_api_key"] = key[:4] + "****" + key[-4:] if len(key) > 8 else "****"
    return data


@app.post("/api/config")
async def update_config(req: ConfigUpdate):
    """更新单个配置项"""
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
