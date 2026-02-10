from datetime import datetime
import json
from typing import Optional

from models import db, AuditLog


# =====================================================
# Audit logging (WRITE ONLY)
# =====================================================

def log_event(
    *,
    company_id: int,
    event_type: str,
    actor_user_id: Optional[int] = None,
    license_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    extra: Optional[dict] = None,
) -> AuditLog:
    """
    Write a single audit log entry.

    Rules:
    - Always company-scoped
    - Never raises on JSON errors
    """

    try:
        extra_json = json.dumps(extra) if extra else None
    except (TypeError, ValueError):
        extra_json = None

    log = AuditLog(
        company_id=company_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        license_id=license_id,
        ip_address=ip_address,
        user_agent=user_agent,
        extra_data=extra_json,
        created_at=datetime.utcnow(),
    )

    db.session.add(log)
    db.session.commit()
    return log


# =====================================================
# Serialization helper (READ ONLY)
# =====================================================

def serialize_log(log: AuditLog) -> dict:
    try:
        extra = json.loads(log.extra_data) if log.extra_data else None
    except (json.JSONDecodeError, TypeError):
        extra = None

    return {
        "id": log.id,
        "company_id": log.company_id,
        "event_type": log.event_type,
        "actor_user_id": log.actor_user_id,
        "license_id": log.license_id,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "extra": extra,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }
