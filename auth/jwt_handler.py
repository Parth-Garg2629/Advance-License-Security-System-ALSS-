# auth/jwt_handler.py

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    verify_jwt_in_request,
    get_jwt,
    get_jwt_identity,
)


class JWTContextError(Exception):
    """Raised when JWT is invalid or incomplete"""


# =====================================================
# Token Creation (used by login / refresh)
# =====================================================

def create_tokens(user_id: int, role: str, company_id: int):
    """
    Create JWT access & refresh tokens.

    Access token:
    - short lived
    - contains role + company_id

    Refresh token:
    - long lived
    """

    additional_claims = {
        "role": role,
        "company_id": company_id,
    }

    access_token = create_access_token(
        identity=user_id,
        additional_claims=additional_claims,
    )

    refresh_token = create_refresh_token(
        identity=user_id,
    )

    return access_token, refresh_token


# =====================================================
# JWT Context Loader (Phase 3 – Part 3)
# =====================================================

def load_jwt_context() -> dict:
    """
    Verifies JWT using flask_jwt_extended and extracts
    trusted identity & scope.

    Returns:
        {
            "user_id": int,
            "role": str,
            "company_id": int,
            "jti": str
        }

    Raises:
        JWTContextError
    """

    try:
        verify_jwt_in_request()
    except Exception:
        raise JWTContextError("Invalid or missing JWT")

    jwt_data = get_jwt()
    user_id = get_jwt_identity()

    role = jwt_data.get("role")
    company_id = jwt_data.get("company_id")
    jti = jwt_data.get("jti")

    if not user_id or not role or not company_id or not jti:
        raise JWTContextError("JWT missing required claims")

    return {
        "user_id": user_id,
        "role": role,
        "company_id": company_id,
        "jti": jti,
    }
