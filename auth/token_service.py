import os
from datetime import timedelta
from cryptography.fernet import Fernet

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 📁 Dedicated database directory
DB_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(DB_DIR, exist_ok=True)


class Config:
    # 🔐 Flask secret key
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-change-this"
    )

    # 🗄️ Database (SQLite in /database folder)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    "sqlite:///" + os.path.abspath(os.path.join(DB_DIR, "alss.db"))
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 🔑 JWT configuration
    JWT_SECRET_KEY = os.environ.get(
        "JWT_SECRET_KEY",
        "jwt-dev-secret-change-this"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=10)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=14)

    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # 🔒 Encryption key (for license keys, secrets, etc.)
    # ⚠️ In production, ALWAYS set ALSS_ENCRYPTION_KEY as env variable
    ENCRYPTION_KEY = os.environ.get(
        "ALSS_ENCRYPTION_KEY",
        Fernet.generate_key()
    )
