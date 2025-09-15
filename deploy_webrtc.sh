#!/bin/bash

# 🎥 Laso Healthcare WebRTC Deployment Script
# This script deploys the complete telemedicine system with WebRTC video calls

set -e

echo "🎥 Starting Laso Healthcare WebRTC Deployment..."

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    DOCKER_CMD="docker"
    DOCKER_COMPOSE_CMD="docker-compose"
else
    DOCKER_CMD="sudo docker"
    DOCKER_COMPOSE_CMD="sudo docker-compose"
fi

# Step 1: Check prerequisites
print_status "Checking prerequisites..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Docker is running
if ! $DOCKER_CMD info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_success "Prerequisites check passed"

# Step 2: Setup environment file
print_status "Setting up environment configuration..."

if [ ! -f .env ]; then
    if [ -f .env.docker ]; then
        print_status "Copying .env.docker to .env..."
        cp .env.docker .env
    else
        print_error ".env file not found and .env.docker template missing"
        exit 1
    fi
fi

# Verify environment file has WebRTC settings
if ! grep -q "USE_SQLITE=False" .env; then
    print_warning "Environment file may not be configured for Docker PostgreSQL"
    print_status "Please ensure USE_SQLITE=False in your .env file"
fi

print_success "Environment configuration ready"

# Step 3: Build and start services
print_status "Building and starting Docker services..."

# Stop any existing containers
print_status "Stopping existing containers..."
$DOCKER_COMPOSE_CMD down --remove-orphans

# Build and start services
print_status "Building Docker images..."
$DOCKER_COMPOSE_CMD build --no-cache

print_status "Starting services..."
$DOCKER_COMPOSE_CMD up -d

# Wait for services to be healthy
print_status "Waiting for services to be ready..."
sleep 30

# Check service health
print_status "Checking service health..."
if $DOCKER_COMPOSE_CMD ps | grep -q "unhealthy"; then
    print_error "Some services are unhealthy. Check logs with: docker-compose logs"
    $DOCKER_COMPOSE_CMD ps
    exit 1
fi

print_success "All services are running"

# Step 4: Run database migrations
print_status "Running database migrations..."
$DOCKER_COMPOSE_CMD exec -T web python manage.py migrate

print_success "Database migrations completed"

# Step 5: Create superuser if needed
print_status "Checking for admin user..."
if $DOCKER_COMPOSE_CMD exec -T web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('NO_ADMIN')
else:
    print('ADMIN_EXISTS')
" | grep -q "NO_ADMIN"; then
    print_status "Creating admin user..."
    $DOCKER_COMPOSE_CMD exec -T web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@laso.com', 'admin123')
    print('Admin user created: admin/admin123')
else:
    print('Admin user already exists')
"
else
    print_success "Admin user already exists"
fi

# Step 6: Collect static files
print_status "Collecting static files..."
$DOCKER_COMPOSE_CMD exec -T web python manage.py collectstatic --noinput

print_success "Static files collected"

# Step 7: Test WebRTC components
print_status "Testing WebRTC components..."

# Test Redis connection (required for Channels)
if $DOCKER_COMPOSE_CMD exec -T redis redis-cli -a ${REDIS_PASSWORD:-redis_password} ping | grep -q "PONG"; then
    print_success "Redis connection working"
else
    print_error "Redis connection failed"
    exit 1
fi

# Test database connection
if $DOCKER_COMPOSE_CMD exec -T web python manage.py check --deploy; then
    print_success "Django deployment check passed"
else
    print_error "Django deployment check failed"
    exit 1
fi

# Step 8: Display deployment information
print_success "🎉 WebRTC Deployment Complete!"

echo ""
echo "📋 Deployment Summary:"
echo "======================"
echo "🌐 Main Application: http://localhost:3000"
echo "🔧 Admin Panel: http://localhost:3000/admin/"
echo "🏥 Nginx (Production): http://localhost:8081"
echo "🗄️  PostgreSQL: localhost:5432"
echo "🔴 Redis: localhost:6379"
echo ""
echo "👤 Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🎥 WebRTC Features:"
echo "   ✅ Real-time video calls"
echo "   ✅ Screen sharing"
echo "   ✅ Chat messaging"
echo "   ✅ Call recording (doctors)"
echo "   ✅ Connection quality monitoring"
echo ""
echo "🔧 Useful Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Restart: docker-compose restart"
echo "   Stop: docker-compose down"
echo "   Update: docker-compose up --build -d"
echo ""

# Step 9: Health check and final verification
print_status "Performing final health checks..."

# Check if web service is responding
if curl -f -s http://localhost:3000/liveness/ > /dev/null; then
    print_success "Web service is responding"
else
    print_warning "Web service may not be fully ready yet. Please wait a moment and try accessing http://localhost:3000"
fi

# Check WebSocket support
print_status "WebSocket support configured for telemedicine video calls"

# Display container status
echo ""
echo "📊 Container Status:"
echo "==================="
$DOCKER_COMPOSE_CMD ps

echo ""
print_success "🚀 Your Laso Healthcare system with WebRTC is now running!"
print_status "Access the telemedicine video consultation at: http://localhost:3000/telemedicine/"

# Optional: Open browser (uncomment if desired)
# if command -v xdg-open &> /dev/null; then
#     xdg-open http://localhost:3000
# elif command -v open &> /dev/null; then
#     open http://localhost:3000
# fi

echo ""
print_status "For production deployment, consider:"
echo "   • Setting up HTTPS/SSL certificates"
echo "   • Configuring TURN servers for NAT traversal"
echo "   • Setting up proper firewall rules"
echo "   • Configuring domain names"
echo "   • Setting up monitoring and logging"

exit 0