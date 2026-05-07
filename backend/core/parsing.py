# backend/core/parsing.py
# 公共 JSON 解析工具 — 从 LLM 响应中提取结构化 JSON，含降级处理

from __future__ import annotations

import json
import re
from typing import Any


def extract_json(text: str) -> dict[str, Any] | None:
    """从 LLM 响应文本中提取第一个 JSON 对象。

    尝试策略：regex 匹配 {...} → json.loads → 降级返回 None
    """
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except (json.JSONDecodeError, ValueError):
        return None


def parse_structured_output(text: str, defaults: dict[str, Any]) -> dict[str, Any]:
    """从 LLM 响应中提取 JSON 并与默认值合并。

    Args:
        text: LLM 原始响应文本
        defaults: 各字段的默认值，如 {"stance": "neutral", "confidence": 0.5, ...}

    Returns:
        提取成功则用提取值覆盖 defaults，失败则用 text 填充 summary 字段
    """
    parsed = extract_json(text)
    if parsed is not None:
        result = dict(defaults)
        for key in defaults:
            if key in parsed:
                result[key] = parsed[key]
        return result

    # 降级：无法解析 JSON，用原始文本填充
    result = dict(defaults)
    if "summary" in result:
        result["summary"] = text[:1000]
    if "key_points" in result:
        result["key_points"] = [text[:200]]
    return result
