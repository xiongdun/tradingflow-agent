# tests/test_exceptions.py
# 自定义异常体系测试

from __future__ import annotations

import pytest


class TestVibeError:
    """测试基础异常"""

    def test_base_exception(self):
        from backend.core.exceptions import VibeError
        with pytest.raises(VibeError):
            raise VibeError("test error")


class TestDataFetchError:
    """测试数据获取异常"""

    def test_message_format(self):
        from backend.core.exceptions import DataFetchError
        err = DataFetchError("akshare", "600519", "timeout")
        assert "akshare" in str(err)
        assert "600519" in str(err)
        assert "timeout" in str(err)
        assert err.provider == "akshare"
        assert err.symbol == "600519"

    def test_is_vibe_error(self):
        from backend.core.exceptions import DataFetchError, VibeError
        err = DataFetchError("test", "SYM")
        assert isinstance(err, VibeError)


class TestSkillExecutionError:
    """测试技能执行异常"""

    def test_message_format(self):
        from backend.core.exceptions import SkillExecutionError
        err = SkillExecutionError("financial_data", "missing param")
        assert "financial_data" in str(err)
        assert "missing param" in str(err)
        assert err.skill_name == "financial_data"


class TestWorkflowBuildError:
    """测试工作流构建异常"""

    def test_message_format(self):
        from backend.core.exceptions import WorkflowBuildError
        err = WorkflowBuildError("invalid mode")
        assert "invalid mode" in str(err)


class TestAnalysisError:
    """测试分析执行异常"""

    def test_message_format(self):
        from backend.core.exceptions import AnalysisError
        err = AnalysisError("AAPL", "LLM timeout")
        assert "AAPL" in str(err)
        assert "LLM timeout" in str(err)
        assert err.symbol == "AAPL"


class TestConfigError:
    """测试配置异常"""

    def test_is_vibe_error(self):
        from backend.core.exceptions import ConfigError, VibeError
        err = ConfigError("bad config")
        assert isinstance(err, VibeError)
