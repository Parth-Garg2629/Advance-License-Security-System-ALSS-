from flask import Blueprint, render_template, abort, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash

from models import db, User, Company, AuditLog
from utils.audit import log_audit

# =====================================================
# SUPER ADMIN BLUEPRINT
# =====================================================
super_admin_bp = Blueprint(
    "super_admin",
    __name__,
    url_prefix="/super"
)

# =====================================================
# SUPER ADMIN GUARD (API ONLY)
# =====================================================
def require_super_admin():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != "SUPER_ADMIN":
        abort(403)

    return user

# =====================================================
# ====================== UI ROUTES ====================
# ❌ NO jwt_required HERE
# =====================================================

@super_admin_bp.route("/dashboard")
def super_dashboard():
    return render_template(
        "super_admin/super_dashboard.html",
        stats={
            "total_companies": Company.query.count(),
            "active_companies": Company.query.filter_by(status="ACTIVE").count(),
            "total_users": User.query.count(),
            "total_logs": AuditLog.query.count(),
        }
    )


@super_admin_bp.route("/companies")
def super_companies():
    companies = Company.query.order_by(Company.created_at.desc()).all()
    return render_template("super_admin/super_company.html", companies=companies)


@super_admin_bp.route("/users")
def super_users():
    users = (
        User.query
        .outerjoin(Company, User.company_id == Company.id)
        .order_by(User.created_at.desc())
        .all()
    )
    return render_template("super_admin/super_users.html", users=users)

# =====================================================
# ===================== COMPANY CRUD ==================
# ✅ API = JWT REQUIRED
# =====================================================

@super_admin_bp.route("/api/companies", methods=["GET"])
@jwt_required()
def api_list_companies():
    require_super_admin()

    return jsonify([{
        "id": c.id,
        "name": c.name,
        "status": c.status,
        "created_at": c.created_at.isoformat(),
    } for c in Company.query.order_by(Company.created_at.desc()).all()])


@super_admin_bp.route("/api/companies", methods=["POST"])
@jwt_required()
def api_create_company():
    require_super_admin()

    name = (request.json or {}).get("name")
    if not name:
        return jsonify({"error": "company_name_required"}), 400

    company = Company(name=name, status="ACTIVE")
    db.session.add(company)
    db.session.commit()

    log_audit(
        event_type="COMPANY_CREATED",
        status="success",
        company_id=company.id
    )

    return jsonify({"message": "company_created"}), 201


@super_admin_bp.route("/api/companies/<int:company_id>", methods=["PUT"])
@jwt_required()
def api_update_company(company_id):
    require_super_admin()

    company = Company.query.get_or_404(company_id)
    company.name = (request.json or {}).get("name", company.name)

    db.session.commit()

    log_audit(
        event_type="COMPANY_UPDATED",
        status="success",
        company_id=company.id
    )

    return jsonify({"message": "company_updated"})


@super_admin_bp.route("/api/companies/<int:company_id>/status", methods=["PATCH"])
@jwt_required()
def api_company_status(company_id):
    require_super_admin()

    company = Company.query.get_or_404(company_id)
    status = (request.json or {}).get("status")

    if status not in ("ACTIVE", "SUSPENDED"):
        return jsonify({"error": "invalid_status"}), 400

    company.status = status
    db.session.commit()

    log_audit(
        event_type="COMPANY_STATUS_CHANGED",
        status="success",
        company_id=company.id,
        message=f"{company.name} → {status}",
    )

    return jsonify({"status": status})

# =====================================================
# ===================== CLIENT CRUD ===================
# =====================================================

@super_admin_bp.route("/api/clients", methods=["GET"])
@jwt_required()
def list_clients():
    require_super_admin()

    return jsonify([{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "company_id": u.company_id,
        "active": u.is_active,
        "created_at": u.created_at.isoformat(),
    } for u in User.query.filter_by(role="COMPANY_VIEWER").all()])


@super_admin_bp.route("/api/clients", methods=["POST"])
@jwt_required()
def create_client():
    admin = require_super_admin()
    data = request.json or {}

    if not all(k in data for k in ("username", "password", "company_id")):
        return jsonify({"error": "missing_fields"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "username_exists"}), 409

    user = User(
        username=data["username"],
        password_hash=generate_password_hash(data["password"]),
        role="COMPANY_VIEWER",
        company_id=data["company_id"],
        is_active=True,
    )

    db.session.add(user)
    db.session.commit()

    log_audit(event_type="CLIENT_CREATED", user_id=admin.id)
    return jsonify({"message": "client_created"}), 201


@super_admin_bp.route("/api/clients/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_client(user_id):
    require_super_admin()

    user = User.query.get_or_404(user_id)
    if user.role != "COMPANY_VIEWER":
        abort(404)

    data = request.json or {}
    user.email = data.get("email", user.email)
    user.is_active = data.get("is_active", user.is_active)

    db.session.commit()

    log_audit(event_type="CLIENT_UPDATED", user_id=user.id)
    return jsonify({"message": "client_updated"})


@super_admin_bp.route("/api/clients/<int:user_id>", methods=["DELETE"])
@jwt_required()
def disable_client(user_id):
    require_super_admin()

    user = User.query.get_or_404(user_id)
    if user.role != "COMPANY_VIEWER":
        abort(404)

    user.is_active = False
    db.session.commit()

    log_audit(event_type="CLIENT_DISABLED", user_id=user.id)
    return jsonify({"message": "client_disabled"})
