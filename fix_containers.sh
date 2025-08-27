#!/bin/bash

echo "Fixing Docker containers for Laso Healthcare..."

# Stop all containers
echo "Stopping containers..."
docker-compose down

# Rebuild containers with the fixes
echo "Rebuilding containers..."
docker-compose build --no-cache

# Start containers
echo "Starting containers..."
docker-compose up -d

# Wait a moment for containers to start
sleep 10

# Check container status
echo "Container status:"
docker-compose ps

echo ""
echo "Checking logs for any remaining issues:"
echo "=== Web container logs ==="
docker logs laso_web --tail=10

echo ""
echo "=== Celery worker logs ==="
docker logs laso_celery --tail=10

echo ""
echo "=== Celery beat logs ==="
docker logs laso_celery_beat --tail=10

echo ""
echo "Fix script completed. The following issues have been addressed:"
echo "1. Fixed Celery module name from 'laso' to 'meditrack'"
echo "2. Added Celery configuration files"
echo "3. Added host.docker.internal to ALLOWED_HOSTS"
echo "4. Static files should be collected during container build"