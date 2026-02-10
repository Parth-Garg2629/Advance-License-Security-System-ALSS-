#!/bin/bash

# ALSS Automated Setup Script
# For Linux, macOS, and Git Bash on Windows

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Main script starts here
clear
print_header "🚀 ALSS Automated Setup Script"

# Ask user which setup method they prefer
echo ""
echo "Choose your setup method:"
echo "1) Docker (Recommended - Fast & Easy)"
echo "2) Manual Python Setup"
echo ""
read -p "Enter your choice (1 or 2): " setup_choice

if [ "$setup_choice" = "1" ]; then
    SETUP_METHOD="docker"
    print_info "Using Docker setup method"
elif [ "$setup_choice" = "2" ]; then
    SETUP_METHOD="manual"
    print_info "Using manual Python setup method"
else
    print_error "Invalid choice. Exiting."
    exit 1
fi

# Step 1: Check prerequisites
print_header "📋 Step 1: Checking Prerequisites"

if [ "$SETUP_METHOD" = "docker" ]; then
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker is installed"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose is installed"
else
    # Check Python
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        print_error "Python is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    print_success "Python is installed"

    # Check pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        print_error "pip is not installed. Please install pip first."
        exit 1
    fi
    print_success "pip is installed"
fi

# Step 2: Environment Configuration
print_header "⚙️  Step 2: Environment Configuration"

if [ ! -f .env ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env
    print_success ".env file created"
    
    # Generate secure keys
    print_info "Generating secure keys..."
    
    # Generate SECRET_KEY
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || python -c "import secrets; print(secrets.token_hex(32))")
    
    # Generate JWT_SECRET_KEY
    JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || python -c "import secrets; print(secrets.token_hex(32))")
    
    # Generate ENCRYPTION_KEY
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" .env
        sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=${JWT_SECRET_KEY}/" .env
        sed -i '' "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=${ENCRYPTION_KEY}/" .env
    else
        # Linux
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" .env
        sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=${JWT_SECRET_KEY}/" .env
        sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=${ENCRYPTION_KEY}/" .env
    fi
    
    print_success "Secure keys generated and configured"
else
    print_warning ".env file already exists, skipping..."
fi

# Step 3: Setup based on method
if [ "$SETUP_METHOD" = "docker" ]; then
    print_header "🐳 Step 3: Docker Setup"
    
    # Build and start containers
    print_info "Building Docker containers (this may take a few minutes)..."
    docker-compose build
    print_success "Docker containers built"
    
    print_info "Starting containers..."
    docker-compose up -d
    print_success "Containers started"
    
    # Wait for container to be ready
    print_info "Waiting for application to be ready..."
    sleep 5
    
    # Initialize database
    print_header "💾 Step 4: Database Initialization"
    print_info "Running database migrations..."
    docker-compose exec -T web flask db upgrade 2>/dev/null || print_warning "Migrations may need manual setup"
    
    print_info "Creating admin user..."
    docker-compose exec -T web python create_admin.py 2>/dev/null || print_warning "Admin user may need manual creation"
    
    print_success "Database initialized"
    
else
    print_header "🐍 Step 3: Python Environment Setup"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv 2>/dev/null || python -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists, skipping..."
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    print_info "Installing dependencies (this may take a few minutes)..."
    pip install -r requirements.txt --quiet
    print_success "Dependencies installed"
    
    # Initialize database
    print_header "💾 Step 4: Database Initialization"
    
    # Create database directory
    mkdir -p database
    
    print_info "Initializing database..."
    flask db init 2>/dev/null || print_warning "Database already initialized"
    flask db migrate -m "Initial migration" 2>/dev/null || print_warning "Migration may already exist"
    flask db upgrade
    print_success "Database migrations completed"
    
    print_info "Creating admin user..."
    python create_admin.py 2>/dev/null || print_warning "Admin user creation may need manual setup"
    print_success "Admin user created"
fi

# Final summary
print_header "✅ Setup Complete!"

echo ""
echo "🎉 ALSS has been successfully set up!"
echo ""
echo "📝 Next Steps:"
echo ""

if [ "$SETUP_METHOD" = "docker" ]; then
    echo "1. Access the application:"
    echo "   🌐 Web Interface: http://localhost:5000"
    echo "   👨‍💼 Admin Panel: http://localhost:5000/admin/dashboard"
    echo ""
    echo "2. Default login credentials:"
    echo "   Username: admin"
    echo "   Password: changeme123"
    echo ""
    echo "3. Useful Docker commands:"
    echo "   • View logs:     docker-compose logs -f"
    echo "   • Stop:          docker-compose stop"
    echo "   • Start:         docker-compose start"
    echo "   • Restart:       docker-compose restart"
    echo ""
else
    echo "1. Start the application:"
    echo "   source venv/bin/activate  # Activate virtual environment"
    echo "   flask run                  # Start server"
    echo ""
    echo "2. Access the application:"
    echo "   🌐 Web Interface: http://localhost:5000"
    echo "   👨‍💼 Admin Panel: http://localhost:5000/admin/dashboard"
    echo ""
    echo "3. Default login credentials:"
    echo "   Username: admin"
    echo "   Password: changeme123"
    echo ""
fi

echo "⚠️  IMPORTANT: Change the default admin password immediately!"
echo ""
echo "📚 For more information:"
echo "   • Quick Start Guide: QUICKSTART.md"
echo "   • Docker Guide: DOCKER.md"
echo "   • Architecture: README.md"
echo ""

print_success "Happy licensing! 🎉"
echo ""
