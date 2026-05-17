# backend/output/report.py
# 报告生成器 — 将分析结果转换为 Markdown 格式报告（支持多语言）

from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.agents.base import AgentOpinion
from backend.core.locale import get_report_text, get_stance_emoji, get_action_emoji


def generate_markdown_report(report: dict[str, Any], lang: str | None = None) -> str:
    """将 FinalReport 字典转换为格式化的 Markdown 分析报告"""
    stock = report.get("stock", "")
    market = report.get("market", "")
    stance = report.get("overall_stance", "neutral")
    confidence = report.get("overall_confidence", 0)
    action = report.get("action_suggestion", "hold")
    opinions = report.get("agent_opinions", [])

    def T(key):
        return get_report_text(key, lang)

    lines = [
        T("report_title").format(stock=stock, market=market),
        "",
        f"{T('generated_at')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        T("section_overall"),
        "",
        f"| {T('col_indicator')} | {T('col_result')} |",
        "|------|------|",
        f"| {T('overall_stance')} | {get_stance_emoji(stance, lang)} |",
        f"| {T('confidence')} | {confidence:.0%} |",
        f"| {T('action_advice')} | {get_action_emoji(action, lang)} |",
        "",
    ]

    # 分析师共识观点
    consensus = report.get("consensus_points", [])
    if consensus:
        lines.append(T("consensus"))
        lines.append("")
        for point in consensus:
            lines.append(f"- {point}")
        lines.append("")

    # 分析师分歧观点
    disagreements = report.get("disagreement_points", [])
    if disagreements:
        lines.append(T("disagreement"))
        lines.append("")
        for point in disagreements:
            lines.append(f"- {point}")
        lines.append("")

    # 关键风险提示
    risks = report.get("key_risks", [])
    if risks:
        lines.append(T("risks"))
        lines.append("")
        for risk in risks:
            lines.append(f"- {risk}")
        lines.append("")

    # 投资机会
    opportunities = report.get("opportunities", [])
    if opportunities:
        lines.append(T("opportunities"))
        lines.append("")
        for opp in opportunities:
            lines.append(f"- {opp}")
        lines.append("")

    # 综合分析总结
    summary = report.get("summary", "")
    if summary:
        lines.append(T("summary"))
        lines.append("")
        lines.append(summary)
        lines.append("")

    # 各分析师详细观点
    lines.append("---")
    lines.append("")
    lines.append(T("agents_title"))
    lines.append("")

    for op in opinions:
        try:
            agent_op = AgentOpinion(**op) if isinstance(op, dict) else op
            emoji = get_stance_emoji(agent_op.stance, lang)
            lines.extend([
                f"### {agent_op.agent_name} — {emoji} ({T('confidence')}: {agent_op.confidence:.0%})",
                "",
            ])
            if agent_op.key_points:
                lines.append(T("key_points"))
                for point in agent_op.key_points:
                    lines.append(f"- {point}")
                lines.append("")
            if agent_op.risk_factors:
                lines.append(T("risk_factors"))
                for risk in agent_op.risk_factors:
                    lines.append(f"- {risk}")
                lines.append("")
            lines.append(f"{T('agent_summary')} {agent_op.summary}")
            lines.append("")
            lines.append("---")
            lines.append("")
        except Exception:
            lines.append(f"- {op}")
            lines.append("")

    # 免责声明
    lines.append("")
    lines.append(T("disclaimer"))

    return "\n".join(lines)


def generate_html_report(report: dict[str, Any], lang: str | None = None) -> str:
    """将分析报告转换为带样式的 HTML 格式"""
    md = generate_markdown_report(report, lang)
    title = get_report_text("html_title", lang)
    html_lines = [
        "<!DOCTYPE html>",
        f"<html><head><meta charset='utf-8'><title>{title}</title>",
        "<style>",
        "body { font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #1a1a2e; background: #f8f9fa; }",
        "h1 { color: #6366f1; border-bottom: 2px solid #6366f1; padding-bottom: 8px; }",
        "h2 { color: #4f46e5; } h3 { color: #374151; }",
        "table { border-collapse: collapse; width: 100%; margin: 12px 0; }",
        "th, td { border: 1px solid #dee2e6; padding: 8px 12px; text-align: left; }",
        "th { background: #f1f3f5; }",
        "hr { border: none; border-top: 1px solid #dee2e6; margin: 16px 0; }",
        "blockquote { border-left: 4px solid #6366f1; padding-left: 12px; color: #6b7280; }",
        "</style></head><body>",
    ]
    for line in md.split("\n"):
        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("---"):
            html_lines.append("<hr>")
        elif line.startswith("- "):
            html_lines.append(f"<li>{line[2:]}</li>")
        elif line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if all(c.replace("-", "") == "" for c in cells):
                continue
            html_lines.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
        elif line.startswith("*"):
            html_lines.append(f"<blockquote>{line}</blockquote>")
        elif line.strip():
            html_lines.append(f"<p>{line}</p>")
    html_lines.append("</body></html>")
    return "\n".join(html_lines)


def generate_text_report(report: dict[str, Any], lang: str | None = None) -> str:
    """将分析报告转换为纯文本格式"""
    import re
    md = generate_markdown_report(report, lang)
    text = re.sub(r'[#*_`~]', '', md)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return text
