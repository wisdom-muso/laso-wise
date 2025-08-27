#!/bin/bash

echo "Starting Laso Healthcare Docker setup..."

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down

# Remove old images (optional, uncomment if needed)
# docker-compose down --rmi all

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Django Configuration
DEBUG=False
SECRET_KEY=django-insecure-docker-production-key-change-me-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,65.108.91.110,host.docker.internal,*

# Database Configuration (using SQLite in Docker for simplicity)
USE_SQLITE=True

# Email Configuration (set to console backend for now)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Logging
LOG_TO_FILE=True

# Redis Configuration
REDIS_PASSWORD=redis_password
REDIS_URL=redis://:redis_password@redis:6379/0

# Optional API Keys (can be empty for basic functionality)
OPENAI_API_KEY=
HUGGINGFACE_API_KEY=

# Database Settings (for PostgreSQL if needed)
POSTGRES_DB=laso_healthcare
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=laso_password
EOF
fi

# Build and start containers
echo "Building and starting containers..."
docker-compose up -d --build

# Wait for containers to be ready
echo "Waiting for containers to start..."
sleep 30

# Check container status
echo "Container status:"
docker-compose ps

# Check logs
echo "Recent logs:"
docker-compose logs --tail=20 web

echo "Setup complete! You can access the application at:"
echo "- http://localhost:8000 (direct)"
echo "- http://65.108.91.110:8000 (if on remote server)"
echo ""
echo "To view logs: docker-compose logs -f web"
echo "To stop: docker-compose down"