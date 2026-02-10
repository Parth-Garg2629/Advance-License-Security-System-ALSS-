# services/license_service.py

from datetime import datetime, timedelta
import secrets
from typing import Optional

from extensions import db
from models import License, User, Device, Activation, AuditLog
from utils.crypto import encrypt_value


# =====================================================
# CONSTANTS (LOCKED)
# =====================================================

HEARTBEAT_TTL = timedelta(days=7)


# =====================================================
# INTERNAL HELPERS
# =====================================================

def _utc_now():
    return datetime.utcnow()


def _is_license_expired(lic: License) -> bool:
    return bool(lic.expires_at and lic.expires_at < _utc_now())


def _get_license_by_raw_key(raw_key: str) -> Optional[License]:
    encrypted = encrypt_value(raw_key)
    return License.query.filter_by(_license_key=encrypted).first()


# =====================================================
# LICENSE KEY UTILS
# =====================================================

def generate_license_key(length: int = 32) -> str:
    return secrets.token_urlsafe(length)[:length]


# =====================================================
# LICENSE CREATION  ✅ PATCHED (SUPER_ADMIN SAFE)
# =====================================================

def create_license(
    *,
    owner_user_id: int,
    max_devices: int = 1,
    expires_at: Optional[datetime] = None,
    company_id: Optional[int] = None,   # 🔑 NEW (OPTIONAL)
) -> License:

    owner = User.query.get(owner_user_id)
    if not owner:
        raise ValueError("OWNER_NOT_FOUND")

    # -------------------------------------------------
    # COMPANY RESOLUTION
    # -------------------------------------------------
    if owner.role == "SUPER_ADMIN":
        if not company_id:
            raise ValueError("COMPANY_ID_REQUIRED_FOR_SUPER_ADMIN")
        resolved_company_id = company_id
    else:
        resolved_company_id = owner.company_id

    lic = License(
        vendor_id=owner_user_id,
        company_id=resolved_company_id,
        max_devices=max_devices,
        expires_at=expires_at,
        status="ACTIVE",
    )

    lic.key = generate_license_key()

    db.session.add(lic)
    db.session.add(
        AuditLog(
            action="LICENSE_CREATED",
            user_id=owner_user_id,
            license=lic,
            status="success",
            message="License created",
        )
    )
    db.session.commit()

    return lic


# =====================================================
# A1 — DEVICE ACTIVATION (STRICT + IDEMPOTENT)
# =====================================================

def activate_license_for_device(
    *,
    license_key: str,
    fingerprint: str,
    os_name: str,
) -> Activation:

    lic = _get_license_by_raw_key(license_key)
    if not lic:
        raise ValueError("LICENSE_NOT_FOUND")

    now = _utc_now()

    if _is_license_expired(lic):
        raise ValueError("LICENSE_EXPIRED")

    if lic.status != "ACTIVE":
        raise ValueError(f"LICENSE_{lic.status}")

    # -----------------------------
    # DEVICE LOOKUP / CREATE
    # -----------------------------
    device = Device.query.filter_by(fingerprint=fingerprint).first()

    if not device:
        device = Device(
            fingerprint=fingerprint,
            os_name=os_name,
            status="ACTIVE",
            created_at=now,
        )
        db.session.add(device)
        db.session.flush()

    if device.status != "ACTIVE":
        raise ValueError("DEVICE_BLOCKED")

    # -----------------------------
    # IDEMPOTENT ACTIVATION
    # -----------------------------
    existing = Activation.query.filter_by(
        license_id=lic.id,
        device_id=device.id,
        status="ACTIVE",
    ).first()

    if existing:
        existing.last_seen_at = now
        db.session.commit()
        return existing

    # -----------------------------
    # STRICT max_devices ENFORCEMENT
    # -----------------------------
    active_count = Activation.query.filter_by(
        license_id=lic.id,
        status="ACTIVE",
    ).count()

    if active_count >= lic.max_devices:
        raise ValueError("DEVICE_LIMIT_REACHED")

    activation = Activation(
        license_id=lic.id,
        device_id=device.id,
        status="ACTIVE",
        activated_at=now,
        last_seen_at=now,
    )

    db.session.add(activation)
    db.session.add(
        AuditLog(
            action="LICENSE_ACTIVATED",
            license_id=lic.id,
            status="success",
            message="Device activated",
        )
    )
    db.session.commit()

    return activation


# =====================================================
# A2 — RUNTIME VERIFY + HEARTBEAT
# =====================================================

def verify_license_for_device(
    *,
    license_key: str,
    fingerprint: str,
) -> dict:

    lic = _get_license_by_raw_key(license_key)
    if not lic:
        return {"allowed": False, "reason": "LICENSE_NOT_FOUND"}

    now = _utc_now()

    if _is_license_expired(lic):
        return {"allowed": False, "reason": "LICENSE_EXPIRED"}

    if lic.status != "ACTIVE":
        return {"allowed": False, "reason": f"LICENSE_{lic.status}"}

    device = Device.query.filter_by(fingerprint=fingerprint).first()
    if not device:
        return {"allowed": False, "reason": "DEVICE_NOT_REGISTERED"}

    if device.status != "ACTIVE":
        return {"allowed": False, "reason": "DEVICE_BLOCKED"}

    activation = Activation.query.filter_by(
        license_id=lic.id,
        device_id=device.id,
        status="ACTIVE",
    ).first()

    if not activation:
        return {"allowed": False, "reason": "NOT_ACTIVATED"}

    # -----------------------------
    # HEARTBEAT TTL AUTO-RELEASE
    # -----------------------------
    if activation.last_seen_at and now - activation.last_seen_at > HEARTBEAT_TTL:
        _auto_release_activation(activation, "heartbeat_expired")
        return {"allowed": False, "reason": "HEARTBEAT_EXPIRED"}

    activation.last_seen_at = now
    db.session.commit()

    return {"allowed": True, "reason": "OK"}


# =====================================================
# A2 — AUTO RELEASE (INTERNAL)
# =====================================================

def _auto_release_activation(
    activation: Activation,
    reason: str,
):
    activation.status = "INACTIVE"
    activation.deactivated_at = _utc_now()

    db.session.add(
        AuditLog(
            action="LICENSE_AUTO_RELEASED",
            license_id=activation.license_id,
            status="success",
            message=reason,
        )
    )
    db.session.commit()


# =====================================================
# A3 — ADMIN DEVICE REVOKE (HARD OVERRIDE)
# =====================================================

def admin_revoke_device(
    *,
    license_id: int,
    device_id: int,
    admin_user_id: int,
    block_device: bool = True,
    reason: Optional[str] = None,
) -> bool:

    activation = Activation.query.filter_by(
        license_id=license_id,
        device_id=device_id,
        status="ACTIVE",
    ).first()

    if not activation:
        return False

    activation.status = "INACTIVE"
    activation.deactivated_at = _utc_now()

    device = Device.query.get(device_id)
    if device and block_device:
        device.status = "BLOCKED"

    db.session.add(
        AuditLog(
            action="DEVICE_REVOKED_BY_ADMIN",
            user_id=admin_user_id,
            license_id=license_id,
            status="success",
            message=reason or "Device revoked by admin",
        )
    )
    db.session.commit()

    return True


# =====================================================
# PUBLIC API — DEVICE DEACTIVATION
# =====================================================

def deactivate_license_for_device(
    *,
    license_key: str,
    fingerprint: str,
) -> Activation:

    lic = _get_license_by_raw_key(license_key)
    if not lic:
        raise ValueError("LICENSE_NOT_FOUND")

    device = Device.query.filter_by(fingerprint=fingerprint).first()
    if not device:
        raise ValueError("DEVICE_NOT_FOUND")

    activation = Activation.query.filter_by(
        license_id=lic.id,
        device_id=device.id,
        status="ACTIVE",
    ).first()

    if not activation:
        raise ValueError("ACTIVATION_NOT_FOUND")

    activation.status = "INACTIVE"
    activation.deactivated_at = _utc_now()

    db.session.add(
        AuditLog(
            action="DEVICE_DEACTIVATED",
            license_id=lic.id,
            status="success",
            message="Device deactivated",
        )
    )
    db.session.commit()

    return activation
