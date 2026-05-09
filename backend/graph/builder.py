# backend/graph/builder.py
# 工作流构建器 Facade — 根据模式分发到对应的 Strategy 构建器
from __future__ import annotations
import hashlib
import json
from typing import Any

# Cache for compiled graphs — keyed by definition hash
_compile_cache: dict[str, Any] = {}
_COMPILE_CACHE_MAX = 50


def build_parallel_workflow(*args, **kwargs) -> Any:
    from backend.graph.builders.parallel import build_parallel_workflow as _build
    return _build(*args, **kwargs)


def validate_workflow_def(workflow_def: dict[str, Any]) -> list[str]:
    """校验工作流定义的完整性，返回错误列表（空列表表示通过）。

    检查项：
    - version 是否支持
    - mode 是否合法
    - agents 列表中 role 是否已注册
    - skills 是否存在
    """
    from backend.agents.registry import get_agent_class
    from backend.skills.registry import get_skill
    from backend.agents.generic import GenericAgent

    errors: list[str] = []

    version = workflow_def.get("version")
    if version is not None and version > 1:
        errors.append(f"不支持的工作流模板版本: {version}（当前仅支持 version 1）")

    mode = workflow_def.get("mode", "parallel")
    valid_modes = {"parallel", "conditional", "multi_round", "adaptive"}
    if mode not in valid_modes:
        errors.append(f"未知的工作流模式: {mode}，可选: {', '.join(valid_modes)}")

    agents_raw = workflow_def.get("agents", [])
    for agent_def in agents_raw:
        role = agent_def.get("role", "") if isinstance(agent_def, dict) else agent_def
        if not role:
            errors.append("Agent 定义缺少 role 字段")
            continue
        cls = get_agent_class(role)
        if cls is None and isinstance(role, str) and role.startswith("custom_"):
            cls = GenericAgent
        if cls is None:
            errors.append(f"未知的 Agent 角色: {role}")
        elif cls is not GenericAgent:
            # GenericAgent 接受任意 role，只校验已注册 Agent 的 skills
            skills = agent_def.get("skills", []) if isinstance(agent_def, dict) else []
            for skill_name in skills:
                if get_skill(skill_name) is None:
                    errors.append(f"Agent '{role}' 引用了未知技能: {skill_name}")

    if mode == "conditional":
        for i, stage in enumerate(workflow_def.get("stages", [])):
            if "agents" not in stage:
                errors.append(f"条件阶段 {i} 缺少 agents 字段")
                continue
            for role in stage.get("agents", []):
                cls = get_agent_class(role)
                if cls is None and isinstance(role, str) and role.startswith("custom_"):
                    cls = GenericAgent
                if cls is None:
                    errors.append(f"条件阶段 {i} 引用了未知 Agent 角色: {role}")

    if mode == "multi_round":
        rounds = workflow_def.get("rounds", 2)
        if not isinstance(rounds, int) or rounds < 1:
            errors.append(f"multi_round 模式的 rounds 参数必须为正整数，当前值: {rounds}")

    return errors


def build_from_json(workflow_def: dict[str, Any]) -> Any:
    """从 JSON 工作流定义构建执行图。

    支持三种模式：
    - parallel（默认）：所有分析师并行执行
    - conditional：按阶段条件执行
    - multi_round：多轮迭代交叉审阅
    - adaptive：根据股票特征动态选择分析师
    """
    from backend.core.exceptions import WorkflowBuildError

    errors = validate_workflow_def(workflow_def)
    if errors:
        raise WorkflowBuildError("工作流定义校验失败:\n" + "\n".join(f"  - {e}" for e in errors))

    # Cache lookup — use JSON-stable hash of the definition
    cache_key = hashlib.md5(
        json.dumps(workflow_def, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    if cache_key in _compile_cache:
        return _compile_cache[cache_key]

    mode = workflow_def.get("mode", "parallel")
    summarizer_prompt = workflow_def.get("summarizer_prompt", "")

    # 条件分支模式
    if mode == "conditional":
        from backend.graph.builders.conditional import build_conditional_workflow
        graph = build_conditional_workflow(
            stages=workflow_def.get("stages", []),
            summarizer_prompt=summarizer_prompt,
        )
    # 多轮迭代模式
    elif mode == "multi_round":
        from backend.graph.builders.multi_round import build_multi_round_workflow
        agents_raw = workflow_def.get("agents", [])
        agent_roles = agents_raw if (agents_raw and isinstance(agents_raw[0], str)) else [a["role"] for a in agents_raw]
        graph = build_multi_round_workflow(
            agent_roles=agent_roles,
            rounds=workflow_def.get("rounds", 2),
            summarizer_prompt=summarizer_prompt,
        )
    # 自适应模式
    elif mode == "adaptive":
        from backend.graph.builders.adaptive import build_adaptive_workflow
        graph = build_adaptive_workflow(summarizer_prompt=summarizer_prompt)
    # 并行模式（默认）
    else:
        from backend.graph.builders.parallel import build_parallel_workflow as _parallel
        agents_raw = workflow_def.get("agents", [])
        graph = _parallel(
            agent_roles=[a["role"] for a in agents_raw],
            extra_prompts={a["role"]: a.get("extra_prompt", "") for a in agents_raw if a.get("extra_prompt")},
            summarizer_prompt=summarizer_prompt,
            agent_skills={a["role"]: a["skills"] for a in agents_raw if a.get("skills")} or None,
            agent_names={a["role"]: a["name"] for a in agents_raw if a.get("name")} or None,
            system_prompts={a["role"]: a["system_prompt"] for a in agents_raw if a.get("system_prompt")} or None,
        )

    # Store in cache with size limit
    if len(_compile_cache) >= _COMPILE_CACHE_MAX:
        _compile_cache.pop(next(iter(_compile_cache)))
    _compile_cache[cache_key] = graph
    return graph
