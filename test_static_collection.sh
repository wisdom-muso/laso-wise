#!/bin/bash

echo "🧪 Testing Static File Collection Fix"
echo "===================================="

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
echo "🔍 Applied fixes:"
echo "   ✅ Created missing source map file: static/assets/plugins/custom/flotcharts/jquery.flot.js.map"
echo "   ✅ Updated WhiteNoise storage to use ForgivingCompressedStaticFilesStorage"
echo "   ✅ Added WhiteNoise configuration to skip .map files during compression"
echo "   ✅ Fixed .env file configuration"
echo ""

echo "🔨 Testing Docker build..."
echo ""

# Stop any running containers
echo "1. Stopping existing containers..."
$DOCKER_COMPOSE down

# Clean up old images
echo "2. Removing old images..."
$DOCKER_COMPOSE down --rmi local

# Build only the web service to test static collection
echo "3. Building web service..."
$DOCKER_COMPOSE build web

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ BUILD SUCCESSFUL!"
    echo ""
    echo "🚀 Starting services..."
    $DOCKER_COMPOSE up -d
    
    echo ""
    echo "⏳ Waiting for services to start..."
    sleep 15
    
    echo ""
    echo "📊 Container Status:"
    $DOCKER_COMPOSE ps
    
    echo ""
    echo "🔍 Quick health check:"
    if docker ps --format "table {{.Names}}" | grep -q "laso_web"; then
        echo "✅ Web container is running"
        echo ""
        echo "📋 Recent logs:"
        docker logs laso_web --tail=10
    else
        echo "❌ Web container failed to start"
        echo ""
        echo "📋 Build logs:"
        docker logs laso_web --tail=20
    fi
    
else
    echo ""
    echo "❌ BUILD FAILED!"
    echo ""
    echo "📋 Checking for additional static file issues..."
    
    # Try to collect static files in a temporary container to see the exact error
    echo "Running collectstatic in isolation..."
    docker run --rm -v $(pwd):/app -w /app python:3.12-slim bash -c "
        apt-get update && apt-get install -y libpq-dev build-essential
        pip install -r requirements.txt
        python manage.py collectstatic --noinput --verbosity=2
    "
fi

echo ""
echo "📝 TROUBLESHOOTING TIPS:"
echo "   • If build still fails, check for other missing .map files"
echo "   • Verify all static files are present in static/ directory"
echo "   • Check Django settings for STATICFILES_DIRS configuration"
echo "   • Review WhiteNoise documentation for advanced configuration"
echo ""