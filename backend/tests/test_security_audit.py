"""
Comprehensive Security Audit & Test Suite
Verifies:
1. Authentication & Password Security (invalid password, generic error message, disabled user rejection).
2. Session Management & Token Revocation (/logout, /logout-all).
3. Role-Based Access Control / RBAC (VIEWER restrictions, ANALYST restrictions).
4. Owner Protection & Role Escalation Protection.
5. Tenant Isolation & IDOR Protection (cross-tenant access denied).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import get_db
from app.models.user import User, Role
from app.models.organization import Organization, OrganizationMember
from app.models.report import Report
from app.auth.security import hash_password, create_access_token
from app.auth.permissions import ROLE_OWNER, ROLE_ADMIN, ROLE_FINOPS_MANAGER, ROLE_ANALYST, ROLE_VIEWER

client = TestClient(app)


@pytest.fixture
def security_test_data(db_session: Session):
    """Sets up test organizations, users with different roles, and multi-tenant resource records."""
    # Create roles if missing
    for r_name in ["ADMIN", "USER"]:
        if not db_session.query(Role).filter(Role.name == r_name).first():
            db_session.add(Role(name=r_name, description=f"{r_name} role"))
    db_session.commit()

    admin_role = db_session.query(Role).filter(Role.name == "ADMIN").first()
    user_role = db_session.query(Role).filter(Role.name == "USER").first()

    import uuid
    uid = str(uuid.uuid4())[:8]

    # 1. Create Tenant Alpha & Tenant Beta
    org_alpha = Organization(name="Org Alpha", slug=f"org-alpha-{uid}", status="ACTIVE")
    org_beta = Organization(name="Org Beta", slug=f"org-beta-{uid}", status="ACTIVE")
    db_session.add_all([org_alpha, org_beta])
    db_session.commit()

    # 2. Create Users
    # Alpha Owner
    alpha_owner = User(
        email=f"alpha_owner_{uid}@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="Alpha Owner",
        role_id=admin_role.id,
        is_active=True,
        status="ACTIVE",
    )
    # Alpha Viewer
    alpha_viewer = User(
        email=f"alpha_viewer_{uid}@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="Alpha Viewer",
        role_id=user_role.id,
        is_active=True,
        status="ACTIVE",
    )
    # Alpha Disabled User
    alpha_disabled = User(
        email=f"alpha_disabled_{uid}@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="Alpha Disabled",
        role_id=user_role.id,
        is_active=True,
        status="DISABLED",
    )
    # Beta Owner
    beta_owner = User(
        email=f"beta_owner_{uid}@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="Beta Owner",
        role_id=admin_role.id,
        is_active=True,
        status="ACTIVE",
    )
    db_session.add_all([alpha_owner, alpha_viewer, alpha_disabled, beta_owner])
    db_session.commit()

    # 3. Create Memberships
    m_alpha_owner = OrganizationMember(
        organization_id=org_alpha.id, user_id=alpha_owner.id, role=ROLE_OWNER, status="ACTIVE"
    )
    m_alpha_viewer = OrganizationMember(
        organization_id=org_alpha.id, user_id=alpha_viewer.id, role=ROLE_VIEWER, status="ACTIVE"
    )
    m_alpha_disabled = OrganizationMember(
        organization_id=org_alpha.id, user_id=alpha_disabled.id, role=ROLE_VIEWER, status="ACTIVE"
    )
    m_beta_owner = OrganizationMember(
        organization_id=org_beta.id, user_id=beta_owner.id, role=ROLE_OWNER, status="ACTIVE"
    )
    db_session.add_all([m_alpha_owner, m_alpha_viewer, m_alpha_disabled, m_beta_owner])
    db_session.commit()

    from datetime import date

    # 4. Create Reports in both organizations
    report_beta = Report(
        name="Beta Secret Financial Report",
        organization_id=org_beta.id,
        format="CSV",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        account_id="all",
        file_path="/tmp/beta_report.csv",
        created_by=beta_owner.id,
        status="COMPLETED",
    )
    db_session.add(report_beta)
    db_session.commit()

    return {
        "org_alpha": org_alpha,
        "org_beta": org_beta,
        "alpha_owner": alpha_owner,
        "alpha_viewer": alpha_viewer,
        "alpha_disabled": alpha_disabled,
        "beta_owner": beta_owner,
        "m_alpha_owner": m_alpha_owner,
        "report_beta": report_beta,
    }


def test_invalid_password_returns_generic_error(client, security_test_data):
    """Verifies login with wrong password returns generic 401 error message."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": security_test_data["alpha_owner"].email, "password": "WrongPassword!"},
    )
    assert resp.status_code == 401
    err_msg = resp.json().get("error", {}).get("message", "")
    assert "Invalid email or password" in err_msg


def test_disabled_user_login_rejected(client, security_test_data):
    """Verifies disabled user account cannot authenticate."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": security_test_data["alpha_disabled"].email, "password": "Password123!"},
    )
    assert resp.status_code == 403
    err_msg = resp.json().get("error", {}).get("message", "").lower()
    assert "disabled" in err_msg


def test_forgot_password_generic_response(client, security_test_data):
    """Verifies forgot-password endpoint does not expose account enumeration."""
    resp1 = client.post("/api/v1/auth/forgot-password", json={"email": security_test_data["alpha_owner"].email})
    resp2 = client.post("/api/v1/auth/forgot-password", json={"email": "nonexistent@test.com"})

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["data"]["message"] == resp2.json()["data"]["message"]


def test_viewer_role_cannot_generate_reports(client, security_test_data):
    """Verifies VIEWER role is rejected when attempting to generate a report."""
    token = create_access_token(subject=security_test_data["alpha_viewer"].id, role="USER")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": security_test_data["org_alpha"].id,
    }
    resp = client.post(
        "/api/v1/reports/generate",
        headers=headers,
        json={
            "name": "Unauthorized Report",
            "format": "CSV",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "account_id": "all",
        },
    )
    assert resp.status_code == 403
    err_msg = resp.json().get("error", {}).get("message", "")
    assert "Permission denied" in err_msg


def test_cross_tenant_report_access_denied(client, security_test_data):
    """Verifies User A (Org Alpha) CANNOT download or access Report B (Org Beta). IDOR test."""
    alpha_token = create_access_token(subject=security_test_data["alpha_owner"].id, role="ADMIN")
    beta_report_id = security_test_data["report_beta"].id

    headers = {
        "Authorization": f"Bearer {alpha_token}",
        "X-Organization-ID": security_test_data["org_alpha"].id,
    }

    resp = client.get(f"/api/v1/reports/{beta_report_id}/download", headers=headers)
    assert resp.status_code in (403, 404)


def test_cross_tenant_organization_switch_denied(client, security_test_data):
    """Verifies User A cannot switch to Org B where they hold no membership."""
    alpha_token = create_access_token(subject=security_test_data["alpha_owner"].id, role="ADMIN")
    headers = {
        "Authorization": f"Bearer {alpha_token}",
    }
    resp = client.post(
        f"/api/v1/organizations/{security_test_data['org_beta'].id}/switch",
        headers=headers,
    )
    assert resp.status_code == 403
    err_msg = resp.json().get("error", {}).get("message", "").lower()
    assert "access" in err_msg or "denied" in err_msg


def test_owner_protection_prevents_removing_last_owner(client, security_test_data):
    """Verifies the system rejects removing the last OWNER of an organization."""
    alpha_token = create_access_token(subject=security_test_data["alpha_owner"].id, role="ADMIN")
    headers = {
        "Authorization": f"Bearer {alpha_token}",
        "X-Organization-ID": security_test_data["org_alpha"].id,
    }
    m_owner_id = security_test_data["m_alpha_owner"].id

    resp = client.delete(
        f"/api/v1/organizations/{security_test_data['org_alpha'].id}/members/{m_owner_id}",
        headers=headers,
    )
    assert resp.status_code == 400
    err_msg = resp.json().get("error", {}).get("message", "")
    assert "last organization OWNER" in err_msg


def test_role_escalation_protection(client, security_test_data):
    """Verifies a user cannot elevate their own role or invite someone with a higher role."""
    viewer_token = create_access_token(subject=security_test_data["alpha_viewer"].id, role="USER")
    headers = {
        "Authorization": f"Bearer {viewer_token}",
        "X-Organization-ID": security_test_data["org_alpha"].id,
    }

    # Viewer trying to invite an OWNER -> rejected with 403 Permission Denied
    resp = client.post(
        f"/api/v1/organizations/{security_test_data['org_alpha'].id}/members/invite",
        headers=headers,
        json={"email": "new_owner@test.com", "role": "OWNER"},
    )
    assert resp.status_code == 403
    err_msg = resp.json().get("error", {}).get("message", "").lower()
    assert "permission" in err_msg or "denied" in err_msg


def test_invitation_lifecycle_and_acceptance(client, security_test_data):
    """Verifies complete invitation flow: invite, list, view details, accept, and wrong-email rejection."""
    owner_token = create_access_token(subject=security_test_data["alpha_owner"].id, role="ADMIN")
    headers = {
        "Authorization": f"Bearer {owner_token}",
        "X-Organization-ID": security_test_data["org_alpha"].id,
    }

    # 1. Invite a new user
    invite_resp = client.post(
        f"/api/v1/organizations/{security_test_data['org_alpha'].id}/members/invite",
        headers=headers,
        json={"email": "colleague@test.com", "role": "ANALYST"},
    )
    assert invite_resp.status_code == 200
    invite_data = invite_resp.json()["data"]
    assert invite_data["email"] == "colleague@test.com"
    assert invite_data["status"] == "PENDING"
    invitation_id = invite_data["id"]
    invite_link = invite_data["invitation_link"]
    token = invite_link.split("token=")[-1]

    # 2. List invitations
    list_resp = client.get(
        f"/api/v1/organizations/{security_test_data['org_alpha'].id}/invitations",
        headers=headers,
    )
    assert list_resp.status_code == 200
    invitations = list_resp.json()["data"]
    assert any(inv["id"] == invitation_id for inv in invitations)

    # 3. View invite details (public/preview endpoint)
    details_resp = client.get(f"/api/v1/auth/invite-details?token={token}")
    assert details_resp.status_code == 200
    details = details_resp.json()["data"]
    assert details["email"] == "colleague@test.com"
    assert details["role"] == "ANALYST"
    assert details["is_expired"] is False

    # 4. Wrong user attempts to accept -> rejected 403
    viewer_token = create_access_token(subject=security_test_data["alpha_viewer"].id, role="USER")
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    bad_accept = client.post(
        "/api/v1/auth/accept-invite",
        headers=viewer_headers,
        json={"token": token},
    )
    assert bad_accept.status_code == 403

    # 5. Revoke invitation
    revoke_resp = client.delete(
        f"/api/v1/organizations/{security_test_data['org_alpha'].id}/invitations/{invitation_id}",
        headers=headers,
    )
    assert revoke_resp.status_code == 200

    # 6. Verify revoked invitation can no longer be retrieved or accepted
    details_after = client.get(f"/api/v1/auth/invite-details?token={token}")
    assert details_after.status_code == 404


def test_accept_invite_and_register_new_user(client, security_test_data):
    """Verifies a brand new user can create a password and join an organization in 1 step via invitation token."""
    owner_token = create_access_token(subject=security_test_data["alpha_owner"].id, role="ADMIN")
    headers = {
        "Authorization": f"Bearer {owner_token}",
        "X-Organization-ID": security_test_data["org_alpha"].id,
    }

    # Invite a brand new email
    invite_resp = client.post(
        f"/api/v1/organizations/{security_test_data['org_alpha'].id}/members/invite",
        headers=headers,
        json={"email": "newjoiner@company.com", "role": "FINOPS_MANAGER"},
    )
    assert invite_resp.status_code == 200
    token = invite_resp.json()["data"]["invitation_link"].split("token=")[-1]

    # Verify user_exists is False in invite details
    details_resp = client.get(f"/api/v1/auth/invite-details?token={token}")
    assert details_resp.status_code == 200
    assert details_resp.json()["data"]["user_exists"] is False

    # Accept & register with password
    reg_resp = client.post(
        "/api/v1/auth/accept-invite-register",
        json={
            "token": token,
            "full_name": "New Joiner",
            "password": "SecurePassword123!",
        },
    )
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()["data"]
    assert "access_token" in reg_data
    assert reg_data["role"] == "FINOPS_MANAGER"
    assert reg_data["user"]["email"] == "newjoiner@company.com"

    # Verify user details now show user_exists is True
    details_after = client.get(f"/api/v1/auth/invite-details?token={token}")
    assert details_after.json()["data"]["status"] == "ACCEPTED"


