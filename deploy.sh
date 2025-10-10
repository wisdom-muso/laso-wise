#!/bin/bash

# =============================================================================
# LASO Healthcare Management System - VPS Deployment Script
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="laso-wise"
VPS_IP="65.108.91.110"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"

# Functions
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

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]] && ! groups $USER | grep -q docker; then
        log_warning "You may need to run this script with sudo or add your user to the docker group."
    fi
    
    log_success "System requirements check passed!"
}

setup_environment() {
    log_info "Setting up environment..."
    
    # Copy production environment file
    if [[ ! -f ".env" ]]; then
        if [[ -f "$ENV_FILE" ]]; then
            cp "$ENV_FILE" ".env"
            log_success "Environment file copied from $ENV_FILE"
        else
            log_error "Environment file $ENV_FILE not found!"
            exit 1
        fi
    else
        log_warning ".env file already exists. Skipping environment setup."
    fi
}

build_and_deploy() {
    log_info "Building and deploying LASO Healthcare System..."
    
    # Stop existing containers if running
    log_info "Stopping existing containers..."
    docker compose -f "$COMPOSE_FILE" down --remove-orphans || true
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker compose -f "$COMPOSE_FILE" pull || true
    
    # Build the application
    log_info "Building application containers..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    
    # Start the services
    log_info "Starting services..."
    docker compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check service status
    docker compose -f "$COMPOSE_FILE" ps
}

run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10
    
    # Run migrations
    docker compose -f "$COMPOSE_FILE" exec -T web python manage.py migrate
    
    # Collect static files
    log_info "Collecting static files..."
    docker compose -f "$COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput
    
    log_success "Database migrations completed!"
}

create_superuser() {
    log_info "Creating superuser account..."
    
    # Check if admin user already exists
    if docker compose -f "$COMPOSE_FILE" exec -T web python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('exists' if User.objects.filter(username='admin').exists() else 'not_exists')" | grep -q "exists"; then
        log_warning "Admin user already exists. Skipping superuser creation."
    else
        # Create superuser
        docker compose -f "$COMPOSE_FILE" exec -T web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin', 'admin@laso.com', '8gJW48Tz8YXDrF57')
print('Superuser created successfully!')
"
        log_success "Superuser created with username: admin"
    fi
}

setup_firewall() {
    log_info "Setting up firewall rules..."
    
    # Check if ufw is available
    if command -v ufw &> /dev/null; then
        # Allow SSH (important!)
        sudo ufw allow ssh
        
        # Allow HTTP and HTTPS
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        
        # Enable firewall if not already enabled
        sudo ufw --force enable
        
        log_success "Firewall configured successfully!"
    else
        log_warning "UFW firewall not available. Please configure firewall manually."
    fi
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check if services are running
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_success "Services are running!"
    else
        log_error "Some services are not running properly."
        docker compose -f "$COMPOSE_FILE" ps
        exit 1
    fi
    
    # Test HTTP endpoint
    sleep 5
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302"; then
        log_success "HTTP endpoint is responding!"
    else
        log_warning "HTTP endpoint may not be responding correctly."
    fi
    
    # Show final status
    echo ""
    log_success "=== DEPLOYMENT COMPLETED SUCCESSFULLY ==="
    echo ""
    echo -e "${GREEN}🌐 Your LASO Healthcare System is now available at:${NC}"
    echo -e "${BLUE}   http://$VPS_IP${NC}"
    echo ""
    echo -e "${GREEN}🔐 Admin Login Credentials:${NC}"
    echo -e "${BLUE}   Username: admin${NC}"
    echo -e "${BLUE}   Password: 8gJW48Tz8YXDrF57${NC}"
    echo ""
    echo -e "${GREEN}📊 Available Services:${NC}"
    echo -e "${BLUE}   • Admin Panel: http://$VPS_IP/admin/${NC}"
    echo -e "${BLUE}   • Patient Management System${NC}"
    echo -e "${BLUE}   • Appointment Scheduling${NC}"
    echo -e "${BLUE}   • Telemedicine Platform${NC}"
    echo -e "${BLUE}   • Medical Records & Imaging${NC}"
    echo ""
}

show_logs() {
    log_info "Showing recent logs..."
    docker compose -f "$COMPOSE_FILE" logs --tail=50
}

# Main deployment process
main() {
    echo ""
    echo -e "${GREEN}=== LASO Healthcare Management System - VPS Deployment ===${NC}"
    echo -e "${BLUE}Target VPS: $VPS_IP${NC}"
    echo ""
    
    check_requirements
    setup_environment
    build_and_deploy
    run_migrations
    create_superuser
    setup_firewall
    verify_deployment
    
    echo ""
    log_success "Deployment completed successfully!"
    echo ""
    
    # Ask if user wants to see logs
    read -p "Would you like to see the application logs? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        show_logs
    fi
}

# Handle script arguments
case "${1:-}" in
    "logs")
        docker compose -f "$COMPOSE_FILE" logs -f
        ;;
    "status")
        docker compose -f "$COMPOSE_FILE" ps
        ;;
    "stop")
        docker compose -f "$COMPOSE_FILE" down
        ;;
    "restart")
        docker compose -f "$COMPOSE_FILE" restart
        ;;
    "update")
        docker compose -f "$COMPOSE_FILE" pull
        docker compose -f "$COMPOSE_FILE" up -d
        ;;
    *)
        main
        ;;
esac