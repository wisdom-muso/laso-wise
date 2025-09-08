#!/bin/bash

# Laso Healthcare Deployment Issues Fix Script
# This script addresses CSS/UI and Celery beat database issues

set -e

echo "🔧 Laso Healthcare Deployment Issues Fix"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Determine docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

print_status "Using Docker Compose command: $DOCKER_COMPOSE"

echo ""
echo "🔍 Applied fixes:"
echo "   ✅ Enhanced WhiteNoise configuration for better static file handling"
echo "   ✅ Updated Celery Beat configuration with proper database settings"
echo "   ✅ Fixed Docker Compose to use PostgreSQL instead of SQLite"
echo "   ✅ Added proper health checks and dependencies"
echo "   ✅ Enhanced logging configuration for better debugging"
echo ""

# Check if .env file exists and update it
if [ -f .env ]; then
    print_status "Updating .env file with recommended settings..."
    
    # Backup existing .env
    cp .env .env.backup
    
    # Update USE_SQLITE setting
    if grep -q "USE_SQLITE=" .env; then
        sed -i 's/USE_SQLITE=.*/USE_SQLITE=False/' .env
    else
        echo "USE_SQLITE=False" >> .env
    fi
    
    # Add DATABASE_URL if not present
    if ! grep -q "DATABASE_URL=" .env; then
        echo "# Database URL will be set automatically in Docker Compose" >> .env
        echo "# DATABASE_URL=postgresql://laso_user:laso_password@db:5432/laso_healthcare" >> .env
    fi
    
    print_success ".env file updated"
else
    print_warning ".env file not found. Please run deploy.sh first to create it."
fi

# Stop existing containers
print_status "Stopping existing containers..."
$DOCKER_COMPOSE down --remove-orphans 2>/dev/null || true

# Clean up old images to ensure fresh build
print_status "Cleaning up old images..."
$DOCKER_COMPOSE down --rmi local 2>/dev/null || true

# Build and start services
print_status "Building and starting services with fixes..."
if ! $DOCKER_COMPOSE up --build -d; then
    print_error "Failed to build and start services. Checking logs..."
    $DOCKER_COMPOSE logs --tail=50
    exit 1
fi

# Wait for database to be ready
print_status "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if $DOCKER_COMPOSE exec -T db pg_isready -U ${POSTGRES_USER:-laso_user} -d ${POSTGRES_DB:-laso_healthcare} 2>/dev/null; then
        print_success "PostgreSQL is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "PostgreSQL failed to start within 30 seconds"
        $DOCKER_COMPOSE logs db
        exit 1
    fi
    echo -n "."
    sleep 1
done

# Wait for web service to be healthy
print_status "Waiting for web service to be healthy..."
for i in {1..60}; do
    if $DOCKER_COMPOSE ps web | grep -q "healthy"; then
        print_success "Web service is healthy!"
        break
    fi
    if [ $i -eq 60 ]; then
        print_warning "Web service health check timeout. Checking logs..."
        $DOCKER_COMPOSE logs web --tail=20
    fi
    echo -n "."
    sleep 2
done

# Check service status
print_status "Checking service status..."
$DOCKER_COMPOSE ps

# Test static files
print_status "Testing static file collection..."
if $DOCKER_COMPOSE exec -T web python manage.py collectstatic --noinput --dry-run; then
    print_success "Static files configuration is correct!"
else
    print_warning "Static files collection test failed. Check configuration."
fi

# Test Celery beat
print_status "Testing Celery beat configuration..."
if $DOCKER_COMPOSE exec -T celery-beat celery -A laso inspect ping; then
    print_success "Celery beat is responding correctly!"
else
    print_warning "Celery beat test failed. Check logs with: $DOCKER_COMPOSE logs celery-beat"
fi

# Show final status
print_success "🎉 Deployment fixes applied successfully!"
echo ""
echo "📋 Service Status:"
$DOCKER_COMPOSE ps
echo ""
echo "🌐 Access your application:"
echo "   - Main Application: http://localhost:8000"
echo "   - Admin Panel: http://localhost:8000/admin"
echo "   - Health Check: http://localhost:8000/health/"
echo ""
echo "🔍 To monitor logs:"
echo "   - All services: $DOCKER_COMPOSE logs -f"
echo "   - Web only: $DOCKER_COMPOSE logs -f web"
echo "   - Celery beat: $DOCKER_COMPOSE logs -f celery-beat"
echo ""
echo "🛑 To stop services:"
echo "   $DOCKER_COMPOSE down"
echo ""

# Test the application
print_status "Testing application health..."
sleep 5
if curl -f http://localhost:8000/health/ >/dev/null 2>&1; then
    print_success "Application health check passed!"
else
    print_warning "Application health check failed. The app might still be starting up."
    print_status "Check logs with: $DOCKER_COMPOSE logs -f web"
fi

echo ""
print_success "✨ Fixes Summary:"
echo "   🎨 CSS/UI Issue: Enhanced WhiteNoise configuration for proper static file serving"
echo "   🔄 Celery Beat Issue: Fixed database configuration and connection handling"
echo "   🐳 Docker: Updated to use PostgreSQL consistently across all services"
echo "   📊 Monitoring: Added better health checks and logging"
echo ""
print_warning "📝 Next Steps for VPS Deployment:"
echo "   1. Copy this fixed codebase to your VPS"
echo "   2. Update your .env file with production settings"
echo "   3. Run this script on your VPS: ./fix_deployment_issues.sh"
echo "   4. Configure your domain/SSL in nginx if needed"