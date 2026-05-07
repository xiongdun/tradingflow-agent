# backend/core/llm.py
# LLM 工厂模块 — 根据配置创建对应的大语言模型实例

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from backend.core.config import Settings


def create_llm(settings: Settings | None = None) -> BaseChatModel:
    """根据配置创建 LLM 实例。

    支持的供应商：openai、deepseek、qwen、xiaomi/mimo、claude、ollama
    """
    if settings is None:
        from backend.core.config import load_settings
        settings = load_settings()

    provider = settings.llm_provider.lower()

    # OpenAI 兼容接口（适用于 OpenAI、DeepSeek、Qwen、小米 MiMo 等）
    if provider in ("openai", "deepseek", "qwen", "xiaomi", "mimo"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            request_timeout=120,  # HTTP 请求超时 120 秒，防止连接挂死
        )

    # Anthropic Claude
    if provider == "claude":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.llm_model or "claude-sonnet-4-20250514",
            api_key=settings.llm_api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    # 本地 Ollama 模型（如 qwen2.5:14b）
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.llm_model or "qwen2.5:14b",
            temperature=settings.llm_temperature,
        )

    raise ValueError(
        f"不支持的 LLM 供应商: {provider}，可选: openai, deepseek, qwen, claude, ollama"
    )
