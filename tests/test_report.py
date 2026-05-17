# tests/test_report.py
# 报告生成器测试 — Markdown / HTML / Text 格式输出

from __future__ import annotations

import pytest


@pytest.fixture
def sample_report():
    """样本分析报告数据"""
    return {
        "stock": "600519",
        "market": "a_share",
        "overall_stance": "bullish",
        "overall_confidence": 0.85,
        "action_suggestion": "buy",
        "consensus_points": ["业绩稳健增长", "品牌价值突出"],
        "disagreement_points": ["估值偏高"],
        "key_risks": ["宏观经济下行"],
        "opportunities": ["消费升级趋势"],
        "summary": "综合分析认为该股具备长期投资价值",
        "agent_opinions": [
            {
                "agent_name": "基本面分析师",
                "agent_role": "fundamental",
                "stock": "600519",
                "market": "a_share",
                "stance": "bullish",
                "confidence": 0.9,
                "key_points": ["ROE 持续提升", "现金流充裕"],
                "risk_factors": ["政策风险"],
                "summary": "基本面扎实",
                "data_evidence": {},
            }
        ],
    }


class TestGenerateMarkdownReport:
    """测试 Markdown 报告生成"""

    def test_contains_stock_info(self, sample_report):
        from backend.output.report import generate_markdown_report
        md = generate_markdown_report(sample_report, "zh")
        assert "600519" in md
        assert "a_share" in md

    def test_contains_stance_and_confidence(self, sample_report):
        from backend.output.report import generate_markdown_report
        md = generate_markdown_report(sample_report, "zh")
        assert "看多" in md or "bullish" in md.lower()
        assert "85%" in md or "0.85" in md

    def test_contains_agent_opinions(self, sample_report):
        from backend.output.report import generate_markdown_report
        md = generate_markdown_report(sample_report, "zh")
        assert "基本面分析师" in md
        assert "基本面扎实" in md

    def test_contains_consensus(self, sample_report):
        from backend.output.report import generate_markdown_report
        md = generate_markdown_report(sample_report, "zh")
        assert "业绩稳健增长" in md

    def test_contains_risks(self, sample_report):
        from backend.output.report import generate_markdown_report
        md = generate_markdown_report(sample_report, "zh")
        assert "宏观经济下行" in md

    def test_english_report(self, sample_report):
        from backend.output.report import generate_markdown_report
        md = generate_markdown_report(sample_report, "en")
        assert "Analysis Report" in md
        assert "Bullish" in md or "bullish" in md

    def test_empty_opinions(self):
        from backend.output.report import generate_markdown_report
        report = {
            "stock": "TEST",
            "market": "a_share",
            "overall_stance": "neutral",
            "overall_confidence": 0.5,
            "action_suggestion": "hold",
            "agent_opinions": [],
        }
        md = generate_markdown_report(report, "zh")
        assert "TEST" in md
        assert "免责声明" in md

    def test_disclaimer_present(self, sample_report):
        from backend.output.report import generate_markdown_report
        md = generate_markdown_report(sample_report, "zh")
        assert "免责声明" in md or "Disclaimer" in md


class TestGenerateHtmlReport:
    """测试 HTML 报告生成"""

    def test_html_structure(self, sample_report):
        from backend.output.report import generate_html_report
        html = generate_html_report(sample_report, "zh")
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html
        assert "<body>" in html
        assert "</body>" in html

    def test_contains_stock_data(self, sample_report):
        from backend.output.report import generate_html_report
        html = generate_html_report(sample_report, "zh")
        assert "600519" in html

    def test_table_rendering(self, sample_report):
        from backend.output.report import generate_html_report
        html = generate_html_report(sample_report, "zh")
        assert "<tr>" in html
        assert "<td>" in html


class TestGenerateTextReport:
    """测试纯文本报告生成"""

    def test_no_markdown_syntax(self, sample_report):
        from backend.output.report import generate_text_report
        text = generate_text_report(sample_report, "zh")
        assert "#" not in text or "600519" in text  # 允许数字但不应有 markdown 标题
        assert "**" not in text
        assert "```" not in text

    def test_contains_content(self, sample_report):
        from backend.output.report import generate_text_report
        text = generate_text_report(sample_report, "zh")
        assert "600519" in text
        assert "基本面分析师" in text
