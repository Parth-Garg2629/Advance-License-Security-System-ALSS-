from werkzeug.security import generate_password_hash
from app import create_app
from models import db, User

app = create_app()

USERNAME = "admin"
PASSWORD = "admin123"  # jo chaaho rakh sakta hai, bas yaad rakhna


def seed_admin():
    with app.app_context():
        existing = User.query.filter_by(username=USERNAME).first()
        if existing:
            print("Admin user already exists:", existing.username)
            return

        admin = User(
            username=USERNAME,
            email="admin@example.com",
            password_hash=generate_password_hash(PASSWORD),
            role="ADMIN",
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created:")
        print("  username:", USERNAME)
        print("  password:", PASSWORD)


if __name__ == "__main__":
    seed_admin()
