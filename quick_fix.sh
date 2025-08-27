#!/bin/bash

echo "🚀 Quick Fix for Laso Healthcare Containers"
echo "=========================================="

# Stop containers
echo "1. Stopping containers..."
docker-compose down

# Remove specific containers to force rebuild
echo "2. Removing old containers..."
docker-compose rm -f web celery celery-beat

# Remove images to force rebuild
echo "3. Removing old images..."
docker rmi $(docker images -q laso-wise_web laso-wise_celery laso-wise_celery-beat 2>/dev/null) 2>/dev/null || echo "Images not found, continuing..."

# Build web service only (others inherit from same image)
echo "4. Building web service..."
docker-compose build --no-cache web

# Start essential services
echo "5. Starting database and cache..."
docker-compose up -d db redis

# Wait for database
echo "6. Waiting for database..."
sleep 10

# Start web with verbose output
echo "7. Starting web service..."
docker-compose up -d web

# Wait and check
sleep 5
echo "8. Checking web service..."
docker logs laso_web --tail=20

# Start Celery services
echo "9. Starting Celery services..."
docker-compose up -d celery celery-beat

sleep 5
echo "10. Checking Celery services..."
docker logs laso_celery --tail=10
docker logs laso_celery_beat --tail=10

echo ""
echo "✅ Quick fix complete!"
echo "Check the logs above for any errors."