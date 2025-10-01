#!/bin/bash

# =============================================================================
# LASO Healthcare - Registration Fix Script for VPS Deployment
# =============================================================================
# This script fixes common registration issues on VPS deployment

set -e  # Exit on any error

echo "🏥 LASO Healthcare - Registration Fix Script"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    print_warning "Running as root. This is not recommended for production."
fi

# Check if Docker is running
print_step "Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi
print_status "Docker is running"

# Check if docker-compose is available
print_step "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install it first."
    exit 1
fi
print_status "Docker Compose is available"

# Check if we're in the correct directory
if [[ ! -f "manage.py" ]] || [[ ! -f "docker-compose.production.yml" ]]; then
    print_error "Please run this script from the LASO project root directory"
    exit 1
fi

# Backup current environment file
print_step "Backing up current environment..."
if [[ -f ".env" ]]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    print_status "Environment file backed up"
fi

# Copy the VPS environment file
print_step "Setting up VPS environment configuration..."
if [[ -f ".env.vps" ]]; then
    cp .env.vps .env
    print_status "VPS environment configuration applied"
else
    print_warning ".env.vps not found, using .env.production"
    if [[ -f ".env.production" ]]; then
        cp .env.production .env
    else
        print_error "No environment file found. Please create .env file manually."
        exit 1
    fi
fi

# Update CSRF trusted origins with current IP
print_step "Updating CSRF trusted origins..."
VPS_IP=$(curl -s ifconfig.me || echo "65.108.91.110")
print_status "Detected VPS IP: $VPS_IP"

# Update .env file with current IP
sed -i "s/65\.108\.91\.110/$VPS_IP/g" .env
print_status "Updated environment with current IP"

# Stop existing containers
print_step "Stopping existing containers..."
docker-compose -f docker-compose.production.yml down --remove-orphans
print_status "Containers stopped"

# Remove old volumes if requested
read -p "Do you want to reset the database? This will delete all data! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Removing database volumes..."
    docker volume rm laso-wise_postgres_data 2>/dev/null || true
    docker volume rm laso-wise_redis_data 2>/dev/null || true
    print_status "Database volumes removed"
fi

# Build and start containers
print_step "Building and starting containers..."
docker-compose -f docker-compose.production.yml up -d --build
print_status "Containers started"

# Wait for services to be ready
print_step "Waiting for services to start..."
sleep 30

# Check service health
print_step "Checking service health..."
docker-compose -f docker-compose.production.yml ps

# Run migrations
print_step "Running database migrations..."
docker-compose -f docker-compose.production.yml exec -T web python manage.py migrate --noinput
print_status "Migrations completed"

# Collect static files
print_step "Collecting static files..."
docker-compose -f docker-compose.production.yml exec -T web python manage.py collectstatic --noinput
print_status "Static files collected"

# Create superuser if it doesn't exist
print_step "Creating admin user..."
docker-compose -f docker-compose.production.yml exec -T web python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@laso.com', '8gJW48Tz8YXDrF57')
    print('✅ Admin user created successfully')
else:
    print('ℹ️  Admin user already exists')
EOF

# Run registration diagnostic
print_step "Running registration diagnostic..."
docker-compose -f docker-compose.production.yml exec -T web python debug_registration.py

# Test registration endpoint
print_step "Testing registration endpoint..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/core/patients/register/ || echo "000")
if [[ "$RESPONSE" == "200" ]]; then
    print_status "Registration endpoint is accessible"
else
    print_warning "Registration endpoint returned HTTP $RESPONSE"
fi

# Display final information
echo ""
echo "============================================="
echo "🎉 Registration Fix Complete!"
echo "============================================="
echo ""
echo "📋 SYSTEM STATUS:"
echo "  • VPS IP: $VPS_IP"
echo "  • Main URL: http://$VPS_IP/"
echo "  • Admin Panel: http://$VPS_IP/admin/"
echo "  • Registration: http://$VPS_IP/register/"
echo "  • Direct Registration: http://$VPS_IP/core/patients/register/"
echo ""
echo "🔐 ADMIN CREDENTIALS:"
echo "  • Username: admin"
echo "  • Password: 8gJW48Tz8YXDrF57"
echo ""
echo "🔧 TROUBLESHOOTING:"
echo "  • Check logs: docker-compose -f docker-compose.production.yml logs web"
echo "  • Restart services: docker-compose -f docker-compose.production.yml restart"
echo "  • Run diagnostic: docker-compose -f docker-compose.production.yml exec web python debug_registration.py"
echo ""
echo "📝 REGISTRATION TESTING:"
echo "  1. Go to: http://$VPS_IP/register/"
echo "  2. Fill out the form with unique username and email"
echo "  3. Check for detailed error messages if registration fails"
echo "  4. Check container logs for backend errors"
echo ""

# Final health check
print_step "Performing final health check..."
if curl -s http://localhost/health/ > /dev/null; then
    print_status "✅ Application is healthy and ready!"
else
    print_warning "⚠️  Health check failed. Check the logs for issues."
fi

echo "🏥 Registration fix script completed!"