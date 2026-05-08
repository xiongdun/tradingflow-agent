# backend/graph/state.py
# 图状态定义 — LangGraph 工作流中各节点共享的状态结构

from __future__ import annotations

from typing import Annotated, Any

from typing_extensions import TypedDict


def merge_opinions(existing: list, new: list) -> list:
    """归并函数：将新的分析师意见追加到已有列表中，按 agent_role 去重。

    LangGraph 使用此函数作为 opinions 字段的 reducer，
    确保多个并行分析师节点可以安全地同时写入意见而不会互相覆盖。
    """
    combined = existing + new
    seen = set()
    deduped = []
    for op in combined:
        # 优先使用 agent_role 作为去重键，降级到 agent_name
        role_key = op.get("agent_role", "") or op.get("agent_name", id(op))
        round_no = op.get("round")
        key = (role_key, round_no) if round_no is not None else role_key
        if key not in seen:
            seen.add(key)
            deduped.append(op)
    return deduped


class AgentState(TypedDict):
    """分析图中所有节点共享的全局状态

    - symbol/market: 待分析的股票和市场
    - opinions: 各分析师的意见列表（通过 merge_opinions 归并）
    - final_report: 总结分析师生成的最终报告
    - workflow_name/status/error: 工作流元数据
    - round: 当前迭代轮次（多轮模式使用）
    - selected_agents: 自适应模式选中的 Agent 列表
    """
    symbol: str                         # 股票代码
    market: str                         # 市场类型
    opinions: Annotated[list[dict[str, Any]], merge_opinions]  # 分析师意见（自动去重归并）
    final_report: dict[str, Any] | None  # 最终分析报告
    workflow_name: str                   # 工作流名称
    status: str                          # 运行状态："running" / "completed" / "error"
    error: str | None                    # 错误信息
    round: int                           # 当前迭代轮次（多轮模式，默认 0）
    selected_agents: list[str]           # 自适应模式选中的 Agent 角色列表
    status_callback: Any                 # 可选异步回调 (status, role, name, extra) -> None
