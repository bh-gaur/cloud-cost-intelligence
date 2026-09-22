"""
End-to-End API Router Tests
"""

import pytest


def test_health_endpoints(client):
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json()["data"]["status"] == "healthy"

    r1_v1 = client.get("/api/v1/health")
    assert r1_v1.status_code == 200
    assert r1_v1.json()["data"]["status"] == "healthy"

    r2 = client.get("/health/db")
    assert r2.status_code == 200
    assert r2.json()["data"]["database"] == "connected"

    r3 = client.get("/health/aws")
    assert r3.status_code == 200
    assert r3.json()["data"]["is_ready"] is True


def test_dashboard_summary_api(client, user_headers):
    response = client.get("/api/v1/dashboard/summary", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "today_cost" in data["data"]
    assert "today_vs_yesterday" in data["data"]


def test_dashboard_kpis_api(client, user_headers):
    response = client.get("/api/v1/dashboard/kpis", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_monthly_spend" in data["data"]


def test_costs_table_api(client, user_headers):
    response = client.get("/api/v1/costs?page=1&page_size=10", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) <= 10
    assert data["meta"]["page"] == 1


def test_services_api(client, user_headers):
    response = client.get("/api/v1/services", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_accounts_api(client, user_headers):
    response = client.get("/api/v1/accounts", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_regions_api(client, user_headers):
    response = client.get("/api/v1/regions", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_optimization_api(client, user_headers):
    response = client.get("/api/v1/optimization/recommendations", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) > 0


def test_alerts_api(client, user_headers):
    response = client.get("/api/v1/alerts/budgets", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_dashboard_custom_date_trends_api(client, user_headers):
    response = client.get(
        "/api/v1/dashboard/trends?range=custom&start_date=2026-08-15&end_date=2026-09-01",
        headers=user_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "CUSTOM (2026-08-15 to 2026-09-01)" in data["data"]["range_label"]
    assert len(data["data"]["points"]) > 0

