#!/bin/bash

# =============================================================================
# LASO Healthcare System - Quick VPS Deployment Script
# =============================================================================
# Quick deployment script for VPS: 65.108.91.110
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 LASO Healthcare System - Quick VPS Deployment${NC}"
echo -e "${BLUE}=================================================${NC}"

# Check if running on VPS
VPS_IP="65.108.91.110"
CURRENT_IP=$(curl -s ifconfig.me || echo "unknown")
echo -e "${BLUE}Current IP: $CURRENT_IP${NC}"
echo -e "${BLUE}Target VPS: $VPS_IP${NC}"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Please install Docker first."
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    error "Docker Compose is not available. Please install Docker Compose."
fi

log "Setting up environment for VPS deployment..."

# Create .env file for VPS
if [[ -f ".env.vps.production" ]]; then
    cp .env.vps.production .env
    log "Using VPS production environment"
elif [[ -f ".env.vps" ]]; then
    cp .env.vps .env
    log "Using VPS environment"
else
    error "No VPS environment file found!"
fi

log "Stopping existing containers..."
docker compose down --remove-orphans || true

log "Building and starting services..."
docker compose up -d --build

log "Waiting for services to start..."
sleep 30

log "Checking service status..."
docker compose ps

log "Running database migrations..."
docker compose exec -T web python manage.py migrate

log "Collecting static files..."
docker compose exec -T web python manage.py collectstatic --noinput

log "Creating admin user..."
docker compose exec -T web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@laso.com', '8gJW48Tz8YXDrF57')
    print('Admin user created!')
else:
    print('Admin user already exists')
"

log "Testing application..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302"; then
    log "✅ Application is responding!"
else
    echo -e "${YELLOW}⚠️  Application may not be responding correctly${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo ""
echo -e "${BLUE}📱 Access your application:${NC}"
echo -e "${YELLOW}   🌐 Web: http://$VPS_IP/${NC}"
echo -e "${YELLOW}   🔐 Admin: http://$VPS_IP/admin/${NC}"
echo ""
echo -e "${BLUE}👤 Admin credentials:${NC}"
echo -e "${YELLOW}   Username: admin${NC}"
echo -e "${YELLOW}   Password: 8gJW48Tz8YXDrF57${NC}"
echo ""
echo -e "${BLUE}🛠️  Management commands:${NC}"
echo -e "${YELLOW}   Status: docker compose ps${NC}"
echo -e "${YELLOW}   Logs: docker compose logs -f${NC}"
echo -e "${YELLOW}   Restart: docker compose restart${NC}"
echo ""