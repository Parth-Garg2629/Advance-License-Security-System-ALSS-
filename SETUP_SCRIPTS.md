# 🔧 Automated Setup Scripts

ALSS provides automated setup scripts to get you started quickly!

## 📜 Available Scripts

### 🐧 Linux / macOS / Git Bash (setup.sh)
For Unix-based systems and Windows Git Bash users.

**Usage:**
```bash
# Make executable
chmod +x setup.sh

# Run the script
./setup.sh
```

### 🪟 Windows PowerShell (setup.ps1)
For Windows PowerShell users.

**Usage:**
```powershell
# Run with execution policy bypass
PowerShell -ExecutionPolicy Bypass -File setup.ps1
```

## ⚡ What the Scripts Do

Both scripts provide an **interactive setup** with two options:

1. **Docker Setup (Recommended)** - Fast, consistent, production-ready
2. **Manual Python Setup** - Traditional virtual environment approach

### Automated Steps:

✅ **Prerequisite Checks**
- Verifies Docker/Python installation
- Checks for required dependencies

✅ **Environment Configuration**
- Creates `.env` file from template
- Generates secure random keys:
  - `SECRET_KEY` (Flask session security)
  - `JWT_SECRET_KEY` (Token authentication)
  - `ENCRYPTION_KEY` (License encryption)

✅ **Application Setup**
- Docker: Builds containers and starts services
- Manual: Creates virtual environment and installs dependencies

✅ **Database Initialization**
- Runs migrations
- Creates default admin user

✅ **Ready to Use**
- Application accessible at http://localhost:5000
- Default credentials provided

## 🎯 Quick Start

### For Docker Users:

```bash
# Linux/Mac/Git Bash
./setup.sh

# Windows PowerShell
PowerShell -ExecutionPolicy Bypass -File setup.ps1

# Choose option 1 (Docker)
# Script handles everything automatically!
```

### For Manual Setup Users:

```bash
# Run the script
./setup.sh  # or setup.ps1 on Windows

# Choose option 2 (Manual Python)
# Script sets up virtual environment and dependencies
```

## 📝 After Setup

1. **Access the Application**
   - Web Interface: http://localhost:5000
   - Admin Panel: http://localhost:5000/admin/dashboard

2. **Default Credentials**
   - Username: `admin`
   - Password: `changeme123`

3. **⚠️ IMPORTANT**: Change the default password immediately!

## 🐛 Troubleshooting

### Script Permission Denied (Linux/Mac)

```bash
chmod +x setup.sh
./setup.sh
```

### PowerShell Execution Policy Error

```powershell
# Option 1: Run with bypass (recommended)
PowerShell -ExecutionPolicy Bypass -File setup.ps1

# Option 2: Change policy temporarily
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup.ps1
```

### Prerequisites Not Found

The script will tell you what's missing and provide download links.

**For Docker:**
- Install [Docker Desktop](https://docs.docker.com/get-docker/)

**For Manual Setup:**
- Install [Python 3.8+](https://www.python.org/downloads/)

## 🔄 Re-running the Script

The scripts are **idempotent** - safe to run multiple times:
- Skips existing `.env` file
- Skips existing virtual environment
- Won't overwrite your data

## 📚 More Information

- **Complete Guide**: See [QUICKSTART.md](QUICKSTART.md)
- **Docker Details**: See [DOCKER.md](DOCKER.md)
- **Architecture**: See [README.md](README.md)

---

**Enjoy your automated setup! 🎉**
