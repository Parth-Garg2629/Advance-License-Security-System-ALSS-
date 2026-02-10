# 🚀 ALSS Quick Start Guide

Get your Advanced License Security System up and running in minutes!

## 📋 Prerequisites

- **Python 3.8+** installed
- **pip** package manager
- **Git** (optional, for cloning)

## ⚡ Quick Setup (5 Minutes)

### 1️⃣ Clone or Download the Project

```bash
git clone <your-repo-url>
cd ALSS_web2
```

### 2️⃣ Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux
```

Edit `.env` and configure:

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-this-in-production

# Database
DATABASE_URI=sqlite:///database/alss.db

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production
JWT_ACCESS_TOKEN_EXPIRES=600         # 10 minutes
JWT_REFRESH_TOKEN_EXPIRES=1209600    # 14 days

# Encryption Key (Generate using: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-fernet-encryption-key-here

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=changeme123  # Change immediately after first login!
```

### 5️⃣ Initialize Database

```bash
# Create database directory
mkdir database

# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade

# Create default admin user (if script exists)
python create_admin.py
```

### 6️⃣ Run the Application

```bash
flask run
```

Or with custom host/port:

```bash
flask run --host=0.0.0.0 --port=5000
```

### 7️⃣ Access the Application

Open your browser and navigate to:

- **Web Interface**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin/dashboard
- **API Docs**: http://localhost:5000/api/docs (if available)

**Default Login:**
- Username: `admin`
- Password: `changeme123` (or what you set in .env)

---

## 🔧 Common Tasks

### Create a New Admin User

```bash
python -c "from app import app, db; from models import User; \
user = User(username='newadmin', email='admin@company.com', role='SUPER_ADMIN'); \
user.set_password('NewPassword123'); \
with app.app_context(): db.session.add(user); db.session.commit(); \
print('Admin user created!')"
```

### Reset Database

```bash
# ⚠️ WARNING: This deletes all data!
flask db downgrade base
flask db upgrade
```

### Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Run Tests (if available)

```bash
pytest
# Or with coverage
pytest --cov=.
```

---

## 📚 User Roles & Access

| Role | Access Level | Permissions |
|------|--------------|-------------|
| **SUPER_ADMIN** | Global | All companies, users, licenses, system settings |
| **COMPANY_ADMIN** | Company | Company licenses, devices, users, audit logs |
| **COMPANY_VIEWER** | Company | Read-only access to company resources |

---

## 🔑 First Steps After Login

### For Super Admins:

1. **Change Default Password** → Settings → Change Password
2. **Create Company** → Super Admin → Companies → Add New
3. **Create Company Admin** → Super Admin → Users → Add New (assign to company)
4. **Configure System Settings** → Super Admin → Settings

### For Company Admins:

1. **Change Default Password** → Settings → Change Password
2. **Create License** → Admin Dashboard → Licenses → Create New
   - Set max devices (e.g., 5)
   - Set expiry date
   - Copy the license key
3. **Manage Users** → Admin Dashboard → Users → Add User
4. **Monitor Devices** → Admin Dashboard → Devices

---

## 🔌 API Usage (Client Software)

### 1. Activate License

**Endpoint:** `POST /api/activate`

```bash
curl -X POST http://localhost:5000/api/activate \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "your-license-key-here",
    "device_fingerprint": "unique-device-id-12345",
    "os_name": "Windows 11",
    "os_version": "10.0.22000",
    "machine_name": "DESKTOP-ABC123"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "License activated successfully",
  "activation_id": "abc123..."
}
```

### 2. Heartbeat (Verify License)

**Endpoint:** `POST /api/heartbeat`

```bash
curl -X POST http://localhost:5000/api/heartbeat \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "your-license-key-here",
    "device_fingerprint": "unique-device-id-12345"
  }'
```

### 3. Validate License

**Endpoint:** `POST /api/validate`

```bash
curl -X POST http://localhost:5000/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "your-license-key-here"
  }'
```

---

## 🐛 Troubleshooting

### Database Locked Error
```bash
# Close all connections, then:
flask db upgrade --sql > migration.sql
sqlite3 database/alss.db < migration.sql
```

### Port Already in Use
```bash
# Use different port
flask run --port=5001
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Migration Issues
```bash
# Remove migrations and restart
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

---

## 📖 Next Steps

- 📘 Read the full [README.md](README.md) for architecture details
- 🔒 Review security best practices
- 🧪 Set up automated testing
- 🚀 Deploy to production (see DEPLOYMENT.md if available)

---

## 💡 Quick Tips

- 🔐 **Always change default passwords** in production
- 🔑 **Keep encryption keys secure** - losing them means losing license data
- 📝 **Enable audit logging** to track all system activities
- 🔄 **Regular backups** of the database are essential
- ⏱️ **Monitor heartbeats** to track active licenses in real-time

---

## 🆘 Need Help?

- 📧 Email: support@yourcompany.com
- 📚 Documentation: [Full Docs](README.md)
- 🐞 Issues: [GitHub Issues](https://github.com/yourrepo/issues)

---

**Happy Licensing! 🎉**
