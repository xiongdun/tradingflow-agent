# backend/core/locale.py
# 多语言支持 — 后端报告文本的中英文翻译

from __future__ import annotations




# ── 报告文本翻译 ──
REPORT_LOCALE: dict[str, dict[str, str]] = {
    "zh": {
        "report_title": "# 📊 标的分析报告: {stock} ({market})",
        "generated_at": "**生成时间**",
        "section_overall": "## 🎯 综合研判",
        "col_indicator": "指标",
        "col_result": "结果",
        "overall_stance": "整体立场",
        "confidence": "置信度",
        "action_advice": "投资建议",
        "consensus": "### ✅ 分析师共识",
        "disagreement": "### ⚔️ 分歧观点",
        "risks": "### ⚠️ 关键风险",
        "opportunities": "### 💡 投资机会",
        "summary": "### 📝 分析总结",
        "agents_title": "## 👥 各分析师观点",
        "key_points": "**核心论点:**",
        "risk_factors": "**风险提示:**",
        "agent_summary": "**总结:**",
        "disclaimer": "*⚠️ 免责声明：本报告由 AI 自动生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。*",
        "html_title": "分析报告",
        "stance_bullish": "🟢 看多",
        "stance_bearish": "🔴 看空",
        "stance_neutral": "🟡 中性",
        "action_buy": "✅ 建议买入",
        "action_sell": "❌ 建议卖出",
        "action_hold": "⏸️ 建议持有",
        "action_watch": "👀 建议观望",
    },
    "en": {
        "report_title": "# 📊 Analysis Report: {stock} ({market})",
        "generated_at": "**Generated At**",
        "section_overall": "## 🎯 Overall Assessment",
        "col_indicator": "Indicator",
        "col_result": "Result",
        "overall_stance": "Overall Stance",
        "confidence": "Confidence",
        "action_advice": "Action Advice",
        "consensus": "### ✅ Analyst Consensus",
        "disagreement": "### ⚔️ Disagreements",
        "risks": "### ⚠️ Key Risks",
        "opportunities": "### 💡 Opportunities",
        "summary": "### 📝 Analysis Summary",
        "agents_title": "## 👥 Analyst Opinions",
        "key_points": "**Key Points:**",
        "risk_factors": "**Risk Factors:**",
        "agent_summary": "**Summary:**",
        "disclaimer": "*⚠️ Disclaimer: This report is AI-generated for reference only and does not constitute investment advice. Investing involves risks.*",
        "html_title": "Analysis Report",
        "stance_bullish": "🟢 Bullish",
        "stance_bearish": "🔴 Bearish",
        "stance_neutral": "🟡 Neutral",
        "action_buy": "✅ Buy",
        "action_sell": "❌ Sell",
        "action_hold": "⏸️ Hold",
        "action_watch": "👀 Watch",
    },
}


def get_report_text(key: str, lang: str | None = None) -> str:
    """获取报告文本。未指定语言时从 config 读取默认值。"""
    if lang is None:
        try:
            from backend.core.config import load_settings
            lang = load_settings().language
        except Exception:
            lang = "zh"
    return REPORT_LOCALE.get(lang, REPORT_LOCALE["zh"]).get(key, key)


def get_stance_emoji(stance: str, lang: str | None = None) -> str:
    """获取立场标签（含 emoji）"""
    mapping = {
        "bullish": get_report_text("stance_bullish", lang),
        "bearish": get_report_text("stance_bearish", lang),
        "neutral": get_report_text("stance_neutral", lang),
    }
    return mapping.get(stance, stance)


def get_action_emoji(action: str, lang: str | None = None) -> str:
    """获取投资建议标签（含 emoji）"""
    mapping = {
        "buy": get_report_text("action_buy", lang),
        "sell": get_report_text("action_sell", lang),
        "hold": get_report_text("action_hold", lang),
        "watch": get_report_text("action_watch", lang),
    }
    return mapping.get(action, action)


def get_frontend_locale(lang: str | None = None) -> dict[str, str]:
    """获取前端语言包（用于 /api/locale/:lang 端点）"""
    if lang is None:
        try:
            from backend.core.config import load_settings
            lang = load_settings().language
        except Exception:
            lang = "zh"
    return REPORT_LOCALE.get(lang, REPORT_LOCALE["zh"])
