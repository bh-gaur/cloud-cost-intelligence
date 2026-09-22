"""
Tests for Authentication and RBAC
"""

import pytest
from app.auth.security import hash_password, verify_password, create_access_token, decode_token


def test_password_hashing():
    raw_password = "SuperSecurePassword123!"
    hashed = hash_password(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_lifecycle():
    token = create_access_token(subject="user-123", role="ADMIN")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "ADMIN"
    assert payload["type"] == "access"


def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


def test_login_invalid_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "InvalidPassword"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


def test_get_current_user(client, admin_headers):
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "admin@test.local"
    assert data["data"]["role"] == "ADMIN"

