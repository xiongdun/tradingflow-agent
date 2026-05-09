# tests/test_llm.py
# LLM 工厂测试 — 各供应商实例创建、配置传递

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.core.config import Settings


class TestCreateLlm:
    """测试 create_llm 工厂函数"""

    def test_deepseek_provider(self):
        from backend.core.llm import create_llm
        settings = Settings(
            llm_provider="deepseek",
            llm_model="deepseek-chat",
            llm_api_key="test-key",
            llm_base_url="https://api.deepseek.com/v1",
        )
        with patch("langchain_openai.ChatOpenAI") as mock:
            create_llm(settings)
            mock.assert_called_once()
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["model"] == "deepseek-chat"
            assert call_kwargs["api_key"] == "test-key"
            assert call_kwargs["base_url"] == "https://api.deepseek.com/v1"

    def test_openai_provider(self):
        from backend.core.llm import create_llm
        settings = Settings(llm_provider="openai", llm_model="gpt-4", llm_api_key="key")
        with patch("langchain_openai.ChatOpenAI") as mock:
            create_llm(settings)
            mock.assert_called_once()
            assert mock.call_args.kwargs["model"] == "gpt-4"

    def test_qwen_provider(self):
        from backend.core.llm import create_llm
        settings = Settings(llm_provider="qwen", llm_model="qwen-max", llm_api_key="key")
        with patch("langchain_openai.ChatOpenAI") as mock:
            create_llm(settings)
            mock.assert_called_once()

    def test_xiaomi_provider(self):
        from backend.core.llm import create_llm
        settings = Settings(llm_provider="xiaomi", llm_model="mimo", llm_api_key="key")
        with patch("langchain_openai.ChatOpenAI") as mock:
            create_llm(settings)
            mock.assert_called_once()

    def test_mimo_alias(self):
        from backend.core.llm import create_llm
        settings = Settings(llm_provider="mimo", llm_model="mimo", llm_api_key="key")
        with patch("langchain_openai.ChatOpenAI") as mock:
            create_llm(settings)
            mock.assert_called_once()

    def test_claude_provider(self):
        from backend.core.llm import create_llm
        settings = Settings(llm_provider="claude", llm_api_key="key", llm_model="claude-3")
        mock_chat = MagicMock()
        mock_module = MagicMock(ChatAnthropic=mock_chat)
        with patch.dict("sys.modules", {"langchain_anthropic": mock_module}):
            create_llm(settings)
            mock_chat.assert_called_once()
            model = mock_chat.call_args.kwargs["model"]
            assert "claude" in model.lower()

    def test_ollama_provider(self):
        from backend.core.llm import create_llm
        settings = Settings(llm_provider="ollama", llm_model="")
        mock_chat = MagicMock()
        mock_module = MagicMock(ChatOllama=mock_chat)
        with patch.dict("sys.modules", {"langchain_ollama": mock_module}):
            create_llm(settings)
            mock_chat.assert_called_once()
            assert mock_chat.call_args.kwargs["model"] == "qwen2.5:14b"

    def test_ollama_custom_model(self):
        from backend.core.llm import create_llm
        settings = Settings(llm_provider="ollama", llm_model="llama3")
        mock_chat = MagicMock()
        mock_module = MagicMock(ChatOllama=mock_chat)
        with patch.dict("sys.modules", {"langchain_ollama": mock_module}):
            create_llm(settings)
            assert mock_chat.call_args.kwargs["model"] == "llama3"

    def test_invalid_provider_raises(self):
        from backend.core.llm import create_llm
        settings = Settings(llm_provider="invalid_provider")
        with pytest.raises(ValueError, match="不支持的 LLM 供应商"):
            create_llm(settings)

    def test_default_settings_loading(self):
        from backend.core.llm import create_llm
        with patch("backend.core.config.load_settings") as mock_load:
            mock_load.return_value = Settings(llm_provider="deepseek", llm_api_key="key")
            with patch("langchain_openai.ChatOpenAI"):
                create_llm()
            mock_load.assert_called_once()

    def test_temperature_and_max_tokens(self):
        from backend.core.llm import create_llm
        settings = Settings(
            llm_provider="deepseek",
            llm_api_key="key",
            llm_temperature=0.7,
            llm_max_tokens=2048,
        )
        with patch("langchain_openai.ChatOpenAI") as mock:
            create_llm(settings)
            kwargs = mock.call_args.kwargs
            assert kwargs["temperature"] == 0.7
            assert kwargs["max_tokens"] == 2048
