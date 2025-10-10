#!/bin/bash

# =============================================================================
# LASO Healthcare Management System - Complete VPS Deployment Script
# =============================================================================
# This script will deploy the LASO Healthcare System to your VPS
# VPS IP: 65.108.91.110
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="laso-wise"
VPS_IP="65.108.91.110"
REPO_URL="https://github.com/lasoappwise/laso-wise.git"
INSTALL_DIR="/opt/laso-wise"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="8gJW48Tz8YXDrF57"

# Functions
print_banner() {
    echo -e "${CYAN}"
    echo "=================================================================="
    echo "    LASO Healthcare Management System - VPS Deployment"
    echo "=================================================================="
    echo -e "Target VPS: ${YELLOW}$VPS_IP${CYAN}"
    echo -e "Installation Directory: ${YELLOW}$INSTALL_DIR${CYAN}"
    echo "=================================================================="
    echo -e "${NC}"
}

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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_info "Running as root user"
        SUDO=""
    else
        log_info "Running as non-root user, will use sudo"
        SUDO="sudo"
        # Check if user has sudo privileges
        if ! $SUDO -n true 2>/dev/null; then
            log_error "This script requires sudo privileges. Please run with sudo or as root."
            exit 1
        fi
    fi
}

check_system() {
    log_step "Checking system requirements..."
    
    # Check OS
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        log_info "Operating System: $NAME $VERSION"
    else
        log_warning "Cannot determine OS version"
    fi
    
    # Check available memory
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $MEMORY_GB -lt 2 ]]; then
        log_warning "System has less than 2GB RAM. Minimum 2GB recommended."
    else
        log_success "Memory check passed: ${MEMORY_GB}GB available"
    fi
    
    # Check available disk space
    DISK_GB=$(df -BG / | awk 'NR==2{gsub(/G/,"",$4); print $4}')
    if [[ $DISK_GB -lt 20 ]]; then
        log_warning "Less than 20GB disk space available. This may cause issues."
    else
        log_success "Disk space check passed: ${DISK_GB}GB available"
    fi
}

install_dependencies() {
    log_step "Installing system dependencies..."
    
    # Update package list
    log_info "Updating package list..."
    $SUDO apt update
    
    # Install basic dependencies
    log_info "Installing basic packages..."
    $SUDO apt install -y curl wget git ufw software-properties-common apt-transport-https ca-certificates gnupg lsb-release
    
    log_success "System dependencies installed successfully!"
}

install_docker() {
    log_step "Installing Docker..."
    
    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        log_info "Docker is already installed"
        docker --version
    else
        log_info "Installing Docker..."
        
        # Add Docker's official GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # Add Docker repository
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | $SUDO tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Update package list and install Docker
        $SUDO apt update
        $SUDO apt install -y docker-ce docker-ce-cli containerd.io
        
        log_success "Docker installed successfully!"
    fi
    
    # Start and enable Docker service
    $SUDO systemctl start docker
    $SUDO systemctl enable docker
    
    # Add current user to docker group (if not root)
    if [[ $EUID -ne 0 ]]; then
        $SUDO usermod -aG docker $USER
        log_info "Added $USER to docker group. You may need to log out and back in."
    fi
}

install_docker_compose() {
    log_step "Installing Docker Compose..."
    
    # Check if Docker Compose is already installed
    if docker compose version &> /dev/null; then
        log_info "Docker Compose is already installed"
        docker compose version
    else
        log_info "Installing Docker Compose..."
        
        # Install Docker Compose plugin
        $SUDO apt install -y docker-compose-plugin
        
        log_success "Docker Compose installed successfully!"
    fi
}

setup_firewall() {
    log_step "Configuring firewall..."
    
    # Reset UFW to defaults
    $SUDO ufw --force reset
    
    # Set default policies
    $SUDO ufw default deny incoming
    $SUDO ufw default allow outgoing
    
    # Allow SSH (CRITICAL - don't lock yourself out!)
    $SUDO ufw allow ssh
    $SUDO ufw allow 22/tcp
    
    # Allow HTTP and HTTPS
    $SUDO ufw allow 80/tcp
    $SUDO ufw allow 443/tcp
    
    # Enable firewall
    $SUDO ufw --force enable
    
    # Show status
    $SUDO ufw status
    
    log_success "Firewall configured successfully!"
}

clone_repository() {
    log_step "Cloning LASO Healthcare repository..."
    
    # Create installation directory
    $SUDO mkdir -p $INSTALL_DIR
    $SUDO chown $USER:$USER $INSTALL_DIR
    
    # Clone repository
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        log_info "Repository already exists, updating..."
        cd $INSTALL_DIR
        git pull origin master
    else
        log_info "Cloning repository..."
        git clone $REPO_URL $INSTALL_DIR
        cd $INSTALL_DIR
    fi
    
    log_success "Repository cloned successfully!"
}

setup_environment() {
    log_step "Setting up environment configuration..."
    
    cd $INSTALL_DIR
    
    # Create .env file from VPS production template
    if [[ -f ".env.vps.production" ]]; then
        cp .env.vps.production .env
        log_success "Environment file created from VPS production template"
    elif [[ -f ".env.vps" ]]; then
        cp .env.vps .env
        log_success "Environment file created from VPS template"
    elif [[ -f ".env.production" ]]; then
        cp .env.production .env
        log_success "Environment file created from production template"
    else
        log_error "No environment template found!"
        exit 1
    fi
    
    # Update ALLOWED_HOSTS with VPS IP
    sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=$VPS_IP,localhost,127.0.0.1,*.$VPS_IP/" .env
    sed -i "s/CSRF_TRUSTED_ORIGINS=.*/CSRF_TRUSTED_ORIGINS=http:\/\/$VPS_IP,https:\/\/$VPS_IP/" .env
    
    log_success "Environment configuration completed!"
}

deploy_application() {
    log_step "Deploying LASO Healthcare application..."
    
    cd $INSTALL_DIR
    
    # Stop any existing containers
    log_info "Stopping existing containers..."
    docker compose down --remove-orphans || true
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker compose pull || true
    
    # Build application containers
    log_info "Building application containers..."
    docker compose build --no-cache
    
    # Start services
    log_info "Starting services..."
    docker compose up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to start..."
    sleep 30
    
    # Check service status
    docker compose ps
    
    log_success "Application deployed successfully!"
}

setup_database() {
    log_step "Setting up database..."
    
    cd $INSTALL_DIR
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 15
    
    # Run database migrations
    log_info "Running database migrations..."
    docker compose exec -T web python manage.py migrate
    
    # Collect static files
    log_info "Collecting static files..."
    docker compose exec -T web python manage.py collectstatic --noinput
    
    # Create superuser
    log_info "Creating admin superuser..."
    docker compose exec -T web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$ADMIN_USERNAME').exists():
    User.objects.create_superuser('$ADMIN_USERNAME', 'admin@laso.com', '$ADMIN_PASSWORD')
    print('Superuser created successfully!')
else:
    print('Superuser already exists')
"
    
    log_success "Database setup completed!"
}

verify_deployment() {
    log_step "Verifying deployment..."
    
    cd $INSTALL_DIR
    
    # Check if services are running
    if docker compose ps | grep -q "Up"; then
        log_success "Services are running!"
    else
        log_error "Some services are not running properly."
        docker compose ps
        return 1
    fi
    
    # Test HTTP endpoint
    sleep 5
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302"; then
        log_success "HTTP endpoint is responding!"
    else
        log_warning "HTTP endpoint may not be responding correctly."
    fi
    
    # Test specific health endpoint
    if curl -s -o /dev/null -w "%{http_code}" http://localhost/liveness/ | grep -q "200"; then
        log_success "Health endpoint is responding!"
    else
        log_warning "Health endpoint may not be responding correctly."
    fi
    
    log_success "Deployment verification completed!"
}

create_management_scripts() {
    log_step "Creating management scripts..."
    
    cd $INSTALL_DIR
    
    # Create status script
    cat > laso-status.sh << 'EOF'
#!/bin/bash
cd /opt/laso-wise
echo "=== LASO Healthcare System Status ==="
echo "Services:"
docker compose ps
echo ""
echo "Logs (last 20 lines):"
docker compose logs --tail=20
EOF
    
    # Create restart script
    cat > laso-restart.sh << 'EOF'
#!/bin/bash
cd /opt/laso-wise
echo "Restarting LASO Healthcare System..."
docker compose restart
echo "Services restarted!"
docker compose ps
EOF
    
    # Create update script
    cat > laso-update.sh << 'EOF'
#!/bin/bash
cd /opt/laso-wise
echo "Updating LASO Healthcare System..."
git pull origin master
docker compose down
docker compose build --no-cache
docker compose up -d
echo "System updated!"
docker compose ps
EOF
    
    # Make scripts executable
    chmod +x laso-status.sh laso-restart.sh laso-update.sh
    
    log_success "Management scripts created!"
}

show_completion_info() {
    echo ""
    echo -e "${GREEN}=================================================================="
    echo "    🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉"
    echo "=================================================================="
    echo -e "${NC}"
    echo -e "${CYAN}🌐 Your LASO Healthcare System is now available at:${NC}"
    echo -e "${YELLOW}   http://$VPS_IP/${NC}"
    echo ""
    echo -e "${CYAN}🔐 Admin Login Credentials:${NC}"
    echo -e "${YELLOW}   Username: $ADMIN_USERNAME${NC}"
    echo -e "${YELLOW}   Password: $ADMIN_PASSWORD${NC}"
    echo ""
    echo -e "${CYAN}📊 Available Services:${NC}"
    echo -e "${YELLOW}   • Admin Panel: http://$VPS_IP/admin/${NC}"
    echo -e "${YELLOW}   • Patient Management System${NC}"
    echo -e "${YELLOW}   • Appointment Scheduling${NC}"
    echo -e "${YELLOW}   • Telemedicine Platform${NC}"
    echo -e "${YELLOW}   • Medical Records & Imaging${NC}"
    echo ""
    echo -e "${CYAN}🛠️ Management Commands:${NC}"
    echo -e "${YELLOW}   • Check Status: cd $INSTALL_DIR && ./laso-status.sh${NC}"
    echo -e "${YELLOW}   • Restart System: cd $INSTALL_DIR && ./laso-restart.sh${NC}"
    echo -e "${YELLOW}   • Update System: cd $INSTALL_DIR && ./laso-update.sh${NC}"
    echo -e "${YELLOW}   • View Logs: cd $INSTALL_DIR && docker compose logs -f${NC}"
    echo ""
    echo -e "${CYAN}📁 Installation Directory: ${YELLOW}$INSTALL_DIR${NC}"
    echo ""
    echo -e "${GREEN}=================================================================="
    echo -e "${NC}"
}

# Main deployment process
main() {
    print_banner
    
    check_root
    check_system
    install_dependencies
    install_docker
    install_docker_compose
    setup_firewall
    clone_repository
    setup_environment
    deploy_application
    setup_database
    verify_deployment
    create_management_scripts
    show_completion_info
    
    log_success "🚀 LASO Healthcare System deployment completed successfully!"
}

# Handle script interruption
trap 'log_error "Deployment interrupted!"; exit 1' INT TERM

# Run main function
main "$@"