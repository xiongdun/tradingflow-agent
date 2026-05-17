# tests/test_locale.py
# 多语言模块测试 — 翻译查找、emoji 映射、语言包获取

from __future__ import annotations

from unittest.mock import patch



class TestGetReportText:
    """测试 get_report_text 函数"""

    def test_zh_translation(self):
        from backend.core.locale import get_report_text
        result = get_report_text("report_title", "zh")
        assert "标的分析报告" in result

    def test_en_translation(self):
        from backend.core.locale import get_report_text
        result = get_report_text("report_title", "en")
        assert "Analysis Report" in result

    def test_unknown_key_returns_key(self):
        from backend.core.locale import get_report_text
        result = get_report_text("nonexistent_key_xyz", "zh")
        assert result == "nonexistent_key_xyz"

    def test_unknown_lang_fallback_zh(self):
        from backend.core.locale import get_report_text
        result = get_report_text("report_title", "fr")
        assert "标的分析报告" in result

    def test_auto_lang_from_config(self):
        from backend.core.locale import get_report_text
        with patch("backend.core.config.load_settings") as mock_settings:
            mock_settings.return_value.language = "en"
            result = get_report_text("report_title")
            assert "Analysis Report" in result


class TestGetStanceEmoji:
    """测试 get_stance_emoji 函数"""

    def test_bullish_zh(self):
        from backend.core.locale import get_stance_emoji
        result = get_stance_emoji("bullish", "zh")
        assert "看多" in result

    def test_bearish_en(self):
        from backend.core.locale import get_stance_emoji
        result = get_stance_emoji("bearish", "en")
        assert "Bearish" in result

    def test_neutral(self):
        from backend.core.locale import get_stance_emoji
        result = get_stance_emoji("neutral", "zh")
        assert "中性" in result

    def test_unknown_stance(self):
        from backend.core.locale import get_stance_emoji
        result = get_stance_emoji("unknown_stance", "zh")
        assert result == "unknown_stance"


class TestGetActionEmoji:
    """测试 get_action_emoji 函数"""

    def test_buy_zh(self):
        from backend.core.locale import get_action_emoji
        result = get_action_emoji("buy", "zh")
        assert "买入" in result

    def test_sell_en(self):
        from backend.core.locale import get_action_emoji
        result = get_action_emoji("sell", "en")
        assert "Sell" in result

    def test_hold(self):
        from backend.core.locale import get_action_emoji
        result = get_action_emoji("hold", "zh")
        assert "持有" in result

    def test_watch(self):
        from backend.core.locale import get_action_emoji
        result = get_action_emoji("watch", "zh")
        assert "观望" in result


class TestGetFrontendLocale:
    """测试 get_frontend_locale 函数"""

    def test_returns_dict(self):
        from backend.core.locale import get_frontend_locale
        result = get_frontend_locale("zh")
        assert isinstance(result, dict)
        assert "report_title" in result

    def test_zh_en_different(self):
        from backend.core.locale import get_frontend_locale
        zh = get_frontend_locale("zh")
        en = get_frontend_locale("en")
        assert zh["report_title"] != en["report_title"]
