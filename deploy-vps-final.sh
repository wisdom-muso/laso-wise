#!/bin/bash

# LASO Healthcare VPS Deployment Script - Final Version
# Deploys the LASO Healthcare system on VPS at 65.108.91.110
# Author: LASO Healthcare Team
# Version: 2.0

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
VPS_IP="65.108.91.110"
DOMAIN=${DOMAIN:-$VPS_IP}
EMAIL=${EMAIL:-"admin@laso.com"}
POSTGRES_DB=${POSTGRES_DB:-"laso_healthcare"}
POSTGRES_USER=${POSTGRES_USER:-"laso_user"}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-"laso2403"}
REDIS_PASSWORD=${REDIS_PASSWORD:-"laso2403"}
SECRET_KEY=${SECRET_KEY:-"hk\$6b!2g*3q1o+0r@u4z#b@t@*j8=5f5+g3e#9ly2n^+%h5!z5"}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-"admin123"}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        log_info "Please run as a regular user with sudo privileges"
        exit 1
    fi
}

# Function to check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check OS
    if [[ ! -f /etc/os-release ]]; then
        log_error "Cannot determine OS version"
        exit 1
    fi
    
    # Check available memory
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $MEMORY_GB -lt 2 ]]; then
        log_warning "System has less than 2GB RAM. Performance may be affected."
    fi
    
    # Check available disk space
    DISK_GB=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
    if [[ $DISK_GB -lt 10 ]]; then
        log_error "Insufficient disk space. At least 10GB required."
        exit 1
    fi
    
    log_success "System requirements check passed"
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
    log_warning "Please log out and log back in to apply group changes, then run this script again"
    exit 0
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
    
    # Install UFW if not present
    if ! command_exists ufw; then
        sudo apt-get install -y ufw
    fi
    
    # Reset UFW to defaults
    sudo ufw --force reset
    
    # Set default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH
    sudo ufw allow ssh
    sudo ufw allow 22
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80
    sudo ufw allow 443
    
    # Allow port 3000 for the application
    sudo ufw allow 3000
    
    # Enable UFW
    sudo ufw --force enable
    
    log_success "Firewall configured successfully"
}

# Function to create environment file
create_env_file() {
    log_info "Creating environment file..."
    
    # Use the VPS-specific environment file
    if [[ -f ".env.vps" ]]; then
        cp .env.vps .env
        log_success "VPS environment file copied"
    else
        # Create environment file from scratch
        cat > .env << EOF
# Django Settings - VPS Production Configuration
DEBUG=False
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=${DOMAIN},localhost,127.0.0.1,*
CSRF_TRUSTED_ORIGINS=http://${DOMAIN},https://${DOMAIN},http://${DOMAIN}:3000,https://${DOMAIN}:3000,http://${DOMAIN}:80,https://${DOMAIN}:443

# Database Settings
USE_SQLITE=False
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}

# Redis Settings
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# Email Settings
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=${EMAIL}
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True

# AI Settings (optional)
OPENAI_API_KEY=
HUGGINGFACE_API_KEY=

# Logging
LOG_TO_FILE=True
EOF
        log_success "Environment file created"
    fi
}

# Function to create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p backups
    mkdir -p logs
    mkdir -p docker/nginx/ssl
    
    # Set proper permissions
    chmod 755 backups logs
    chmod 755 docker/nginx/ssl
    
    log_success "Directories created"
}

# Function to stop existing services
stop_existing_services() {
    log_info "Stopping any existing services..."
    
    # Stop any running Docker containers
    if docker ps -q | grep -q .; then
        docker stop $(docker ps -q) || true
    fi
    
    # Stop any services using port 80 or 3000
    sudo pkill -f "nginx" || true
    sudo pkill -f ":80" || true
    sudo pkill -f ":3000" || true
    
    # Stop Apache if running
    sudo systemctl stop apache2 2>/dev/null || true
    sudo systemctl disable apache2 2>/dev/null || true
    
    log_success "Existing services stopped"
}

# Function to build and start services
deploy_services() {
    log_info "Building and starting services..."
    
    # Remove any existing containers
    docker-compose down --remove-orphans || true
    
    # Pull latest images
    docker-compose pull || true
    
    # Build the application
    docker-compose build --no-cache
    
    # Start services
    docker-compose up -d
    
    log_success "Services started"
}

# Function to wait for services
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for database
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose exec -T db pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} >/dev/null 2>&1; then
            log_success "Database is ready"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "Database failed to start after ${max_attempts} attempts"
            return 1
        fi
        
        log_info "Waiting for database... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    # Wait for web service
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:3000/health/ >/dev/null 2>&1; then
            log_success "Web service is ready"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_warning "Web service health check failed, but continuing..."
            break
        fi
        
        log_info "Waiting for web service... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
}

# Function to run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
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
    User.objects.create_superuser('admin', '${EMAIL}', '${ADMIN_PASSWORD}')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF
    
    log_success "Admin user setup completed"
}

# Function to check service health
check_health() {
    log_info "Checking service health..."
    
    # Check if services are running
    local running_services=$(docker-compose ps --services --filter "status=running" | wc -l)
    local total_services=$(docker-compose ps --services | wc -l)
    
    if [[ $running_services -eq $total_services ]]; then
        log_success "All services are running ($running_services/$total_services)"
    else
        log_warning "Some services may not be running ($running_services/$total_services)"
        docker-compose ps
    fi
    
    # Check application health
    if curl -f http://localhost:3000/ >/dev/null 2>&1; then
        log_success "Application is responding"
    else
        log_warning "Application may not be fully ready yet"
    fi
    
    # Check admin panel
    if curl -f http://localhost:3000/admin/ >/dev/null 2>&1; then
        log_success "Admin panel is accessible"
    else
        log_warning "Admin panel may not be ready yet"
    fi
}

# Function to display deployment information
show_deployment_info() {
    log_success "🎉 LASO Healthcare System Deployment Completed Successfully!"
    echo
    echo "==============================================="
    echo "🏥 LASO HEALTHCARE MANAGEMENT SYSTEM"
    echo "==============================================="
    echo
    echo "🌐 Access URLs:"
    echo "   Main Application: http://${DOMAIN}:3000"
    echo "   Admin Panel:      http://${DOMAIN}:3000/admin/"
    echo
    echo "🔐 Admin Credentials:"
    echo "   Username: admin"
    echo "   Password: ${ADMIN_PASSWORD}"
    echo
    echo "🗄️ Database Information:"
    echo "   Host:     localhost:5432"
    echo "   Database: ${POSTGRES_DB}"
    echo "   Username: ${POSTGRES_USER}"
    echo "   Password: ${POSTGRES_PASSWORD}"
    echo
    echo "🔄 Redis Cache:"
    echo "   Host:     localhost:6379"
    echo "   Password: ${REDIS_PASSWORD}"
    echo
    echo "==============================================="
    echo "🚨 IMPORTANT SECURITY NOTES:"
    echo "==============================================="
    echo "1. 🔑 Change the default admin password immediately"
    echo "2. 📧 Configure email settings in .env file"
    echo "3. 🔒 Set up SSL certificates for HTTPS"
    echo "4. 🛡️ Review firewall settings"
    echo "5. 💾 Set up automated backups"
    echo
    echo "==============================================="
    echo "🛠️ USEFUL COMMANDS:"
    echo "==============================================="
    echo "View logs:        docker-compose logs -f"
    echo "Restart services: docker-compose restart"
    echo "Stop services:    docker-compose down"
    echo "Update app:       git pull && docker-compose up -d --build"
    echo "Backup database:  docker-compose exec db pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup.sql"
    echo
    echo "==============================================="
    echo "🏥 HEALTHCARE FEATURES AVAILABLE:"
    echo "==============================================="
    echo "✅ Patient Management"
    echo "✅ Appointment Scheduling"
    echo "✅ Telemedicine Platform"
    echo "✅ Treatment Management"
    echo "✅ Medical Imaging"
    echo "✅ Lab Test Management"
    echo "✅ User Management"
    echo "✅ Analytics & Reporting"
    echo "✅ Real-time Notifications"
    echo "✅ AI Integration Support"
    echo
    echo "🎊 Your healthcare management system is ready to use!"
    echo
}

# Function to save credentials
save_credentials() {
    log_info "Saving credentials to file..."
    
    cat > admin_credentials.txt << EOF
LASO Healthcare System - Admin Credentials
==========================================

Application URL: http://${DOMAIN}:3000
Admin Panel URL: http://${DOMAIN}:3000/admin/

Admin Username: admin
Admin Password: ${ADMIN_PASSWORD}

Database:
- Host: localhost:5432
- Database: ${POSTGRES_DB}
- Username: ${POSTGRES_USER}
- Password: ${POSTGRES_PASSWORD}

Redis:
- Host: localhost:6379
- Password: ${REDIS_PASSWORD}

Generated on: $(date)
EOF
    
    chmod 600 admin_credentials.txt
    log_success "Credentials saved to admin_credentials.txt"
}

# Main deployment function
main() {
    echo "🏥 LASO Healthcare VPS Deployment Script v2.0"
    echo "=============================================="
    echo
    
    # Pre-flight checks
    check_root
    check_requirements
    
    # Check if we're in the right directory
    if [[ ! -f "docker-compose.yml" ]]; then
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
    fi
    
    # Install Docker Compose if not present
    if ! command_exists docker-compose; then
        install_docker_compose
    fi
    
    # Setup firewall
    setup_firewall
    
    # Stop existing services
    stop_existing_services
    
    # Create necessary directories
    create_directories
    
    # Create environment file
    create_env_file
    
    # Deploy services
    deploy_services
    
    # Wait for services to be ready
    wait_for_services
    
    # Run database migrations
    run_migrations
    
    # Collect static files
    collect_static
    
    # Create superuser
    create_superuser
    
    # Check health
    check_health
    
    # Save credentials
    save_credentials
    
    # Show deployment information
    show_deployment_info
}

# Run main function
main "$@"