#!/bin/bash

# LASO Healthcare - Database Startup Fix Script
# This script diagnoses and fixes PostgreSQL container startup issues

set -e

echo "🔍 LASO Healthcare - Database Startup Diagnostic & Fix"
echo "======================================================"

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

# Check if Docker is running
print_status "Checking Docker status..."
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi
print_success "Docker is running"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found in current directory"
    exit 1
fi

# Stop all containers first
print_status "Stopping all containers..."
docker-compose down --remove-orphans

# Remove any existing volumes if they're corrupted
print_warning "Checking for corrupted volumes..."
if docker volume ls | grep -q "laso-wise_postgres_data"; then
    print_status "Found existing postgres volume. Checking if it needs to be reset..."
    read -p "Do you want to reset the PostgreSQL database? This will delete all data. (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing PostgreSQL volume..."
        docker volume rm laso-wise_postgres_data || true
        print_success "PostgreSQL volume removed"
    fi
fi

# Check environment variables
print_status "Checking environment variables..."
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating default environment file..."
    cat > .env << EOF
# Database Configuration
POSTGRES_DB=laso_healthcare
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=laso_secure_password_2024

# Redis Configuration
REDIS_PASSWORD=redis_secure_password_2024

# Django Configuration
SECRET_KEY=django-insecure-change-this-in-production-$(openssl rand -hex 32)
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,65.108.91.110,host.docker.internal,*
USE_SQLITE=False

# Email Configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True

# API Keys (optional)
OPENAI_API_KEY=
HUGGINGFACE_API_KEY=

# Logging
LOG_TO_FILE=True
EOF
    print_success "Created .env file with default values"
else
    print_success ".env file exists"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p docker/postgres
mkdir -p docker/nginx
mkdir -p backups
mkdir -p logs

# Create PostgreSQL initialization script if it doesn't exist
if [ ! -f "docker/postgres/init.sql" ]; then
    print_status "Creating PostgreSQL initialization script..."
    cat > docker/postgres/init.sql << 'EOF'
-- LASO Healthcare Database Initialization
-- This script sets up the initial database configuration

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE laso_healthcare'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'laso_healthcare')\gexec

-- Connect to the database
\c laso_healthcare;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE laso_healthcare TO laso_user;
EOF
    print_success "Created PostgreSQL initialization script"
fi

# Create nginx configuration if it doesn't exist
if [ ! -f "docker/nginx/nginx.conf" ]; then
    print_status "Creating Nginx configuration..."
    mkdir -p docker/nginx
    cat > docker/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    upstream web {
        server web:8000;
    }

    server {
        listen 80;
        server_name _;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Media files
        location /media/ {
            alias /var/www/media/;
            expires 1y;
            add_header Cache-Control "public";
        }

        # Proxy to Django
        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
    }
}
EOF
    print_success "Created Nginx configuration"
fi

# Start PostgreSQL service first
print_status "Starting PostgreSQL service..."
docker-compose up -d db

# Wait for PostgreSQL to be ready
print_status "Waiting for PostgreSQL to be ready..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose exec -T db pg_isready -U laso_user -d laso_healthcare >/dev/null 2>&1; then
        print_success "PostgreSQL is ready!"
        break
    fi
    echo -n "."
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    print_error "PostgreSQL failed to start within $timeout seconds"
    print_status "Checking PostgreSQL logs..."
    docker-compose logs db
    exit 1
fi

# Start Redis
print_status "Starting Redis service..."
docker-compose up -d redis

# Wait for Redis to be ready
print_status "Waiting for Redis to be ready..."
timeout=30
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose exec -T redis redis-cli --raw incr ping >/dev/null 2>&1; then
        print_success "Redis is ready!"
        break
    fi
    echo -n "."
    sleep 1
    counter=$((counter + 1))
done

if [ $counter -ge $timeout ]; then
    print_error "Redis failed to start within $timeout seconds"
    print_status "Checking Redis logs..."
    docker-compose logs redis
    exit 1
fi

# Build and start web service
print_status "Building and starting web service..."
docker-compose up -d --build web

# Wait for web service to be ready
print_status "Waiting for web service to be ready..."
timeout=120
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:3000/liveness/ >/dev/null 2>&1; then
        print_success "Web service is ready!"
        break
    fi
    echo -n "."
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    print_warning "Web service health check failed, but continuing..."
fi

# Run database migrations
print_status "Running database migrations..."
if docker-compose exec -T web python manage.py migrate; then
    print_success "Database migrations completed successfully"
else
    print_error "Database migrations failed"
    print_status "Checking web service logs..."
    docker-compose logs web
    exit 1
fi

# Create superuser if needed
print_status "Checking for superuser..."
if ! docker-compose exec -T web python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('Superuser exists' if User.objects.filter(is_superuser=True).exists() else 'No superuser')" | grep -q "Superuser exists"; then
    print_status "Creating superuser..."
    docker-compose exec -T web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@laso.com', 'admin123', user_type='admin')
    print('Superuser created: admin/admin123')
else:
    print('Admin user already exists')
"
fi

# Start remaining services
print_status "Starting remaining services..."
docker-compose up -d

# Final health check
print_status "Performing final health check..."
sleep 10

print_status "Service status:"
docker-compose ps

print_status "Testing database connection..."
if docker-compose exec -T web python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"; then
    print_success "Database connection test passed"
else
    print_error "Database connection test failed"
    exit 1
fi

print_success "Database startup fix completed successfully!"
print_status "Your application should now be accessible at:"
print_status "  - Main application: http://localhost:3000"
print_status "  - Nginx proxy: http://localhost:8081"
print_status "  - Admin interface: http://localhost:3000/admin/"
print_status "  - Default admin credentials: admin/admin123"

echo ""
print_status "To monitor logs, use:"
echo "  docker-compose logs -f"
echo ""
print_status "To stop all services, use:"
echo "  docker-compose down"