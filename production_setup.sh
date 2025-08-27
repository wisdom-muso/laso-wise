#!/bin/bash

echo "🚀 Setting up Laso Healthcare for Production..."

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating production .env file..."
    cat > .env << 'EOF'
# Django Configuration
DEBUG=False
SECRET_KEY=production-secret-key-change-me-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,65.108.91.110,host.docker.internal,*

# Database Configuration
USE_SQLITE=True

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Logging
LOG_TO_FILE=True

# Redis Configuration
REDIS_PASSWORD=production_redis_password
REDIS_URL=redis://:production_redis_password@redis:6379/0

# Optional API Keys
OPENAI_API_KEY=
HUGGINGFACE_API_KEY=

# Database Settings (for PostgreSQL if needed)
POSTGRES_DB=laso_healthcare
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=secure_postgres_password
EOF
    echo "✅ Production .env file created"
fi

# Build and start containers
echo "Building and starting production containers..."
docker-compose up -d --build

# Wait for containers to be ready
echo "Waiting for containers to start..."
sleep 30

# Run database migrations
echo "Running database migrations..."
docker-compose exec web python manage.py migrate --noinput

# Create superuser (only essential setup, no demo data)
echo "Setting up essential configuration..."
docker-compose exec web python manage.py setup_laso_healthcare --create-superuser --setup-notifications

# Clean up any existing demo data
echo "Cleaning up demo data..."
docker-compose exec web python manage.py cleanup_demo_data --confirm

# Collect static files
echo "Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput

# Check container status
echo "Container status:"
docker-compose ps

echo ""
echo "✅ Production setup complete!"
echo ""
echo "🔐 Default admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🌐 Access your application at:"
echo "   - http://localhost:8000 (local)"
echo "   - http://65.108.91.110:8000 (remote server)"
echo ""
echo "📝 Important security notes:"
echo "   1. Change the admin password immediately"
echo "   2. Update the SECRET_KEY in .env file"
echo "   3. Configure proper email settings"
echo "   4. Set up SSL/HTTPS for production"
echo ""
echo "📊 To view logs: docker-compose logs -f web"
echo "🛑 To stop: docker-compose down"