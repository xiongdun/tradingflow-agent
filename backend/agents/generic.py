# backend/agents/generic.py
# 通用 Agent — 支持用户自定义角色的通用分析师

from __future__ import annotations

from backend.agents.base import BaseAgent


class GenericAgent(BaseAgent):
    """通用分析师 — 支持任意自定义角色名称，使用通用分析框架"""

    default_skills = ["stock_info", "kline_data"]  # 默认使用基础数据技能

    def __init__(self, llm, skills=None, extra_prompt="", role: str = "custom", name: str = ""):
        self.role = role
        self.name = name or f"{role}分析师"
        self.system_prompt = f"""你是一位专业的股票分析师，角色定位为「{self.name}」。

你的分析框架：
1. 基于你被分配的数据技能获取相关信息
2. 从你的专业视角出发，独立思考，给出独到见解
3. 关注数据中的异常值和关键趋势
4. 结合市场环境给出可操作的建议

你的立场：独立判断，不随大流，注重数据支撑。"""
        super().__init__(llm=llm, skills=skills, extra_prompt=extra_prompt)
