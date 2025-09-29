#!/bin/bash

# Laso Healthcare VPS Deployment Script
# This script deploys the application to the VPS at 65.108.91.110

set -e

# Configuration
VPS_HOST="65.108.91.110"
VPS_USER="root"
APP_DIR="/opt/laso-wise"
BACKUP_DIR="/opt/laso-wise-backup-$(date +%Y%m%d_%H%M%S)"

echo "🚀 Starting deployment to VPS: $VPS_HOST"

# Function to run commands on VPS
run_on_vps() {
    ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_HOST "$1"
}

# Function to copy files to VPS
copy_to_vps() {
    scp -o StrictHostKeyChecking=no -r "$1" $VPS_USER@$VPS_HOST:"$2"
}

echo "📋 Step 1: Checking VPS connection..."
if ! run_on_vps "echo 'VPS connection successful'"; then
    echo "❌ Failed to connect to VPS. Please check your SSH connection."
    exit 1
fi

echo "🐳 Step 2: Installing Docker and Docker Compose on VPS..."
run_on_vps "
    # Update system
    apt-get update
    
    # Install Docker if not already installed
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        systemctl enable docker
        systemctl start docker
    fi
    
    # Install Docker Compose if not already installed
    if ! command -v docker-compose &> /dev/null; then
        curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    
    echo 'Docker and Docker Compose installed successfully'
"

echo "📁 Step 3: Creating application directory on VPS..."
run_on_vps "
    # Backup existing installation if it exists
    if [ -d '$APP_DIR' ]; then
        echo 'Backing up existing installation...'
        cp -r $APP_DIR $BACKUP_DIR
        echo 'Backup created at $BACKUP_DIR'
    fi
    
    # Create application directory
    mkdir -p $APP_DIR
    cd $APP_DIR
"

echo "📤 Step 4: Copying application files to VPS..."
# Create a temporary directory with only necessary files
TEMP_DIR=$(mktemp -d)
cp -r . $TEMP_DIR/
cd $TEMP_DIR

# Remove unnecessary files
rm -rf .git __pycache__ *.pyc .pytest_cache node_modules
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Copy files to VPS
copy_to_vps "$TEMP_DIR/*" "$APP_DIR/"
copy_to_vps "$TEMP_DIR/.*" "$APP_DIR/" 2>/dev/null || true

# Clean up temp directory
rm -rf $TEMP_DIR

echo "🔧 Step 5: Setting up environment on VPS..."
run_on_vps "
    cd $APP_DIR
    
    # Make sure .env file exists
    if [ ! -f .env ]; then
        echo 'Creating .env file...'
        cat > .env << 'EOF'
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this-in-production-$(openssl rand -hex 32)
ALLOWED_HOSTS=localhost,127.0.0.1,65.108.91.110,*

USE_SQLITE=False
POSTGRES_DB=laso_healthcare
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=laso_secure_password_$(openssl rand -hex 16)

REDIS_PASSWORD=redis_secure_password_$(openssl rand -hex 16)

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
LOG_TO_FILE=True
EOF
    fi
    
    # Set proper permissions
    chmod 600 .env
    chmod +x deploy-to-vps.sh
"

echo "🐳 Step 6: Building and starting Docker containers..."
run_on_vps "
    cd $APP_DIR
    
    # Stop existing containers if running
    docker compose down 2>/dev/null || true
    
    # Build and start containers
    docker compose build --no-cache
    docker compose up -d
    
    # Wait for services to be healthy
    echo 'Waiting for services to start...'
    sleep 30
    
    # Check service status
    docker compose ps
"

echo "🗄️ Step 7: Running database migrations..."
run_on_vps "
    cd $APP_DIR
    
    # Run migrations
    docker compose exec -T web python manage.py migrate
    
    # Create superuser if it doesn't exist
    docker compose exec -T web python manage.py shell -c \"
from django.contrib.auth import get_user_model
from users.models import User
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@laso.com', 'admin123', first_name='Admin', last_name='User', user_type='admin')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
\"
    
    # Collect static files
    docker compose exec -T web python manage.py collectstatic --noinput
"

echo "🔥 Step 8: Setting up firewall rules..."
run_on_vps "
    # Install ufw if not already installed
    apt-get install -y ufw
    
    # Configure firewall
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    
    echo 'Firewall configured successfully'
"

echo "🧪 Step 9: Testing deployment..."
if curl -f -s http://$VPS_HOST > /dev/null; then
    echo "✅ Deployment successful! Application is accessible at http://$VPS_HOST"
else
    echo "⚠️ Deployment completed but application may not be fully ready yet."
    echo "Please wait a few minutes and check http://$VPS_HOST"
fi

echo "📊 Step 10: Deployment summary..."
run_on_vps "
    cd $APP_DIR
    echo '=== Docker Container Status ==='
    docker compose ps
    echo ''
    echo '=== Application Logs (last 20 lines) ==='
    docker compose logs --tail=20 web
    echo ''
    echo '=== Disk Usage ==='
    df -h
    echo ''
    echo '=== Memory Usage ==='
    free -h
"

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📝 Important Information:"
echo "   • Application URL: http://$VPS_HOST"
echo "   • Admin Panel: http://$VPS_HOST/admin/"
echo "   • Admin Username: admin"
echo "   • Admin Password: admin123"
echo "   • Application Directory: $APP_DIR"
echo "   • Backup Directory: $BACKUP_DIR (if backup was created)"
echo ""
echo "🔧 Useful Commands:"
echo "   • View logs: ssh $VPS_USER@$VPS_HOST 'cd $APP_DIR && docker compose logs -f'"
echo "   • Restart services: ssh $VPS_USER@$VPS_HOST 'cd $APP_DIR && docker compose restart'"
echo "   • Update application: ./deploy-to-vps.sh"
echo ""
echo "⚠️ Security Notes:"
echo "   • Change the default admin password immediately"
echo "   • Update the SECRET_KEY in .env file"
echo "   • Consider setting up SSL certificates for HTTPS"
echo "   • Review and update database passwords"
echo ""