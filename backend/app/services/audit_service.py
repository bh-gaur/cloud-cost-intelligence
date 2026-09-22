"""
Audit Logging Service
Records critical security, data access, and configuration events without exposing secrets.
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        status: str = "SUCCESS",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        organization_id: Optional[str] = None,
        org_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AuditLog:
        # Sanitize details to guarantee zero secrets in audit log
        clean_details = {}
        if details:
            for k, v in details.items():
                lower_k = k.lower()
                if any(sec in lower_k for sec in ("password", "secret", "token", "key", "credential")):
                    clean_details[k] = "********"
                else:
                    clean_details[k] = v

        entry = AuditLog(
            organization_id=organization_id or org_id,
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            details=clean_details,
        )
        db.add(entry)
        db.commit()
        return entry

