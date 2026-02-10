# utils/enforcement.py

from datetime import datetime
from models import db, License, Device, Activation


class EnforcementError(Exception):
    """Base class for enforcement failures."""


class LicenseInvalid(EnforcementError):
    pass


class LicenseExpired(EnforcementError):
    pass


class DeviceBlocked(EnforcementError):
    pass


class DeviceLimitExceeded(EnforcementError):
    pass


def enforce_license_device(
    *,
    license_id: int,
    fingerprint: str,
    os_name: str | None = None,
):
    """
    Enforces runtime license + device rules.

    Returns:
        (license, device, activation)

    Raises:
        LicenseInvalid
        LicenseExpired
        DeviceBlocked
        DeviceLimitExceeded
    """

    # -------------------------------------------------
    # 1. Load license
    # -------------------------------------------------
    license = License.query.get(license_id)
    if not license or license.status != "ACTIVE":
        raise LicenseInvalid("License is not active or does not exist")

    if license.expires_at and license.expires_at < datetime.utcnow():
        raise LicenseExpired("License has expired")

    # -------------------------------------------------
    # 2. Load or create device
    # -------------------------------------------------
    device = Device.query.filter_by(fingerprint=fingerprint).first()

    if device:
        if device.status != "ACTIVE":
            raise DeviceBlocked("Device is blocked")
    else:
        device = Device(
            fingerprint=fingerprint,
            os_name=os_name or "UNKNOWN",
            status="ACTIVE",
        )
        db.session.add(device)
        db.session.flush()  # get device.id safely

    # -------------------------------------------------
    # 3. Check existing activation
    # -------------------------------------------------
    activation = Activation.query.filter_by(
        license_id=license.id,
        device_id=device.id,
        status="ACTIVE",
    ).first()

    if activation:
        # already activated → update last seen
        activation.last_seen_at = datetime.utcnow()
        device.last_seen_at = datetime.utcnow()
        db.session.commit()
        return license, device, activation

    # -------------------------------------------------
    # 4. Enforce max_devices
    # -------------------------------------------------
    active_count = Activation.query.filter_by(
        license_id=license.id,
        status="ACTIVE",
    ).count()

    if active_count >= license.max_devices:
        raise DeviceLimitExceeded("Device limit exceeded")

    # -------------------------------------------------
    # 5. Create activation
    # -------------------------------------------------
    activation = Activation(
        license_id=license.id,
        device_id=device.id,
        status="ACTIVE",
        activated_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
    )

    device.last_seen_at = datetime.utcnow()

    db.session.add(activation)
    db.session.commit()

    return license, device, activation
