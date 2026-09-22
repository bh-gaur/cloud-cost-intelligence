"""
Centralized Permission Model & Organization Role Permission Mapping
Defines granular permissions and maps them to organization roles:
OWNER, ADMIN, FINOPS_MANAGER, ANALYST, VIEWER.
"""

from typing import Dict, Set
from fastapi import Depends, HTTPException, status
from app.auth.tenant_context import TenantContext, get_tenant_context


# Organization Roles
ROLE_OWNER = "OWNER"
ROLE_ADMIN = "ADMIN"
ROLE_FINOPS_MANAGER = "FINOPS_MANAGER"
ROLE_ANALYST = "ANALYST"
ROLE_VIEWER = "VIEWER"

ALL_ROLES = {ROLE_OWNER, ROLE_ADMIN, ROLE_FINOPS_MANAGER, ROLE_ANALYST, ROLE_VIEWER}

# Granular Permission Strings
PERM_ORG_READ = "organization.read"
PERM_ORG_UPDATE = "organization.update"

PERM_MEMBERS_READ = "members.read"
PERM_MEMBERS_INVITE = "members.invite"
PERM_MEMBERS_UPDATE = "members.update"
PERM_MEMBERS_REMOVE = "members.remove"

PERM_AWS_READ = "aws_accounts.read"
PERM_AWS_CREATE = "aws_accounts.create"
PERM_AWS_UPDATE = "aws_accounts.update"
PERM_AWS_DELETE = "aws_accounts.delete"

PERM_COSTS_READ = "costs.read"
PERM_COSTS_EXPORT = "costs.export"

PERM_REPORTS_READ = "reports.read"
PERM_REPORTS_CREATE = "reports.create"
PERM_REPORTS_DOWNLOAD = "reports.download"
PERM_REPORTS_DELETE = "reports.delete"

PERM_OPTIMIZATION_READ = "optimization.read"
PERM_OPTIMIZATION_MANAGE = "optimization.manage"

PERM_ALERTS_READ = "alerts.read"
PERM_ALERTS_CREATE = "alerts.create"
PERM_ALERTS_UPDATE = "alerts.update"
PERM_ALERTS_DELETE = "alerts.delete"

PERM_BUDGETS_READ = "budgets.read"
PERM_BUDGETS_MANAGE = "budgets.manage"

PERM_INTEGRATIONS_READ = "integrations.read"
PERM_INTEGRATIONS_MANAGE = "integrations.manage"

PERM_SETTINGS_READ = "settings.read"
PERM_SETTINGS_UPDATE = "settings.update"

# Complete Role Permission Matrix
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    ROLE_OWNER: {
        PERM_ORG_READ, PERM_ORG_UPDATE,
        PERM_MEMBERS_READ, PERM_MEMBERS_INVITE, PERM_MEMBERS_UPDATE, PERM_MEMBERS_REMOVE,
        PERM_AWS_READ, PERM_AWS_CREATE, PERM_AWS_UPDATE, PERM_AWS_DELETE,
        PERM_COSTS_READ, PERM_COSTS_EXPORT,
        PERM_REPORTS_READ, PERM_REPORTS_CREATE, PERM_REPORTS_DOWNLOAD, PERM_REPORTS_DELETE,
        PERM_OPTIMIZATION_READ, PERM_OPTIMIZATION_MANAGE,
        PERM_ALERTS_READ, PERM_ALERTS_CREATE, PERM_ALERTS_UPDATE, PERM_ALERTS_DELETE,
        PERM_BUDGETS_READ, PERM_BUDGETS_MANAGE,
        PERM_INTEGRATIONS_READ, PERM_INTEGRATIONS_MANAGE,
        PERM_SETTINGS_READ, PERM_SETTINGS_UPDATE,
    },
    ROLE_ADMIN: {
        PERM_ORG_READ, PERM_ORG_UPDATE,
        PERM_MEMBERS_READ, PERM_MEMBERS_INVITE, PERM_MEMBERS_UPDATE, PERM_MEMBERS_REMOVE,
        PERM_AWS_READ, PERM_AWS_CREATE, PERM_AWS_UPDATE, PERM_AWS_DELETE,
        PERM_COSTS_READ, PERM_COSTS_EXPORT,
        PERM_REPORTS_READ, PERM_REPORTS_CREATE, PERM_REPORTS_DOWNLOAD, PERM_REPORTS_DELETE,
        PERM_OPTIMIZATION_READ, PERM_OPTIMIZATION_MANAGE,
        PERM_ALERTS_READ, PERM_ALERTS_CREATE, PERM_ALERTS_UPDATE, PERM_ALERTS_DELETE,
        PERM_BUDGETS_READ, PERM_BUDGETS_MANAGE,
        PERM_INTEGRATIONS_READ, PERM_INTEGRATIONS_MANAGE,
        PERM_SETTINGS_READ, PERM_SETTINGS_UPDATE,
    },
    ROLE_FINOPS_MANAGER: {
        PERM_ORG_READ,
        PERM_MEMBERS_READ, PERM_MEMBERS_INVITE, PERM_MEMBERS_UPDATE,
        PERM_AWS_READ,
        PERM_COSTS_READ, PERM_COSTS_EXPORT,
        PERM_REPORTS_READ, PERM_REPORTS_CREATE, PERM_REPORTS_DOWNLOAD,
        PERM_OPTIMIZATION_READ, PERM_OPTIMIZATION_MANAGE,
        PERM_ALERTS_READ, PERM_ALERTS_CREATE, PERM_ALERTS_UPDATE, PERM_ALERTS_DELETE,
        PERM_BUDGETS_READ, PERM_BUDGETS_MANAGE,
        PERM_INTEGRATIONS_READ,
        PERM_SETTINGS_READ,
    },
    ROLE_ANALYST: {
        PERM_ORG_READ,
        PERM_MEMBERS_READ,
        PERM_AWS_READ,
        PERM_COSTS_READ, PERM_COSTS_EXPORT,
        PERM_REPORTS_READ, PERM_REPORTS_CREATE, PERM_REPORTS_DOWNLOAD,
        PERM_OPTIMIZATION_READ,
        PERM_ALERTS_READ,
        PERM_BUDGETS_READ,
        PERM_INTEGRATIONS_READ,
        PERM_SETTINGS_READ,
    },
    ROLE_VIEWER: {
        PERM_ORG_READ,
        PERM_MEMBERS_READ,
        PERM_AWS_READ,
        PERM_COSTS_READ,
        PERM_REPORTS_READ,
        PERM_OPTIMIZATION_READ,
        PERM_ALERTS_READ,
        PERM_BUDGETS_READ,
        PERM_INTEGRATIONS_READ,
        PERM_SETTINGS_READ,
    },
}


def has_permission(role: str, permission: str) -> bool:
    """Checks whether an organization role possesses a specific permission."""
    role_upper = (role or "").upper()
    allowed_perms = ROLE_PERMISSIONS.get(role_upper, set())
    return permission in allowed_perms


class RequirePermission:
    """FastAPI Dependency Guard enforcing specific permission on active organization tenant context."""

    def __init__(self, permission: str):
        self.permission = permission

    def __call__(self, tenant_ctx: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        if not has_permission(tenant_ctx.org_role, self.permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required permission: '{self.permission}'",
            )
        return tenant_ctx
