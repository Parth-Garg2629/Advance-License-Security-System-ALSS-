from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_login import login_required
from datetime import datetime
import pytz
import secrets

from models import db, User, Device, License, AuditLog, Activation
from utils.audit import log_audit
from utils.csv_export import generate_csv
from services.license_service import admin_revoke_device

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
IST = pytz.timezone("Asia/Kolkata")

# =====================================================
# HELPERS
# =====================================================

def current_user():
    try:
        uid = get_jwt_identity()
        if not uid:
            return None
        return User.query.get(int(uid))
    except Exception:
        return None

def is_read_only(user: User) -> bool:
    return user.role == "COMPANY_VIEWER"

def license_scope(user: User):
    if user.role == "SUPER_ADMIN":
        return License.query
    return License.query.filter(License.company_id == user.company_id)

def to_ist_safe(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)
    return dt.astimezone(IST)

def safe_license_key(lic: License):
    try:
        return lic.key
    except Exception:
        return "CORRUPTED_KEY"

def license_expiry_meta(lic: License):
    if not lic.expires_at:
        return {
            "status": lic.status,
            "expires_at": None,
            "seconds_left": None,
        }

    now = datetime.utcnow()
    expired = lic.expires_at < now

    return {
        "status": "EXPIRED" if expired else lic.status,
        "expires_at": to_ist_safe(lic.expires_at).isoformat(),
        "seconds_left": max(int((lic.expires_at - now).total_seconds()), 0),
    }

# =====================================================
# UI ROUTES
# =====================================================

@admin_bp.route("/")
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@admin_bp.route("/licenses")
@login_required
def licenses():
    return render_template("licenses.html")

@admin_bp.route("/devices")
@login_required
def devices():
    return render_template("devices.html")

@admin_bp.route("/audit")
@login_required
def audit():
    return render_template("audit_logs.html")

@admin_bp.route("/exports")
@login_required
def exports():
    return render_template("exports.html")

@admin_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

# =====================================================
# PROFILE API
# =====================================================

@admin_bp.route("/api/profile", methods=["GET"])
@jwt_required()
def api_profile():
    u = current_user()
    if not u:
        return jsonify({"error": "unauthorized"}), 401

    return jsonify({
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "company_id": u.company_id,
    }), 200

# =====================================================
# LICENSE APIs
# =====================================================

@admin_bp.route("/api/licenses", methods=["GET"])
@jwt_required()
def api_licenses():
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    licenses = license_scope(user).order_by(License.created_at.desc()).all()
    out = []

    for lic in licenses:
        meta = license_expiry_meta(lic)

        out.append({
            "id": lic.id,
            "key": safe_license_key(lic),
            "status": meta["status"],
            "max_devices": lic.max_devices,
            "company_id": lic.company_id,
            "created_at": to_ist_safe(lic.created_at).isoformat(),
            "expires_at": meta["expires_at"],
            "seconds_left": meta["seconds_left"],
        })

    return jsonify(out), 200


@admin_bp.route("/api/licenses", methods=["POST"])
@jwt_required()
def create_license():
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    if is_read_only(user):
        return jsonify({"error": "read_only"}), 403

    data = request.get_json(silent=True) or {}

    expires_at = None
    if data.get("expires_at"):
        try:
            expires_at = datetime.fromisoformat(data["expires_at"])
        except ValueError:
            return jsonify({"error": "invalid_expiry"}), 400

    if user.role == "SUPER_ADMIN":
        company_id = data.get("company_id")
        if not company_id:
            return jsonify({"error": "company_id_required"}), 400
        company_id = int(company_id)
    else:
        company_id = user.company_id

    lic = License(
        company_id=company_id,
        vendor_id=user.id,
        max_devices=int(data.get("max_devices", 1)),
        expires_at=expires_at,
        status="ACTIVE",
    )

    raw_key = secrets.token_urlsafe(32)
    lic.key = raw_key

    db.session.add(lic)
    db.session.commit()

    log_audit(
        action="LICENSE_CREATED",
        user_id=user.id,
        license_id=lic.id,
        status="success",
        message=f"License issued by {user.username}",
    )

    return jsonify({"message": "created", "license_key": raw_key}), 201


@admin_bp.route("/api/licenses/<int:license_id>", methods=["PUT"])
@jwt_required()
def update_license(license_id):
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    if is_read_only(user):
        return jsonify({"error": "read_only"}), 403

    lic = license_scope(user).filter_by(id=license_id).first_or_404()
    data = request.get_json(silent=True) or {}

    if "status" in data:
        lic.status = data["status"]

    if "max_devices" in data:
        lic.max_devices = int(data["max_devices"])

    if "expires_at" in data:
        lic.expires_at = (
            datetime.fromisoformat(data["expires_at"])
            if data["expires_at"] else None
        )

    db.session.commit()

    log_audit(
        action="LICENSE_UPDATED",
        user_id=user.id,
        license_id=lic.id,
        status="success",
        message="License updated",
    )

    return jsonify({"message": "updated"}), 200


@admin_bp.route("/api/licenses/<int:license_id>", methods=["DELETE"])
@jwt_required()
def revoke_license(license_id):
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    if is_read_only(user):
        return jsonify({"error": "read_only"}), 403

    lic = license_scope(user).filter_by(id=license_id).first_or_404()
    lic.status = "REVOKED"
    db.session.commit()

    log_audit(
        action="LICENSE_REVOKED",
        user_id=user.id,
        license_id=lic.id,
        status="success",
        message="License revoked",
    )

    return jsonify({"message": "revoked"}), 200

# =====================================================
# DEVICES API (CORRECT JOIN)
# =====================================================

@admin_bp.route("/api/devices", methods=["GET"])
@jwt_required()
def api_devices():
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    q = (
        db.session.query(Device, Activation)
        .join(Activation, Activation.device_id == Device.id)
        .join(License, Activation.license_id == License.id)
        .filter(Activation.status == "ACTIVE")
    )

    if user.role != "SUPER_ADMIN":
        q = q.filter(License.company_id == user.company_id)

    rows = q.all()

    return jsonify([
        {
            "id": d.id,
            "fingerprint": d.fingerprint[:8] + "...",
            "os_name": d.os_name,
            "status": d.status,
            "last_seen": (
                to_ist_safe(a.last_seen_at).strftime("%d/%m/%Y %H:%M:%S")
                if a.last_seen_at else None
            ),
        }
        for d, a in rows
    ]), 200

# =====================================================
# AUDIT LOGS API (NO company_id COLUMN ASSUMPTION)
# =====================================================

@admin_bp.route("/api/audit-logs", methods=["GET"])
@jwt_required()
def api_audit_logs():
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    q = AuditLog.query.outerjoin(User, AuditLog.user_id == User.id)

    if user.role == "SUPER_ADMIN":
        pass
    elif user.role == "COMPANY_ADMIN":
        q = q.filter(User.company_id == user.company_id)
    else:
        return jsonify({"error": "forbidden"}), 403

    logs = q.order_by(AuditLog.created_at.desc()).limit(200).all()

    return jsonify([
        {
            "id": l.id,
            "action": l.action,
            "status": l.status,
            "message": l.message,
            "username": l.user.username if l.user else "SYSTEM",
            "role": l.user.role if l.user else "SYSTEM",
            "created_at": to_ist_safe(l.created_at).strftime("%d/%m/%Y %H:%M:%S"),
        }
        for l in logs
    ]), 200

# =====================================================
# CSV EXPORTS
# =====================================================

@admin_bp.route("/api/export/audit-logs", methods=["GET"])
@jwt_required()
def export_audit_logs_csv():
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    q = AuditLog.query.outerjoin(User, AuditLog.user_id == User.id)

    if user.role == "SUPER_ADMIN":
        pass
    elif user.role == "COMPANY_ADMIN":
        q = q.filter(User.company_id == user.company_id)
    else:
        return jsonify({"error": "forbidden"}), 403

    logs = q.order_by(AuditLog.created_at.desc()).limit(1000).all()

    headers = ["Time (IST)", "Action", "Status", "Username", "Role", "Message"]
    rows = []

    for l in logs:
        rows.append([
            to_ist_safe(l.created_at).strftime("%d/%m/%Y %H:%M:%S"),
            l.action,
            l.status,
            l.user.username if l.user else "SYSTEM",
            l.user.role if l.user else "SYSTEM",
            l.message or "",
        ])

    return generate_csv(headers, rows, "audit_logs.csv")

# =====================================================
# DEVICE REVOKE
# =====================================================

@admin_bp.route("/api/devices/<int:device_id>/revoke", methods=["POST"])
@jwt_required()
def revoke_device_api(device_id):
    admin = current_user()
    if not admin:
        return jsonify({"error": "unauthorized"}), 401

    if admin.role not in ("COMPANY_ADMIN", "SUPER_ADMIN"):
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}
    license_id = data.get("license_id")
    block_device = bool(data.get("block_device", True))
    reason = data.get("reason", "Revoked by admin")

    if not license_id:
        return jsonify({"error": "license_id_required"}), 400

    lic = License.query.get_or_404(license_id)
    device = Device.query.get_or_404(device_id)

    if admin.role != "SUPER_ADMIN" and lic.company_id != admin.company_id:
        return jsonify({"error": "cross_company_access"}), 403

    success = admin_revoke_device(
        license_id=lic.id,
        device_id=device.id,
        admin_user_id=admin.id,
        block_device=block_device,
        reason=reason,
    )

    if not success:
        return jsonify({"error": "no_active_activation"}), 400

    Activation.query.filter_by(
        license_id=lic.id,
        device_id=device.id,
        status="ACTIVE"
    ).update({"status": "REVOKED"})

    db.session.commit()

    return jsonify({
        "status": "revoked",
        "device_id": device.id,
        "license_id": lic.id,
        "blocked": block_device,
    }), 200

# =====================================================
# DASHBOARD WIDGET APIs
# =====================================================

@admin_bp.route("/api/dashboard/licenses", methods=["GET"])
@jwt_required()
def dashboard_active_licenses():
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    q = License.query.filter(License.status == "ACTIVE")

    if user.role != "SUPER_ADMIN":
        q = q.filter(License.company_id == user.company_id)

    licenses = q.order_by(License.created_at.desc()).limit(5).all()

    return jsonify([
        {
            "key": safe_license_key(l),
            "status": l.status,
            "created_at": to_ist_safe(l.created_at).strftime("%d/%m/%Y %H:%M:%S"),
        }
        for l in licenses
    ]), 200


@admin_bp.route("/api/dashboard/audit", methods=["GET"])
@jwt_required()
def dashboard_critical_audit_logs():
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    q = AuditLog.query.outerjoin(User, AuditLog.user_id == User.id)

    if user.role == "SUPER_ADMIN":
        pass
    elif user.role == "COMPANY_ADMIN":
        q = q.filter(User.company_id == user.company_id)
    else:
        return jsonify({"error": "forbidden"}), 403

    logs = q.order_by(AuditLog.created_at.desc()).limit(5).all()

    return jsonify([
        {
            "event": l.action,
            "time": to_ist_safe(l.created_at).strftime("%d/%m/%Y %H:%M:%S"),
            "status": l.status,
            "message": l.message or "",
        }
        for l in logs
    ]), 200
