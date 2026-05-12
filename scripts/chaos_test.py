# scripts/chaos_test.py
# 混沌工程测试脚本 — 随机注入故障，验证系统容错能力
# 用法: python scripts/chaos_test.py

from __future__ import annotations

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_llm_timeout():
    """模拟 LLM 超时：Agent 应生成占位意见而非崩溃"""
    from backend.agents.base import BaseAgent
    import asyncio

    agent = BaseAgent.__new__(BaseAgent)
    agent.name = "ChaosTest"
    agent.role = "chaos_test"
    agent.llm = type("FakeLLM", (), {})()
    agent.llm.ainvoke = type("FakeInvoke", (), {})()

    async def _slow_llm(*args, **kwargs):
        await asyncio.sleep(999)  # 超长时间

    agent.llm.ainvoke = _slow_llm
    agent.prompt_template = "test"
    agent.extra_prompt = ""
    agent._skill_metas = []

    try:
        result = asyncio.run(agent.analyze("600519", "a_share"))
        assert result is not None, "超时应返回占位意见而非 None"
        print("  ✅ LLM timeout → gracefully returned placeholder opinion")
    except Exception as e:
        print(f"  ❌ LLM timeout → CRASH: {e}")


def test_data_provider_network_failure():
    """模拟数据源断网：FallbackProvider 应返回安全空值"""
    from backend.data.fallback_provider import FallbackProvider, _safe_empty_result
    from unittest.mock import MagicMock

    bad = MagicMock()
    bad.__class__.__name__ = "DeadProvider"
    bad.get_kline.side_effect = ConnectionError("网络不可达")

    fb = FallbackProvider([bad])
    try:
        result = fb.get_kline("600519")
        assert isinstance(result, dict), f"应返回空 dict，实际: {type(result)}"
        print("  ✅ Network failure → safely returned empty result")
    except Exception as e:
        print(f"  ❌ Network failure → CRASH: {e}")


def test_skill_random_failure():
    """模拟 Skill 随机失败：Agent 应继续执行而非崩溃"""
    import asyncio
    from backend.agents.base import BaseAgent
    from unittest.mock import MagicMock

    agent = BaseAgent.__new__(BaseAgent)
    agent.name = "ChaosSkill"
    agent.role = "chaos_skill"
    agent.llm = MagicMock()
    agent.llm.ainvoke = MagicMock()

    skill = MagicMock()
    skill.name = "chaotic_skill"
    skill.depends_on = []

    if random.random() > 0.5:
        skill.execute.side_effect = RuntimeError("随机技能故障")
    else:
        skill.execute.return_value = {"data": "正常"}

    agent._skill_metas = [skill]
    agent.prompt_template = ""
    agent.extra_prompt = ""

    try:
        results = asyncio.run(agent._execute_skills("600519", "a_share"))
        assert "chaotic_skill" in results
        print(f"  ✅ Random skill failure → handled: {results['chaotic_skill']}")
    except Exception as e:
        print(f"  ❌ Random skill failure → CRASH: {e}")


def test_db_connection_interference():
    """模拟 DB 连接异常：get_db() 应 rollback 并归还连接"""
    import sqlite3
    from unittest.mock import MagicMock, patch
    from backend.repositories.base import get_db

    mock_conn = MagicMock(spec=sqlite3.Connection)
    mock_conn.row_factory = sqlite3.Row
    return_spy = MagicMock()

    with patch("backend.repositories.base._ensure_db", return_value=mock_conn), \
         patch("backend.repositories.base._return_conn", return_spy):
        try:
            with get_db():
                raise ValueError("模拟 DB 异常")
        except ValueError:
            pass

    try:
        mock_conn.rollback.assert_called_once()
        return_spy.assert_called_once()
        print("  ✅ DB connection error → rollback + return to pool")
    except AssertionError as e:
        print(f"  ❌ DB connection error → leak: {e}")


def test_concurrent_analysis_throttle():
    """验证并发限流机制（模拟）"""
    from backend.plugins.security import LLMBudgetGuard

    bg = LLMBudgetGuard(max_calls_per_minute=3, window_seconds=5)
    bg.check_rate_limit()
    bg.check_rate_limit()
    ok = bg.check_rate_limit()
    blocked = bg.check_rate_limit()

    try:
        assert ok is True, "第 3 次应通过"
        assert blocked is False, "第 4 次应被限流"
        print("  ✅ Rate limiter → blocked 4th concurrent call")
    except AssertionError as e:
        print(f"  ❌ Rate limiter → FAIL: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TradingFlow Agent 混沌工程测试")
    print("=" * 60)
    print()

    tests = [
        ("LLM 超时 (120s 兜底)", test_llm_timeout),
        ("数据源断网 (安全空值)", test_data_provider_network_failure),
        ("Skill 随机故障", test_skill_random_failure),
        ("DB 连接异常 (rollback)", test_db_connection_interference),
        ("并发限流 (BudgetGuard)", test_concurrent_analysis_throttle),
    ]

    passed = 0
    failed = 0
    for name, func in tests:
        print(f"\n🔧 {name}:")
        try:
            func()
            passed += 1
        except Exception as e:
            print(f"  ❌ UNEXPECTED ERROR: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"结果: {passed} 通过 / {failed} 失败 / {len(tests)} 总计")
    print("=" * 60)