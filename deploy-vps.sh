#!/bin/bash

# LASO Healthcare VPS Deployment Script
# This script deploys the LASO Healthcare system on a VPS running on port 3000
# Author: LASO Healthcare Team
# Version: 1.0

set -e  # Exit on any error

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

# Configuration
PROJECT_NAME="laso-wise"
DOMAIN=${DOMAIN:-"localhost"}
EMAIL=${EMAIL:-"admin@example.com"}
POSTGRES_DB=${POSTGRES_DB:-"laso_healthcare"}
POSTGRES_USER=${POSTGRES_USER:-"laso_user"}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-$(openssl rand -base64 32)}
REDIS_PASSWORD=${REDIS_PASSWORD:-$(openssl rand -base64 32)}
SECRET_KEY=${SECRET_KEY:-$(openssl rand -base64 50)}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root for security reasons"
   exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Docker
install_docker() {
    log_info "Installing Docker..."
    
    # Update package index
    sudo apt-get update
    
    # Install required packages
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up the stable repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    log_success "Docker installed successfully"
}

# Function to install Docker Compose
install_docker_compose() {
    log_info "Installing Docker Compose..."
    
    # Download Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Make it executable
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Create symlink for easier access
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_success "Docker Compose installed successfully"
}

# Function to setup firewall
setup_firewall() {
    log_info "Setting up firewall..."
    
    # Enable UFW
    sudo ufw --force enable
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80
    sudo ufw allow 443
    
    # Allow port 3000 for the application
    sudo ufw allow 3000
    
    # Allow PostgreSQL (only from localhost)
    sudo ufw allow from 127.0.0.1 to any port 5432
    
    # Allow Redis (only from localhost)
    sudo ufw allow from 127.0.0.1 to any port 6379
    
    log_success "Firewall configured successfully"
}

# Function to create environment file
create_env_file() {
    log_info "Creating environment file..."
    
    cat > .env << EOF
# Django Settings
DEBUG=False
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=${DOMAIN},localhost,127.0.0.1,*

# Database Settings
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Redis Settings
REDIS_PASSWORD=${REDIS_PASSWORD}

# Email Settings (configure as needed)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=${EMAIL}
EMAIL_HOST_PASSWORD=your_email_password
EMAIL_USE_TLS=True

# AI Settings (optional)
OPENAI_API_KEY=your_openai_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Logging
LOG_TO_FILE=True
EOF
    
    log_success "Environment file created"
}

# Function to create backup directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p backups
    mkdir -p logs
    mkdir -p docker/nginx/ssl
    
    log_success "Directories created"
}

# Function to generate SSL certificates (self-signed for development)
generate_ssl_certs() {
    log_info "Generating SSL certificates..."
    
    if [ ! -f "docker/nginx/ssl/cert.pem" ]; then
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout docker/nginx/ssl/key.pem \
            -out docker/nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=${DOMAIN}"
        
        log_success "SSL certificates generated"
    else
        log_info "SSL certificates already exist"
    fi
}

# Function to build and start services
deploy_services() {
    log_info "Building and starting services..."
    
    # Pull latest images
    docker-compose pull
    
    # Build the application
    docker-compose build --no-cache
    
    # Start services
    docker-compose up -d
    
    log_success "Services started"
}

# Function to run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    sleep 30
    
    # Run migrations
    docker-compose exec -T web python manage.py migrate
    
    log_success "Database migrations completed"
}

# Function to collect static files
collect_static() {
    log_info "Collecting static files..."
    
    docker-compose exec -T web python manage.py collectstatic --noinput
    
    log_success "Static files collected"
}

# Function to create superuser
create_superuser() {
    log_info "Creating admin superuser..."
    
    docker-compose exec -T web python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', '${EMAIL}', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF
    
    log_success "Admin user setup completed"
}

# Function to check service health
check_health() {
    log_info "Checking service health..."
    
    # Wait for services to be fully ready
    sleep 10
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        log_success "Services are running"
        
        # Check application health
        if curl -f http://localhost:3000/health/ >/dev/null 2>&1; then
            log_success "Application is healthy and responding"
        else
            log_warning "Application may not be fully ready yet"
        fi
    else
        log_error "Some services are not running properly"
        docker-compose ps
        return 1
    fi
}

# Function to display deployment information
show_deployment_info() {
    log_success "Deployment completed successfully!"
    echo
    echo "=== DEPLOYMENT INFORMATION ==="
    echo "Application URL: http://${DOMAIN}:3000"
    echo "Admin Panel: http://${DOMAIN}:3000/admin/"
    echo "Admin Username: admin"
    echo "Admin Password: admin123"
    echo
    echo "Database:"
    echo "  Host: localhost:5432"
    echo "  Database: ${POSTGRES_DB}"
    echo "  Username: ${POSTGRES_USER}"
    echo "  Password: ${POSTGRES_PASSWORD}"
    echo
    echo "Redis:"
    echo "  Host: localhost:6379"
    echo "  Password: ${REDIS_PASSWORD}"
    echo
    echo "=== IMPORTANT NOTES ==="
    echo "1. Change the default admin password immediately"
    echo "2. Configure email settings in .env file"
    echo "3. Set up proper SSL certificates for production"
    echo "4. Configure your domain DNS to point to this server"
    echo "5. Backup your .env file securely"
    echo
    echo "=== USEFUL COMMANDS ==="
    echo "View logs: docker-compose logs -f"
    echo "Restart services: docker-compose restart"
    echo "Stop services: docker-compose down"
    echo "Update application: git pull && docker-compose up -d --build"
    echo
}

# Main deployment function
main() {
    log_info "Starting LASO Healthcare VPS deployment..."
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Update system packages
    log_info "Updating system packages..."
    sudo apt-get update && sudo apt-get upgrade -y
    
    # Install required packages
    log_info "Installing required packages..."
    sudo apt-get install -y curl wget git openssl ufw
    
    # Install Docker if not present
    if ! command_exists docker; then
        install_docker
        log_warning "Docker installed. Please log out and log back in, then run this script again."
        exit 0
    fi
    
    # Install Docker Compose if not present
    if ! command_exists docker-compose; then
        install_docker_compose
    fi
    
    # Setup firewall
    setup_firewall
    
    # Create necessary directories
    create_directories
    
    # Create environment file
    create_env_file
    
    # Generate SSL certificates
    generate_ssl_certs
    
    # Deploy services
    deploy_services
    
    # Run database migrations
    run_migrations
    
    # Collect static files
    collect_static
    
    # Create superuser
    create_superuser
    
    # Check health
    check_health
    
    # Show deployment information
    show_deployment_info
}

# Run main function
main "$@"