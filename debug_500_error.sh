#!/bin/bash

echo "🔍 Debugging 500 Server Error on Login Page"
echo "=========================================="

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

echo "📊 Container Status:"
$DOCKER_COMPOSE ps

echo ""
echo "🔍 Checking Web Container Logs:"
echo "================================"
docker logs laso_web --tail=50

echo ""
echo "🔍 Checking Celery Worker Logs:"
echo "==============================="
docker logs laso_celery --tail=20

echo ""
echo "🔍 Checking Database Connection:"
echo "==============================="
docker exec laso_web python manage.py check --database default

echo ""
echo "🔍 Testing Django Shell Access:"
echo "==============================="
docker exec laso_web python manage.py shell -c "
from django.conf import settings
print('DEBUG:', settings.DEBUG)
print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS)
print('SECRET_KEY length:', len(settings.SECRET_KEY))
"

echo ""
echo "🔍 Testing Static Files:"
echo "======================="
docker exec laso_web python manage.py collectstatic --dry-run --noinput

echo ""
echo "🔍 Checking URL Configuration:"
echo "============================="
docker exec laso_web python manage.py show_urls | grep -E "(login|admin)" || echo "show_urls command not available"

echo ""
echo "🌐 Testing HTTP Response:"
echo "======================="
curl -I http://65.108.91.110:8000/login/ || echo "Could not connect to server"

echo ""
echo "📋 Debug Information Complete"