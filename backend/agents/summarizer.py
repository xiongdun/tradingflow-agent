# backend/agents/summarizer.py
# 总结研判 Agent — 综合所有分析师意见，生成最终投资报告

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from backend.agents.base import AgentOpinion, BaseAgent
from backend.agents.registry import agent


class FinalReport(BaseModel):
    """最终综合分析报告"""
    stock: str                        # 股票代码
    market: str                       # 市场类型
    overall_stance: str               # 整体立场：bullish/bearish/neutral
    overall_confidence: float         # 整体置信度：0.0 ~ 1.0
    consensus_points: list[str]       # 分析师共识观点
    disagreement_points: list[str]    # 分析师分歧观点
    key_risks: list[str]              # 关键风险
    opportunities: list[str]          # 投资机会
    action_suggestion: str            # 投资建议：buy/sell/hold/watch
    summary: str                      # 综合分析总结
    agent_opinions: list[dict[str, Any]]  # 各分析师原始意见


@agent(
    "总结研判分析师", "summarizer", [],
    "综合所有分析师意见，生成最终投资研判报告。"
)
class SummarizerAgent(BaseAgent):
    """综合研判 Agent — 充当投资委员会主席，权衡各方观点并给出结论"""

    name = "总结研判分析师"
    role = "summarizer"
    default_skills: list[str] = []
    system_prompt = ""

    def __init__(self, llm: BaseChatModel, extra_prompt: str = ""):
        super().__init__(llm=llm, skills=[], extra_prompt=extra_prompt)

    async def summarize(self, symbol: str, market: str,
                        opinions: list[dict[str, Any]]) -> FinalReport:
        """综合所有分析师意见，生成最终报告"""
        system_prompt = """你是投资委员会的主席，负责综合各位分析师的意见，给出最终的投资研判。

你的职责：
1. **客观汇总**：准确理解每位分析师的立场和核心论点
2. **识别共识**：找出多数分析师认同的观点（这些通常更可靠）
3. **正视分歧**：明确列出不同分析师之间的分歧点
4. **权衡利弊**：综合考虑机会和风险
5. **果断决策**：给出明确的投资建议（买入/卖出/持有/观望）

注意事项：
- 不要简单地取"多数票"，要分析分歧的深层原因
- 当技术面和基本面矛盾时，长期看基本面更重要，短期看技术面更有效
- 情绪面和新闻面往往是短期催化剂，基本面才是长期决定因素
- 你要有自己的独立判断，不只是做一个汇总者

输出 JSON 格式：
{
    "overall_stance": "bullish/bearish/neutral",
    "overall_confidence": 0.0-1.0,
    "consensus_points": ["共识1", ...],
    "disagreement_points": ["分歧1", ...],
    "key_risks": ["风险1", ...],
    "opportunities": ["机会1", ...],
    "action_suggestion": "buy/sell/hold/watch",
    "summary": "完整的分析总结报告"
}"""
        if self.extra_prompt:
            system_prompt += f"\n\n额外指示：{self.extra_prompt}"

        # 格式化各分析师意见为文本
        opinions_text = ""
        for op in opinions:
            agent_op = AgentOpinion(**op) if isinstance(op, dict) else op
            opinions_text += f"""
### {agent_op.agent_name} ({agent_op.agent_role})
- **立场**: {agent_op.stance} | **置信度**: {agent_op.confidence}
- **核心论点**: {', '.join(agent_op.key_points)}
- **风险提示**: {', '.join(agent_op.risk_factors)}
- **总结**: {agent_op.summary}
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""以下是各位分析师对 {symbol} ({market}) 的分析意见：

{opinions_text}

请综合以上所有分析师的意见，给出你的最终研判报告。"""),
        ]

        response = await self.llm.ainvoke(messages)
        report = _parse_report(response.content, symbol, market, opinions)
        return report

    async def run(self, state: dict) -> dict:
        """LangGraph 节点函数 — 异步执行综合研判"""
        report = await self.summarize(state["symbol"], state["market"], state.get("opinions", []))
        return {"final_report": report.model_dump()}


def _parse_report(content: str, symbol: str, market: str,
                  opinions: list[dict]) -> FinalReport:
    """将 LLM 响应解析为 FinalReport 结构化对象"""
    from backend.core.parsing import parse_structured_output

    defaults = {
        "overall_stance": "neutral",
        "overall_confidence": 0.5,
        "consensus_points": [],
        "disagreement_points": [],
        "key_risks": [],
        "opportunities": [],
        "action_suggestion": "hold",
        "summary": content[:1000],
    }
    parsed = parse_structured_output(content, defaults)
    return FinalReport(
        stock=symbol,
        market=market,
        overall_stance=parsed["overall_stance"],
        overall_confidence=float(parsed["overall_confidence"]),
        consensus_points=parsed["consensus_points"],
        disagreement_points=parsed["disagreement_points"],
        key_risks=parsed["key_risks"],
        opportunities=parsed["opportunities"],
        action_suggestion=parsed["action_suggestion"],
        summary=parsed["summary"],
        agent_opinions=opinions,
    )
