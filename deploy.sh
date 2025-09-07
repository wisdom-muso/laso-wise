#!/bin/bash

# Laso Healthcare Deployment Script
# This script helps deploy the Laso Healthcare system with PostgreSQL 17

set -e

echo "🚀 Starting Laso Healthcare Deployment..."

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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Determine docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

print_status "Using Docker Compose command: $DOCKER_COMPOSE"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating a default one..."
    cat > .env << EOF
# Database Configuration
POSTGRES_DB=laso_healthcare
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=laso_secure_password_$(date +%s)

# Redis Configuration
REDIS_PASSWORD=redis_secure_password_$(date +%s)

# Django Configuration
SECRET_KEY=django_secret_key_$(openssl rand -base64 32 2>/dev/null || echo "fallback_secret_key_$(date +%s)")
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,65.108.91.110

# Email Configuration (optional - update with your settings)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True

# AI Configuration (optional)
OPENAI_API_KEY=
HUGGINGFACE_API_KEY=
EOF
    print_success ".env file created with secure defaults"
else
    print_status ".env file already exists"
fi

# Stop any running containers
print_status "Stopping any running containers..."
$DOCKER_COMPOSE down --remove-orphans 2>/dev/null || true

# Build and start services
print_status "Building and starting services with PostgreSQL 17..."
if ! $DOCKER_COMPOSE up --build -d; then
    print_error "Failed to build and start services. Check Docker logs for details."
    print_status "Showing recent logs..."
    $DOCKER_COMPOSE logs --tail=50
    exit 1
fi

# Wait for database to be ready
print_status "Waiting for PostgreSQL 17 to be ready..."
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

# Check if services are healthy
print_status "Checking service health..."
$DOCKER_COMPOSE ps

# Run migrations
print_status "Running database migrations..."
if ! $DOCKER_COMPOSE exec -T web python manage.py migrate; then
    print_error "Database migrations failed"
    $DOCKER_COMPOSE logs web
    exit 1
fi

# Create superuser if it doesn't exist
print_status "Setting up default users..."
$DOCKER_COMPOSE exec -T web python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()

# Create admin user if it doesn't exist
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@laso-healthcare.com',
        password='admin123',
        user_type='admin',
        first_name='System',
        last_name='Administrator'
    )
    print("Admin user created")
else:
    print("Admin user already exists")
EOF

# Collect static files
print_status "Collecting static files..."
if ! $DOCKER_COMPOSE exec -T web python manage.py collectstatic --noinput; then
    print_warning "Static file collection failed, but continuing..."
fi

# Show final status
print_success "🎉 Deployment completed successfully!"
echo ""
echo "📋 Service Status:"
$DOCKER_COMPOSE ps
echo ""
echo "🌐 Access your application:"
echo "   - Main Application: http://localhost:8000"
echo "   - Admin Panel: http://localhost:8000/admin"
echo "   - Health Check: http://localhost:8000/health/"
echo ""
echo "👤 Default Login Credentials:"
echo "   - Username: admin"
echo "   - Password: admin123"
echo ""
echo "📊 To view logs:"
echo "   $DOCKER_COMPOSE logs -f"
echo ""
echo "🛑 To stop services:"
echo "   $DOCKER_COMPOSE down"

print_warning "Remember to update your .env file with production settings!"

# Test the application
print_status "Testing application health..."
sleep 5
if curl -f http://localhost:8000/health/ >/dev/null 2>&1; then
    print_success "Application health check passed!"
else
    print_warning "Application health check failed. The app might still be starting up."
    print_status "Check logs with: $DOCKER_COMPOSE logs -f web"
fi