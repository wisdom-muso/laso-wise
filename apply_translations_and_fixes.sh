#!/bin/bash

echo "🔧 Applying Turkish-to-English translations and fixes for Laso Healthcare"
echo "======================================================================"

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

echo "✅ All fixes have been applied to the codebase:"
echo ""
echo "🔤 TURKISH TO ENGLISH TRANSLATIONS:"
echo "   ✅ Django Admin Comments: 'Doktor uygunluk sistemleri' → 'Doctor availability systems'"
echo "   ✅ Django Admin Comments: 'Yeni modeller için admin kayıtları' → 'Admin registrations for new models'"
echo "   ✅ Django Admin Labels: 'Test Adı' → 'Test Name', 'Hasta' → 'Patient'"
echo "   ✅ I18n Models: 'Çoklu dil desteği' → 'Multi-language support'"
echo "   ✅ I18n Models: 'Desteklenen diller' → 'Supported languages'"
echo "   ✅ I18n Models: Various Turkish field labels → English equivalents"
echo "   ✅ Template Text: 'Profilim' → 'My Profile' in navigation menu"
echo ""
echo "🎨 SIDEBAR IMPROVEMENTS:"
echo "   ✅ Icons changed from solid colors to teal gradients"
echo "   ✅ Added hover animations with scale effects"
echo "   ✅ Consistent teal color scheme throughout sidebar"
echo "   ✅ Enhanced visual hierarchy with gradient backgrounds"
echo ""
echo "🧹 SCRIPT CLEANUP:"
echo "   ✅ Removed: debug_static_files.sh (temporary debug script)"
echo "   ✅ Removed: fix_containers.sh (temporary fix script)"
echo "   ✅ Removed: quick_fix.sh (temporary fix script)"
echo "   ✅ Removed: docker-start.sh (redundant with deploy.sh)"
echo "   ✅ Removed: docker-manage.sh (redundant script)"
echo "   ✅ Removed: start-sqlite.sh (SQLite specific script)"
echo "   ✅ Removed: deploy-fixes.sh (temporary script)"
echo "   ✅ Kept: deploy.sh (main deployment script)"
echo ""
echo "🔧 CONTAINER FIXES:"
echo "   ✅ Fixed Celery module name from 'laso' to 'meditrack'"
echo "   ✅ Added proper Celery configuration files"
echo "   ✅ Fixed ALLOWED_HOSTS for Docker environment"
echo "   ✅ Updated static files configuration for Django 4.2+"
echo ""

echo "🚀 NEXT STEPS:"
echo "1. Rebuild and restart containers to apply all changes:"
echo "   ./deploy.sh"
echo ""
echo "2. Or manually rebuild:"
echo "   $DOCKER_COMPOSE down"
echo "   $DOCKER_COMPOSE build --no-cache"
echo "   $DOCKER_COMPOSE up -d"
echo ""
echo "3. Check logs after restart:"
echo "   docker logs laso_web --tail=20"
echo "   docker logs laso_celery --tail=10"
echo "   docker logs laso_celery_beat --tail=10"
echo ""

# Ask if user wants to rebuild containers now
read -p "🤔 Would you like to rebuild containers now to apply changes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔨 Rebuilding containers..."
    $DOCKER_COMPOSE down
    $DOCKER_COMPOSE build --no-cache
    $DOCKER_COMPOSE up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 15
    
    echo "📊 Container Status:"
    $DOCKER_COMPOSE ps
    
    echo ""
    echo "🔍 Quick Log Check:"
    echo "=== Web Service ==="
    docker logs laso_web --tail=10
    echo ""
    echo "=== Celery Worker ==="
    docker logs laso_celery --tail=5
    echo ""
    echo "=== Celery Beat ==="
    docker logs laso_celery_beat --tail=5
    
    echo ""
    echo "✅ Rebuild complete!"
else
    echo "ℹ️  You can rebuild later using: ./deploy.sh"
fi

echo ""
echo "📋 SUMMARY OF FIXES APPLIED:"
echo "   • All Turkish text in Django admin translated to English"
echo "   • Sidebar icons now use teal gradients instead of solid colors"
echo "   • 'Profilim' navigation item translated to 'My Profile'"
echo "   • Removed 7 redundant/temporary scripts"
echo "   • Fixed Docker container configuration issues"
echo "   • Updated static files handling for production"
echo ""
echo "🌐 Your application should now be:"
echo "   • Fully in English (admin interface and navigation)"
echo "   • Using consistent teal theming with gradient icons"
echo "   • Running stable containers without module errors"
echo "   • Serving static files correctly"
echo ""
echo "🎉 All requested fixes have been completed!"