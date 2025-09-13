#!/bin/bash

# =============================================================================
# LASO Healthcare Management System - Production Deployment Script
# =============================================================================
# This script deploys the LASO Healthcare system for production use
# 
# Usage: ./deploy-production.sh [OPTIONS]
# Options:
#   --domain DOMAIN     Set custom domain (default: localhost)
#   --ssl               Enable SSL/HTTPS setup
#   --backup            Create backup before deployment
#   --reset             Reset all data (WARNING: destroys existing data)
#   --help              Show this help message
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DOMAIN="localhost"
ENABLE_SSL=false
CREATE_BACKUP=false
RESET_DATA=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

show_help() {
    cat << EOF
LASO Healthcare Management System - Production Deployment

Usage: $0 [OPTIONS]

Options:
    --domain DOMAIN     Set custom domain (default: localhost)
    --ssl               Enable SSL/HTTPS setup
    --backup            Create backup before deployment
    --reset             Reset all data (WARNING: destroys existing data)
    --help              Show this help message

Examples:
    $0                                    # Basic deployment
    $0 --domain example.com --ssl         # Deploy with custom domain and SSL
    $0 --backup --reset                   # Reset with backup
    
Prerequisites:
    - Docker and Docker Compose installed
    - Sufficient disk space (minimum 2GB)
    - Open ports: 3000, 8081, 5432, 6379
    
EOF
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    # Check available disk space (minimum 2GB)
    available_space=$(df . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 2097152 ]; then
        log_warning "Low disk space detected. Minimum 2GB recommended."
    fi
    
    log_success "Prerequisites check passed"
}

generate_secure_passwords() {
    log_info "Generating secure passwords..."
    
    # Generate random passwords
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
    
    log_success "Secure passwords generated"
}

create_env_file() {
    log_info "Creating production environment configuration..."
    
    # Get server IP
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "127.0.0.1")
    
    cat > .env << EOF
# =============================================================================
# LASO Healthcare Management System - Production Configuration
# Generated on: $(date)
# =============================================================================

# Django Settings
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,${SERVER_IP},${DOMAIN},*

# Database Configuration
POSTGRES_DB=laso_healthcare
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=${DB_PASSWORD}

# Redis Configuration
REDIS_PASSWORD=${REDIS_PASSWORD}

# Email Settings (Configure for production)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True

# Security Settings
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# AI Features (Optional - Add your API keys)
OPENAI_API_KEY=
HUGGINGFACE_API_KEY=

# Backup Settings
BACKUP_RETENTION_DAYS=30
EOF

    log_success "Environment configuration created"
}

create_backup() {
    if [ "$CREATE_BACKUP" = true ]; then
        log_info "Creating backup..."
        
        BACKUP_DIR="backups"
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        
        mkdir -p "$BACKUP_DIR"
        
        if docker compose ps | grep -q "laso_postgres.*Up"; then
            docker compose exec -T db pg_dump -U laso_user laso_healthcare > "$BACKUP_DIR/$BACKUP_FILE"
            log_success "Backup created: $BACKUP_DIR/$BACKUP_FILE"
        else
            log_warning "Database not running, skipping backup"
        fi
    fi
}

deploy_application() {
    log_info "Deploying LASO Healthcare Management System..."
    
    # Stop existing containers if running
    if docker compose ps -q | grep -q .; then
        log_info "Stopping existing containers..."
        docker compose down
    fi
    
    # Reset data if requested
    if [ "$RESET_DATA" = true ]; then
        log_warning "Resetting all data (volumes will be removed)..."
        docker compose down -v
        docker system prune -f
    fi
    
    # Build and start services
    log_info "Building and starting services..."
    docker compose up -d --build
    
    # Wait for services to be ready
    log_info "Waiting for services to initialize..."
    sleep 60
    
    # Check if services are healthy
    check_services_health
    
    # Run database migrations
    log_info "Running database migrations..."
    docker compose exec web python manage.py makemigrations
    docker compose exec web python manage.py migrate
    
    # Collect static files
    log_info "Collecting static files..."
    docker compose exec web python manage.py collectstatic --noinput
    
    # Create superuser
    create_admin_user
    
    # Restart celery-beat to clear any warnings
    log_info "Restarting task scheduler..."
    docker compose restart celery-beat
    
    log_success "Application deployed successfully!"
}

check_services_health() {
    log_info "Checking service health..."
    
    # Wait for services to be healthy
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker compose ps | grep -q "healthy"; then
            local healthy_count=$(docker compose ps | grep -c "healthy")
            local total_services=4  # web, db, redis, celery
            
            if [ "$healthy_count" -ge "$total_services" ]; then
                log_success "All services are healthy"
                return 0
            fi
        fi
        
        log_info "Waiting for services to be healthy... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    log_error "Services failed to become healthy within expected time"
    docker compose ps
    exit 1
}

create_admin_user() {
    log_info "Creating admin user..."
    
    # Generate random admin password
    ADMIN_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/")
    
    docker compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@laso-healthcare.com', '${ADMIN_PASSWORD}')
    print('Admin user created successfully')
else:
    print('Admin user already exists')
"
    
    # Save credentials to file
    cat > admin_credentials.txt << EOF
LASO Healthcare Management System - Admin Credentials
Generated on: $(date)

Username: admin
Password: ${ADMIN_PASSWORD}
Email: admin@laso-healthcare.com

IMPORTANT: Please change this password after first login!
Access the admin panel at: http://${DOMAIN}:3000/admin
EOF
    
    chmod 600 admin_credentials.txt
    log_success "Admin credentials saved to admin_credentials.txt"
}

setup_ssl() {
    if [ "$ENABLE_SSL" = true ]; then
        log_info "Setting up SSL/HTTPS..."
        
        # This is a placeholder for SSL setup
        # In production, you would typically use Let's Encrypt or similar
        log_warning "SSL setup is not implemented in this script"
        log_info "For production SSL, consider using:"
        log_info "1. Let's Encrypt with certbot"
        log_info "2. Cloudflare SSL"
        log_info "3. Load balancer SSL termination"
    fi
}

show_deployment_info() {
    local server_ip=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
    
    cat << EOF

${GREEN}=============================================================================
🎉 LASO Healthcare Management System Deployed Successfully!
=============================================================================${NC}

${BLUE}📋 Access Information:${NC}
   Main Application: http://${server_ip}:3000
   Admin Panel:      http://${server_ip}:3000/admin
   Health Check:     http://${server_ip}:3000/health/
   Nginx (Alt):      http://${server_ip}:8081

${BLUE}🔐 Admin Credentials:${NC}
   Check the file: admin_credentials.txt
   
${BLUE}🐳 Docker Services:${NC}
   Web Server:       Django + Gunicorn
   Database:         PostgreSQL 17
   Cache:            Redis 7
   Task Queue:       Celery
   Task Scheduler:   Celery Beat
   Load Balancer:    Nginx

${BLUE}📁 Important Files:${NC}
   Configuration:    .env
   Admin Creds:      admin_credentials.txt
   Backups:          backups/

${BLUE}🔧 Management Commands:${NC}
   View logs:        docker compose logs -f web
   Stop system:      docker compose down
   Start system:     docker compose up -d
   Restart service:  docker compose restart web
   Database shell:   docker compose exec db psql -U laso_user laso_healthcare

${YELLOW}⚠️  Security Reminders:${NC}
   1. Change the admin password after first login
   2. Configure email settings in .env for production
   3. Set up SSL/HTTPS for production use
   4. Configure firewall rules
   5. Set up regular backups

${GREEN}🚀 Your healthcare management system is ready to use!${NC}

EOF
}

cleanup_on_error() {
    log_error "Deployment failed. Cleaning up..."
    docker compose down 2>/dev/null || true
    exit 1
}

# =============================================================================
# Main Script Logic
# =============================================================================

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --ssl)
            ENABLE_SSL=true
            shift
            ;;
        --backup)
            CREATE_BACKUP=true
            shift
            ;;
        --reset)
            RESET_DATA=true
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

# Set up error handling
trap cleanup_on_error ERR

# Main deployment process
main() {
    log_info "Starting LASO Healthcare Management System deployment..."
    log_info "Domain: $DOMAIN"
    log_info "SSL: $ENABLE_SSL"
    log_info "Backup: $CREATE_BACKUP"
    log_info "Reset: $RESET_DATA"
    
    check_prerequisites
    generate_secure_passwords
    create_env_file
    create_backup
    deploy_application
    setup_ssl
    show_deployment_info
    
    log_success "Deployment completed successfully!"
}

# Run main function
main "$@"