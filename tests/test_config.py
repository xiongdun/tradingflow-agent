# tests/test_config.py
# 配置模块测试 — Settings 加载、默认值、环境变量覆盖

from __future__ import annotations

from unittest.mock import patch



class TestSettings:
    """测试 Settings 配置模型"""

    def test_default_values(self, tmp_path):
        from backend.core.config import Settings
        env_file = tmp_path / ".env"
        env_file.write_text("")
        with patch("backend.core.config.ENV_FILE", env_file):
            s = Settings(_env_file=str(env_file))
            assert s.llm_provider == "deepseek"
            assert s.llm_model == "deepseek-chat"
            assert s.llm_base_url == "https://api.deepseek.com/v1"
            assert s.llm_temperature == 0.3
            assert s.llm_max_tokens == 4096
            assert s.default_market == "a_share"
            assert s.analysis_timeout == 120
            assert s.api_host == "0.0.0.0"
            assert s.api_port == 8000
            assert s.log_level == "INFO"
            assert s.color_scheme == "cn"
            assert s.language == "zh"

    def test_env_override(self, tmp_path):
        from backend.core.config import Settings
        env_file = tmp_path / ".env"
        env_file.write_text("LLM_PROVIDER=openai\nLLM_MODEL=gpt-4\nAPI_PORT=9000\n")
        with patch("backend.core.config.ENV_FILE", env_file):
            s = Settings(_env_file=str(env_file))
            assert s.llm_provider == "openai"
            assert s.llm_model == "gpt-4"
            assert s.api_port == 9000

    def test_market_type_literal(self):
        from backend.core.config import Settings
        s = Settings()
        assert s.default_market in ("a_share", "h_stock", "us_stock")


class TestConfigWriter:
    """测试 .env 文件写入功能"""

    def test_update_setting_create_new(self, tmp_path):
        from backend.core.config_writer import update_setting
        env_file = tmp_path / ".env"
        with patch("backend.core.config_writer.ENV_FILE", env_file):
            with patch("backend.core.config_writer.PROJECT_ROOT", tmp_path):
                update_setting("NEW_KEY", "new_value")
                assert env_file.exists()
                content = env_file.read_text()
                assert "NEW_KEY=new_value" in content

    def test_update_setting_modify_existing(self, tmp_path):
        from backend.core.config_writer import update_setting
        env_file = tmp_path / ".env"
        env_file.write_text("EXISTING_KEY=old_value\nOTHER=keep\n")
        with patch("backend.core.config_writer.ENV_FILE", env_file):
            with patch("backend.core.config_writer.PROJECT_ROOT", tmp_path):
                update_setting("EXISTING_KEY", "updated_value")
                content = env_file.read_text()
                assert "EXISTING_KEY=updated_value" in content
                assert "OTHER=keep" in content
                assert "old_value" not in content

    def test_update_settings_batch(self, tmp_path):
        from backend.core.config_writer import update_settings
        env_file = tmp_path / ".env"
        env_file.write_text("KEY_A=1\n")
        with patch("backend.core.config_writer.ENV_FILE", env_file):
            with patch("backend.core.config_writer.PROJECT_ROOT", tmp_path):
                update_settings({"KEY_A": "10", "KEY_B": "20"})
                content = env_file.read_text()
                assert "KEY_A=10" in content
                assert "KEY_B=20" in content

    def test_update_settings_empty(self, tmp_path):
        from backend.core.config_writer import update_settings
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=val\n")
        with patch("backend.core.config_writer.ENV_FILE", env_file):
            with patch("backend.core.config_writer.PROJECT_ROOT", tmp_path):
                update_settings({})
                content = env_file.read_text()
                assert "KEY=val" in content
