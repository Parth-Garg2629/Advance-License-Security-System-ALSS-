# utils/audit.py

from datetime import datetime
from typing import Optional

from extensions import db
from models import AuditLog


# =====================================================
# CENTRAL AUDIT LOGGER (SINGLE SOURCE OF TRUTH)
# =====================================================
def log_audit(
    *,
    action: str,
    status: str = "success",
    user_id: Optional[int] = None,
    license_id: Optional[int] = None,
    message: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    extra_data: Optional[str] = None,
):
    """
    Centralized audit logging utility.

    DESIGN CONTRACT (DO NOT VIOLATE):
    - NO Flask request usage
    - NO RBAC enforcement
    - NO redirects
    - NO logging side-effects
    - NEVER raises exceptions

    NOTES:
    - user_id=None => SYSTEM action
    - company scoping is handled at query time
    """

    try:
        audit = AuditLog(
            action=action,
            status=status,
            user_id=user_id,
            license_id=license_id,
            message=message,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data,
            created_at=datetime.utcnow(),
        )

        db.session.add(audit)
        db.session.commit()

    except Exception:
        # Audit must NEVER break core flows
        db.session.rollback()
