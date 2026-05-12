# tests/test_analysis_api.py
# API 端点错误状态码测试 — 验证分析端点 HTTP 状态码

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.skipif(
    False,
    reason="",
)


@pytest.fixture(scope="module")
def client():
    """创建 FastAPI TestClient"""
    from backend.main import app
    from fastapi.testclient import TestClient
    import backend.core.discovery
    backend.core.discovery.auto_discover()
    with TestClient(app) as c:
        yield c


class TestAnalysisAPIStatusCodes:

    def test_workflow_not_found_returns_404(self, client):
        resp = client.post("/api/analyze", json={
            "symbol": "600519",
            "workflow": "definitely_nonexistent_12345",
        })
        assert resp.status_code == 404
        assert "definitely_nonexistent_12345" in resp.json()["error"]

    def test_analysis_failure_returns_500(self, client):
        with patch("backend.core.analysis_service.AnalysisService.run_and_save",
                   side_effect=RuntimeError("LLM 调用失败")):
            resp = client.post("/api/analyze", json={
                "symbol": "600519",
                "workflow": "deep_analysis",
            })
            assert resp.status_code == 500
            assert resp.json()["status"] == "error"

    def test_analysis_success_returns_200(self, client):
        mock_result = {"report": {"overall_stance": "bullish"}, "markdown": "# R", "opinions": []}
        with patch("backend.core.analysis_service.AnalysisService.run_and_save",
                   new_callable=AsyncMock, return_value=mock_result), \
             patch("backend.core.analysis_service.AnalysisService.load_workflow",
                   return_value={"name": "deep_analysis", "mode": "parallel",
                                 "agents": [{"role": "fundamental"}]}):
            resp = client.post("/api/analyze", json={"symbol": "600519"})
            assert resp.status_code == 200
            assert resp.json()["status"] == "completed"


class TestHealthEndpoint:

    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_config(self, client):
        resp = client.get("/api/config")
        assert resp.status_code == 200
        assert "llm_provider" in resp.json()