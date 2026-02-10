from app import create_app
from models import db, User, Company
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():

    # =========================
    # COMPANY
    # =========================
    company = Company.query.filter_by(name="Acme Corp").first()
    if not company:
        company = Company(name="Acme Corp", status="ACTIVE")
        db.session.add(company)
        db.session.commit()
        print("Company created: Acme Corp")

    # =========================
    # SUPER ADMIN (GLOBAL)
    # =========================
    if not User.query.filter_by(username="superadmin").first():
        db.session.add(User(
            username="superadmin",
            email="super@alss.local",
            role="SUPER_ADMIN",
            password_hash=generate_password_hash("Super@123"),
            company_id=None
        ))
        print("SUPER_ADMIN created")

    # =========================
    # COMPANY ADMIN
    # =========================
    if not User.query.filter_by(username="admin1").first():
        db.session.add(User(
            username="admin1",
            email="admin@acme.local",
            role="COMPANY_ADMIN",
            password_hash=generate_password_hash("Admin@123"),
            company_id=company.id
        ))
        print("COMPANY_ADMIN created")

    # =========================
    # COMPANY VIEWER
    # =========================
    if not User.query.filter_by(username="viewer1").first():
        db.session.add(User(
            username="viewer1",
            email="viewer@acme.local",
            role="COMPANY_VIEWER",
            password_hash=generate_password_hash("Viewer@123"),
            company_id=company.id
        ))
        print("COMPANY_VIEWER created")

    db.session.commit()

print("✔ User bootstrap completed.")
