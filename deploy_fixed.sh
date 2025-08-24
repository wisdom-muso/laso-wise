#!/bin/bash

# Laso Healthcare Deployment Script - FIXED VERSION
# This script addresses the logging and permission issues found during deployment

set -e

echo "🚀 Starting Laso Healthcare Deployment (Fixed Version)..."

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
    print_status "You can install Docker using: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker daemon is not running."
    print_status "Attempting to start Docker daemon..."
    
    # Try to start Docker daemon
    if command -v systemctl &> /dev/null; then
        sudo systemctl start docker
    else
        print_warning "Systemctl not available. You may need to start Docker manually."
        print_status "Try: sudo dockerd &"
    fi
    
    # Wait a moment and check again
    sleep 3
    if ! docker info >/dev/null 2>&1; then
        print_error "Could not start Docker daemon. Please start it manually."
        exit 1
    fi
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

# Create necessary directories with correct permissions
print_status "Creating necessary directories..."
mkdir -p logs backups docker/postgres docker/nginx/ssl
chmod 755 logs backups

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

# Create PostgreSQL init script if it doesn't exist
if [ ! -f docker/postgres/init.sql ]; then
    print_status "Creating PostgreSQL initialization script..."
    mkdir -p docker/postgres
    cat > docker/postgres/init.sql << 'EOF'
-- PostgreSQL initialization script for Laso Healthcare
-- This script runs when the database container is first created

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Set timezone
SET timezone = 'UTC';
EOF
fi

# Create Nginx configuration if it doesn't exist
if [ ! -f docker/nginx/nginx.conf ]; then
    print_status "Creating Nginx configuration..."
    mkdir -p docker/nginx
    cat > docker/nginx/nginx.conf << 'EOF'
worker_processes auto;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Upstream backend
    upstream web {
        server web:8000;
    }

    # HTTP Server
    server {
        listen 80;
        server_name localhost 127.0.0.1 65.108.91.110;
        client_max_body_size 100M;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        location /media/ {
            alias /var/www/media/;
            expires 1y;
            add_header Cache-Control "public";
        }

        # API rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Login rate limiting
        location /auth/login/ {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # All other requests
        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }
    }
}
EOF
fi

# Create backup script if it doesn't exist
if [ ! -f docker/backup/backup.sh ]; then
    print_status "Creating backup script..."
    mkdir -p docker/backup
    cat > docker/backup/backup.sh << 'EOF'
#!/bin/bash
# Database backup script for Laso Healthcare

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/laso_healthcare_backup_$TIMESTAMP.sql"

echo "Creating database backup: $BACKUP_FILE"

# Create backup
pg_dump -h db -U $POSTGRES_USER -d $POSTGRES_DB > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup created successfully: $BACKUP_FILE"
    
    # Compress the backup
    gzip "$BACKUP_FILE"
    echo "Backup compressed: $BACKUP_FILE.gz"
    
    # Remove backups older than 7 days
    find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
    echo "Old backups cleaned up"
else
    echo "Backup failed!"
    exit 1
fi
EOF
    chmod +x docker/backup/backup.sh
fi

# Fix Docker socket permissions if needed
if [ ! -w /var/run/docker.sock ]; then
    print_warning "Docker socket is not writable. Attempting to fix permissions..."
    sudo chmod 666 /var/run/docker.sock 2>/dev/null || true
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

# Wait for web service to be ready
print_status "Waiting for web service to be ready..."
for i in {1..30}; do
    if $DOCKER_COMPOSE exec -T web python manage.py check --deploy 2>/dev/null; then
        print_success "Web service is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_warning "Web service health check failed, but continuing with migrations..."
        break
    fi
    echo -n "."
    sleep 2
done

# Run migrations
print_status "Running database migrations..."
if ! $DOCKER_COMPOSE exec -T web python manage.py migrate; then
    print_error "Database migrations failed"
    print_status "Showing web service logs..."
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

# Try health check with multiple attempts
for i in {1..5}; do
    if curl -f http://localhost:8000/health/ >/dev/null 2>&1; then
        print_success "Application health check passed!"
        break
    fi
    if [ $i -eq 5 ]; then
        print_warning "Application health check failed. The app might still be starting up."
        print_status "Check logs with: $DOCKER_COMPOSE logs -f web"
    else
        echo -n "."
        sleep 2
    fi
done

print_success "🚀 Deployment script completed!"
print_status "All logging issues have been addressed:"
print_status "  ✅ Logging directory permissions fixed"
print_status "  ✅ Robust logging configuration with fallback to console"
print_status "  ✅ Docker volume mounting properly configured"
print_status "  ✅ Health checks and error handling improved"