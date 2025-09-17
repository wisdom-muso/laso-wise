#!/bin/bash

# LASO Healthcare Development Setup Script
# This script sets up the development environment with SQLite

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to setup development environment
setup_dev_env() {
    log_info "Setting up development environment..."
    
    # Create development environment file
    cat > .env.dev << EOF
# Development Environment Configuration
DEBUG=True
SECRET_KEY=dev-secret-key-not-for-production
ALLOWED_HOSTS=localhost,127.0.0.1,*
USE_SQLITE=True

# Email (console backend for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# AI Features (optional for development)
ENABLE_AI_FEATURES=False
OPENAI_API_KEY=your_openai_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Logging
LOG_TO_FILE=False
EOF
    
    log_success "Development environment file created (.env.dev)"
}

# Function to run with Docker
run_docker_dev() {
    log_info "Starting development environment with Docker..."
    
    # Use development compose file
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    
    # Wait for services to start
    sleep 10
    
    # Run migrations
    log_info "Running database migrations..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
    
    # Create superuser if it doesn't exist
    log_info "Creating development superuser..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec -T web python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Development superuser created: admin/admin123')
else:
    print('Development superuser already exists')
EOF
    
    # Collect static files
    log_info "Collecting static files..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput
    
    log_success "Development environment is ready!"
    echo
    echo "=== DEVELOPMENT ACCESS ==="
    echo "Application: http://localhost:3000"
    echo "Admin Panel: http://localhost:3000/admin/"
    echo "Admin Credentials: admin/admin123"
    echo
    echo "=== USEFUL COMMANDS ==="
    echo "View logs: docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f"
    echo "Django shell: docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py shell"
    echo "Run tests: docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py test"
    echo "Stop services: docker-compose -f docker-compose.yml -f docker-compose.dev.yml down"
}

# Function to run locally with SQLite
run_local_dev() {
    log_info "Setting up local development environment..."
    
    # Check if Python is available
    if ! command_exists python3; then
        log_error "Python 3 is required for local development"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    log_info "Installing dependencies..."
    pip install -r requirements.txt
    
    # Set environment variables
    export DEBUG=True
    export USE_SQLITE=True
    export SECRET_KEY=dev-secret-key-not-for-production
    export ALLOWED_HOSTS=localhost,127.0.0.1,*
    export EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
    
    # Run migrations
    log_info "Running database migrations..."
    python manage.py migrate
    
    # Create superuser if it doesn't exist
    log_info "Creating development superuser..."
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Development superuser created: admin/admin123')
else:
    print('Development superuser already exists')
EOF
    
    # Collect static files
    log_info "Collecting static files..."
    python manage.py collectstatic --noinput
    
    log_success "Local development environment is ready!"
    echo
    echo "=== DEVELOPMENT ACCESS ==="
    echo "To start the server, run:"
    echo "source venv/bin/activate"
    echo "python manage.py runserver 0.0.0.0:3000"
    echo
    echo "Then access:"
    echo "Application: http://localhost:3000"
    echo "Admin Panel: http://localhost:3000/admin/"
    echo "Admin Credentials: admin/admin123"
}

# Main function
main() {
    log_info "LASO Healthcare Development Setup"
    echo
    echo "Choose development setup method:"
    echo "1) Docker (recommended)"
    echo "2) Local Python environment"
    echo "3) Setup environment files only"
    echo
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            setup_dev_env
            run_docker_dev
            ;;
        2)
            setup_dev_env
            run_local_dev
            ;;
        3)
            setup_dev_env
            log_success "Environment files created. You can now set up manually."
            ;;
        *)
            log_error "Invalid choice. Please run the script again."
            exit 1
            ;;
    esac
}

# Run main function
main "$@"