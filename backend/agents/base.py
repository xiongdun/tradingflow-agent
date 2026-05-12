# backend/agents/base.py
# Agent 基类 — 所有分析师 Agent 的抽象基类

from __future__ import annotations

import asyncio
from abc import ABC
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from backend.skills.registry import SkillMeta, get_skills_by_names

# ─── backward-compatible re-exports ───
from backend.agents.registry import agent, _agents_registry, get_agent_class, list_all_agents  # noqa: F401
from backend.agents.models import AgentOpinion


def _get_skill_timeout() -> int:
    from backend.core.config import load_settings
    return load_settings().skill_timeout


def _get_llm_timeout() -> int:
    from backend.core.config import load_settings
    return load_settings().llm_timeout


class BaseAgent(ABC):
    """所有分析 Agent 的基类。

    子类必须定义：
    - name: Agent 显示名称
    - role: Agent 角色标识符
    - system_prompt: Agent 的人设和指令
    - default_skills: 默认技能名称列表
    """

    name: str = ""                    # 显示名称
    role: str = ""                    # 角色标识
    system_prompt: str = ""           # 系统提示词
    default_skills: list[str] = []    # 默认技能列表

    def __init__(self, llm: BaseChatModel, skills: list[str] | None = None,
                 extra_prompt: str = ""):
        self.llm = llm                                # 大模型实例
        self.skill_names = skills or self.default_skills  # 使用指定技能或默认技能
        self.extra_prompt = extra_prompt              # 额外提示词
        self._skill_metas: list[SkillMeta] = get_skills_by_names(self.skill_names)

    def _build_system_message(self, symbol: str, market: str,
                              cross_review: str = "") -> SystemMessage:
        """构建系统消息，包含 Agent 人设、可用技能和输出格式要求"""
        skill_desc = "\n".join(
            f"- {s.name}: {s.description}" for s in self._skill_metas
        )
        prompt = f"""{self.system_prompt}

你可以使用以下技能来获取数据：
{skill_desc}

当前分析的股票: {symbol} (市场: {market})

请基于你获取的数据，以你的专业视角进行分析。
你的输出必须是以下 JSON 格式：
{{
    "stance": "bullish/bearish/neutral",
    "confidence": 0.0-1.0,
    "key_points": ["论点1", "论点2", ...],
    "risk_factors": ["风险1", "风险2", ...],
    "summary": "你的分析总结"
}}

注意：你要站在自己的专业立场上给出独立观点，不要随大流。"""
        if self.extra_prompt:
            prompt += f"\n\n额外指示：{self.extra_prompt}"
        if cross_review:
            prompt += f"\n\n以下是交叉审阅员对你和其他分析师上一轮意见的审阅反馈，请参考并修正你的分析：\n{cross_review}"
        return SystemMessage(content=prompt)

    async def _execute_one_skill(self, skill_meta: SkillMeta, symbol: str, market: str,
                                  dep_results: dict[str, Any] | None = None) -> tuple[str, Any]:
        """执行单个技能，返回 (技能名, 结果)。依赖结果通过 dep_results 注入。"""
        import functools
        try:
            loop = asyncio.get_running_loop()
            extra_kwargs = {k: v for k, v in (dep_results or {}).items()
                           if k in skill_meta.depends_on}
            fn = functools.partial(skill_meta.execute, symbol=symbol, market=market, **extra_kwargs)
            data = await asyncio.wait_for(
                loop.run_in_executor(None, fn),
                timeout=_get_skill_timeout(),
            )
            return skill_meta.name, data
        except asyncio.TimeoutError:
            logger.warning(f"[{self.name}] 技能 {skill_meta.name} 执行超时 ({_get_skill_timeout()}s)")
            return skill_meta.name, {"error": f"技能执行超时 ({_get_skill_timeout()}s)"}
        except Exception as e:
            logger.warning(f"[{self.name}] 技能 {skill_meta.name} 执行异常: {e}")
            return skill_meta.name, {"error": str(e)}

    async def _execute_skills(self, symbol: str, market: str,
                               status_callback=None) -> dict[str, Any]:
        """按依赖拓扑序执行技能，无依赖的技能并行执行。

        技能函数是同步的（涉及 akshare 等阻塞 I/O），
        通过线程池并行执行避免串行等待。
        """
        results: dict[str, Any] = {}
        remaining = list(self._skill_metas)
        executed: set[str] = set()

        while remaining:
            ready = [s for s in remaining if all(d in executed for d in s.depends_on)]
            if not ready:
                logger.warning(f"[{self.name}] 检测到循环或缺失依赖，降级为串行执行")
                for s in remaining:
                    name, data = await self._execute_one_skill(s, symbol, market, results)
                    results[name] = data if data is not None else {}
                    executed.add(name)
                    if status_callback:
                        try:
                            await status_callback("skill_done", self.role, self.name, {"skill": name})
                        except Exception:
                            pass
                break

            tasks = [self._execute_one_skill(s, symbol, market, results) for s in ready]
            batch_results = await asyncio.gather(*tasks)
            for name, data in batch_results:
                results[name] = data if data is not None else {}
                executed.add(name)
                if status_callback:
                    try:
                        await status_callback("skill_done", self.role, self.name, {"skill": name})
                    except Exception:
                        pass
            remaining = [s for s in remaining if s.name not in executed]

        return results

    async def analyze(self, symbol: str, market: str,
                      cross_review: str = "", status_callback=None) -> AgentOpinion:
        """执行完整分析流程：技能收集数据 → LLM 推理 → 结构化输出"""
        # 第 1 步：通过技能获取数据
        logger.info(f"[{self.name}] 开始分析 {symbol}，执行 {len(self._skill_metas)} 个技能...")
        data = await self._execute_skills(symbol, market, status_callback=status_callback)
        logger.info(f"[{self.name}] 技能执行完成，开始 LLM 推理...")

        # 第 2 步：构建包含数据的提示词
        sys_msg = self._build_system_message(symbol, market, cross_review)
        data_text = "\n\n".join(
            f"=== {name} ===\n{_format_data(v)}" for name, v in data.items()
        )
        human_msg = HumanMessage(
            content=f"请基于以下数据分析股票 {symbol}：\n\n{data_text}"
        )

        # 第 3 步：LLM 推理（带超时）
        try:
            response = await asyncio.wait_for(
                self.llm.ainvoke([sys_msg, human_msg]),
                timeout=_get_llm_timeout(),
            )
        except asyncio.TimeoutError:
            logger.error(f"[{self.name}] LLM 推理超时 ({_get_llm_timeout()}s)")
            return AgentOpinion(
                agent_name=self.name, agent_role=self.role,
                stock=symbol, market=market,
                stance="neutral", confidence=0.0,
                key_points=["LLM 推理超时，无法生成分析结果"],
                risk_factors=["分析超时"],
                summary=f"LLM 推理超时 ({_get_llm_timeout()}s)，请检查 API 连通性或降低数据量。",
                data_evidence=data,
            )

        # 记录 Token 用量
        try:
            from backend.core.token_tracker import record_tokens, extract_token_usage
            input_tokens, output_tokens = extract_token_usage(
                getattr(response, "response_metadata", None) or getattr(response, "usage_metadata", None)
            )
            if input_tokens or output_tokens:
                record_tokens(input_tokens, output_tokens)
        except ImportError:
            pass

        logger.info(f"[{self.name}] LLM 推理完成，解析输出...")
        # 第 4 步：解析结构化输出
        opinion = _parse_opinion(response.content, self.name, self.role, symbol, market, data)
        return opinion

    async def run(self, state: dict) -> dict:
        """LangGraph 节点函数 — 异步执行分析并追加意见到状态"""
        callback = state.get("status_callback")

        # 报告 agent 开始执行
        if callback:
            try:
                await callback("running", self.role, self.name, {})
            except Exception:
                pass

        try:
            opinion = await self.analyze(
                state["symbol"], state["market"],
                cross_review=state.get("cross_review", ""),
                status_callback=callback,
            )
        except Exception as e:
            if callback:
                try:
                    await callback("error", self.role, self.name, {"message": str(e)})
                except Exception:
                    pass
            raise

        # 报告 agent 执行完成
        if callback:
            try:
                await callback("done", self.role, self.name, {})
            except Exception:
                pass

        opinion_data = opinion.model_dump()
        if "round" in state:
            opinion_data["round"] = state.get("round", 0)
        return {"opinions": [opinion_data]}


def _format_data(data: Any) -> str:
    """将数据字典格式化为 LLM 可读的文本"""
    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            if isinstance(v, (list, dict)):
                lines.append(f"{k}: {_format_data(v)}")
            else:
                lines.append(f"{k}: {v}")
        return "\n".join(lines)
    if isinstance(data, list):
        return "\n".join(f"- {item}" for item in data[:20])
    return str(data)


def _parse_opinion(content: str, agent_name: str, agent_role: str,
                   symbol: str, market: str, data: dict) -> AgentOpinion:
    """将 LLM 响应解析为 AgentOpinion 结构化对象"""
    from backend.core.parsing import parse_structured_output

    defaults = {
        "stance": "neutral",
        "confidence": 0.5,
        "key_points": [],
        "risk_factors": [],
        "summary": content[:500],
    }
    parsed = parse_structured_output(content, defaults)
    try:
        raw = parsed.get("confidence", 0.5)
        confidence_val = float(raw) if raw is not None else 0.5
    except (ValueError, TypeError):
        confidence_val = 0.5
    return AgentOpinion(
        agent_name=agent_name,
        agent_role=agent_role,
        stock=symbol,
        market=market,
        stance=parsed["stance"],
        confidence=confidence_val,
        key_points=parsed["key_points"],
        risk_factors=parsed["risk_factors"],
        summary=parsed["summary"],
        data_evidence=data,
    )
