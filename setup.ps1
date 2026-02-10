# ALSS Automated Setup Script for Windows PowerShell
# Run with: PowerShell -ExecutionPolicy Bypass -File setup.ps1

# Color functions
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Print-Info($message) {
    Write-ColorOutput Cyan "ℹ $message"
}

function Print-Success($message) {
    Write-ColorOutput Green "✓ $message"
}

function Print-Warning($message) {
    Write-ColorOutput Yellow "⚠ $message"
}

function Print-Error($message) {
    Write-ColorOutput Red "✗ $message"
}

function Print-Header($message) {
    Write-Host ""
    Write-ColorOutput Cyan "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-ColorOutput Cyan "  $message"
    Write-ColorOutput Cyan "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host ""
}

# Main script starts here
Clear-Host
Print-Header "🚀 ALSS Automated Setup Script"

# Ask user which setup method they prefer
Write-Host ""
Write-Host "Choose your setup method:"
Write-Host "1) Docker (Recommended - Fast & Easy)"
Write-Host "2) Manual Python Setup"
Write-Host ""
$setupChoice = Read-Host "Enter your choice (1 or 2)"

if ($setupChoice -eq "1") {
    $SETUP_METHOD = "docker"
    Print-Info "Using Docker setup method"
} elseif ($setupChoice -eq "2") {
    $SETUP_METHOD = "manual"
    Print-Info "Using manual Python setup method"
} else {
    Print-Error "Invalid choice. Exiting."
    exit 1
}

# Step 1: Check prerequisites
Print-Header "📋 Step 1: Checking Prerequisites"

if ($SETUP_METHOD -eq "docker") {
    # Check Docker
    try {
        $null = docker --version
        Print-Success "Docker is installed"
    } catch {
        Print-Error "Docker is not installed. Please install Docker Desktop for Windows first."
        Write-Host "Visit: https://docs.docker.com/desktop/install/windows-install/"
        exit 1
    }

    # Check Docker Compose
    try {
        $null = docker-compose --version
        Print-Success "Docker Compose is installed"
    } catch {
        try {
            $null = docker compose version
            Print-Success "Docker Compose is installed"
        } catch {
            Print-Error "Docker Compose is not installed. Please install Docker Compose first."
            exit 1
        }
    }
} else {
    # Check Python
    try {
        $null = python --version
        Print-Success "Python is installed"
    } catch {
        Print-Error "Python is not installed. Please install Python 3.8+ first."
        Write-Host "Visit: https://www.python.org/downloads/"
        exit 1
    }

    # Check pip
    try {
        $null = pip --version
        Print-Success "pip is installed"
    } catch {
        Print-Error "pip is not installed. Please install pip first."
        exit 1
    }
}

# Step 2: Environment Configuration
Print-Header "⚙️  Step 2: Environment Configuration"

if (-not (Test-Path .env)) {
    Print-Info "Creating .env file from template..."
    Copy-Item .env.example .env
    Print-Success ".env file created"
    
    # Generate secure keys
    Print-Info "Generating secure keys..."
    
    # Generate SECRET_KEY
    $SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
    
    # Generate JWT_SECRET_KEY
    $JWT_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
    
    # Generate ENCRYPTION_KEY
    $ENCRYPTION_KEY = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    
    # Update .env file
    (Get-Content .env) -replace 'SECRET_KEY=.*', "SECRET_KEY=$SECRET_KEY" | Set-Content .env
    (Get-Content .env) -replace 'JWT_SECRET_KEY=.*', "JWT_SECRET_KEY=$JWT_SECRET_KEY" | Set-Content .env
    (Get-Content .env) -replace 'ENCRYPTION_KEY=.*', "ENCRYPTION_KEY=$ENCRYPTION_KEY" | Set-Content .env
    
    Print-Success "Secure keys generated and configured"
} else {
    Print-Warning ".env file already exists, skipping..."
}

# Step 3: Setup based on method
if ($SETUP_METHOD -eq "docker") {
    Print-Header "🐳 Step 3: Docker Setup"
    
    # Build and start containers
    Print-Info "Building Docker containers (this may take a few minutes)..."
    docker-compose build
    Print-Success "Docker containers built"
    
    Print-Info "Starting containers..."
    docker-compose up -d
    Print-Success "Containers started"
    
    # Wait for container to be ready
    Print-Info "Waiting for application to be ready..."
    Start-Sleep -Seconds 5
    
    # Initialize database
    Print-Header "💾 Step 4: Database Initialization"
    Print-Info "Running database migrations..."
    try {
        docker-compose exec -T web flask db upgrade
    } catch {
        Print-Warning "Migrations may need manual setup"
    }
    
    Print-Info "Creating admin user..."
    try {
        docker-compose exec -T web python create_admin.py
    } catch {
        Print-Warning "Admin user may need manual creation"
    }
    
    Print-Success "Database initialized"
    
} else {
    Print-Header "🐍 Step 3: Python Environment Setup"
    
    # Create virtual environment
    if (-not (Test-Path venv)) {
        Print-Info "Creating virtual environment..."
        python -m venv venv
        Print-Success "Virtual environment created"
    } else {
        Print-Warning "Virtual environment already exists, skipping..."
    }
    
    # Activate virtual environment
    Print-Info "Activating virtual environment..."
    & .\venv\Scripts\Activate.ps1
    
    # Install dependencies
    Print-Info "Installing dependencies (this may take a few minutes)..."
    pip install -r requirements.txt --quiet
    Print-Success "Dependencies installed"
    
    # Initialize database
    Print-Header "💾 Step 4: Database Initialization"
    
    # Create database directory
    if (-not (Test-Path database)) {
        New-Item -ItemType Directory -Path database | Out-Null
    }
    
    Print-Info "Initializing database..."
    try {
        flask db init
    } catch {
        Print-Warning "Database already initialized"
    }
    
    try {
        flask db migrate -m "Initial migration"
    } catch {
        Print-Warning "Migration may already exist"
    }
    
    flask db upgrade
    Print-Success "Database migrations completed"
    
    Print-Info "Creating admin user..."
    try {
        python create_admin.py
        Print-Success "Admin user created"
    } catch {
        Print-Warning "Admin user creation may need manual setup"
    }
}

# Final summary
Print-Header "✅ Setup Complete!"

Write-Host ""
Write-Host "🎉 ALSS has been successfully set up!"
Write-Host ""
Write-Host "📝 Next Steps:"
Write-Host ""

if ($SETUP_METHOD -eq "docker") {
    Write-Host "1. Access the application:"
    Write-Host "   🌐 Web Interface: http://localhost:5000"
    Write-Host "   👨‍💼 Admin Panel: http://localhost:5000/admin/dashboard"
    Write-Host ""
    Write-Host "2. Default login credentials:"
    Write-Host "   Username: admin"
    Write-Host "   Password: changeme123"
    Write-Host ""
    Write-Host "3. Useful Docker commands:"
    Write-Host "   • View logs:     docker-compose logs -f"
    Write-Host "   • Stop:          docker-compose stop"
    Write-Host "   • Start:         docker-compose start"
    Write-Host "   • Restart:       docker-compose restart"
    Write-Host ""
} else {
    Write-Host "1. Start the application:"
    Write-Host "   .\venv\Scripts\Activate.ps1  # Activate virtual environment"
    Write-Host "   flask run                     # Start server"
    Write-Host ""
    Write-Host "2. Access the application:"
    Write-Host "   🌐 Web Interface: http://localhost:5000"
    Write-Host "   👨‍💼 Admin Panel: http://localhost:5000/admin/dashboard"
    Write-Host ""
    Write-Host "3. Default login credentials:"
    Write-Host "   Username: admin"
    Write-Host "   Password: changeme123"
    Write-Host ""
}

Write-Host "⚠️  IMPORTANT: Change the default admin password immediately!"
Write-Host ""
Write-Host "📚 For more information:"
Write-Host "   • Quick Start Guide: QUICKSTART.md"
Write-Host "   • Docker Guide: DOCKER.md"
Write-Host "   • Architecture: README.md"
Write-Host ""

Print-Success "Happy licensing! 🎉"
Write-Host ""
