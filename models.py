# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import pytz

from werkzeug.security import generate_password_hash, check_password_hash
from utils.crypto import encrypt_value, decrypt_value
from utils.time import to_ist

db = SQLAlchemy()
IST = pytz.timezone("Asia/Kolkata")


# =====================================================
# TIME HELPERS
# =====================================================

def utc_now():
    return datetime.utcnow()


# =====================================================
# Company
# =====================================================

class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    users = db.relationship("User", backref="company", lazy=True)
    licenses = db.relationship("License", backref="company", lazy=True)


# =====================================================
# User (Flask-Login compatible)
# =====================================================

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(30), nullable=False, default="COMPANY_VIEWER")
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)

    is_temp_password = db.Column(db.Boolean, default=True)
    password_changed_at = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    licenses = db.relationship("License", back_populates="vendor", lazy=True)
    audit_logs = db.relationship("AuditLog", back_populates="user", lazy=True)

    def set_password(self, raw: str, temp: bool = True):
        self.password_hash = generate_password_hash(raw)
        self.is_temp_password = temp
        self.password_changed_at = None if temp else utc_now()

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)


# =====================================================
# License
# =====================================================

class License(db.Model):
    __tablename__ = "licenses"

    id = db.Column(db.Integer, primary_key=True)
    _license_key = db.Column("license_key", db.Text, unique=True, nullable=False)

    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    status = db.Column(db.String(20), default="ACTIVE")
    max_devices = db.Column(db.Integer, default=1)
    expires_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    vendor = db.relationship("User", back_populates="licenses")
    activations = db.relationship("Activation", back_populates="license", lazy=True)
    audit_logs = db.relationship("AuditLog", back_populates="license", lazy=True)

    @property
    def key(self):
        """
        BACKWARD SAFE:
        - Old tokens that can't be decrypted won't crash APIs
        - UI will show masked placeholder instead
        """
        try:
            return decrypt_value(self._license_key)
        except Exception:
            return "[UNREADABLE_KEY]"

    @key.setter
    def key(self, raw):
        self._license_key = encrypt_value(raw)


# =====================================================
# Device
# =====================================================

class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    fingerprint = db.Column(db.String(64), unique=True, nullable=False)
    os_name = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(20), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=utc_now)
    last_seen_at = db.Column(db.DateTime, nullable=True)

    activations = db.relationship("Activation", back_populates="device", lazy=True)


# =====================================================
# Activation
# =====================================================

class Activation(db.Model):
    __tablename__ = "activations"

    id = db.Column(db.Integer, primary_key=True)
    license_id = db.Column(db.Integer, db.ForeignKey("licenses.id"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)

    status = db.Column(db.String(20), default="ACTIVE")
    activated_at = db.Column(db.DateTime, default=utc_now)
    deactivated_at = db.Column(db.DateTime, nullable=True)
    last_seen_at = db.Column(db.DateTime, nullable=True)

    license = db.relationship("License", back_populates="activations")
    device = db.relationship("Device", back_populates="activations")


# =====================================================
# Audit Log
# =====================================================

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    license_id = db.Column(db.Integer, db.ForeignKey("licenses.id"), nullable=True)

    status = db.Column(db.String(20), default="success")
    message = db.Column(db.Text, nullable=True)

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    extra_data = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    user = db.relationship("User", back_populates="audit_logs")
    license = db.relationship("License", back_populates="audit_logs")

    def get_extra_data(self):
        return self.extra_data

    def created_at_ist(self):
        return to_ist(self.created_at)


# =====================================================
# Token Blocklist
# =====================================================

class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=True)
    revoked_at = db.Column(db.DateTime, default=utc_now)
    reason = db.Column(db.String(255), nullable=True)
