# extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask import request

# =====================================================
# Database instance (SINGLE SOURCE)
# =====================================================
db = SQLAlchemy()


# =====================================================
# Rate limit key function
# =====================================================
def rate_limit_key():
    """
    STRICT rate-limit key:
    ONLY license_key + fingerprint
    """

    data = request.get_json(silent=True) or {}

    license_key = (
        data.get("license_key")
        or request.headers.get("X-License-Key")
    )

    fingerprint = (
        data.get("fingerprint")
        or request.headers.get("X-Device-Fingerprint")
    )

    # isolate invalid identities
    if not license_key or not fingerprint:
        return f"invalid:{request.remote_addr}"

    return f"{license_key}:{fingerprint}"


# =====================================================
# Global limiter instance
# =====================================================
limiter = Limiter(
    key_func=rate_limit_key,
    default_limits=["200 per day", "50 per hour"],
)
