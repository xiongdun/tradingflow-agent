# backend/core/config.py
# 配置读取模块 — Settings 模型定义与 .env 加载（写入功能已迁移至 config_writer.py）

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings

# 项目根目录（backend/core/ 的上两级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# .env 配置文件路径
ENV_FILE = PROJECT_ROOT / ".env"

# 支持的市场类型：A股、港股、美股
MarketType = Literal["a_share", "h_stock", "us_stock"]


class Settings(BaseSettings):
    """应用配置项，从 .env 文件自动加载"""

    # ── LLM 大模型配置 ──
    llm_provider: str = "deepseek"          # LLM 供应商（openai/deepseek/qwen/claude/ollama）
    llm_model: str = "deepseek-chat"        # 模型名称
    llm_api_key: str = ""                   # API 密钥
    llm_base_url: str = "https://api.deepseek.com/v1"  # API 基础地址
    llm_temperature: float = 0.3            # 温度参数（越低越确定性）
    llm_max_tokens: int = 4096              # 最大生成 token 数

    # ── 分析配置 ──
    default_market: MarketType = "a_share"  # 默认分析市场
    analysis_timeout: int = 120             # 分析超时时间（秒）

    # ── 服务器配置 ──
    api_host: str = "0.0.0.0"              # API 监听地址
    api_port: int = 8000                    # API 监听端口

    # ── 日志配置 ──
    log_level: str = "INFO"                 # 日志级别

    # ── 显示配置 ──
    color_scheme: str = "cn"                # 涨跌颜色方案：cn=红涨绿跌（中国），international=绿涨红跌（国际）
    language: str = "zh"                    # 界面语言：zh=中文，en=英文

    # ── 数据源配置 ──
    provider_priority: str = ""             # 数据源优先级 JSON（由 API 自动维护）

    model_config = {
        "env_file": str(ENV_FILE),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def load_settings() -> Settings:
    """从 .env 文件加载配置"""
    return Settings()


# 向后兼容 re-export（将在下个版本移除）
def update_setting(key: str, value: str) -> None:
    from backend.core.config_writer import update_setting as _update
    _update(key, value)

def update_settings(updates: dict[str, str]) -> None:
    from backend.core.config_writer import update_settings as _update
    _update(updates)
