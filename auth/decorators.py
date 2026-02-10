from functools import wraps
from flask import jsonify, g, request

from flask_jwt_extended import (
    verify_jwt_in_request,
    get_jwt,
    get_jwt_identity,
)

from models import User, TokenBlocklist


# =====================================================
# JWT CONTEXT REQUIRED (SINGLE SOURCE OF TRUTH)
# =====================================================

def jwt_context_required():
    """
    Enforces:
    - Valid JWT access token (STRICT)
    - Token not revoked
    - User exists
    - Company ACTIVE (if applicable)
    - Injects trusted context into flask.g
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):

            # -------------------------------------------------
            # 1️⃣ Verify JWT (STRICT)
            # -------------------------------------------------
            try:
                verify_jwt_in_request()
            except Exception:
                return jsonify({"error": "invalid_or_missing_token"}), 401

            claims = get_jwt()
            user_id = get_jwt_identity()

            # -------------------------------------------------
            # 2️⃣ Token blocklist check
            # -------------------------------------------------
            jti = claims.get("jti")
            if jti and TokenBlocklist.query.filter_by(jti=jti).first():
                return jsonify({"error": "token_revoked"}), 401

            # -------------------------------------------------
            # 3️⃣ Load user
            # -------------------------------------------------
            if not user_id:
                return jsonify({"error": "unauthorized"}), 401

            user = User.query.get(int(user_id))
            if not user:
                return jsonify({"error": "user_not_found"}), 401

            role = user.role

            # -------------------------------------------------
            # 4️⃣ Company enforcement (NON SUPER_ADMIN)
            # -------------------------------------------------
            if role != "SUPER_ADMIN":
                if not user.company:
                    return jsonify({"error": "company_not_found"}), 401

                if user.company.status != "ACTIVE":
                    return jsonify({
                        "error": "company_suspended",
                        "message": "Company access is suspended"
                    }), 403

            # -------------------------------------------------
            # 5️⃣ Inject trusted context
            # -------------------------------------------------
            g.current_user = user
            g.current_role = role
            g.company_id = user.company_id

            return fn(*args, **kwargs)

        return wrapper

    return decorator


# =====================================================
# ROLE ENFORCEMENT
# =====================================================

def roles_required(*roles):
    """
    Restrict route access by role.

    Usage:
        @jwt_context_required()
        @roles_required("COMPANY_ADMIN", "SUPER_ADMIN")
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            role = getattr(g, "current_role", None)

            if role not in roles:
                return jsonify({
                    "error": "forbidden",
                    "required_roles": roles,
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator
