# routes/api_routes.py

from flask import Blueprint, jsonify, request, g, Response
from datetime import datetime
import csv
import io

from auth.decorators import jwt_context_required, roles_required
from models import (
    License,
    Device,
    User,
    AuditLog,
)
from services.license_service import (
    activate_license_for_device,
    deactivate_license_for_device,
)
from extensions import db, limiter

api_bp = Blueprint("api", __name__)


# =====================================================
# HEALTH CHECK
# =====================================================

@api_bp.route("/ping")
def ping():
    return jsonify({"status": "ok", "message": "API alive"}), 200


# =====================================================
# LICENSE APIs — Company Scoped
# =====================================================

@api_bp.route("/api/licenses", methods=["GET"])
@jwt_context_required()
def list_licenses():
    licenses = License.query.filter_by(company_id=g.company_id).all()

    return jsonify({
        "licenses": [
            {
                "id": lic.id,
                "key": lic.key,
                "status": lic.status,
                "owner_user_id": lic.owner_user_id,
                "created_at": lic.created_at.isoformat(),
            }
            for lic in licenses
        ]
    }), 200


@api_bp.route("/api/licenses", methods=["POST"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def create_license():
    data = request.get_json(silent=True) or {}

    key = data.get("key")
    if not key:
        return jsonify({"error": "license_key_required"}), 400

    license_obj = License(
        key=key,
        status="ACTIVE",
        company_id=g.company_id,
        owner_user_id=g.current_user.id,
    )

    db.session.add(license_obj)
    db.session.commit()

    return jsonify({
        "license": {
            "id": license_obj.id,
            "key": license_obj.key,
            "status": license_obj.status,
        }
    }), 201


@api_bp.route("/api/licenses/<int:license_id>", methods=["GET"])
@jwt_context_required()
def get_license(license_id):
    license_obj = License.query.filter_by(
        id=license_id,
        company_id=g.company_id
    ).first()

    if not license_obj:
        return jsonify({"error": "license_not_found"}), 404

    return jsonify({
        "license": {
            "id": license_obj.id,
            "key": license_obj.key,
            "status": license_obj.status,
            "owner_user_id": license_obj.owner_user_id,
            "created_at": license_obj.created_at.isoformat(),
        }
    }), 200


@api_bp.route("/api/licenses/<int:license_id>", methods=["PUT"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def update_license(license_id):
    license_obj = License.query.filter_by(
        id=license_id,
        company_id=g.company_id
    ).first()

    if not license_obj:
        return jsonify({"error": "license_not_found"}), 404

    data = request.get_json(silent=True) or {}

    if "status" in data:
        license_obj.status = data["status"]

    db.session.commit()

    return jsonify({
        "license": {
            "id": license_obj.id,
            "status": license_obj.status,
        }
    }), 200


@api_bp.route("/api/licenses/<int:license_id>/revoke", methods=["POST"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def revoke_license(license_id):
    license_obj = License.query.filter_by(
        id=license_id,
        company_id=g.company_id
    ).first()

    if not license_obj:
        return jsonify({"error": "license_not_found"}), 404

    if license_obj.status != "REVOKED":
        license_obj.status = "REVOKED"
        db.session.commit()

    return jsonify({
        "license": {
            "id": license_obj.id,
            "status": license_obj.status,
        }
    }), 200


# =====================================================
# DEVICE APIs — Company Scoped
# =====================================================

@api_bp.route("/api/device/register", methods=["POST"])
@limiter.limit("5 per minute")
def register_device():
    data = request.get_json(silent=True) or {}

    license_key = data.get("license_key")
    fingerprint = data.get("fingerprint")
    os_name = data.get("os_name")

    if not license_key or not fingerprint or not os_name:
        return jsonify({"error": "missing_fields"}), 400

    try:
        activation = activate_license_for_device(
            license_key=license_key,
            fingerprint=fingerprint,
            os_name=os_name,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 403

    return jsonify({
        "status": "ok",
        "license_id": activation.license_id,
        "device_id": activation.device_id,
        "activation_id": activation.id,
    }), 200


@api_bp.route("/api/devices", methods=["GET"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def list_devices():
    devices = Device.query.filter_by(company_id=g.company_id).all()

    return jsonify({
        "devices": [
            {
                "id": dev.id,
                "fingerprint": dev.fingerprint,
                "status": dev.status,
                "created_at": dev.created_at.isoformat(),
            }
            for dev in devices
        ]
    }), 200


@api_bp.route("/api/devices/<int:device_id>/block", methods=["POST"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def block_device(device_id):
    device = Device.query.filter_by(
        id=device_id,
        company_id=g.company_id
    ).first()

    if not device:
        return jsonify({"error": "device_not_found"}), 404

    device.status = "BLOCKED"
    db.session.commit()

    return jsonify({
        "device_id": device.id,
        "status": device.status,
    }), 200


@api_bp.route("/api/devices/<int:device_id>/unblock", methods=["POST"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def unblock_device(device_id):
    device = Device.query.filter_by(
        id=device_id,
        company_id=g.company_id
    ).first()

    if not device:
        return jsonify({"error": "device_not_found"}), 404

    device.status = "ACTIVE"
    db.session.commit()

    return jsonify({
        "device_id": device.id,
        "status": device.status,
    }), 200


@api_bp.route("/api/device/deactivate", methods=["POST"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def deactivate_device():
    data = request.get_json(silent=True) or {}

    license_key = data.get("license_key")
    fingerprint = data.get("fingerprint")

    if not license_key or not fingerprint:
        return jsonify({"error": "missing_fields"}), 400

    try:
        activation = deactivate_license_for_device(
            license_key=license_key,
            fingerprint=fingerprint,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "status": "ok",
        "license_id": activation.license_id,
        "device_id": activation.device_id,
    }), 200


# =====================================================
# USER / ADMIN APIs — Company Scoped
# =====================================================

@api_bp.route("/api/users", methods=["GET"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def list_users():
    users = User.query.filter_by(company_id=g.company_id).all()

    return jsonify({
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "status": u.status,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ]
    }), 200


@api_bp.route("/api/users", methods=["POST"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def create_user():
    data = request.get_json(silent=True) or {}

    email = data.get("email")
    role = data.get("role")

    if not email or not role:
        return jsonify({"error": "missing_fields"}), 400

    if g.current_role == "COMPANY_ADMIN" and role == "SUPER_ADMIN":
        return jsonify({"error": "forbidden_role"}), 403

    user = User(
        email=email,
        role=role,
        company_id=g.company_id,
        status="ACTIVE",
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
        }
    }), 201


@api_bp.route("/api/users/<int:user_id>/role", methods=["POST"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def update_user_role(user_id):
    if user_id == g.current_user.id:
        return jsonify({"error": "cannot_modify_self"}), 403

    user = User.query.filter_by(
        id=user_id,
        company_id=g.company_id
    ).first()

    if not user:
        return jsonify({"error": "user_not_found"}), 404

    data = request.get_json(silent=True) or {}
    new_role = data.get("role")

    if not new_role:
        return jsonify({"error": "role_required"}), 400

    if g.current_role == "COMPANY_ADMIN" and new_role == "SUPER_ADMIN":
        return jsonify({"error": "forbidden_role"}), 403

    user.role = new_role
    db.session.commit()

    return jsonify({
        "user_id": user.id,
        "role": user.role,
    }), 200


@api_bp.route("/api/users/<int:user_id>/deactivate", methods=["POST"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def deactivate_user(user_id):
    if user_id == g.current_user.id:
        return jsonify({"error": "cannot_modify_self"}), 403

    user = User.query.filter_by(
        id=user_id,
        company_id=g.company_id
    ).first()

    if not user:
        return jsonify({"error": "user_not_found"}), 404

    user.status = "INACTIVE"
    db.session.commit()

    return jsonify({
        "user_id": user.id,
        "status": user.status,
    }), 200


# =====================================================
# AUDIT LOG APIs — READ ONLY
# =====================================================

@api_bp.route("/api/audit/logs", methods=["GET"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def list_audit_logs():
    query = AuditLog.query.filter_by(company_id=g.company_id)

    action = request.args.get("action")
    actor_user_id = request.args.get("actor_user_id")
    from_ts = request.args.get("from")
    to_ts = request.args.get("to")

    if action:
        query = query.filter_by(action=action)

    if actor_user_id:
        query = query.filter_by(actor_user_id=actor_user_id)

    if from_ts:
        try:
            query = query.filter(AuditLog.created_at >= datetime.fromisoformat(from_ts))
        except ValueError:
            return jsonify({"error": "invalid_from_datetime"}), 400

    if to_ts:
        try:
            query = query.filter(AuditLog.created_at <= datetime.fromisoformat(to_ts))
        except ValueError:
            return jsonify({"error": "invalid_to_datetime"}), 400

    page = max(int(request.args.get("page", 1)), 1)
    limit = min(int(request.args.get("limit", 50)), 100)

    logs = query.order_by(AuditLog.created_at.desc()) \
        .offset((page - 1) * limit) \
        .limit(limit) \
        .all()

    return jsonify({
        "page": page,
        "limit": limit,
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "actor_user_id": log.actor_user_id,
                "created_at": log.created_at.isoformat(),
                "metadata": log.metadata,
            }
            for log in logs
        ]
    }), 200


# =====================================================
# EXPORT APIs — CSV ONLY (Phase 3 – Part 4)
# =====================================================

def _csv_response(filename: str, headers: list, rows: list):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        },
    )


@api_bp.route("/api/export/licenses", methods=["GET"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def export_licenses():
    query = License.query.filter_by(company_id=g.company_id)

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    licenses = query.all()

    rows = [
        [l.id, l.key, l.status, l.owner_user_id, l.created_at.isoformat()]
        for l in licenses
    ]

    return _csv_response(
        "licenses.csv",
        ["id", "key", "status", "owner_user_id", "created_at"],
        rows,
    )


@api_bp.route("/api/export/devices", methods=["GET"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def export_devices():
    query = Device.query.filter_by(company_id=g.company_id)

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    devices = query.all()

    rows = [
        [d.id, d.fingerprint, d.status, d.created_at.isoformat()]
        for d in devices
    ]

    return _csv_response(
        "devices.csv",
        ["id", "fingerprint", "status", "created_at"],
        rows,
    )


@api_bp.route("/api/export/users", methods=["GET"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def export_users():
    query = User.query.filter_by(company_id=g.company_id)

    role = request.args.get("role")
    status = request.args.get("status")

    if role:
        query = query.filter_by(role=role)
    if status:
        query = query.filter_by(status=status)

    users = query.all()

    rows = [
        [u.id, u.email, u.role, u.status, u.created_at.isoformat()]
        for u in users
    ]

    return _csv_response(
        "users.csv",
        ["id", "email", "role", "status", "created_at"],
        rows,
    )


@api_bp.route("/api/export/audit-logs", methods=["GET"])
@jwt_context_required()
@roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
def export_audit_logs():
    query = AuditLog.query.filter_by(company_id=g.company_id)

    action = request.args.get("action")
    if action:
        query = query.filter_by(action=action)

    logs = query.order_by(AuditLog.created_at.desc()).all()

    rows = [
        [l.id, l.action, l.actor_user_id, l.created_at.isoformat(), str(l.metadata)]
        for l in logs
    ]

    return _csv_response(
        "audit_logs.csv",
        ["id", "action", "actor_user_id", "created_at", "metadata"],
        rows,
    )
