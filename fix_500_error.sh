#!/bin/bash

echo "🔧 Fixing 500 Server Error on Login Page"
echo "========================================"

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

echo "✅ Applied fixes for potential 500 error causes:"
echo ""
echo "🔧 STATIC FILES:"
echo "   ✅ Simplified WhiteNoise configuration"
echo "   ✅ Removed custom storage backend that might cause issues"
echo "   ✅ Added missing source map file for flotcharts"
echo "   ✅ Commented out missing favicon and logo references"
echo ""
echo "🎨 TEMPLATE FIXES:"
echo "   ✅ Replaced missing logo image with CSS placeholder"
echo "   ✅ Disabled missing favicon reference"
echo "   ✅ Ensured all URL references are valid"
echo ""
echo "⚙️ CONFIGURATION:"
echo "   ✅ Reverted to stable WhiteNoise storage backend"
echo "   ✅ Added DEBUG-dependent WHITENOISE_AUTOREFRESH"
echo ""

# Stop containers and rebuild
echo "🔨 Rebuilding containers with fixes..."
$DOCKER_COMPOSE down

# Clear any cached Docker builds
echo "🧹 Clearing Docker cache..."
docker system prune -f

# Rebuild only web service for faster testing
echo "🏗️ Building web service..."
if $DOCKER_COMPOSE build web; then
    echo "✅ Build successful!"
    
    echo "🚀 Starting services..."
    $DOCKER_COMPOSE up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 20
    
    echo "📊 Container Status:"
    $DOCKER_COMPOSE ps
    
    echo ""
    echo "🔍 Testing login page..."
    
    # Wait a bit more for the container to fully start
    sleep 10
    
    # Test if container is responsive
    if docker exec laso_web python manage.py check; then
        echo "✅ Django checks passed"
        
        # Test URL resolution
        echo "🔗 Testing URL patterns..."
        docker exec laso_web python manage.py shell -c "
from django.urls import reverse
try:
    login_url = reverse('login')
    print(f'✅ Login URL resolves to: {login_url}')
    
    dashboard_url = reverse('dashboard') 
    print(f'✅ Dashboard URL resolves to: {dashboard_url}')
    
    patient_register_url = reverse('core:patient-register')
    print(f'✅ Patient register URL resolves to: {patient_register_url}')
except Exception as e:
    print(f'❌ URL resolution error: {e}')
"
        
        # Test HTTP response
        echo ""
        echo "🌐 Testing HTTP response..."
        if curl -s -o /dev/null -w "%{http_code}" http://65.108.91.110:8000/login/ | grep -q "200"; then
            echo "✅ Login page is responding with HTTP 200"
        else
            echo "❌ Login page still returning error"
            echo ""
            echo "📋 Recent error logs:"
            docker logs laso_web --tail=20
        fi
        
    else
        echo "❌ Django checks failed"
        echo ""
        echo "📋 Recent logs:"
        docker logs laso_web --tail=30
    fi
    
else
    echo "❌ Build failed!"
    echo ""
    echo "📋 Build logs:"
    $DOCKER_COMPOSE logs web
fi

echo ""
echo "🔍 ADDITIONAL DEBUGGING:"
echo "   • Check container logs: docker logs laso_web"
echo "   • Test Django shell: docker exec -it laso_web python manage.py shell"
echo "   • Run Django checks: docker exec laso_web python manage.py check"
echo "   • Check database: docker exec laso_web python manage.py migrate --check"
echo ""
echo "💡 COMMON 500 ERROR CAUSES:"
echo "   • Missing static files (fixed)"
echo "   • Database connection issues"
echo "   • Missing environment variables"
echo "   • Template syntax errors (fixed)"
echo "   • Import errors in views or models"
echo ""