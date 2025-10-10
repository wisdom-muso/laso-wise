#!/bin/bash

# =============================================================================
# LASO Healthcare System - Test Deployment Script
# =============================================================================
# Quick test to verify the password fix works
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing LASO Healthcare System Deployment${NC}"
echo -e "${BLUE}=============================================${NC}"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    error "Docker is not installed"
fi

if ! docker compose version &> /dev/null; then
    error "Docker Compose is not available"
fi

log "Setting up test environment..."

# Use production environment
if [[ -f ".env.production" ]]; then
    cp .env.production .env
    log "Using production environment"
else
    error "No .env.production file found!"
fi

log "Stopping any existing containers..."
docker compose -f docker-compose.production.yml down --remove-orphans || true

log "Starting database and Redis only for testing..."
docker compose -f docker-compose.production.yml up -d db redis

log "Waiting for services to start..."
sleep 15

log "Testing database connection..."
if docker compose -f docker-compose.production.yml exec -T db pg_isready -U laso_user -d laso_healthcare; then
    log "✅ Database connection successful!"
else
    error "❌ Database connection failed!"
fi

log "Testing Redis connection..."
if docker compose -f docker-compose.production.yml exec -T redis redis-cli -a laso2403 ping | grep -q "PONG"; then
    log "✅ Redis connection successful!"
else
    error "❌ Redis connection failed!"
fi

log "Starting web application..."
docker compose -f docker-compose.production.yml up -d web

log "Waiting for web application..."
sleep 20

log "Testing web application..."
if docker compose -f docker-compose.production.yml exec -T web python manage.py check; then
    log "✅ Django application check passed!"
else
    error "❌ Django application check failed!"
fi

log "Running database migrations..."
if docker compose -f docker-compose.production.yml exec -T web python manage.py migrate; then
    log "✅ Database migrations successful!"
else
    error "❌ Database migrations failed!"
fi

log "Testing database connectivity from Django..."
if docker compose -f docker-compose.production.yml exec -T web python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful!')"; then
    log "✅ Django database connection successful!"
else
    error "❌ Django database connection failed!"
fi

log "Cleaning up test containers..."
docker compose -f docker-compose.production.yml down

echo ""
echo -e "${GREEN}🎉 All tests passed! Password configuration is working correctly.${NC}"
echo ""
echo -e "${BLUE}✅ Database authentication: FIXED${NC}"
echo -e "${BLUE}✅ Redis authentication: FIXED${NC}"
echo -e "${BLUE}✅ Django connectivity: WORKING${NC}"
echo ""
echo -e "${YELLOW}You can now deploy to your VPS using:${NC}"
echo -e "${YELLOW}  ./deploy.sh${NC}"
echo ""