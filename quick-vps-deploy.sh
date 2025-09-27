#!/bin/bash

# Quick VPS Deployment Script for LASO Healthcare
# Run this on your VPS at 65.108.91.110

echo "🏥 LASO Healthcare - Quick VPS Deployment"
echo "=========================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Please run as a regular user with sudo privileges, not as root"
   exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "⚠️  Docker installed. Please log out and log back in, then run this script again."
    exit 0
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "🔧 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 3000
sudo ufw --force enable

# Stop conflicting services
echo "🛑 Stopping conflicting services..."
sudo systemctl stop apache2 2>/dev/null || true
sudo systemctl disable apache2 2>/dev/null || true

# Use VPS environment
echo "⚙️  Setting up environment..."
cp .env.vps .env

# Deploy services
echo "🚀 Deploying services..."
docker-compose down --remove-orphans || true
docker-compose up -d --build

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 30

# Run migrations
echo "🗄️  Running database migrations..."
docker-compose exec web python manage.py migrate

# Create admin user
echo "👤 Creating admin user..."
docker-compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@laso.com', 'admin123')
    print('✅ Admin user created!')
else:
    print('ℹ️  Admin user already exists')
"

# Check status
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "🌐 Access your application:"
echo "   Main App:    http://65.108.91.110:3000"
echo "   Admin Panel: http://65.108.91.110:3000/admin/"
echo ""
echo "🔐 Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "⚠️  IMPORTANT: Change the admin password immediately!"
echo ""
echo "🛠️  Useful commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Restart:      docker-compose restart"
echo "   Stop:         docker-compose down"
echo ""
echo "🏥 Your healthcare management system is ready!"