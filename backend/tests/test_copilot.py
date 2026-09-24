"""
Tests for FinOps AI Copilot & Optimization Advisor
"""

import pytest
from fastapi.testclient import TestClient


def test_copilot_insights_endpoint(client: TestClient, admin_headers: dict):
    """Verifies that the FinOps Copilot insights endpoint returns valid health scores and telemetry."""
    response = client.get("/api/v1/copilot/insights?account_id=all", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]

    assert "health_score" in data
    assert "total_monthly_spend" in data
    assert "potential_monthly_savings" in data
    assert "executive_summary" in data
    assert isinstance(data["top_opportunities"], list)
    assert isinstance(data["anomalies"], list)
    assert isinstance(data["quick_wins"], list)
    assert 0 <= data["health_score"] <= 100


def test_copilot_chat_endpoint(client: TestClient, admin_headers: dict):
    """Verifies that the FinOps Copilot chat answers conversational questions with actionable insights."""
    queries = [
        "Why did our cloud costs spike?",
        "Show me instant quick wins to save money",
        "How can we reduce our AWS spending?",
        "Check tagging compliance across our infrastructure",
        "Give me an executive summary of our cloud costs",
    ]

    for q in queries:
        response = client.post(
            "/api/v1/copilot/chat",
            headers=admin_headers,
            json={"query": q, "account_id": "all"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "reply" in data
        assert len(data["reply"]) > 20
        assert "suggested_actions" in data
        assert isinstance(data["suggested_actions"], list)

