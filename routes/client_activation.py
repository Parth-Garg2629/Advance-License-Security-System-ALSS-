from flask import Blueprint, request, jsonify
from datetime import datetime

from models import db
from utils.enforcement import (
    enforce_license_device,
    LicenseInvalid,
    LicenseExpired,
    DeviceBlocked,
    DeviceLimitExceeded,
)
from utils.audit import log_audit

client_activation_bp = Blueprint(
    "client_activation",
    __name__,
    url_prefix="/api/activate",
)


@client_activation_bp.route("", methods=["POST"])
def activate_device():
    """
    Client runtime activation endpoint.
    Called by protected software at startup / heartbeat.

    Expected JSON:
    {
        "license_id": 123,
        "fingerprint": "abc123...",
        "os_name": "Windows"
    }
    """

    data = request.get_json(silent=True) or {}

    license_id = data.get("license_id")
    fingerprint = data.get("fingerprint")
    os_name = data.get("os_name")

    if not license_id or not fingerprint:
        return jsonify({
            "error": "invalid_request",
            "message": "license_id and fingerprint are required"
        }), 400

    try:
        license, device, activation = enforce_license_device(
            license_id=int(license_id),
            fingerprint=fingerprint,
            os_name=os_name,
        )

        log_audit(
            event_type="DEVICE_ACTIVATED",
            status="success",
            license_id=license.id,
            message=f"Device {device.fingerprint[:8]} activated",
            extra_data={
                "device_id": device.id,
                "activation_id": activation.id,
            },
        )

        return jsonify({
            "status": "allowed",
            "license_status": license.status,
            "expires_at": license.expires_at.isoformat() if license.expires_at else None,
            "max_devices": license.max_devices,
            "device_id": device.id,
            "activation_id": activation.id,
        }), 200

    except LicenseInvalid as e:
        _audit_fail("LICENSE_INVALID", license_id, fingerprint, str(e))
        return jsonify({"error": "license_invalid"}), 403

    except LicenseExpired as e:
        _audit_fail("LICENSE_EXPIRED", license_id, fingerprint, str(e))
        return jsonify({"error": "license_expired"}), 403

    except DeviceBlocked as e:
        _audit_fail("DEVICE_BLOCKED", license_id, fingerprint, str(e))
        return jsonify({"error": "device_blocked"}), 403

    except DeviceLimitExceeded as e:
        _audit_fail("DEVICE_LIMIT_EXCEEDED", license_id, fingerprint, str(e))
        return jsonify({"error": "device_limit_exceeded"}), 403

    except Exception as e:
        _audit_fail("ACTIVATION_ERROR", license_id, fingerprint, str(e))
        return jsonify({"error": "internal_error"}), 500


def _audit_fail(event, license_id, fingerprint, message):
    log_audit(
        event_type=event,
        status="failed",
        license_id=license_id,
        message=message,
        extra_data={
            "fingerprint": fingerprint[:16],
            "time": datetime.utcnow().isoformat(),
        },
    )
