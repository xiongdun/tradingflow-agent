# backend/plugins/workflow_engine.py
# v2 工作流引擎 — 从 JSON 定义构建 LangGraph StateGraph，支持混合节点类型
#
# v2 节点类型：
#   skill     — 调用已注册的技能函数
#   adapter   — 使用 NodeAdapter 包装外部项目
#   agent     — 包装已注册的分析 Agent（LLM + skills）
#   condition — 条件分支路由
#   loop      — 循环控制节点

from __future__ import annotations

from typing import Any, Callable

from langgraph.graph import END, START, StateGraph
from loguru import logger

from backend.graph.state import AgentState


# ──────────────────── v2 工作流定义格式 ────────────────────
#
# {
#   "version": 2,
#   "name": "混合工作流",
#   "description": "...",
#   "nodes": [
#     {"id": "data_fetch", "type": "skill", "skill": "kline_data", "params": {}},
#     {"id": "api_call",   "type": "adapter", "adapter": "my_api", "config": {}},
#     {"id": "analyst",    "type": "agent", "role": "technical", "skills": ["kline_data"]},
#     {"id": "gate",       "type": "condition", "field": "opinions", "rules": [...]},
#     {"id": "loop_node",  "type": "loop", "max_iterations": 3, "body_nodes": [...]}
#   ],
#   "edges": [
#     {"source": "START", "target": "data_fetch"},
#     {"source": "data_fetch", "target": "api_call"},
#     {"source": "api_call", "target": "analyst"},
#     {"source": "analyst", "target": "gate"},
#     {"source": "gate", "target": "summarizer", "condition": "always"},
#     {"source": "gate", "target": "analyst", "condition": "needs_more"}
#   ],
#   "summarizer_prompt": ""
# }


def build_v2_workflow(workflow_def: dict[str, Any]) -> Any:
    """从 v2 JSON 定义构建编译后的 LangGraph StateGraph。

    与 v1 的 mode-based 构建器不同，v2 通过显式的 nodes + edges
    拓扑定义工作流，支持任意混合节点类型。

    Args:
        workflow_def: v2 格式的工作流定义字典

    Returns:
        编译后的 LangGraph CompiledGraph
    """
    nodes_raw = workflow_def.get("nodes", [])
    edges_raw = workflow_def.get("edges", [])
    summarizer_prompt = workflow_def.get("summarizer_prompt", "")

    # 分类节点
    skill_nodes: list[dict] = []
    adapter_nodes: list[dict] = []
    agent_nodes: list[dict] = []
    condition_nodes: list[dict] = []
    loop_nodes: list[dict] = []

    for node_def in nodes_raw:
        ntype = node_def.get("type", "")
        if ntype == "skill":
            skill_nodes.append(node_def)
        elif ntype == "adapter":
            adapter_nodes.append(node_def)
        elif ntype == "agent":
            agent_nodes.append(node_def)
        elif ntype == "condition":
            condition_nodes.append(node_def)
        elif ntype == "loop":
            loop_nodes.append(node_def)

    # ── 构建 StateGraph ──
    builder = StateGraph(AgentState)

    # 注册所有 skill 节点
    for node_def in skill_nodes:
        node_id = node_def["id"]
        skill_name = node_def.get("skill", "")
        params = node_def.get("params", {})
        output_key = node_def.get("output_key", node_id)
        builder.add_node(node_id, _make_skill_node(skill_name, params, output_key))

    # 注册所有 adapter 节点
    for node_def in adapter_nodes:
        node_id = node_def["id"]
        adapter_type = node_def.get("adapter", "")
        config = node_def.get("config", node_def.get("adapter_config", {}))
        output_key = node_def.get("output_key", node_id)
        builder.add_node(node_id, _make_adapter_node(adapter_type, config, output_key))

    # 注册所有 agent 节点
    for node_def in agent_nodes:
        node_id = node_def["id"]
        role = node_def.get("role", "")
        skills = node_def.get("skills", [])
        extra_prompt = node_def.get("extra_prompt", "")
        agent_name = node_def.get("name", "")
        builder.add_node(node_id, _make_agent_node(role, skills, extra_prompt, agent_name))

    # 注册所有 condition 节点
    for node_def in condition_nodes:
        node_id = node_def["id"]
        builder.add_node(node_id, _make_condition_node())

    # 注册所有 loop 节点
    for node_def in loop_nodes:
        node_id = node_def["id"]
        max_iter = node_def.get("max_iterations", 3)
        builder.add_node(node_id, _make_loop_node(max_iter))

    # 注册 summarizer 节点（始终存在）
    builder.add_node("summarizer", _make_summarizer_node(summarizer_prompt))

    # ── 构建边 ──
    node_ids = {n["id"] for n in nodes_raw}
    node_ids.add("summarizer")

    # 收集 condition 节点的条件边
    condition_edges: dict[str, list[dict]] = {}
    for edge in edges_raw:
        src = edge["source"]
        if any(c["id"] == src for c in condition_nodes):
            condition_edges.setdefault(src, []).append(edge)

    # 收集 loop 节点的边
    loop_edge_map: dict[str, str] = {}
    for edge in edges_raw:
        src = edge["source"]
        if any(lo["id"] == src for lo in loop_nodes):
            loop_edge_map[src] = edge["target"]

    for edge in edges_raw:
        src = edge["source"]
        tgt = edge["target"]

        if src == "START":
            if tgt not in node_ids:
                logger.warning(f"[v2] 边引用不存在的节点: {tgt}")
                continue
            builder.add_edge(START, tgt)
            continue

        # condition 节点的边由 conditional_edges 统一处理
        if any(c["id"] == src for c in condition_nodes):
            continue
        # loop 节点的边由 conditional_edges 统一处理
        if src in loop_edge_map:
            continue

        # 普通边
        if src not in node_ids:
            logger.warning(f"[v2] 边引用不存在的源节点: {src}")
            continue
        if tgt == "END":
            builder.add_edge(src, "summarizer")
        elif tgt == "summarizer":
            builder.add_edge(src, "summarizer")
        elif tgt in node_ids:
            builder.add_edge(src, tgt)
        else:
            logger.warning(f"[v2] 边引用不存在的目标节点: {tgt}")

    # 为 condition 节点添加条件边
    for node_def in condition_nodes:
        nid = node_def["id"]
        edges_for_node = condition_edges.get(nid, [])
        if not edges_for_node:
            builder.add_edge(nid, "summarizer")
            continue
        route_map = {}
        for e in edges_for_node:
            label = e.get("condition", "default")
            route_map[label] = e["target"]
        if "default" not in route_map:
            route_map["default"] = "summarizer"
        builder.add_conditional_edges(
            nid,
            _make_condition_router(route_map),
            route_map,
        )

    # 为 loop 节点添加条件边
    for node_def in loop_nodes:
        nid = node_def["id"]
        max_iter = node_def.get("max_iterations", 3)
        loop_target = loop_edge_map.get(nid, "summarizer")
        route_map = {
            "continue": loop_target,
            "done": "summarizer",
        }
        builder.add_conditional_edges(
            nid,
            _make_loop_router(max_iter),
            route_map,
        )

    return builder.compile()


# ──────────────────── 节点工厂函数 ────────────────────

def _make_skill_node(skill_name: str, params: dict, output_key: str) -> Callable:
    """创建技能节点函数"""
    async def skill_node(state: dict) -> dict:
        from backend.skills.registry import get_skill
        from backend.core.exceptions import SkillExecutionError

        meta = get_skill(skill_name)
        if meta is None:
            raise SkillExecutionError(skill_name, f"技能未注册: {skill_name}")

        ctx = {**state.get("dynamic_data", {}), **params}
        try:
            result = meta.execute(
                symbol=state.get("symbol", ""),
                market=state.get("market", ""),
                **ctx,
            )
        except Exception as e:
            logger.error(f"[v2] 技能 {skill_name} 执行失败: {e}")
            return {"dynamic_data": {output_key: {"error": str(e)}}}

        dynamic = dict(state.get("dynamic_data", {}))
        dynamic[output_key] = result
        return {"dynamic_data": dynamic}
    return skill_node


def _make_adapter_node(adapter_type: str, config: dict, output_key: str) -> Callable:
    """创建适配器节点函数"""
    async def adapter_node(state: dict) -> dict:
        from backend.plugins.adapters.base import create_adapter

        try:
            instance = create_adapter(adapter_type, config)
        except ValueError as e:
            logger.error(f"[v2] 适配器创建失败: {e}")
            return {"dynamic_data": {output_key: {"error": str(e)}}}

        try:
            invoke_state = {**state, **state.get("dynamic_data", {})}
            result = await instance.invoke(invoke_state)
        except Exception as e:
            logger.error(f"[v2] 适配器 {adapter_type} 执行失败: {e}")
            return {"dynamic_data": {output_key: {"error": str(e)}}}

        dynamic = dict(state.get("dynamic_data", {}))
        dynamic.update(result)
        return {"dynamic_data": dynamic}
    return adapter_node


def _make_agent_node(role: str, skills: list[str], extra_prompt: str, agent_name: str) -> Callable:
    """创建 Agent 节点函数 — 包装已注册的分析 Agent"""
    async def agent_node(state: dict) -> dict:
        from backend.agents.registry import get_agent_class, get_agent_skills
        from backend.agents.generic import GenericAgent
        from backend.core.config import load_settings
        from backend.core.llm import create_llm

        cls = get_agent_class(role)
        if cls is None and role.startswith("custom_"):
            cls = GenericAgent
        if cls is None:
            logger.error(f"[v2] 未知 Agent 角色: {role}")
            return {"opinions": [{"agent_role": role, "agent_name": role,
                    "stance": "neutral", "confidence": 0,
                    "summary": f"Agent 角色未注册: {role}",
                    "round": state.get("round", 0)}]}

        settings = load_settings()
        llm = create_llm(settings)
        agent_skills = skills or get_agent_skills(role)

        if cls is GenericAgent:
            agent = cls(llm=llm, skills=agent_skills, extra_prompt=extra_prompt,
                        role=role, name=agent_name)
        else:
            agent = cls(llm=llm, skills=agent_skills, extra_prompt=extra_prompt)
        if agent_name:
            agent.name = agent_name

        return await agent.run(state)
    return agent_node


def _make_condition_node() -> Callable:
    """创建条件分支节点函数 — 条件节点本身不修改状态"""
    async def condition_node(state: dict) -> dict:
        return {}
    return condition_node


def _make_loop_node(max_iterations: int) -> Callable:
    """创建循环控制节点函数"""
    async def loop_node(state: dict) -> dict:
        counter = state.get("loop_counter", 0) + 1
        return {"loop_counter": counter}
    return loop_node


def _make_summarizer_node(summarizer_prompt: str) -> Callable:
    """创建 Summarizer 节点函数"""
    async def summarizer_node(state: dict) -> dict:
        from backend.agents.summarizer import SummarizerAgent
        from backend.core.config import load_settings
        from backend.core.llm import create_llm

        settings = load_settings()
        llm = create_llm(settings)
        summarizer = SummarizerAgent(llm=llm, extra_prompt=summarizer_prompt)
        return await summarizer.run(state)
    return summarizer_node


# ──────────────────── 路由函数 ────────────────────

def _make_condition_router(route_map: dict[str, str]) -> Callable:
    """为 condition 节点创建路由函数

    内置条件标签：
      has_bearish     — opinions 中存在看空意见
      has_bullish     — opinions 中存在看多意见
      high_confidence — 平均置信度 > 0.7
      low_confidence  — 平均置信度 < 0.4
      has_error       — 有 Agent 报错
      dynamic:<key>   — dynamic_data 中指定 key 有值
      always          — 默认路由（兜底）
    """
    def router(state: dict) -> str:
        opinions = state.get("opinions", [])
        dynamic = state.get("dynamic_data", {})

        for label, target in route_map.items():
            if label in ("always", "default"):
                continue
            if label == "has_bearish":
                for op in opinions:
                    if op.get("stance") in ("bearish", "strong_bearish"):
                        return target
            elif label == "has_bullish":
                for op in opinions:
                    if op.get("stance") in ("bullish", "strong_bullish"):
                        return target
            elif label == "high_confidence":
                avg = sum(op.get("confidence", 0) for op in opinions) / max(len(opinions), 1)
                if avg > 0.7:
                    return target
            elif label == "low_confidence":
                avg = sum(op.get("confidence", 0) for op in opinions) / max(len(opinions), 1)
                if avg < 0.4:
                    return target
            elif label.startswith("has_error"):
                if any(op.get("error") for op in opinions):
                    return target
            elif label.startswith("dynamic:"):
                key = label.split(":", 1)[1]
                if dynamic.get(key):
                    return target

        return route_map.get("default", route_map.get("always", "summarizer"))
    return router


def _make_loop_router(max_iterations: int) -> Callable:
    """为 loop 节点创建路由函数"""
    def router(state: dict) -> str:
        counter = state.get("loop_counter", 0)
        if counter >= max_iterations:
            return "done"
        return "continue"
    return router


# ──────────────────── v2 校验 ────────────────────

def validate_v2_workflow(workflow_def: dict[str, Any]) -> list[str]:
    """校验 v2 工作流定义的合法性，返回错误列表。"""
    errors: list[str] = []
    nodes_raw = workflow_def.get("nodes", [])
    edges_raw = workflow_def.get("edges", [])

    node_ids: set[str] = set()
    seen_ids: dict[str, int] = {}

    for node_def in nodes_raw:
        nid = node_def.get("id", "")
        ntype = node_def.get("type", "")

        if not nid:
            errors.append("节点缺少 id 字段")
            continue
        seen_ids[nid] = seen_ids.get(nid, 0) + 1
        if seen_ids[nid] > 1:
            errors.append(f"重复的节点 id: {nid}")
        node_ids.add(nid)

        valid_types = {"skill", "adapter", "agent", "condition", "loop"}
        if ntype not in valid_types:
            errors.append(f"节点 {nid} 的类型无效: {ntype}，可选: {', '.join(valid_types)}")
            continue

        if ntype == "skill" and not node_def.get("skill"):
            errors.append(f"skill 节点 {nid} 缺少 skill 字段")
        if ntype == "adapter" and not node_def.get("adapter"):
            errors.append(f"adapter 节点 {nid} 缺少 adapter 字段")
        if ntype == "agent" and not node_def.get("role"):
            errors.append(f"agent 节点 {nid} 缺少 role 字段")

    # 校验边引用
    referrable = node_ids | {"START", "END", "summarizer"}
    for edge in edges_raw:
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        if src not in referrable:
            errors.append(f"边引用了不存在的源节点: {src}")
        if tgt not in referrable:
            errors.append(f"边引用了不存在的目标节点: {tgt}")

    # 校验必须有 START 出边
    if not any(e["source"] == "START" for e in edges_raw):
        errors.append("缺少从 START 出发的边")

    # 校验至少有一个节点连接到 summarizer/END，
    # 或者存在 loop 节点（隐式路由到 summarizer）
    has_end_edge = any(e["target"] in ("END", "summarizer") for e in edges_raw)
    has_loop = any(n.get("type") == "loop" for n in nodes_raw)
    if not has_end_edge and not has_loop:
        errors.append("没有节点连接到 END 或 summarizer")

    return errors
