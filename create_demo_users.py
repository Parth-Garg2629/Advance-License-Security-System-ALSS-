from app import create_app
from models import db, User, Company
from werkzeug.security import generate_password_hash

app = create_app()
app.app_context().push()

# =========================
# COMPANY
# =========================
company = Company(name="ALSS_CORP", status="ACTIVE")
db.session.add(company)
db.session.commit()

# =========================
# SUPER ADMIN
# =========================
super_admin = User(
    username="superadmin",
    email="super@alss.local",
    password_hash=generate_password_hash("super123"),
    role="SUPER_ADMIN",
    company_id=company.id
)

# =========================
# COMPANY ADMIN
# =========================
admin = User(
    username="admin1",
    email="admin@alss.local",
    password_hash=generate_password_hash("admin123"),
    role="COMPANY_ADMIN",
    company_id=company.id
)

# =========================
# CLIENT / VIEWER
# =========================
client = User(
    username="client1",
    email="client@alss.local",
    password_hash=generate_password_hash("client123"),
    role="COMPANY_VIEWER",
    company_id=company.id
)

db.session.add_all([super_admin, admin, client])
db.session.commit()

print("ALL USERS CREATED SUCCESSFULLY")

'''
username: superadmin
password: super123
username: admin1
password: admin123
username: client1
password: client123

'''