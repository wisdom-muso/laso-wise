#!/bin/bash

# =============================================================================
# LASO Healthcare System - VPS Setup and Migration Script
# =============================================================================
# This script helps you set up the LASO Healthcare system on your VPS
# and run the necessary database migrations
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_USER="laso"
APP_DIR="/opt/laso"
PROJECT_DIR="$APP_DIR/laso-wise"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$APP_DIR/logs"

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

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# =============================================================================
# Step 1: Install System Dependencies
# =============================================================================

install_system_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update system
    apt update && apt upgrade -y
    
    # Install required packages
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        postgresql \
        postgresql-contrib \
        redis-server \
        nginx \
        git \
        curl \
        build-essential \
        libpq-dev \
        supervisor
    
    # Start and enable services
    systemctl start postgresql
    systemctl enable postgresql
    systemctl start redis-server
    systemctl enable redis-server
    
    log_success "System dependencies installed"
}

# =============================================================================
# Step 2: Configure Database
# =============================================================================

configure_database() {
    log_info "Configuring PostgreSQL database..."
    
    # Generate secure password
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Create database and user
    sudo -u postgres psql << EOF
CREATE DATABASE laso_healthcare;
CREATE USER laso_user WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE laso_user SET client_encoding TO 'utf8';
ALTER ROLE laso_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE laso_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE laso_healthcare TO laso_user;
\q
EOF
    
    # Save database credentials
    echo "DB_PASSWORD=$DB_PASSWORD" > /tmp/db_credentials.txt
    chmod 600 /tmp/db_credentials.txt
    
    log_success "Database configured. Password saved to /tmp/db_credentials.txt"
}

# =============================================================================
# Step 3: Create Application User and Directory
# =============================================================================

setup_application_user() {
    log_info "Setting up application user and directories..."
    
    # Create application user
    if ! id "$APP_USER" &>/dev/null; then
        adduser --system --group --home $APP_DIR $APP_USER
    fi
    
    # Create directories
    mkdir -p $APP_DIR
    mkdir -p $LOG_DIR
    chown -R $APP_USER:$APP_USER $APP_DIR
    
    log_success "Application user and directories created"
}

# =============================================================================
# Step 4: Clone and Setup Application
# =============================================================================

setup_application() {
    log_info "Setting up Django application..."
    
    # Clone repository (you'll need to replace with your actual repo URL)
    if [ ! -d "$PROJECT_DIR" ]; then
        log_info "Please clone your repository manually to $PROJECT_DIR"
        log_info "Example: sudo -u $APP_USER git clone <your-repo-url> $PROJECT_DIR"
        read -p "Press Enter after you've cloned the repository..."
    fi
    
    # Create virtual environment
    sudo -u $APP_USER python3 -m venv $VENV_DIR
    
    # Install dependencies
    sudo -u $APP_USER $VENV_DIR/bin/pip install --upgrade pip
    sudo -u $APP_USER $VENV_DIR/bin/pip install -r $PROJECT_DIR/requirements.txt
    
    log_success "Application setup completed"
}

# =============================================================================
# Step 5: Create Environment Configuration
# =============================================================================

create_environment_config() {
    log_info "Creating environment configuration..."
    
    # Get database password
    DB_PASSWORD=$(grep "DB_PASSWORD=" /tmp/db_credentials.txt | cut -d'=' -f2)
    
    # Get server IP
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "127.0.0.1")
    
    # Generate secret key
    SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
    
    # Create .env file
    sudo -u $APP_USER tee $PROJECT_DIR/.env > /dev/null << EOF
# Django Settings
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,$SERVER_IP,*

# Database Configuration
DATABASE_URL=postgresql://laso_user:$DB_PASSWORD@localhost:5432/laso_healthcare

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration (configure for production)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Security Settings
CSRF_TRUSTED_ORIGINS=http://$SERVER_IP,https://$SERVER_IP
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Media and Static Files
MEDIA_ROOT=$PROJECT_DIR/media
STATIC_ROOT=$PROJECT_DIR/staticfiles
EOF
    
    log_success "Environment configuration created"
}

# =============================================================================
# Step 6: Run Database Migrations
# =============================================================================

run_migrations() {
    log_info "Running database migrations..."
    
    cd $PROJECT_DIR
    
    # Make migrations
    sudo -u $APP_USER $VENV_DIR/bin/python manage.py makemigrations
    
    # Run migrations
    sudo -u $APP_USER $VENV_DIR/bin/python manage.py migrate
    
    # Collect static files
    sudo -u $APP_USER $VENV_DIR/bin/python manage.py collectstatic --noinput
    
    # Create media directories
    sudo -u $APP_USER mkdir -p media/profile_pictures
    sudo -u $APP_USER mkdir -p media/medical_documents
    
    log_success "Database migrations completed"
}

# =============================================================================
# Step 7: Create Admin User
# =============================================================================

create_admin_user() {
    log_info "Creating admin superuser..."
    
    # Generate admin password
    ADMIN_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/")
    
    cd $PROJECT_DIR
    sudo -u $APP_USER $VENV_DIR/bin/python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@laso-healthcare.com', '$ADMIN_PASSWORD')
    print('Admin user created successfully')
else:
    print('Admin user already exists')
EOF
    
    # Save admin credentials
    tee $APP_DIR/admin_credentials.txt > /dev/null << EOF
LASO Healthcare Management System - Admin Credentials
Generated on: $(date)

Username: admin
Password: $ADMIN_PASSWORD
Email: admin@laso-healthcare.com

IMPORTANT: Please change this password after first login!
Access the admin panel at: http://your-server-ip:8000/admin
EOF
    
    chmod 600 $APP_DIR/admin_credentials.txt
    chown $APP_USER:$APP_USER $APP_DIR/admin_credentials.txt
    
    log_success "Admin user created. Credentials saved to $APP_DIR/admin_credentials.txt"
}

# =============================================================================
# Step 8: Configure Gunicorn
# =============================================================================

configure_gunicorn() {
    log_info "Configuring Gunicorn..."
    
    # Create Gunicorn configuration
    sudo -u $APP_USER tee $PROJECT_DIR/gunicorn.conf.py > /dev/null << 'EOF'
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/opt/laso/logs/gunicorn_access.log"
errorlog = "/opt/laso/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "laso_healthcare"

# Server mechanics
daemon = False
pidfile = "/opt/laso/laso-wise/gunicorn.pid"
user = "laso"
group = "laso"
EOF
    
    # Create systemd service
    tee /etc/systemd/system/laso-gunicorn.service > /dev/null << EOF
[Unit]
Description=Gunicorn instance to serve LASO Healthcare
After=network.target postgresql.service redis.service

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn --config gunicorn.conf.py laso.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    # Enable and start service
    systemctl daemon-reload
    systemctl enable laso-gunicorn
    systemctl start laso-gunicorn
    
    log_success "Gunicorn configured and started"
}

# =============================================================================
# Step 9: Configure Nginx
# =============================================================================

configure_nginx() {
    log_info "Configuring Nginx..."
    
    # Create Nginx configuration
    tee /etc/nginx/sites-available/laso-healthcare > /dev/null << EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    # Static files
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Host \$http_host;
        proxy_redirect off;
        proxy_buffering off;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/laso-healthcare /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test and restart Nginx
    nginx -t
    systemctl restart nginx
    
    log_success "Nginx configured and restarted"
}

# =============================================================================
# Step 10: Configure Firewall
# =============================================================================

configure_firewall() {
    log_info "Configuring firewall..."
    
    # Install and configure UFW
    apt install -y ufw
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw --force enable
    
    log_success "Firewall configured"
}

# =============================================================================
# Main Installation Function
# =============================================================================

show_final_info() {
    local server_ip=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
    
    cat << EOF

${GREEN}=============================================================================
🎉 LASO Healthcare Management System Setup Complete!
=============================================================================${NC}

${BLUE}📋 Access Information:${NC}
   Main Application: http://$server_ip
   Admin Panel:      http://$server_ip/admin

${BLUE}🔐 Admin Credentials:${NC}
   Check the file: $APP_DIR/admin_credentials.txt
   
${BLUE}🔧 Management Commands:${NC}
   View logs:        sudo journalctl -u laso-gunicorn -f
   Restart app:      sudo systemctl restart laso-gunicorn
   Check status:     sudo systemctl status laso-gunicorn
   
${BLUE}📁 Important Files:${NC}
   Configuration:    $PROJECT_DIR/.env
   Admin Creds:      $APP_DIR/admin_credentials.txt
   Logs:             $LOG_DIR/

${YELLOW}⚠️  Next Steps:${NC}
   1. Change the admin password after first login
   2. Configure email settings in .env for production
   3. Set up SSL/HTTPS for production use
   4. Configure regular backups

${GREEN}🚀 Your healthcare management system is ready to use!${NC}

EOF
}

# =============================================================================
# Main Script Execution
# =============================================================================

main() {
    log_info "Starting LASO Healthcare System VPS setup..."
    
    check_root
    install_system_dependencies
    configure_database
    setup_application_user
    setup_application
    create_environment_config
    run_migrations
    create_admin_user
    configure_gunicorn
    configure_nginx
    configure_firewall
    show_final_info
    
    log_success "Setup completed successfully!"
}

# Show help if requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    cat << EOF
LASO Healthcare System - VPS Setup Script

This script will:
1. Install all required system dependencies
2. Configure PostgreSQL database
3. Set up the Django application
4. Run database migrations
5. Create an admin user
6. Configure Gunicorn and Nginx
7. Set up firewall rules

Usage:
    sudo ./vps-setup-guide.sh

Prerequisites:
- Ubuntu 20.04+ or similar Debian-based system
- Root access (run with sudo)
- Internet connection

EOF
    exit 0
fi

# Run main function
main "$@"