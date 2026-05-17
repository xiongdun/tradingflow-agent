# backend/core/llm.py
# LLM 工厂 — 基于注册表的多供应商支持

from __future__ import annotations

from typing import Callable

from langchain_core.language_models import BaseChatModel

from backend.core.config import Settings


_LLM_BUILDERS: dict[str, Callable[[Settings], BaseChatModel]] = {}


def register_llm(name: str) -> Callable:
    def decorator(fn: Callable[[Settings], BaseChatModel]) -> Callable[[Settings], BaseChatModel]:
        _LLM_BUILDERS[name] = fn
        return fn
    return decorator


# ── 内置供应商 ──


@register_llm("openai")
@register_llm("deepseek")
@register_llm("qwen")
@register_llm("xiaomi")
@register_llm("mimo")
def _build_openai_compat(s: Settings) -> BaseChatModel:
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(  # type: ignore[call-arg]
        model=s.llm_model,
        api_key=s.llm_api_key,  # type: ignore[arg-type]
        base_url=s.llm_base_url,
        temperature=s.llm_temperature,
        max_tokens=s.llm_max_tokens,
        request_timeout=s.llm_timeout,
    )


@register_llm("claude")
def _build_claude(s: Settings) -> BaseChatModel:
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model=s.llm_model or "claude-sonnet-4-20250514",
        api_key=s.llm_api_key,
        temperature=s.llm_temperature,
        max_tokens=s.llm_max_tokens,
    )


@register_llm("ollama")
def _build_ollama(s: Settings) -> BaseChatModel:
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=s.llm_model or "qwen2.5:14b",
        temperature=s.llm_temperature,
    )


# ── 公共 API ──


def create_llm(settings: Settings | None = None) -> BaseChatModel:
    if settings is None:
        from backend.core.config import load_settings
        settings = load_settings()
    provider = settings.llm_provider.lower()
    builder = _LLM_BUILDERS.get(provider)
    if builder is None:
        raise ValueError(
            f"不支持的 LLM 供应商: {provider}，可选: {', '.join(sorted(_LLM_BUILDERS))}"
        )
    return builder(settings)


def list_llm_providers() -> list[str]:
    return sorted(_LLM_BUILDERS.keys())