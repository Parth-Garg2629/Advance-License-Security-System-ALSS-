import os
from datetime import timedelta
from cryptography.fernet import Fernet

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 📁 Dedicated database directory
DB_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DB_DIR, exist_ok=True)


class Config:
    # =====================================================
    # Flask Core
    # =====================================================

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-change-this"
    )

    # Reject very large payloads (anti-abuse)
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024   # 1 MB

    # Fail fast on malformed JSON
    JSON_AS_ASCII = False
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False

    # =====================================================
    # Database
    # =====================================================

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.abspath(os.path.join(DB_DIR, "alss.db"))
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # =====================================================
    # JWT — Token & Session Hardening (STEP 3)
    # =====================================================

    JWT_SECRET_KEY = os.environ.get(
        "JWT_SECRET_KEY",
        "jwt-dev-secret-change-this"
    )

    # 🔒 Short-lived access token
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=10)

    # 🔄 Rotating refresh token (longer-lived)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=14)

    # Tokens only via headers (no cookies)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # Explicit (clarity > magic)
    JWT_COOKIE_CSRF_PROTECT = False

    # =====================================================
    # Encryption (at rest)
    # =====================================================

    # ⚠️ In production, ALWAYS set ALSS_ENCRYPTION_KEY in env
    ENCRYPTION_KEY = os.environ.get(
        "ALSS_ENCRYPTION_KEY",
        Fernet.generate_key()
    )
