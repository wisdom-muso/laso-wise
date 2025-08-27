#!/bin/bash

echo "🔧 Fixing Docker containers for Laso Healthcare..."
echo "================================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Determine which docker compose command to use
if command_exists docker-compose; then
    DOCKER_COMPOSE="docker-compose"
elif command_exists docker && docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Neither docker-compose nor docker compose found!"
    exit 1
fi

echo "Using: $DOCKER_COMPOSE"

# Stop all containers and remove them
echo "🛑 Stopping and removing all containers..."
$DOCKER_COMPOSE down --remove-orphans

# Remove all images to force rebuild
echo "🗑️  Removing old images to force complete rebuild..."
$DOCKER_COMPOSE down --rmi all --volumes --remove-orphans

# Prune Docker to clean up
echo "🧹 Cleaning up Docker system..."
docker system prune -f

# Rebuild containers with the fixes
echo "🔨 Rebuilding containers with fixes..."
$DOCKER_COMPOSE build --no-cache --pull

# Start only essential services first
echo "🚀 Starting database and cache services..."
$DOCKER_COMPOSE up -d db redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 15

# Start web service
echo "🌐 Starting web service..."
$DOCKER_COMPOSE up -d web

# Wait for web service to be ready
echo "⏳ Waiting for web service to start..."
sleep 10

# Start Celery services
echo "🔄 Starting Celery services..."
$DOCKER_COMPOSE up -d celery celery-beat

# Wait a moment for all services to stabilize
echo "⏳ Waiting for all services to stabilize..."
sleep 15

# Check container status
echo ""
echo "📊 Container status:"
$DOCKER_COMPOSE ps

echo ""
echo "🔍 Checking logs for any remaining issues:"
echo "=== Web container logs ==="
docker logs laso_web --tail=15

echo ""
echo "=== Celery worker logs ==="
docker logs laso_celery --tail=15

echo ""
echo "=== Celery beat logs ==="
docker logs laso_celery_beat --tail=15

echo ""
echo "✅ Fix script completed. The following issues have been addressed:"
echo "1. 🔧 Fixed Celery module name from 'laso' to 'meditrack'"
echo "2. 📝 Added Celery configuration files (meditrack/celery.py, meditrack/__init__.py)"
echo "3. 🌐 Added host.docker.internal to ALLOWED_HOSTS"
echo "4. 📁 Static files should be collected during container build"
echo "5. 🗑️  Forced complete rebuild by removing old images"
echo ""
echo "🌐 If successful, your application should be available at:"
echo "   http://localhost (via nginx)"
echo "   http://localhost:8000 (direct to Django)"
echo ""
echo "🔍 To check service health: $DOCKER_COMPOSE ps"
echo "📋 To view all logs: $DOCKER_COMPOSE logs -f"