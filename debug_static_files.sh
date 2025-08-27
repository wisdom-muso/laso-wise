#!/bin/bash

echo "🔍 Debugging Static Files in Docker Container..."
echo "=============================================="

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

echo ""
echo "1. Checking if web container is running..."
if docker ps --format "table {{.Names}}" | grep -q "laso_web"; then
    echo "✅ Web container is running"
else
    echo "❌ Web container is not running"
    exit 1
fi

echo ""
echo "2. Checking static files in container..."
echo "--- Source static directory ---"
docker exec laso_web ls -la /app/static/ || echo "❌ /app/static/ not found"

echo ""
echo "--- Collected static directory ---"
docker exec laso_web ls -la /app/staticfiles/ || echo "❌ /app/staticfiles/ not found"

echo ""
echo "3. Checking specific missing files..."
echo "--- plugins.bundle.css ---"
docker exec laso_web find /app -name "plugins.bundle.css" 2>/dev/null || echo "❌ plugins.bundle.css not found"

echo ""
echo "--- style.bundle.css ---"
docker exec laso_web find /app -name "style.bundle.css" 2>/dev/null || echo "❌ style.bundle.css not found"

echo ""
echo "--- theme.css ---"
docker exec laso_web find /app -name "theme.css" 2>/dev/null || echo "❌ theme.css not found"

echo ""
echo "4. Testing collectstatic command..."
docker exec laso_web python manage.py collectstatic --noinput --verbosity=2

echo ""
echo "5. Checking Django settings for static files..."
docker exec laso_web python manage.py shell -c "
from django.conf import settings
print('STATIC_URL:', settings.STATIC_URL)
print('STATIC_ROOT:', settings.STATIC_ROOT)
print('STATICFILES_DIRS:', settings.STATICFILES_DIRS)
print('STATICFILES_STORAGE:', getattr(settings, 'STATICFILES_STORAGE', 'Not set'))
"

echo ""
echo "6. Checking file permissions..."
docker exec laso_web ls -la /app/staticfiles/ | head -10

echo ""
echo "7. Testing static file serving..."
echo "Making a test request to a static file..."
docker exec laso_web curl -I http://localhost:8000/static/assets/plugins/global/plugins.bundle.css || echo "❌ Static file request failed"

echo ""
echo "🔍 Debug complete. If static files are collected but still not serving,"
echo "   the issue might be with WhiteNoise configuration or URL routing."