# 🚀 ALSS Quick Start Guide

Get your Advanced License Security System up and running in minutes!

## 📋 Prerequisites

**Choose Your Setup Method:**

### 🐳 Docker (Recommended - Easiest)
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Git** (optional, for cloning)

### 🐍 Manual Python Setup
- **Python 3.8+** installed
- **pip** package manager
- **Git** (optional, for cloning)

---

## 🐳 Quick Setup with Docker (Recommended - 3 Minutes)

### 1️⃣ Clone the Project

```bash
git clone https://github.com/Parth-Garg2629/Advance-License-Security-System-ALSS-.git
cd ALSS_web2
```

### 2️⃣ Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Generate secure keys
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())" >> .env
```

Edit `.env` and update the keys that were just generated.

### 3️⃣ Start with Docker Compose

```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4️⃣ Initialize Database

```bash
# Access the container
docker-compose exec web bash

# Initialize database
flask db upgrade
python create_admin.py

# Exit container
exit
```

### 5️⃣ Access the Application

- **Web Interface**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin/dashboard

**Default Login:**
- Username: `admin`
- Password: `changeme123`

**📖 For complete Docker documentation, see [DOCKER.md](DOCKER.md)**

---

## 🐍 Manual Setup (Alternative Method)

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

### Docker Commands

```bash
# Stop containers
docker-compose stop

# Start containers
docker-compose start

# Restart containers
docker-compose restart

# View logs
docker-compose logs -f

# Access container shell
docker-compose exec web bash

# Rebuild and restart
docker-compose up -d --build
```

### Create a New Admin User

**Docker:**
```bash
docker-compose exec web python -c "from app import app, db; from models import User; \
user = User(username='newadmin', email='admin@company.com', role='SUPER_ADMIN'); \
user.set_password('NewPassword123'); \
with app.app_context(): db.session.add(user); db.session.commit(); \
print('Admin user created!')"
```

**Manual:**
```bash
python -c "from app import app, db; from models import User; \
user = User(username='newadmin', email='admin@company.com', role='SUPER_ADMIN'); \
user.set_password('NewPassword123'); \
with app.app_context(): db.session.add(user); db.session.commit(); \
print('Admin user created!')"
```

### Reset Database

**Docker:**
```bash
# ⚠️ WARNING: This deletes all data!
docker-compose exec web flask db downgrade base
docker-compose exec web flask db upgrade
```

**Manual:**
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

**Docker:**
```bash
docker-compose exec web pytest
# Or with coverage
docker-compose exec web pytest --cov=.
```

**Manual:**
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

### Docker Issues

```bash
# Container won't start
docker-compose logs web

# Port already in use
# Edit docker-compose.yml, change ports: - "5001:5000"

# Rebuild from scratch
docker-compose down -v
docker-compose up -d --build
```

### Database Locked Error

**Docker:**
```bash
docker-compose exec web flask db upgrade --sql > migration.sql
docker-compose exec web sqlite3 database/alss.db < migration.sql
```

**Manual:**
```bash
# Close all connections, then:
flask db upgrade --sql > migration.sql
sqlite3 database/alss.db < migration.sql
```

### Port Already in Use

**Docker:**
Edit `docker-compose.yml` and change the port mapping:
```yaml
ports:
  - "5001:5000"  # Changed from 5000:5000
```

**Manual:**
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

**Docker:**
```bash
docker-compose exec web rm -rf migrations/
docker-compose exec web flask db init
docker-compose exec web flask db migrate -m "Initial migration"
docker-compose exec web flask db upgrade
```

**Manual:**
```bash
# Remove migrations and restart
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

---

## 📖 Next Steps

- 🐳 **Docker Users**: Read [DOCKER.md](DOCKER.md) for production deployment and advanced configuration
- 📘 Read the full [README.md](README.md) for architecture details
- 🔒 Review security best practices
- 🧪 Set up automated testing
- 🚀 Deploy to production

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
