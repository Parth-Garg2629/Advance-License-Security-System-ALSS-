from flask import Flask, render_template, redirect, request
from werkzeug.exceptions import HTTPException

from config import Config
from models import db, TokenBlocklist, User

# Blueprints
from auth.auth_routes import auth_bp
from routes.api_routes import api_bp
from routes.admin_routes import admin_bp
from routes.client_routes import client_bp
from super_admin.super_admin_routes import super_admin_bp

# Extensions
from extensions import limiter
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_login import LoginManager, current_user

from logging_config import setup_logging

migrate = Migrate()
jwt = JWTManager()
login_manager = LoginManager()


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # =====================
    # CONFIG
    # =====================
    app.config.from_object(Config)

    # =====================
    # EXTENSIONS
    # =====================
    db.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Flask-Login (UI session only)
    login_manager.init_app(app)
    login_manager.login_view = "login_page"

    # =====================
    # USER LOADER
    # =====================
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # =====================
    # BLUEPRINTS
    # =====================
    app.register_blueprint(auth_bp)                    # /auth/*
    app.register_blueprint(api_bp, url_prefix="/api")  # /api/*
    app.register_blueprint(admin_bp)                   # /admin/*
    app.register_blueprint(client_bp)                  # /client/*
    app.register_blueprint(super_admin_bp)             # /super/*

    # =====================
    # ROOT
    # =====================
    @app.route("/")
    def root():
        return redirect("/login")

    # =====================
    # LOGIN PAGE (UI ONLY)
    # =====================
    @app.route("/login", methods=["GET"])
    def login_page():
        return render_template("login.html")

    # =====================
    # CHANGE PASSWORD UI GATEWAY (ROLE AWARE)
    # =====================
    @app.route("/change-password", methods=["GET"])
    def change_password_ui():
        # Not logged in
        if not current_user.is_authenticated:
            return redirect("/login")

        # Only CLIENT with temp password allowed
        if (
            current_user.role == "COMPANY_VIEWER"
            and current_user.is_temp_password
        ):
            return redirect("/auth/change-password")

        # Everyone else -> their dashboards
        if current_user.role == "SUPER_ADMIN":
            return redirect("/super/dashboard")

        if current_user.role == "COMPANY_ADMIN":
            return redirect("/admin/dashboard")

        return redirect("/client/dashboard")

    # =====================
    # UI GATE (SAFE, NON-INTRUSIVE)
    # =====================
    @app.before_request
    def ui_gate():
        path = request.path

        # Static & auth allowed
        if (
            path.startswith("/static/")
            or path == "/login"
            or path.startswith("/auth/")
        ):
            return

        # APIs handle auth internally
        if (
            path.startswith("/admin/api")
            or path.startswith("/client/api")
            or path.startswith("/api/")
        ):
            return

        return

    # =====================
    # SECURITY HEADERS
    # =====================
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    # =====================
    # LOGGING
    # =====================
    setup_logging(app)

    return app


# =====================
# JWT BLOCKLIST CHECK
# =====================
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload.get("jti")
    if not jti:
        return False
    return TokenBlocklist.query.filter_by(jti=jti).first() is not None


# =====================
# RUN (DEV ONLY)
# =====================
if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        db.create_all()

    app.run(debug=True)
