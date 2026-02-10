# auth/auth_routes.py

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt,
)

from flask_login import login_user  # ✅ FIX: establish UI session

from models import db, User, AuditLog, TokenBlocklist
from extensions import limiter
from utils.audit import log_audit
from auth.jwt_handler import create_tokens

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# =====================================================
# BRUTE FORCE PROTECTION (IP BASED)
# =====================================================

def _too_many_failed_attempts() -> bool:
    ip = request.remote_addr
    window_start = datetime.utcnow() - timedelta(minutes=10)

    return (
        AuditLog.query.filter(
            AuditLog.action == "LOGIN_FAILED",
            AuditLog.ip_address == ip,
            AuditLog.created_at >= window_start,
        ).count()
        >= 5
    )


# =====================================================
# LOGIN
# =====================================================

@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username_and_password_required"}), 400

    # -------------------------------
    # BRUTE FORCE CHECK
    # -------------------------------
    if _too_many_failed_attempts():
        log_audit(
            action="LOGIN_BLOCKED",
            status="failed",
            message="Too many failed login attempts",
            extra_data={"username": username},
        )
        return jsonify({"error": "too_many_failed_attempts"}), 429

    # -------------------------------
    # USER LOOKUP
    # -------------------------------
    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        log_audit(
            action="LOGIN_FAILED",
            status="failed",
            message="Invalid credentials",
            user_id=user.id if user else None,
            extra_data={"username": username},
        )
        return jsonify({"error": "invalid_credentials"}), 401

    # =====================================================
    # ESTABLISH FLASK-LOGIN SESSION (CRITICAL FIX)
    # =====================================================
    login_user(user, remember=True)

    # -------------------------------
    # COMPANY STATUS CHECK
    # -------------------------------
    if user.company and user.company.status != "ACTIVE":
        log_audit(
            action="LOGIN_DENIED",
            status="failed",
            message="Company suspended",
            user_id=user.id,
        )
        return jsonify({"error": "company_suspended"}), 403

    # -------------------------------
    # ISSUE TOKENS
    # -------------------------------
    access_token, refresh_token = create_tokens(
        user_id=str(user.id),
        role=user.role,
        company_id=user.company_id,
    )

    # -------------------------------
    # REDIRECT DECISION (BACKEND AUTHORITY)
    # -------------------------------
    force_password_change = False

    if user.role == "COMPANY_VIEWER" and user.is_temp_password:
        force_password_change = True
        redirect_url = "/change-password"
    else:
        if user.role == "SUPER_ADMIN":
            redirect_url = "/super/dashboard"
        elif user.role == "COMPANY_ADMIN":
            redirect_url = "/admin/dashboard"
        else:
            redirect_url = "/client/dashboard"

    # -------------------------------
    # UPDATE LAST LOGIN
    # -------------------------------
    user.last_login_at = datetime.utcnow()
    db.session.commit()

    log_audit(
        action="LOGIN_SUCCESS",
        status="success",
        message=f"User {user.username} logged in",
        user_id=user.id,
    )

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "redirect": redirect_url,
        "force_password_change": force_password_change,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }
    }), 200


# =====================================================
# CHANGE PASSWORD (CLIENT ONLY)
# =====================================================

@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    # ❌ ADMIN / SUPER_ADMIN BLOCKED
    if user.role != "COMPANY_VIEWER":
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"error": "old_and_new_password_required"}), 400

    if not user.check_password(old_password):
        log_audit(
            action="PASSWORD_CHANGE_FAILED",
            status="failed",
            message="Old password incorrect",
            user_id=user.id,
        )
        return jsonify({"error": "invalid_old_password"}), 401

    # -------------------------------
    # UPDATE PASSWORD
    # -------------------------------
    user.set_password(new_password, temp=False)
    user.password_changed_at = datetime.utcnow()

    db.session.commit()

    log_audit(
        action="PASSWORD_CHANGED",
        status="success",
        message="Client changed password",
        user_id=user.id,
    )

    return jsonify({
        "message": "password_changed",
        "redirect": "/client/dashboard",
    }), 200


# =====================================================
# REFRESH TOKEN (BLOCKED IF TEMP PASSWORD)
# =====================================================

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_access_token():
    user_id = get_jwt_identity()
    claims = get_jwt()

    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "user_not_found"}), 401

    if user.role == "COMPANY_VIEWER" and user.is_temp_password:
        return jsonify({
            "error": "password_change_required",
            "message": "Password change required before refreshing token"
        }), 403

    new_access_token, _ = create_tokens(
        user_id=user_id,
        role=claims.get("role"),
        company_id=claims.get("company_id"),
    )

    log_audit(
        action="TOKEN_REFRESH",
        status="success",
        message="Access token refreshed",
        user_id=user.id,
    )

    return jsonify({"access_token": new_access_token}), 200


# =====================================================
# LOGOUT
# =====================================================

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jwt_payload = get_jwt()
    jti = jwt_payload.get("jti")
    user_id = int(get_jwt_identity())

    db.session.add(TokenBlocklist(
        jti=jti,
        user_id=user_id,
        reason="user_logout",
    ))
    db.session.commit()

    log_audit(
        action="LOGOUT",
        status="success",
        message="User logged out",
        user_id=user_id,
    )

    return jsonify({"message": "logged_out"}), 200
