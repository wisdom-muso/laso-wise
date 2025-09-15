#!/bin/bash

# =============================================================================
# LASO Healthcare System - Migration Runner Script
# =============================================================================
# This script runs Django migrations and creates an admin user
# Use this if you already have the system set up and just need to run migrations
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - adjust these paths if needed
PROJECT_DIR="/opt/laso/laso-wise"
VENV_DIR="$PROJECT_DIR/venv"
APP_USER="laso"

# Alternative paths for different setups
if [ ! -d "$PROJECT_DIR" ]; then
    PROJECT_DIR="$(pwd)"
    VENV_DIR="$PROJECT_DIR/venv"
    APP_USER="$(whoami)"
fi

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Check Environment
# =============================================================================

check_environment() {
    log_info "Checking environment..."
    
    # Check if we're in the right directory
    if [ ! -f "manage.py" ]; then
        log_error "manage.py not found. Please run this script from the Django project directory."
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        log_warning "Virtual environment not found at $VENV_DIR"
        log_info "Creating virtual environment..."
        python3 -m venv venv
        VENV_DIR="$(pwd)/venv"
        log_info "Installing requirements..."
        $VENV_DIR/bin/pip install --upgrade pip
        $VENV_DIR/bin/pip install -r requirements.txt
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_warning ".env file not found. Creating basic configuration..."
        create_basic_env
    fi
    
    log_success "Environment check completed"
}

# =============================================================================
# Create Basic Environment Configuration
# =============================================================================

create_basic_env() {
    log_info "Creating basic .env configuration..."
    
    # Generate secret key using openssl instead of Django
    SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
    
    cat > .env << EOF
# Django Settings
SECRET_KEY=$SECRET_KEY
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*

# Database Configuration (SQLite for development)
USE_SQLITE=True

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Security Settings
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
EOF
    
    log_success "Basic .env file created"
}

# =============================================================================
# Run Migrations
# =============================================================================

run_migrations() {
    log_info "Running database migrations..."
    
    cd "$PROJECT_DIR"
    
    # Activate virtual environment and run migrations
    source $VENV_DIR/bin/activate
    
    # Load environment variables from .env file
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    # Make migrations for all apps
    log_info "Making migrations..."
    python manage.py makemigrations users
    python manage.py makemigrations core
    python manage.py makemigrations appointments
    python manage.py makemigrations treatments
    python manage.py makemigrations telemedicine
    
    # Run migrations
    log_info "Applying migrations..."
    python manage.py migrate
    
    # Collect static files
    log_info "Collecting static files..."
    python manage.py collectstatic --noinput
    
    log_success "Migrations completed successfully"
}

# =============================================================================
# Create Admin User
# =============================================================================

create_admin_user() {
    log_info "Creating admin user..."
    
    cd "$PROJECT_DIR"
    source $VENV_DIR/bin/activate
    
    # Load environment variables from .env file
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    # Check if admin user already exists
    ADMIN_EXISTS=$(python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.filter(username='admin').exists())
" 2>/dev/null)
    
    if [ "$ADMIN_EXISTS" = "True" ]; then
        log_warning "Admin user already exists"
        read -p "Do you want to reset the admin password? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            reset_admin_password
        fi
    else
        # Generate admin password
        ADMIN_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/" 2>/dev/null || echo "admin123")
        
        python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin', 'admin@laso-healthcare.com', '$ADMIN_PASSWORD')
print('Admin user created successfully')
EOF
        
        # Save admin credentials
        cat > admin_credentials.txt << EOF
LASO Healthcare Management System - Admin Credentials
Generated on: $(date)

Username: admin
Password: $ADMIN_PASSWORD
Email: admin@laso-healthcare.com

IMPORTANT: Please change this password after first login!
Access the admin panel at: http://localhost:8000/admin
EOF
        
        chmod 600 admin_credentials.txt
        
        log_success "Admin user created. Credentials saved to admin_credentials.txt"
    fi
}

# =============================================================================
# Reset Admin Password
# =============================================================================

reset_admin_password() {
    log_info "Resetting admin password..."
    
    # Generate new admin password
    ADMIN_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/" 2>/dev/null || echo "admin123")
    
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
admin_user = User.objects.get(username='admin')
admin_user.set_password('$ADMIN_PASSWORD')
admin_user.save()
print('Admin password reset successfully')
EOF
    
    # Update credentials file
    cat > admin_credentials.txt << EOF
LASO Healthcare Management System - Admin Credentials
Updated on: $(date)

Username: admin
Password: $ADMIN_PASSWORD
Email: admin@laso-healthcare.com

IMPORTANT: Please change this password after first login!
Access the admin panel at: http://localhost:8000/admin
EOF
    
    chmod 600 admin_credentials.txt
    
    log_success "Admin password reset. New credentials saved to admin_credentials.txt"
}

# =============================================================================
# Test Database Connection
# =============================================================================

test_database() {
    log_info "Testing database connection..."
    
    cd "$PROJECT_DIR"
    source $VENV_DIR/bin/activate
    
    # Ensure we're using SQLite for development
    export USE_SQLITE=True
    unset DATABASE_URL  # Remove any PostgreSQL URL that might interfere
    
    python manage.py check --database default
    
    if [ $? -eq 0 ]; then
        log_success "Database connection test passed"
    else
        log_error "Database connection test failed"
        log_info "Attempting to fix database configuration..."
        
        # Try to fix the configuration
        if [ -f "fix-database-config.sh" ]; then
            ./fix-database-config.sh
            log_info "Retrying database connection..."
            python manage.py check --database default
            if [ $? -eq 0 ]; then
                log_success "Database connection fixed and working!"
            else
                log_error "Database configuration could not be fixed automatically."
                log_error "Please run: ./fix-database-config.sh manually"
                exit 1
            fi
        else
            log_error "Database configuration fix script not found."
            log_error "Please ensure your .env file has USE_SQLITE=True"
            exit 1
        fi
    fi
}

# =============================================================================
# Start Development Server
# =============================================================================

start_dev_server() {
    log_info "Starting development server..."
    
    cd "$PROJECT_DIR"
    source $VENV_DIR/bin/activate
    
    log_success "Starting Django development server on http://localhost:8000"
    log_info "Press Ctrl+C to stop the server"
    log_info "Admin panel: http://localhost:8000/admin"
    
    python manage.py runserver 0.0.0.0:8000
}

# =============================================================================
# Show Help
# =============================================================================

show_help() {
    cat << EOF
LASO Healthcare System - Migration Runner

This script helps you run Django migrations and set up admin access.

Usage:
    ./run-migrations.sh [OPTIONS]

Options:
    --migrate-only      Only run migrations, don't create admin user
    --admin-only        Only create/reset admin user, don't run migrations
    --start-server      Start development server after migrations
    --help              Show this help message

Examples:
    ./run-migrations.sh                    # Run migrations and create admin
    ./run-migrations.sh --migrate-only     # Only run migrations
    ./run-migrations.sh --start-server     # Run migrations and start server

EOF
}

# =============================================================================
# Main Script Logic
# =============================================================================

main() {
    local migrate_only=false
    local admin_only=false
    local start_server=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --migrate-only)
                migrate_only=true
                shift
                ;;
            --admin-only)
                admin_only=true
                shift
                ;;
            --start-server)
                start_server=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log_info "Starting LASO Healthcare System migration process..."
    
    check_environment
    test_database
    
    if [ "$admin_only" = false ]; then
        run_migrations
    fi
    
    if [ "$migrate_only" = false ]; then
        create_admin_user
    fi
    
    if [ "$start_server" = true ]; then
        start_dev_server
    else
        cat << EOF

${GREEN}=============================================================================
🎉 Migration Process Complete!
=============================================================================${NC}

${BLUE}📋 What was done:${NC}
   ✅ Database migrations applied
   ✅ Static files collected
   ✅ Admin user configured

${BLUE}🔐 Admin Access:${NC}
   Check the file: admin_credentials.txt
   
${BLUE}🚀 Next Steps:${NC}
   1. Start the development server: python manage.py runserver
   2. Access admin panel: http://localhost:8000/admin
   3. Login with credentials from admin_credentials.txt

${BLUE}🔧 Useful Commands:${NC}
   Start server:     python manage.py runserver 0.0.0.0:8000
   Create user:      python manage.py createsuperuser
   Shell access:     python manage.py shell
   
EOF
    fi
    
    log_success "Process completed successfully!"
}

# Run main function
main "$@"