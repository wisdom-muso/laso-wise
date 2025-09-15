#!/bin/bash

# LASO Healthcare System Deployment Script
# This script automates the deployment process on a VPS

set -e

echo "🏥 LASO Healthcare System Deployment Script"
echo "==========================================="

# Configuration
APP_USER="laso"
APP_DIR="/opt/laso/laso-wise"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/opt/laso/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi
    
    if ! command_exists pip3; then
        missing_deps+=("python3-pip")
    fi
    
    if ! command_exists git; then
        missing_deps+=("git")
    fi
    
    if ! command_exists psql; then
        missing_deps+=("postgresql-client")
    fi
    
    if ! command_exists redis-cli; then
        missing_deps+=("redis-tools")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_status "Please install missing dependencies and run again"
        exit 1
    fi
    
    print_status "All prerequisites satisfied ✓"
}

# Setup virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        print_status "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    print_status "Virtual environment activated ✓"
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ -f "$APP_DIR/requirements.txt" ]; then
        pip install -r "$APP_DIR/requirements.txt"
        print_status "Dependencies installed ✓"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Check if .env file exists
    if [ ! -f "$APP_DIR/.env" ]; then
        print_error ".env file not found. Please create it with database configuration."
        exit 1
    fi
    
    # Run migrations
    cd "$APP_DIR"
    python manage.py migrate --settings=laso.settings_production
    print_status "Database migrations completed ✓"
}

# Collect static files
collect_static() {
    print_status "Collecting static files..."
    
    cd "$APP_DIR"
    python manage.py collectstatic --noinput --settings=laso.settings_production
    print_status "Static files collected ✓"
}

# Create log directory
setup_logs() {
    print_status "Setting up log directory..."
    
    if [ ! -d "$LOG_DIR" ]; then
        sudo mkdir -p "$LOG_DIR"
        sudo chown $APP_USER:$APP_USER "$LOG_DIR"
        print_status "Log directory created"
    else
        print_status "Log directory already exists"
    fi
}

# Test configuration
test_configuration() {
    print_status "Testing Django configuration..."
    
    cd "$APP_DIR"
    python manage.py check --settings=laso.settings_production
    
    if [ $? -eq 0 ]; then
        print_status "Configuration test passed ✓"
    else
        print_error "Configuration test failed"
        exit 1
    fi
}

# Restart services
restart_services() {
    print_status "Restarting services..."
    
    # Check if systemd services exist
    if systemctl list-unit-files | grep -q "laso-gunicorn.service"; then
        sudo systemctl restart laso-gunicorn
        print_status "Gunicorn restarted"
    else
        print_warning "laso-gunicorn service not found"
    fi
    
    if systemctl list-unit-files | grep -q "laso-celery.service"; then
        sudo systemctl restart laso-celery
        print_status "Celery restarted"
    else
        print_warning "laso-celery service not found"
    fi
    
    if systemctl list-unit-files | grep -q "nginx.service"; then
        sudo systemctl reload nginx
        print_status "Nginx reloaded"
    else
        print_warning "Nginx service not found"
    fi
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Check if services are running
    local services=("laso-gunicorn" "laso-celery" "postgresql" "redis-server" "nginx")
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            print_status "$service: Running ✓"
        else
            print_warning "$service: Not running"
        fi
    done
    
    # Test database connection
    cd "$APP_DIR"
    if python manage.py check --database default --settings=laso.settings_production >/dev/null 2>&1; then
        print_status "Database connection: OK ✓"
    else
        print_warning "Database connection: Failed"
    fi
}

# Main deployment function
deploy() {
    print_status "Starting deployment process..."
    
    check_prerequisites
    setup_venv
    install_dependencies
    setup_logs
    setup_database
    collect_static
    test_configuration
    restart_services
    health_check
    
    print_status "🎉 Deployment completed successfully!"
    print_status "Your LASO Healthcare System is now running."
    print_status ""
    print_status "Next steps:"
    print_status "1. Create a superuser: python manage.py createsuperuser --settings=laso.settings_production"
    print_status "2. Access your application at: https://your-domain.com"
    print_status "3. Access admin panel at: https://your-domain.com/admin/"
    print_status ""
    print_status "Logs are available at: $LOG_DIR"
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "check")
        check_prerequisites
        health_check
        ;;
    "restart")
        restart_services
        ;;
    "logs")
        print_status "Recent application logs:"
        tail -50 "$LOG_DIR/django.log" 2>/dev/null || print_warning "No Django logs found"
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  check    - Check prerequisites and health"
        echo "  restart  - Restart services"
        echo "  logs     - Show recent logs"
        echo "  help     - Show this help"
        ;;
    *)
        print_error "Unknown command: $1"
        print_status "Use '$0 help' for usage information"
        exit 1
        ;;
esac