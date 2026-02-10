from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required
from datetime import datetime
import pytz

from models import User, License, Activation, Device
from auth.decorators import jwt_context_required
from services.license_service import (
    activate_license_for_device,
    verify_license_for_device,
)

client_bp = Blueprint("client", __name__, url_prefix="/client")
IST = pytz.timezone("Asia/Kolkata")

# =====================================================
# CLIENT DASHBOARD UI
# =====================================================

@client_bp.route("/")
@client_bp.route("/dashboard")
@login_required
def client_dashboard():
    return render_template("client_dashboard.html")

# =====================================================
# CLIENT DASHBOARD API
# =====================================================

@client_bp.route("/api/dashboard", methods=["GET"])
@jwt_context_required()
def client_dashboard_api():
    from flask import g
    user: User = g.current_user

    if user.role != "COMPANY_VIEWER":
        return jsonify({"error": "forbidden"}), 403

    lic = (
        License.query
        .filter(License.company_id == user.company_id, License.status == "ACTIVE")
        .order_by(License.created_at.desc())
        .first()
    )

    if not lic:
        return jsonify({
            "license_status": "NONE",
            "used_devices": 0,
            "max_devices": 0,
            "expires_at": None,
            "seconds_left": None,
            "devices": [],
        }), 200

    now_utc = datetime.utcnow()
    expired = bool(lic.expires_at and lic.expires_at < now_utc)
    license_status = "EXPIRED" if expired else lic.status

    seconds_left = (
        max(int((lic.expires_at - now_utc).total_seconds()), 0)
        if lic.expires_at else None
    )

    expires_at_ist = None
    if lic.expires_at:
        dt = lic.expires_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.utc)
        expires_at_ist = dt.astimezone(IST).isoformat()

    activations = (
        Activation.query
        .filter(
            Activation.license_id == lic.id,
            Activation.status == "ACTIVE",
        )
        .all()
    )

    devices = []
    for act in activations:
        device = Device.query.get(act.device_id)
        if not device:
            continue

        last_seen = None
        if act.last_seen_at:
            dt = act.last_seen_at
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.utc)
            last_seen = dt.astimezone(IST).isoformat()

        devices.append({
            "fingerprint": device.fingerprint[:8] + "...",
            "status": device.status,
            "last_seen": last_seen,
        })

    return jsonify({
        "license_status": license_status,
        "used_devices": len(devices),
        "max_devices": lic.max_devices,
        "expires_at": expires_at_ist,
        "seconds_left": seconds_left,
        "devices": devices,
    }), 200

# =====================================================
# CLIENT LICENSE ACTIVATION
# =====================================================

@client_bp.route("/api/activate", methods=["POST"])
def activate_license_api():
    data = request.get_json(silent=True) or {}

    license_key = data.get("license_key")
    fingerprint = data.get("fingerprint")
    os_name = data.get("os_name")

    if not license_key or not fingerprint or not os_name:
        return jsonify({"allowed": False, "reason": "missing_fields"}), 400

    try:
        activation = activate_license_for_device(
            license_key=license_key,
            fingerprint=fingerprint,
            os_name=os_name,
        )

        return jsonify({
            "allowed": True,
            "message": "device_activated",
            "license_id": activation.license_id,
            "device_id": activation.device_id,
        }), 200

    except ValueError as e:
        return jsonify({"allowed": False, "reason": str(e)}), 403

    except Exception:
        return jsonify({"allowed": False, "reason": "server_error"}), 500

# =====================================================
# CLIENT VERIFY HEARTBEAT
# =====================================================

@client_bp.route("/api/verify", methods=["POST"])
def verify_license_runtime_api():
    data = request.get_json(silent=True) or {}

    license_key = data.get("license_key")
    fingerprint = data.get("fingerprint")

    if not license_key or not fingerprint:
        return jsonify({"allowed": False, "reason": "missing_fields"}), 400

    result = verify_license_for_device(
        license_key=license_key,
        fingerprint=fingerprint,
    )

    return jsonify(result), 200
